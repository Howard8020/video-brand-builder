"""Direct render API — one-shot "brief → finished video" for programmatic callers.

Skips the multi-step UI workflow (create project → generate script → approve
script → generate scenes → approve scenes → render → assemble) and does the
whole pipeline in one call. Designed for external bots (e.g. Grok) that want
to feed prompts directly and get a video URL back.

Auth: same JWT bearer token as the rest of the API.
Rate-limited by the same VBB_RENDER_LIMIT_PER_HOUR / VBB_RENDER_MAX_CONCURRENT.
Credits: if VBB_RENDER_BYPASS_CREDITS=true, no credit check (internal/dev mode).
"""
import os
import time
import json
import logging
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from auth import get_current_user
from models import User
from services.prompts import assemble_prompts
from services.vertex_veo import submit_veo_generation, _get_client
from services.assembly import assemble, ffmpeg_available
from services.storage import assembled_dir, generated_dir
from services.ratelimit import check_render_rate_limit, check_render_concurrency

logger = logging.getLogger("vbb.render_direct")
router = APIRouter(prefix="/api/render-direct", tags=["render-direct"])

_BYPASS = "VBB_RENDER_BYPASS_CREDITS"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Request models ---

class SceneIn(BaseModel):
    name: str
    purpose: str = "example"  # hook | benefit | example | cta
    duration: int = 8  # 4, 6, or 8
    spoken: str = ""
    action: str = ""
    camera: str = ""
    on_screen_text: str = ""  # burned in post, not sent to Veo


class ContinuityIn(BaseModel):
    mode: str = "spokesperson"
    spokesperson: str = ""
    delivery: str = "warm, upbeat, and animated — never flat or monotone"
    setting: str = ""
    lighting: str = ""
    brand: str = ""  # not sent to Veo; reserved for future post-burn


class BriefIn(BaseModel):
    clientName: str
    category: str = ""
    serviceLine: str = ""
    goal: str = ""
    audience: str = ""
    tones: list[str] = []
    cta: str = ""
    platform: str = "TikTok"
    aspect: str = "9:16"
    runtime: int = 24
    visualMode: str = "spokesperson"
    brandNotes: str = ""
    avoid: str = ""


class RenderDirectRequest(BaseModel):
    brief: BriefIn
    continuity: ContinuityIn = ContinuityIn()
    scenes: list[SceneIn]
    tier: str = "standard"  # "standard" | "pro"
    settings: dict = {}  # clipLengths, wpm, etc.


class RenderDirectResponse(BaseModel):
    job_id: str
    status: str  # "queued" | "rendering" | "assembling" | "done" | "failed"
    tier: str
    segment_count: int


class RenderDirectStatus(BaseModel):
    job_id: str
    status: str
    tier: str
    segments_total: int
    segments_done: int
    segments_failed: int
    video_url: Optional[str] = None
    error: Optional[str] = None


# --- In-memory job store (single-worker, same pattern as ratelimit.py) ---
# The Railway service runs --workers 1, so this is shared across all requests.
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _run_job(job_id: str, request: RenderDirectRequest, user_id: str):
    """Background thread: render all segments, assemble, store result."""
    try:
        _set_status(job_id, "rendering")
        brief = request.brief.model_dump()
        continuity = request.continuity.model_dump()
        scenes = [s.model_dump() for s in request.scenes]
        settings = request.settings or {"clipLengths": [4, 6, 8], "wpm": 125}
        tier = request.tier
        aspect = brief.get("aspect", "9:16")

        script = {"title": f"{brief.get('clientName', 'ad')}", "segments": scenes}
        prompts = assemble_prompts(brief, script, {"scenes": scenes}, continuity, settings)
        segs = prompts["segments"]

        gen_dir = generated_dir()
        seg_paths = []
        failed = 0

        for i, seg in enumerate(segs, 1):
            _set_status(job_id, "rendering", segment_index=i, segments_done=i - 1)
            dest = gen_dir / f"rd_{job_id}_seg{i}.mp4"
            result = _render_one_segment(seg, dest, tier, aspect, max_retries=2)
            if result.get("ok"):
                seg_paths.append(dest)
            else:
                failed += 1
                logger.warning("render-direct %s seg %d failed: %s", job_id, i, result.get("error"))

        if failed:
            _set_status(job_id, "failed",
                        error=f"{failed} of {len(segs)} segments failed",
                        segments_failed=failed)
            return

        # Assemble
        _set_status(job_id, "assembling", segments_done=len(seg_paths))
        out_dir = assembled_dir()
        out_name = f"rd_{job_id}.mp4"
        out_path = out_dir / out_name

        info = assemble(seg_paths, out_path)
        video_url = f"/assembled/{out_name}"
        _set_status(job_id, "done",
                    video_url=video_url,
                    segments_done=len(seg_paths))

    except Exception as e:
        logger.error("render-direct %s failed: %s", job_id, e)
        _set_status(job_id, "failed", error=str(e))


