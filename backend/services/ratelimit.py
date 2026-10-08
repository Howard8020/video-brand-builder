"""In-process rate limiting for spend-carrying endpoints.

Why in-process: the service runs a single uvicorn worker (see `start.sh`,
`--workers 1`), so a module-level structure is shared by every request. That
avoids adding Redis or another dependency purely for abuse protection.

Caveat: counters reset when the container restarts or redeploys. That is
acceptable here — the authoritative spend control is the credit balance
(`services/billing.py`); this limiter exists to bound the blast radius of a
runaway loop or a compromised account, where "resets on deploy" is fine.

Tune with env vars:
    VBB_RENDER_LIMIT_PER_DAY    max render submissions per user per day (default 1)
    VBB_RENDER_LIMIT_PER_HOUR   max render submissions per user per hour (default 2)
    VBB_RENDER_MAX_CONCURRENT   max simultaneously open render jobs per user (default 12)

Defaults target the current internal use: ONE 30-second ad per day (~$3 of Veo
at $0.10/sec, ~$90/month). Per-hour is intentionally above per-day so a retry
after a failure is possible without allowing a second ad. Max-concurrent is
deliberately generous because it counts segment JOBS: a 30s ad is ~6 segments
submitted at once, so a low ceiling would block a legitimate retry while the
first ad is still rendering.
"""
import os
import threading
import time
from collections import defaultdict, deque
from typing import Dict, Deque

from fastapi import HTTPException

RENDER_LIMIT_PER_DAY = int(os.getenv("VBB_RENDER_LIMIT_PER_DAY", "1"))
RENDER_LIMIT_PER_HOUR = int(os.getenv("VBB_RENDER_LIMIT_PER_HOUR", "2"))
RENDER_MAX_CONCURRENT = int(os.getenv("VBB_RENDER_MAX_CONCURRENT", "12"))

_WINDOW_SECONDS = 3600.0

_lock = threading.Lock()
_render_hits: Dict[str, Deque[float]] = defaultdict(deque)


def check_render_daily_cap(ads_today: int, user_id: str) -> None:
    """Raise 429 if this user has already started too many ads today.

    `ads_today` is counted by the caller from the database (one row per
    submission), NOT from in-process state — a counter in memory resets on
    every redeploy, which would hand out a free extra render after each deploy.
    The database count is the authoritative spend control.
    """
    if ads_today >= RENDER_LIMIT_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily render limit reached: {RENDER_LIMIT_PER_DAY} ad(s) per day. "
                "This limit bounds real Vertex AI spend; it resets at midnight UTC."
            ),
        )


def check_render_rate_limit(user_id: str) -> None:
    """Raise 429 if this user has submitted too many renders in the last hour.

    Call this BEFORE reserving credits so a rejected request never needs a refund.
    """
    now = time.monotonic()
    with _lock:
        hits = _render_hits[user_id]
        # drop entries outside the rolling window
        while hits and (now - hits[0]) > _WINDOW_SECONDS:
            hits.popleft()

        if len(hits) >= RENDER_LIMIT_PER_HOUR:
            retry_after = int(_WINDOW_SECONDS - (now - hits[0])) + 1
            minutes = max(retry_after // 60, 1)
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Render rate limit reached: {RENDER_LIMIT_PER_HOUR} renders per hour. "
                    f"Try again in about {minutes} minute(s)."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)


def check_render_concurrency(open_jobs: int, user_id: str) -> None:
    """Raise 429 if this user already has too many renders in flight.

    `open_jobs` is counted by the caller from the DB (pending + running rows),
    which keeps this module free of database imports.
    """
    if open_jobs >= RENDER_MAX_CONCURRENT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"You already have {open_jobs} renders in progress. "
                f"Wait for those to finish (max {RENDER_MAX_CONCURRENT} at once) "
                "before starting another."
            ),
        )


def reset() -> None:
    """Clear all counters. Test helper."""
    with _lock:
        _render_hits.clear()