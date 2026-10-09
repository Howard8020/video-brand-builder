#!/bin/bash
# Startup script for Railway deployment
set -e

# ── GCP credentials ──────────────────────────────────────────────
# Railway doesn't have a file system for secrets. Store the credentials
# JSON as the GCP_CREDENTIALS_JSON env var; we write it to disk at startup.
#
# Use printf '%s', NOT echo: this JSON contains backslash escapes inside
# private_key, and some shells' echo interprets those, producing a file that
# google.auth then rejects with "not a valid json file". Write it verbatim and
# verify it parses, so a bad value is reported at boot instead of surfacing
# later as an opaque 500 on the first render.
if [ -n "$GCP_CREDENTIALS_JSON" ]; then
  printf '%s' "$GCP_CREDENTIALS_JSON" > gcp-credentials.json
  if python -c "import json; json.load(open('gcp-credentials.json'))" 2>/dev/null; then
    echo "GCP credentials written to disk (valid JSON)"
  else
    echo "ERROR: GCP_CREDENTIALS_JSON did not produce valid JSON — Veo rendering will fail"
  fi
else
  echo "WARNING: GCP_CREDENTIALS_JSON is not set — Veo rendering will fail"
fi

# ── Database tables (idempotent) ─────────────────────────────────
echo "Running database migrations..."
# Stamp current revision (creates alembic_version table if missing
# for databases that were created by the old create_all pattern)
alembic stamp 95445ac45e04
alembic upgrade head
if [ $? -eq 0 ]; then
    echo "Migrations applied OK"
else
    echo "ERROR: alembic upgrade head failed"
    exit 1
fi

# ── Start server ─────────────────────────────────────────────────
echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
