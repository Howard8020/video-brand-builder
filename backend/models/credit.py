"""CreditBalance model — tracks prepaid credit balance for gating Veo renders.

Ported from spotlight-contractor/backend/models/credit.py.
1 credit = 1 cent. A Standard render costs 999 credits ($9.99).
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class CreditBalance(Base):
    __tablename__ = "credit_balances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False
    )
    balance_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_purchased_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="credit_balance")

    def __repr__(self):
        suf = f"user={self.user_id} balance=${self.balance_cents/100:.2f}"
        return f"<CreditBalance {suf}>"
