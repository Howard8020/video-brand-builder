"""Stripe billing routes — credit prepay model for VBB Veo render tier.

Flow:
1. User buys credits via /create-checkout → Stripe Checkout session
2. User completes payment → webhook checkout.session.completed
3. Webhook adds credits to user's CreditBalance
4. Render route gated behind sufficient balance (see billing.py)

Ported from spotlight-contractor/backend/routes/payments.py.
"""
import os
import json
import logging
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models.credit import CreditBalance
from models import User, ProcessedStripeSession
from auth import get_current_user
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("vbb.payments")
router = APIRouter(prefix="/api/payments", tags=["payments"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

stripe.api_key = STRIPE_SECRET_KEY

# Credits are 1:1 with cents
PRICING_TIERS = {
    "starter": {
        "label": "Starter",
        "credits": 2000,
        "amount_cents": 2000,
        "description": "$20 — 2,000 credits (good for ~2 Standard renders)",
        "popular": False,
    },
    "growth": {
        "label": "Growth",
        "credits": 5500,
        "amount_cents": 5000,
        "description": "$50 — 5,500 credits (save 10% — ~5-6 Standard renders)",
        "popular": True,
    },
    "scale": {
        "label": "Scale",
        "credits": 18000,
        "amount_cents": 15000,
        "description": "$150 — 18,000 credits (save 20% — ~18 Standard renders)",
        "popular": False,
    },
}


class CheckoutRequest(BaseModel):
    amount_cents: int
    success_path: str = "/billing?checkout=success"
    cancel_path: str = "/pricing"


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class BalanceResponse(BaseModel):
    balance_cents: int
    lifetime_purchased_cents: int


class PricingTier(BaseModel):
    label: str
    credits: int
    amount_cents: int
    description: str
    popular: bool


class PricingResponse(BaseModel):
    tiers: dict[str, PricingTier]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_credit_balance(user_id: str, db: Session) -> CreditBalance:
    balance = db.query(CreditBalance).filter(CreditBalance.user_id == user_id).first()
    if not balance:
        balance = CreditBalance(
            user_id=user_id,
            balance_cents=0,
            lifetime_purchased_cents=0,
        )
        db.add(balance)
        db.commit()
        db.refresh(balance)
    return balance


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    if req.amount_cents < 500:
        raise HTTPException(status_code=400, detail="Minimum purchase is $5.00.")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Video Brand Builder Render Credits",
                            "description": f"{req.amount_cents} render credits",
                        },
                        "unit_amount": req.amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "user_id": str(current_user.id),
                "amount_cents": str(req.amount_cents),
                "type": "credit_purchase",
            },
            success_url=f"{FRONTEND_URL}{req.success_path}",
            cancel_url=f"{FRONTEND_URL}{req.cancel_path}",
            customer_email=current_user.email,
        )
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id,
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe checkout failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Stripe checkout failed: {e}")


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    balance = get_or_create_credit_balance(current_user.id, db)
    return BalanceResponse(
        balance_cents=balance.balance_cents,
        lifetime_purchased_cents=balance.lifetime_purchased_cents,
    )


@router.get("/pricing", response_model=PricingResponse)
def get_pricing():
    tiers = {key: PricingTier(**tier) for key, tier in PRICING_TIERS.items()}
    return PricingResponse(tiers=tiers)


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await _handle_checkout_completed(session, db)

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        logger.info("Checkout session expired: %s", session.get("id"))

    return {"status": "received"}


async def _handle_checkout_completed(session: dict, db: Session):
    metadata = session.get("metadata", {})
    if metadata.get("type") != "credit_purchase":
        logger.info("Ignoring non-credit checkout: %s", session.get("id"))
        return

    user_id_str = metadata.get("user_id")
    amount_cents_str = metadata.get("amount_cents")

    if not user_id_str or not amount_cents_str:
        logger.warning("Missing metadata on checkout session %s", session.get("id"))
        return

    try:
        amount_cents = int(amount_cents_str)
    except (ValueError, TypeError):
        logger.error("Invalid metadata values on session %s", session.get("id"))
        return

    payment_status = session.get("payment_status")
    if payment_status != "paid":
        logger.warning(
            "Checkout session %s has payment_status=%s, not crediting",
            session.get("id"), payment_status,
        )
        return

    # Idempotency guard. Stripe retries deliveries — on timeout, on non-2xx, and
    # when someone hits "Resend" in the dashboard — so the same completed session
    # can arrive more than once. Crediting on every delivery would hand out the
    # purchase amount repeatedly. The unique primary key on session_id makes this
    # insert itself the lock: first delivery wins, later ones hit the constraint
    # and are skipped.
    session_id = session.get("id")
    if not session_id:
        logger.error("Completed session has no id — refusing to credit")
        return

    try:
        db.add(
            ProcessedStripeSession(
                session_id=session_id,
                user_id=user_id_str,
                amount_cents=amount_cents,
            )
        )
        db.flush()
    except IntegrityError:
        db.rollback()
        logger.info(
            "Duplicate delivery for session %s — already credited, skipping",
            session_id,
        )
        return

    balance = get_or_create_credit_balance(user_id_str, db)
    balance.balance_cents += amount_cents
    balance.lifetime_purchased_cents += amount_cents
    db.commit()
    logger.info(
        "Credited $%.2f (%d credits) to user %s. New balance: $%.2f",
        amount_cents / 100.0, amount_cents, user_id_str,
        balance.balance_cents / 100.0,
    )
