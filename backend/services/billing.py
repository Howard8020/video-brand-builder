"""Billing service — credit checking and deduction for VBB Veo render tier.

Ported from spotlight-contractor/backend/services/billing.py.
Simplified: no daily_budget/campaign concept. Charges flat per render.
"""
import logging
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.credit import CreditBalance

logger = logging.getLogger("vbb.billing")

# Flat per-ad pricing (not per-second)
RENDER_PRICE_CENTS = {"standard": 999, "pro": 2999}

# Internal-use switch. Video Brand Builders is used in-house to produce our own
# ad videos, so there is no customer to bill. With this on, the credit check and
# the deduction are skipped entirely and the payment code is left intact but
# dormant. Off by default: a missing or malformed value keeps the paid path.
#
#   VBB_RENDER_BYPASS_CREDITS=true  -> renders are not metered or charged
#
# NOTE: with the credit gate disabled, nothing else bounds GCP spend per
# account other than the render rate limit (services/ratelimit.py). Keep that
# limit set, and keep a GCP budget alert configured.
_BYPASS_FLAG = "VBB_RENDER_BYPASS_CREDITS"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def credits_bypassed() -> bool:
    """True when rendering should run unmetered (internal production mode)."""
    return os.getenv(_BYPASS_FLAG, "").strip().lower() in _TRUE_VALUES


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
    if credits_bypassed():
        logger.info("Credit check bypassed (internal mode) — render not metered")
        return

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
    if credits_bypassed():
        # Nothing was deducted, so there is nothing to give back.
        return

    amount = RENDER_PRICE_CENTS.get(tier, RENDER_PRICE_CENTS["standard"])
    balance = get_or_create_credit_balance(user_id, db)
    balance.balance_cents += amount
    db.commit()
    logger.info("Refunded $%.2f to user %s after render failure", amount / 100.0, user_id)
