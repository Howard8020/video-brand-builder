#!/bin/bash
# Startup script for Railway deployment
set -e

# ── GCP credentials ──────────────────────────────────────────────
# Railway doesn't have a file system for secrets. Store the credentials
# JSON as the GCP_CREDENTIALS_JSON env var; we write it to disk at startup.
if [ -n "$GCP_CREDENTIALS_JSON" ]; then
  echo "$GCP_CREDENTIALS_JSON" > gcp-credentials.json
  echo "GCP credentials written to disk"
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
