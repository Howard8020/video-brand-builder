"""Vertex AI Veo video generation — using the google-genai SDK.

Veo generation is async: submit, poll with client.operations.get(), get video
bytes or GCS URI back. The SDK handles the internal polling URL correctly.

Veo 3.1 Fast = $0.10/sec (Standard tier)
Veo 3.1      = $0.40/sec (Pro tier)
"""
import os
import logging
import tempfile
from datetime import datetime, timezone
from typing import Any

import google.auth
from google import genai
from google.genai import types as genai_types

logger = logging.getLogger("vbb.vertex_veo")

_DEFAULT_LOCATION = "us-central1"

VEO_MODELS = {
    "standard": "veo-3.1-fast-generate-001",
    "pro": "veo-3.1-generate-001",
}

# 1080p output is a property of the model tier, not a separate switch: the Pro
# model renders 1080p, Fast is 720p only. Previously NOTHING was passed to
# GenerateVideosConfig.resolution, so every render silently came back 720p even
# when the UI offered a "1080p" tier.
TIER_RESOLUTION = {
    "standard": "720p",
    "pro": "1080p",
}

# Veo refuses clips containing people under the default ("allow_adult"), which
# rejected any ad with children or a family. These ads are our own in-house
# brand spots, so allow_all is the intended setting.
_PERSON_GENERATION = "allow_all"

# Cache the client so we don't re-auth on every call
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    project = os.getenv("GCP_PROJECT_ID", "")
    location = os.getenv("GCP_LOCATION", _DEFAULT_LOCATION)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    if not project:
        raise RuntimeError("GCP_PROJECT_ID is not set in environment")
    if not creds_path or not os.path.exists(creds_path):
        raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS not found at: {creds_path}")

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    _client = genai.Client(project=project, location=location, vertexai=True, credentials=creds)
    return _client


def submit_veo_generation(
    prompt: str,
    duration_seconds: int,
    tier: str = "standard",
    aspect_ratio: str = "9:16",
    resolution: str | None = None,
) -> str:
    """Submit a Veo generation request. Returns the long-running operation name."""
    client = _get_client()
    model_id = VEO_MODELS.get(tier, VEO_MODELS["standard"])
    res = resolution or TIER_RESOLUTION.get(tier, "720p")

    config = genai_types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        number_of_videos=1,
        resolution=res,
        person_generation=_PERSON_GENERATION,
        generate_audio=True,
        negative_prompt="misspelled text, garbled letters, illegible words, distorted text, gibberish on screen",
    )

    op = client.models.generate_videos(
        model=model_id,
        prompt=prompt,
        config=config,
    )

    if op.name:
        logger.info("Veo generation submitted: %s (tier=%s, duration=%ds)", op.name, tier, duration_seconds)
        return op.name  # Return name string for DB storage
    raise RuntimeError(f"Veo response missing operation name: {op}")


def poll_veo_operation(operation_name: str, timeout_seconds: int = 300) -> dict[str, Any]:
    """Poll a Veo operation until done or timeout, using the SDK's operation getter.

    operation_name: the operation name string as returned by submit_veo_generation.

    Returns:
        {'done': bool, 'video_uri': str|None, 'video_bytes': bytes|None, 'error': str|None, 'status': str}
    """
    from google.genai.types import GenerateVideosOperation

    client = _get_client()
    op = GenerateVideosOperation(name=operation_name)
    start = datetime.now(timezone.utc)

    while True:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        if elapsed > timeout_seconds:
            return {"done": False, "status": "timeout", "video_uri": None, "video_bytes": None, "error": "Polling timed out"}

        try:
            result = client.operations.get(op)
        except Exception as e:
            logger.error("Veo poll error: %s", e)
            import time as time_module
            time_module.sleep(5)
            continue

        if result.done:
            if result.response and hasattr(result.response, "generated_videos") and result.response.generated_videos:
                vid = result.response.generated_videos[0].video
                # Prefer GCS URI, fall back to raw bytes
                if vid.uri:
                    return {"done": True, "status": "succeeded", "video_uri": vid.uri, "video_bytes": None, "error": None}
                elif vid.video_bytes:
                    return {"done": True, "status": "succeeded", "video_uri": None, "video_bytes": vid.video_bytes, "error": None}
                else:
                    return {"done": True, "status": "failed", "video_uri": None, "video_bytes": None, "error": "No video data in response"}
            elif result.error:
                return {"done": True, "status": "failed", "video_uri": None, "video_bytes": None, "error": str(result.error)}
            else:
                return {"done": True, "status": "succeeded", "video_uri": None, "video_bytes": None, "error": None}

        import time as time_module
        time_module.sleep(5)
