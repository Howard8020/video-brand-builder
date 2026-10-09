"""Profile routes — manage the user's brand profile (company info, spokesperson, continuity).

Replaces the old "Add Client" workflow. A user sets up their brand once,
and every project uses their brand profile as continuity defaults.

Also handles customer asset uploads (logo, reference images) to GCS or local fallback.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import SessionLocal
from auth import get_current_user
from models import User

logger = logging.getLogger("vbb.profile")
router = APIRouter(prefix="/api/profile", tags=["profile"])

# ── Allowed image types ──────────────────────────────────────────────
_ALLOWED_MIME_TYPES = {"image/png", "image/jpeg"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_GCS_BUCKET = "vbb-customer-assets"
_UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"

# ── GCS client (lazy, cached) ────────────────────────────────────────
_gcs_client = None
_gcs_enabled = False


def _get_gcs_bucket():
    """Return a GCS bucket handle, or None if GCP is not available."""
    global _gcs_client, _gcs_enabled
    if _gcs_client is not None:
        return _gcs_client.bucket(_GCS_BUCKET)

    try:
        import google.auth
        from google.cloud import storage

        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        project = os.getenv("GCP_PROJECT_ID", "")
        if project:
            _gcs_client = storage.Client(project=project, credentials=creds)
            _gcs_enabled = True
            bucket = _gcs_client.bucket(_GCS_BUCKET)
            # Ensure the bucket exists (will raise if not found — caller handles)
            bucket.exists()
            logger.info("GCS enabled: bucket=%s", _GCS_BUCKET)
            return bucket
    except Exception as exc:
        logger.warning("GCS not available, falling back to local storage: %s", exc)

    _gcs_enabled = False
    return None


def _gcs_or_fallback():
    """Return (bucket, local_path, use_gcs) — try GCS first, fall back to local."""
    bucket = _get_gcs_bucket()
    if bucket is not None:
        return bucket, _UPLOADS_DIR, True
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return None, _UPLOADS_DIR, False


# ── Pydantic models ──────────────────────────────────────────────────

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

    # Customer-uploaded assets
    reference_image_path: str = ""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Core profile CRUD ────────────────────────────────────────────────

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


# ── Helpers ──────────────────────────────────────────────────────────

def _validate_image(file: UploadFile) -> None:
    """Validate MIME type and size of an uploaded image. Raises HTTPException on failure."""
    if file.content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Allowed: {', '.join(_ALLOWED_MIME_TYPES)}",
        )
    # Read first chunk to check size
    chunk = file.file.read(_MAX_FILE_SIZE + 1)
    if len(chunk) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")
    # Reset stream position for later reads
    file.file.seek(0)


def _extract_ext(content_type: str) -> str:
    """Return the file extension (including dot) for a known MIME type."""
    if content_type == "image/png":
        return ".png"
    return ".jpg"  # image/jpeg default


def _store_file(
    file: UploadFile,
    user_id: str,
    asset_type: str,  # "logo" or "reference-image"
) -> str:
    """Store the uploaded file to GCS (preferred) or local uploads/ directory.

    Returns the stored path (GCS URI or local relative path).
    """
    ext = _extract_ext(file.content_type)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    unique_id = uuid.uuid4().hex[:8]
    blob_name = f"{user_id}/{asset_type}/{timestamp}_{unique_id}{ext}"

    bucket, local_dir, use_gcs = _gcs_or_fallback()
    contents = file.file.read()

    if use_gcs:
        bucket.blob(blob_name).upload_from_string(contents, content_type=file.content_type)
        stored = f"gs://{_GCS_BUCKET}/{blob_name}"
        logger.info("Uploaded %s to GCS: %s", asset_type, stored)
    else:
        dest = local_dir / blob_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(contents)
        stored = f"uploads/{blob_name}"
        logger.info("Uploaded %s locally: %s", asset_type, stored)

    return stored


def _delete_file(stored_path: str) -> None:
    """Delete a previously stored file (GCS or local). Silently succeeds if missing."""
    if not stored_path:
        return

    if stored_path.startswith("gs://"):
        # GCS path: gs://bucket/blob_name
        try:
            import google.cloud.storage as gcs
            project = os.getenv("GCP_PROJECT_ID", "")
            creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            client = gcs.Client(project=project, credentials=creds)
            parts = stored_path.replace("gs://", "").split("/", 1)
            if len(parts) == 2:
                bucket_name, blob_name = parts
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
                logger.info("Deleted GCS blob: %s", stored_path)
        except Exception as exc:
            logger.warning("Failed to delete GCS blob %s: %s", stored_path, exc)
    else:
        # Local path — strip "uploads/" prefix to get relative path
        relative = stored_path.replace("uploads/", "", 1) if stored_path.startswith("uploads/") else stored_path
        local_path = _UPLOADS_DIR / relative
        try:
            if local_path.exists():
                local_path.unlink()
                logger.info("Deleted local file: %s", local_path)
        except Exception as exc:
            logger.warning("Failed to delete local file %s: %s", local_path, exc)


# ── Upload endpoints ─────────────────────────────────────────────────

@router.post("/logo")
def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a logo image (PNG/JPEG, max 10MB). Stores to GCS or local fallback."""
    _validate_image(file)
    stored = _store_file(file, current_user.id, "logo")

    user = db.query(User).filter(User.id == current_user.id).first()
    profile = user.brand_profile or {}
    profile["logo_path"] = stored
    user.brand_profile = profile
    db.commit()

    return {"path": stored, "status": "ok"}


@router.post("/reference-image")
def upload_reference_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a reference image (PNG/JPEG, max 10MB). Stores to GCS or local fallback."""
    _validate_image(file)
    stored = _store_file(file, current_user.id, "reference-image")

    user = db.query(User).filter(User.id == current_user.id).first()
    profile = user.brand_profile or {}
    profile["reference_image_path"] = stored
    user.brand_profile = profile
    db.commit()

    return {"path": stored, "status": "ok"}


# ── Delete endpoints ─────────────────────────────────────────────────

@router.delete("/logo")
def delete_logo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the uploaded logo file and clear logo_path from the brand profile."""
    user = db.query(User).filter(User.id == current_user.id).first()
    profile = user.brand_profile or {}
    path = profile.get("logo_path", "")

    if not path:
        raise HTTPException(status_code=404, detail="No logo file to delete")

    _delete_file(path)
    profile["logo_path"] = ""
    user.brand_profile = profile
    db.commit()

    return {"status": "ok", "message": "Logo deleted"}


@router.delete("/reference-image")
def delete_reference_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the uploaded reference image and clear reference_image_path from the brand profile."""
    user = db.query(User).filter(User.id == current_user.id).first()
    profile = user.brand_profile or {}
    path = profile.get("reference_image_path", "")

    if not path:
        raise HTTPException(status_code=404, detail="No reference image to delete")

    _delete_file(path)
    profile["reference_image_path"] = ""
    user.brand_profile = profile
    db.commit()

    return {"status": "ok", "message": "Reference image deleted"}