def _render_one_segment(seg: dict, dest: Path, tier: str, aspect: str,
                         max_retries: int = 2) -> dict:
    """Submit + poll one segment, with retries on transient failures."""
    from google.genai.types import GenerateVideosOperation
    client = _get_client()

    for attempt in range(max_retries + 1):
        try:
            op_name = submit_veo_generation(
                seg["prompt"], seg["duration"],
                tier=tier, aspect_ratio=aspect,
            )
        except Exception as e:
            if attempt < max_retries:
                time.sleep(10)
                continue
            return {"ok": False, "error": f"submit failed: {e}"}

        # Poll
        op = GenerateVideosOperation(name=op_name)
        start = time.time()
        timeout = 600
        while True:
            if time.time() - start > timeout:
                break
            try:
                res = client.operations.get(op)
            except Exception:
                time.sleep(5)
                continue
            if res.done:
                if res.error:
                    # Transient errors are retried
                    err_str = str(res.error)
                    if "UNAVAILABLE" in err_str or "code: 14" in err_str:
                        break  # retry
                    return {"ok": False, "error": err_str}
                vids = getattr(res.response, "generated_videos", None) or []
                if not vids:
                    # Could be transient (empty response) or safety filter
                    filtered = getattr(res.response, "rai_media_filtered_count", None)
                    if filtered and filtered > 0:
                        return {"ok": False, "error": f"safety filter ({filtered} filtered)"}
                    break  # retry on empty
                vid = vids[0].video
                data = None
                try:
                    data = client.files.download(file=vid)
                except Exception:
                    pass
                if not data and getattr(vid, "video_bytes", None):
                    data = vid.video_bytes
                if not data and getattr(vid, "uri", None):
                    uri = vid.uri
                    if uri.startswith("gs://"):
                        from google.cloud import storage
                        b, _, blob = uri[5:].partition("/")
                        data = storage.Client().bucket(b).blob(blob).download_as_bytes()
                    elif uri.startswith("http"):
                        import httpx
                        data = httpx.get(uri, timeout=300).content
                if not data:
                    return {"ok": False, "error": "no video data"}
                dest.write_bytes(data)
                return {"ok": True, "bytes": len(data)}
            time.sleep(8)

        # Retry
        if attempt < max_retries:
            logger.info("render-direct: retrying segment (attempt %d)", attempt + 1)
            time.sleep(10)

    return {"ok": False, "error": "exhausted retries"}


def _set_status(job_id: str, status: str, **kwargs):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update({"status": status, **kwargs})


# --- Routes ---

@router.post("", response_model=RenderDirectResponse)
def create_direct_render(
    request: RenderDirectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a one-shot render job: brief + scenes → finished video.

    Returns a job_id immediately. Poll GET /api/render-direct/{job_id} for
    status and the final video URL.

    The pipeline runs in a background thread:
    1. assemble_prompts() builds per-segment Veo prompts
    2. Each segment is submitted to Vertex AI Veo with transient retries
    3. Segments are assembled (stream-copy + loudnorm + faststart)
    4. The finished video URL is stored in the job record
    """
    if not request.scenes:
        raise HTTPException(status_code=400, detail="At least one scene is required")
    if request.tier not in ("standard", "pro"):
        raise HTTPException(status_code=400, detail="tier must be 'standard' or 'pro'")

    # Validate durations
    for s in request.scenes:
        if s.duration not in (4, 6, 8):
            raise HTTPException(
                status_code=400,
                detail=f"Scene '{s.name}' has duration {s.duration}s — must be 4, 6, or 8",
            )

    # Rate limit
    check_render_rate_limit(user.id)
    check_render_concurrency(0, user.id)  # check_render_concurrency checks open jobs

    # Check credits unless bypassed
    if not os.getenv(_BYPASS, "").lower() in ("true", "1"):
        from services.billing import require_sufficient_credits
        try:
            require_sufficient_credits(user.id, request.tier, db)
        except Exception as e:
            raise HTTPException(status_code=402, detail=str(e))

    if not ffmpeg_available():
        raise HTTPException(
            status_code=500,
            detail="ffmpeg is not available on this host — cannot assemble.",
        )

    import uuid
    job_id = f"rd_{uuid.uuid4().hex[:12]}"

    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "user_id": user.id,
            "status": "queued",
            "tier": request.tier,
            "segments_total": len(request.scenes),
            "segments_done": 0,
            "segments_failed": 0,
            "video_url": None,
            "error": None,
            "created_at": time.time(),
        }

    # Start background thread
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, request, user.id),
        daemon=True,
    )
    thread.start()

    return RenderDirectResponse(
        job_id=job_id,
        status="queued",
        tier=request.tier,
        segment_count=len(request.scenes),
    )


@router.get("/{job_id}", response_model=RenderDirectStatus)
def get_direct_render_status(
    job_id: str,
    user: User = Depends(get_current_user),
):
    """Poll the status of a direct render job."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    return RenderDirectStatus(
        job_id=job["job_id"],
        status=job["status"],
        tier=job["tier"],
        segments_total=job["segments_total"],
        segments_done=job["segments_done"],
        segments_failed=job["segments_failed"],
        video_url=job.get("video_url"),
        error=job.get("error"),
    )
