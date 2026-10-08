"""Render routes — submit segment prompts to Vertex AI Veo for video generation.

Only accessible after Gate 2 approval (project status = approved).
Credits are reserved up front, refunded on failure.
"""
import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from auth import get_current_user
from models import User, Project, RenderJob
from services.vertex_veo import submit_veo_generation, poll_veo_operation
from services.billing import require_sufficient_credits, refund_credits, RENDER_PRICE_CENTS
from services.ratelimit import (
    check_render_rate_limit,
    check_render_concurrency,
    check_render_daily_cap,
)
from services.storage import generated_dir

logger = logging.getLogger("vbb.render")
router = APIRouter(prefix="/api/projects", tags=["render"])

GENERATED_DIR = generated_dir()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{project_id}/render")
def start_render(
    project_id: str,
    tier: str = "standard",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start Veo rendering for all approved segments. Reserve credits first."""
    proj = db.query(Project).filter(
        Project.id == project_id, Project.user_id == user.id
    ).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if proj.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Project must be fully approved (Gate 2 complete) before rendering",
        )

    # NOTE: assemble_prompts() stores the list under "segments" (with "social"
    # alongside it). This previously read "prompts", a key that is never set, so
    # every render failed 400 "No prompts found" even after scenes were approved.
    prompts_data = proj.prompts or {}
    segments = prompts_data.get("segments") or []
    if not segments:
        raise HTTPException(status_code=400, detail="No prompts found — approve scenes first")
    if tier not in RENDER_PRICE_CENTS:
        raise HTTPException(status_code=400, detail="Invalid tier. Use 'standard' or 'pro'.")

    # Abuse guards. Deliberately BEFORE any credit reservation so a throttled
    # request never needs a refund — each render costs real GCP money.
    check_render_rate_limit(user.id)

    # Daily cap, counted from the DATABASE rather than memory: an in-process
    # counter resets on every redeploy, which would hand out a free render each
    # time. Every submission writes exactly one job with segment_index == 0, so
    # counting those counts ADS started today (not segments).
    # Naive UTC to match the model's server_default across both SQLite and PG.
    start_of_day = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )
    ads_today = (
        db.query(RenderJob)
        .filter(
            RenderJob.user_id == user.id,
            RenderJob.segment_index == 0,
            RenderJob.created_at >= start_of_day,
        )
        .count()
    )
    check_render_daily_cap(ads_today, user.id)

    open_jobs = (
        db.query(RenderJob)
        .filter(
            RenderJob.user_id == user.id,
            RenderJob.status.in_(["pending", "running"]),
        )
        .count()
    )
    check_render_concurrency(open_jobs, user.id)

    # Reserve credits for the whole ad up front
    require_sufficient_credits(user.id, tier, db)

    # Submit each segment to Veo
    jobs = []
    for i, seg in enumerate(segments):
        duration = seg.get("duration", 6)
        prompt_text = seg.get("prompt", "")
        try:
            op_name = submit_veo_generation(prompt_text, duration, tier)
            job = RenderJob(
                project_id=project_id,
                user_id=user.id,
                # Use the enumeration index: the stored field is "segment"
                # (1-based), and reading "segment_index" left every job at 0.
                segment_index=i,
                tier=tier,
                vertex_operation_name=op_name,
                status="running",
            )
            db.add(job)
            jobs.append(job)
        except RuntimeError as e:
            # Refund the credits if submission fails before any job starts
            refund_credits(user.id, tier, db)
            raise HTTPException(status_code=502, detail=f"Veo submission failed: {e}")

    db.commit()
    return {
        "tier": tier,
        "segment_count": len(jobs),
        "jobs": [{"id": j.id, "segment_index": j.segment_index, "status": j.status} for j in jobs],
    }


@router.get("/{project_id}/render/status")
def render_status(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll all render jobs for this project, updating any that are now done."""
    jobs = db.query(RenderJob).filter(
        RenderJob.project_id == project_id, RenderJob.user_id == user.id
    ).all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No render jobs found for this project")

    for j in jobs:
        if j.status == "running" and j.vertex_operation_name:
            result = poll_veo_operation(j.vertex_operation_name)
            if result["done"]:
                if result["status"] == "succeeded":
                    j.status = "succeeded"
                    if result.get("video_uri"):
                        j.video_url = result["video_uri"]
                    elif result.get("video_bytes"):
                        # Save bytes to generated directory and serve locally
                        filename = f"render_{j.id}.mp4"
                        filepath = os.path.join(GENERATED_DIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(result["video_bytes"])
                        j.video_url = f"/generated/{filename}"
                else:
                    j.status = "failed"
                    j.error_message = result.get("error")
                    refund_credits(user.id, j.tier, db)

    db.commit()
    return {
        "jobs": [
            {
                "id": j.id,
                "segment_index": j.segment_index,
                "status": j.status,
                "video_url": j.video_url,
                "tier": j.tier,
            }
            for j in jobs
        ]
    }
