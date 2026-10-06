from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    brand_profile = Column(JSON, nullable=True)

    credit_balance = relationship("CreditBalance", back_populates="user", uselist=False)

    first_name = Column(String, nullable=True)
    source_asset = Column(String, default='vbb', nullable=False)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime(timezone=True), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)


class Client(Base):
    __tablename__ = "clients"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    brand_notes = Column(String, nullable=True)
    saved_continuity = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    status = Column(String, default="draft")
    brief = Column(JSON, nullable=True)
    script = Column(JSON, nullable=True)
    continuity = Column(JSON, nullable=True)
    scenes = Column(JSON, nullable=True)
    prompts = Column(JSON, nullable=True)
    versions = Column(JSON, nullable=True)
    source_script = Column(String, nullable=True)
    adaptation_note = Column(String, nullable=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProcessedStripeSession(Base):
    """Idempotency ledger for Stripe webhook fulfillment.

    Stripe retries webhook deliveries (on timeouts, non-2xx, or manual resend),
    and the same `checkout.session.completed` event can arrive more than once.
    Without a record of what we have already credited, each duplicate delivery
    silently adds the purchase amount to the user's balance again — free
    credits, real money.

    The primary key on `session_id` makes the insert itself the lock: the first
    delivery wins, every later delivery hits a unique violation and is skipped.
    """

    __tablename__ = "processed_stripe_sessions"

    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True)
    amount_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id = Column(String, primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    tier = Column(String, default="standard")
    vertex_operation_name = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | running | succeeded | failed
    video_url = Column(String, nullable=True)
    cost_cents_charged = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
