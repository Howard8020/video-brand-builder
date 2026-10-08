"""Assemble a project's rendered segments into one postable video.

A render produces one MP4 per segment, but TikTok and YouTube Shorts need a
single file. This joins the segments in order, normalises audio loudness and
writes a platform-ready MP4 next to (but separate from) the raw segments.
"""
import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import SessionLocal
from models import Project, RenderJob, User
from services.assembly import assemble, ffmpeg_available
from services.storage import assembled_dir, generated_dir

logger = logging.getLogger("vbb.assemble")
router = APIRouter(prefix="/api/projects", tags=["assemble"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _slug(text: str, fallback: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", (text or "").strip()).strip("-").lower()
    return slug[:60] or fallback


@router.post("/{project_id}/assemble")
def assemble_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Join all succeeded segments of this project into one video."""
    proj = db.query(Project).filter(
        Project.id == project_id, Project.user_id == user.id
    ).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    jobs = (
        db.query(RenderJob)
        .filter(RenderJob.project_id == project_id, RenderJob.user_id == user.id)
        .order_by(RenderJob.segment_index)
        .all()
    )
    if not jobs:
        raise HTTPException(status_code=400, detail="Nothing rendered yet for this project")

    not_done = [j for j in jobs if j.status != "succeeded"]
    if not_done:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{len(not_done)} of {len(jobs)} segments are not finished "
                f"(statuses: {sorted({j.status for j in not_done})}). "
                "Assemble once every segment has succeeded."
            ),
        )

    if not ffmpeg_available():
        raise HTTPException(
            status_code=500,
            detail="ffmpeg is not available on this host — cannot assemble.",
        )

    # video_url looks like /generated/render_<uuid>.mp4; resolve it against the
    # configured generated dir rather than trusting the stored path blindly.
    gen_dir = generated_dir()
    segment_paths = []
    missing = []
    for job in jobs:
        if not job.video_url:
            missing.append(f"segment {job.segment_index}: no file recorded")
            continue
        filename = Path(job.video_url).name
        candidate = gen_dir / filename
        if not candidate.exists():
            missing.append(f"segment {job.segment_index}: {filename} not on disk")
            continue
        segment_paths.append(candidate)

    if missing:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot assemble — some segment files are missing: "
                + "; ".join(missing)
            ),
        )

    client_name = (proj.brief or {}).get("clientName") or ""
    out_name = f"{_slug(client_name, 'ad')}-{project_id}.mp4"
    out_path = assembled_dir() / out_name

    try:
        info = assemble(segment_paths, out_path)
    except RuntimeError as exc:
        logger.error("assembly failed for project %s: %s", project_id, exc)
        raise HTTPException(status_code=502, detail=f"Assembly failed: {exc}")

    return {
        "project_id": project_id,
        "url": f"/assembled/{out_name}",
        "filename": out_name,
        "segment_count": info.get("segment_count"),
        "duration": info.get("duration"),
        "size_bytes": info.get("size_bytes"),
        "width": info.get("width"),
        "height": info.get("height"),
        "has_audio": info.get("has_audio"),
        "method": info.get("method"),
        "loudness_target_lufs": info.get("loudness_target_lufs"),
    }


@router.get("/{project_id}/assemble")
def assembled_status(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report whether an assembled video already exists for this project."""
    proj = db.query(Project).filter(
        Project.id == project_id, Project.user_id == user.id
    ).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    client_name = (proj.brief or {}).get("clientName") or ""
    existing = assembled_dir() / f"{_slug(client_name, 'ad')}-{project_id}.mp4"
    if not existing.exists():
        return {"assembled": False}

    from services.assembly import probe
    return {
        "assembled": True,
        "url": f"/assembled/{existing.name}",
        "filename": existing.name,
        "size_bytes": existing.stat().st_size,
        **{k: v for k, v in probe(existing).items() if k in ("duration", "width", "height", "has_audio")},
    }