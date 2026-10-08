"""Post-burn on-screen text and branding onto assembled videos.

Veo 3.1 cannot reliably render on-screen text — even short ALL-CAPS words come
back garbled. This module handles the post-production overlay step:

  1. A persistent lower-third branding bar (brand name + tagline) that stays
     on screen for the entire ad.
  2. Per-segment on-screen text labels (e.g. "DESCRIBE IT", "SEE IT") that
     appear during their segment's time range only.

Uses ffmpeg's drawtext filter with a semi-transparent background box for
readability over any video content. The video stream is re-encoded (libx264,
CRF 18) because drawtext requires a video filter — the audio is copied
losslessly.

Requires ffmpeg on PATH (or VBB_FFMPEG pointing at it).
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from services.assembly import ffmpeg_bin, ffprobe_bin, probe

logger = logging.getLogger("vbb.post_burn")

_FFMPEG_TIMEOUT = 600

# Fonts are in D:/vbb/assets/. We pass them as relative filenames and set
# the working directory to the assets dir when running ffmpeg, because
# ffmpeg's drawtext filter parser treats ':' as an option separator and
# cannot handle Windows drive-letter paths (D:\) in fontfile=.
_ASSETS_DIR = os.environ.get("VBB_ASSETS_DIR", "D:/vbb/assets")
_FONT_BOLD = "arialbd.ttf"   # relative — resolved via cwd
_FONT_REGULAR = "arial.ttf"   # relative — resolved via cwd


def _escape_drawtext(text: str) -> str:
    """Escape text for ffmpeg's drawtext filter.

    ffmpeg drawtext uses colons as filter separators and single quotes for
    string literals. We escape both, plus backslashes and percent signs.
    """
    # Replace in order of most specific to least
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    text = text.replace("%", "\\%")
    return text


def _lower_third_filter(
    brand_name: str,
    tagline: str,
    width: int = 1080,
    height: int = 1920,
    start: float = 0,
    end: float | None = None,
) -> str:
    """Build the drawtext filter for the persistent lower-third branding bar.

    The bar sits at the bottom of the frame with a semi-transparent dark
    background. Brand name in bold white on the left, tagline in lighter
    weight to the right.
    """
    # Lower-third bar: y position near bottom, with some margin
    bar_y = height - 120
    brand_x = 40
    tagline_x = 40

    # Escape text values
    brand = _escape_drawtext(brand_name)
    tag = _escape_drawtext(tagline)

    # Timing
    enable = f"between(t,{start},{end if end is not None else 9999})"

    filters = []

    # Background bar — a semi-transparent dark rectangle behind the text.
    # Using drawbox for the background.
    filters.append(
        f"drawbox=x=0:y={bar_y - 10}:w=iw:h=110:color=black@0.45:t=fill:enable='{enable}'"
    )

    # Brand name — bold, larger, white
    filters.append(
        f"drawtext=fontfile={_FONT_BOLD}:"
        f"text='{brand}':"
        f"fontcolor=white:fontsize=36:"
        f"x={brand_x}:y={bar_y}:"
        f"enable='{enable}'"
    )

    # Tagline — regular, smaller, slightly transparent white
    if tag:
        filters.append(
            f"drawtext=fontfile={_FONT_REGULAR}:"
            f"text='{tag}':"
            f"fontcolor=white@0.8:fontsize=22:"
            f"x={tagline_x}:y={bar_y + 50}:"
            f"enable='{enable}'"
        )

    return ",".join(filters)


def _scene_label_filter(
    label: str,
    start: float,
    end: float,
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Build the drawtext filter for a per-segment on-screen text label.

    The label appears at the top of the frame during its segment's time range,
    with a semi-transparent background for readability.
    """
    if not label:
        return ""

    escaped = _escape_drawtext(label.upper())
    enable = f"between(t,{start},{end})"

    # Top-center label with background bar
    return (
        f"drawbox=x=0:y=0:w=iw:h=80:color=black@0.45:t=fill:enable='{enable}',"
        f"drawtext=fontfile={_FONT_BOLD}:"
        f"text='{escaped}':"
        f"fontcolor=white:fontsize=42:"
        f"x=(w-text_w)/2:y=20:"
        f"enable='{enable}'"
    )


def post_burn(
    input_path: Path,
    output_path: Path,
    segments: list[dict[str, Any]],
    brand_name: str = "",
    tagline: str = "",
) -> dict[str, Any]:
    """Burn on-screen text and branding onto an assembled video.

    Args:
        input_path: The assembled MP4 (from services.assembly.assemble).
        output_path: Where to write the finished video with text overlays.
        segments: List of segment dicts, each with:
            - name: scene name
            - duration: segment duration in seconds
            - on_screen_text: text to overlay during this segment (or "")
        brand_name: Brand name for the persistent lower-third (or "" to skip).
        tagline: Tagline for the lower-third (or "" to skip).

    Returns:
        A dict with probe info about the output file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    info = probe(input_path)
    width = info.get("width", 1080)
    height = info.get("height", 1920)
    total_duration = info.get("duration", 40.0)

    # Build the filter chain
    filters = []

    # 1. Persistent lower-third branding bar (entire video)
    if brand_name:
        filters.append(
            _lower_third_filter(
                brand_name=brand_name,
                tagline=tagline,
                width=width,
                height=height,
                start=0,
                end=total_duration,
            )
        )

    # 2. Per-segment on-screen text labels
    t_start = 0.0
    for seg in segments:
        dur = seg.get("duration", 8)
        t_end = t_start + dur
        label = seg.get("on_screen_text", "")
        if label:
            filters.append(
                _scene_label_filter(
                    label=label,
                    start=t_start,
                    end=t_end,
                    width=width,
                    height=height,
                )
            )
        t_start = t_end

    if not filters:
        # No text to burn — just copy
        import shutil
        shutil.copy2(str(input_path), str(output_path))
        result = probe(output_path)
        result["method"] = "copy (no text to burn)"
        return result

    filter_chain = ",".join(filters)

    # Re-encode video with drawtext, copy audio
    cmd = [
        ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_path),
        "-vf", filter_chain,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]

    logger.info("post_burn: %s -> %s (%d filters)", input_path.name, output_path.name, len(filters))

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=_FFMPEG_TIMEOUT,
        encoding="utf-8", errors="replace",
        cwd=_ASSETS_DIR,  # so relative fontfile= paths resolve
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg post_burn failed: {(result.stderr or '').strip()[:800]}"
        )

    out_info = probe(output_path)
    out_info["method"] = "post_burn (drawtext)"
    out_info["filter_count"] = len(filters)
    return out_info
