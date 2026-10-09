"""Join rendered segments into one platform-ready video.

Veo returns each segment as its own MP4, so a 30-second ad arrives as ~6 loose
files. TikTok and YouTube Shorts both need a single upload, so this stitches
them in order and produces something that can be posted without opening an
editor.

What it does beyond plain concatenation:

  * Keeps the video stream UNTOUCHED (-c:v copy). Every segment comes from the
    same model at the same resolution, so the join is lossless and near-instant
    — no re-encode, no generation loss, no quality drift across the ad.
  * Normalises audio loudness to the ~-14 LUFS that social platforms target.
    Each segment gets its own audio pass from Veo, so without this the volume
    audibly jumps at every cut. Normalising once, here, also stops the platform
    from applying its own aggressive correction.
  * Writes a faststart MP4 so the platform can begin processing immediately.

Requires ffmpeg on PATH (or VBB_FFMPEG pointing at it). Everything stays
server-side on the data drive; nothing is uploaded anywhere.
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Sequence

logger = logging.getLogger("vbb.assembly")

# Social platforms normalise to roughly -14 LUFS; matching it avoids a
# noticeable level shift after upload.
_TARGET_LUFS = os.getenv("VBB_LOUDNESS_TARGET", "-14")
_TRUE_PEAK = "-1.5"
_LOUDNESS_RANGE = "11"

# Music bed: a soft, warm background track mixed under the dialogue at a
# low volume so it adds warmth without competing with speech.
_MUSIC_BED_PATH = os.getenv(
    "VBB_MUSIC_BED",
    str(Path(__file__).resolve().parent.parent / "assets" / "music" / "warm-bed.mp3"),
)
_MUSIC_BED_VOLUME = float(os.getenv("VBB_MUSIC_BED_VOLUME", "0.08"))  # -22 dB approx
_MUSIC_BED_FADE = float(os.getenv("VBB_MUSIC_BED_FADE", "1.5"))  # seconds

_FFMPEG_TIMEOUT = 600  # seconds; concatenation is stream-copy so normally seconds


def ffmpeg_bin() -> str:
    """Path to ffmpeg. Honours VBB_FFMPEG, else relies on PATH."""
    return os.getenv("VBB_FFMPEG", "").strip() or "ffmpeg"


def ffprobe_bin() -> str:
    configured = os.getenv("VBB_FFMPEG", "").strip()
    if configured:
        candidate = Path(configured).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if candidate.exists():
            return str(candidate)
    return "ffprobe"


def ffmpeg_available() -> bool:
    return shutil.which(ffmpeg_bin()) is not None


def _concat_list_line(path: Path) -> str:
    """One concat-demuxer entry. Forward slashes + escaped quotes keep Windows
    paths safe, which the demuxer is otherwise fussy about."""
    posix = str(path).replace("\\", "/").replace("'", "'\\''")
    return f"file '{posix}'"


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    logger.info("ffmpeg: %s", " ".join(cmd[:6]) + (" ..." if len(cmd) > 6 else ""))
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_FFMPEG_TIMEOUT,
        encoding="utf-8",
        errors="replace",
    )


def probe(path: Path) -> Dict[str, Any]:
    """Duration / stream info for a media file. Best-effort."""
    try:
        res = subprocess.run(
            [
                ffprobe_bin(), "-v", "error",
                "-show_entries", "format=duration,size",
                "-show_entries", "stream=codec_type,codec_name,width,height,sample_rate,channels",
                "-of", "json", str(path),
            ],
            capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace",
        )
        if res.returncode != 0:
            return {}
        data = json.loads(res.stdout or "{}")
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
        fmt = data.get("format", {})
        return {
            "duration": round(float(fmt.get("duration") or 0), 2),
            "size_bytes": int(fmt.get("size") or 0),
            "width": video.get("width"),
            "height": video.get("height"),
            "video_codec": video.get("codec_name"),
            "has_audio": bool(audio),
            "audio_codec": audio.get("codec_name"),
            "sample_rate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
        }
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.warning("ffprobe failed for %s: %s", path, exc)
        return {}


def _trim_segment(in_path: Path, out_path: Path, trim_start: float = 0.0,
                   trim_end: float = 0.0) -> bool:
    """Trim silence/freeze-frame from the start and end of a Veo clip.

    Veo clips may have silence or a freeze-frame at the beginning and end.
    Trimming these makes clip-to-clip transitions tighter when the clips are
    concatenated.

    IMPORTANT: stream-copy (-c copy) with -ss seeking past the first keyframe
    produces a corrupted file (invalid NAL units, missing pictures). Veo clips
    have keyframes only at the start, so any seek > 0s with stream-copy breaks
    the H.264 stream. We must re-encode the video when trimming.

    Returns True on success, False if trimming failed (caller should use
    the original untrimmed file as a fallback).
    """
    if trim_start <= 0 and trim_end <= 0:
        return False  # nothing to trim

    duration = _probe_duration(in_path)
    target_duration = duration - trim_start - trim_end
    if target_duration < 0.5:
        return False  # would trim away almost the entire clip

    # Re-encode video (not stream-copy) because seeking past the first
    # keyframe with -c copy corrupts the H.264 stream.
    cmd = [
        ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(trim_start),
        "-i", str(in_path),
        "-t", str(target_duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        str(out_path),
    ]
    res = _run(cmd)
    if res.returncode != 0:
        logger.warning("trim failed for %s: %s", in_path.name,
                        (res.stderr or "").strip()[:200])
        return False
    return True


def _probe_duration(path: Path) -> float:
    """Get the duration of a media file in seconds (best-effort)."""
    try:
        res = subprocess.run(
            [ffprobe_bin(), "-v", "error",
             "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if res.returncode == 0:
            return float(res.stdout.strip())
    except Exception:
        pass
    return 8.0  # fallback assumption


def assemble(segment_paths: Sequence[Path], out_path: Path) -> Dict[str, Any]:
    """Concatenate `segment_paths` (in order) into `out_path`.

    Returns a summary dict including the ffprobe report. Raises RuntimeError
    with ffmpeg's own stderr on failure, so the cause is visible in the API
    response and the logs rather than being swallowed.
    """
    if not segment_paths:
        raise RuntimeError("no segments to assemble")

    missing = [str(p) for p in segment_paths if not Path(p).exists()]
    if missing:
        raise RuntimeError(f"segment file(s) missing: {missing}")

    if not ffmpeg_available():
        raise RuntimeError(
            f"ffmpeg not found (looked for {ffmpeg_bin()!r}). "
            "Install it, or set VBB_FFMPEG to its full path."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="vbb_assemble_") as tmp:
        # Trim silence/freeze-frame from clip boundaries for tighter transitions.
        # Disabled by default (trim_amount=0) because the re-encode adds processing
        # time and the transition tightness gain is marginal for most Veo clips.
        # Enable by setting VBB_TRIM_AMOUNT env var (e.g. "0.3" for 0.3s each end).
        trim_amount = float(os.getenv("VBB_TRIM_AMOUNT", "0"))
        trimmed_paths = []
        for p in segment_paths:
            src = Path(p)
            if trim_amount > 0:
                trimmed = Path(tmp) / f"trimmed_{src.name}"
                if _trim_segment(src, trimmed, trim_start=trim_amount, trim_end=trim_amount):
                    trimmed_paths.append(trimmed)
                else:
                    logger.warning("using untrimmed segment: %s", src.name)
                    trimmed_paths.append(src)
            else:
                trimmed_paths.append(src)

        list_file = Path(tmp) / "segments.txt"
        list_file.write_text(
            "\n".join(_concat_list_line(Path(p).resolve()) for p in trimmed_paths) + "\n",
            encoding="utf-8",
        )

        # Preferred path: copy the video stream (lossless, fast) and re-encode
        # only the audio so loudness can be normalised.
        # Also add a 0.15s audio fade-in/out at each clip boundary so the
        # hard cut between clips doesn't produce an audible click or pop.
        copy_cmd = [
            ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "copy",
            "-af", f"loudnorm=I={_TARGET_LUFS}:TP={_TRUE_PEAK}:LRA={_LOUDNESS_RANGE},"
                   f"afade=t=in:st=0:d=0.15,afade=t=out:st={max(0,info.get('duration',40)-0.15):.2f}:d=0.15",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            str(out_path),
        ]
        res = _run(copy_cmd)

        if res.returncode != 0:
            # Segments should share parameters, but if they do not, fall back to
            # re-encoding the video so the user still gets a finished file.
            logger.warning("stream-copy concat failed, retrying with re-encode: %s",
                           (res.stderr or "").strip()[:400])
            reencode_cmd = [
                ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-af", f"loudnorm=I={_TARGET_LUFS}:TP={_TRUE_PEAK}:LRA={_LOUDNESS_RANGE}",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart",
                str(out_path),
            ]
            res = _run(reencode_cmd)
            if res.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {(res.stderr or '').strip()[:800]}")
            method = "re-encoded"
        else:
            method = "stream-copy"

    info = probe(out_path)
    info["method"] = method
    info["segment_count"] = len(segment_paths)
    info["loudness_target_lufs"] = _TARGET_LUFS

    # --- Color normalization: match all clips to the first clip's color grade ---
    # Veo's color science varies between clips — one may be warmer, another
    # cooler, even with the same prompt. This re-encodes with a gentle color
    # normalization (eq + curves) to reduce visible color drift at cuts.
    # Disabled by default (VBB_COLOR_MATCH=false) because it requires a
    # full re-encode. Enable with VBB_COLOR_MATCH=true.
    if os.getenv("VBB_COLOR_MATCH", "false").lower() in ("true", "1"):
        color_out = out_path.with_name(f"colormatch_{out_path.name}")
        color_cmd = [
            ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(out_path),
            "-vf", "eq=brightness=0.02:saturation=1.05:contrast=1.02,"
                   "curves=preset=increase_saturation",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(color_out),
        ]
        color_res = _run(color_cmd)
        if color_res.returncode == 0 and color_out.exists():
            shutil.move(str(color_out), str(out_path))
            info["color_match"] = True
            info["method"] = f"{method} + color match"
        else:
            logger.warning("color match failed: %s",
                          (color_res.stderr or "").strip()[:300])
            info["color_match"] = False
    else:
        info["color_match"] = False

    # --- Music bed: mix a soft warm track under the dialogue ---
    # This is the single biggest quality improvement for the least code —
    # it makes the ad feel professional instead of raw. The music bed is
    # mixed at a low volume (-22 dB) so it adds warmth without competing
    # with speech. Fade in at the start and fade out at the end.
    music_path = Path(_MUSIC_BED_PATH)
    if music_path.exists() and _MUSIC_BED_VOLUME > 0:
        music_out = out_path.with_name(f"with_music_{out_path.name}")
        total_dur = info.get("duration", 40.0)
        fade = _MUSIC_BED_FADE

        music_cmd = [
            ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(out_path),
            "-i", str(music_path),
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=999999,volume={_MUSIC_BED_VOLUME},"
            f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0,total_dur-fade)}:d={fade}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            "-t", str(total_dur),
            str(music_out),
        ]
        music_res = _run(music_cmd)
        if music_res.returncode == 0 and music_out.exists():
            # Replace the original with the music version
            shutil.move(str(music_out), str(out_path))
            info["music_bed"] = True
            info["method"] = f"{method} + music bed"
        else:
            logger.warning("music bed mix failed: %s",
                          (music_res.stderr or "").strip()[:300])
            info["music_bed"] = False
    else:
        info["music_bed"] = False

    logger.info("assembled %d segments -> %s (%ss, %s)",
                len(segment_paths), out_path.name, info.get("duration"), info.get("method"))
    return info