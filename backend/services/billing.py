"""Billing service — credit checking and deduction for VBB Veo render tier.

Ported from spotlight-contractor/backend/services/billing.py.
Simplified: no daily_budget/campaign concept. Charges flat per render.
"""
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.credit import CreditBalance

logger = logging.getLogger("vbb.billing")

# Flat per-ad pricing (not per-second)
RENDER_PRICE_CENTS = {"standard": 999, "pro": 2999}


def get_or_create_credit_balance(user_id: str, db: Session) -> CreditBalance:
    """Get the user's credit balance, creating a zero-balance row if none exists."""
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


def require_sufficient_credits(user_id: str, tier: str, db: Session) -> None:
    """Check user has enough credits for one render, then reserve them.

    Raises 402 HTTPException if insufficient.
    """
    required = RENDER_PRICE_CENTS.get(tier, RENDER_PRICE_CENTS["standard"])
    balance = get_or_create_credit_balance(user_id, db)

    if balance.balance_cents < required:
        shortage_cents = required - balance.balance_cents
        raise HTTPException(
            status_code=402,
            detail=(
                f"Insufficient credits. You need ${required/100:.2f} to "
                f"render this ad. Your balance is ${balance.balance_cents/100:.2f}. "
                f"Please add ${shortage_cents/100:.2f} more."
            ),
        )

    balance.balance_cents -= required
    db.commit()
    logger.info(
        "Reserved $%.2f for render (tier=%s, user=%s). Remaining: $%.2f",
        required / 100.0,
        tier,
        user_id,
        balance.balance_cents / 100.0,
    )


def refund_credits(user_id: str, tier: str, db: Session) -> None:
    """Refund the tier price back to the user's balance (on render failure)."""
    amount = RENDER_PRICE_CENTS.get(tier, RENDER_PRICE_CENTS["standard"])
    balance = get_or_create_credit_balance(user_id, db)
    balance.balance_cents += amount
    db.commit()
    logger.info("Refunded $%.2f to user %s after render failure", amount / 100.0, user_id)
