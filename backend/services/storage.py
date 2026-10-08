"""Filesystem locations for generated artifacts.

Rendered clips used to be written to `<backend>/generated` and served from
there. That is correct for a local install but was wrong on the cloud host,
where the container filesystem is ephemeral and every redeploy silently
deleted finished renders.

The location is now configurable so the storage of record can live on a data
drive (e.g. D:\\vbb\\generated) rather than inside the source tree. Keeping
it outside the repo is what makes the data portable: moving the drive to
another machine moves the renders with it, with only this path changing.

    VBB_GENERATED_DIR   directory for rendered clips (default: <backend>/generated)
"""
import os
from pathlib import Path

_DEFAULT_DIR = Path(__file__).resolve().parent.parent / "generated"
_DEFAULT_ASSEMBLED = Path(__file__).resolve().parent.parent / "assembled"

_ENV_VAR = "VBB_GENERATED_DIR"
_ENV_ASSEMBLED = "VBB_ASSEMBLED_DIR"


def generated_dir() -> Path:
    """Return the directory rendered clips are stored in, creating it if needed."""
    configured = os.getenv(_ENV_VAR, "").strip()
    path = Path(configured).expanduser() if configured else _DEFAULT_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def assembled_dir() -> Path:
    """Directory for joined, platform-ready videos.

    Kept separate from the individual segments so it is obvious which files are
    finished deliverables (safe to upload / archive) and which are intermediates
    that can be regenerated.
    """
    configured = os.getenv(_ENV_ASSEMBLED, "").strip()
    path = Path(configured).expanduser() if configured else _DEFAULT_ASSEMBLED
    path.mkdir(parents=True, exist_ok=True)
    return path


def describe() -> str:
    """Human-readable summary for startup logs (no secrets involved)."""
    configured = os.getenv(_ENV_VAR, "").strip()
    path = generated_dir()
    source = _ENV_VAR if configured else "default (inside repo — NOT portable)"
    return f"generated dir: {path}  [{source}]"