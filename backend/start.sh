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
echo "Creating database tables..."
python -c "
from database import engine, Base
from models import User, Client, Project
from models.credit import CreditBalance
import sqlalchemy as sa

# Create any missing tables
Base.metadata.create_all(bind=engine)

# Add brand_profile column if missing (existing tables aren't altered by create_all)
inspector = sa.inspect(engine)
cols = [c['name'] for c in inspector.get_columns('users')]
if 'brand_profile' not in cols:
    with engine.connect() as conn:
        conn.execute(sa.text('ALTER TABLE users ADD COLUMN brand_profile JSON'))
        conn.commit()
    print('Added brand_profile column to users table')
else:
    print('brand_profile column already exists')

print('Tables created/verified OK')
"

# ── Start server ─────────────────────────────────────────────────
echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
