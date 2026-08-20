"""Profile routes — manage the user's brand profile (company info, spokesperson, continuity).

Replaces the old "Add Client" workflow. A user sets up their brand once,
and every project uses their brand profile as continuity defaults.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import SessionLocal
from auth import get_current_user
from models import User

logger = logging.getLogger("vbb.profile")
router = APIRouter(prefix="/api/profile", tags=["profile"])


class BrandProfile(BaseModel):
    company_name: str = ""
    website: str = ""
    service_category: str = ""
    brand_notes: str = ""
    logo_path: str = ""  # URL or path after upload

    # Spokesperson / continuity
    spokesperson: str = ""
    delivery: str = ""
    setting: str = ""
    lighting: str = ""
    brand_elements: str = ""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's brand profile."""
    # Fresh-read to avoid stale identity-map cache from get_current_user
    user = db.query(User).filter(User.id == current_user.id).first()
    profile = user.brand_profile if user else None
    if not profile:
        return BrandProfile().model_dump()
    return profile


@router.put("")
def update_profile(
    payload: BrandProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's brand profile."""
    # Re-attach user to this session and save
    user = db.query(User).filter(User.id == current_user.id).first()
    user.brand_profile = payload.model_dump()
    db.commit()
    return {"status": "ok", "profile": payload.model_dump()}
