# Video Brand Builder

AI-powered video ad creation platform for home-service businesses. Generate professional video ads from templates using Veo AI video generation.

**Domain:** [videobrandbuilders.ai](https://videobrandbuilders.ai)

## Tech Stack

- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS — deployed on Vercel
- **Backend:** FastAPI + SQLAlchemy — deployed on Railway (project: creative-vibrancy)
- **Database:** PostgreSQL (via Railway)
- **AI Video:** Veo video generation via Google AI SDK (GCP project: video-brand-builder-vertex)
- **Billing:** Stripe credit-prepay billing
- **AI Assistant:** Albert (powered by OpenRouter / Anthropic)

## Features

- **Template Picker** — 7 home-service video templates (plumber, cleaner, landscaper, etc.)
- **AI Video Generation** — Describe your offer, AI generates a professional video ad
- **Albert AI Assistant** — Conversational AI helper for campaign setup and optimization
- **Credit Prepay Billing** — Buy credits, spend per video generation
- **Demo Mode** — Test the platform with a demo account

## Demo Account

- **Email:** demo@videobrandbuilder.ai
- **Password:** Demo2026Pass

## Project Structure

```
video-brand-builder/
├── frontend/              # Next.js 15 frontend
├── backend/               # FastAPI backend
│   ├── main.py
│   ├── routes/
│   ├── models/
│   ├── services/
│   └── config/
├── scripts/                # Utility scripts
├── package.json
└── README.md
```

## Getting Started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

Or with pip:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```
DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
GCP_CREDENTIALS_JSON={"..."}
NEXT_PUBLIC_SITE_URL=https://videobrandbuilders.ai
OPENROUTER_API_KEY=sk-or-...
```

## Ops Floor

### Stack
- Frontend: Next.js 15 (Vercel)
- Backend: FastAPI + SQLAlchemy (Railway, project: creative-vibrancy)
- Database: PostgreSQL (Railway)
- Hosting: Vercel (frontend) + Railway (backend)
- Domain: videobrandbuilders.ai

### Deploy
```bash
# Frontend (Vercel)
cd frontend && npx vercel --prod --yes

# Backend (Railway)
cd backend && git push railway main
```

### Rollback
- Frontend: Vercel instant rollback via Dashboard → Deployments → ⋮ → Rollback to this
- Backend: `git revert` + push, or Railway Dashboard → Deployments → previous deploy

### Backups
- [ ] Database: Railway PostgreSQL automatic daily backups
- [ ] User data: stored in PostgreSQL (via SQLAlchemy models)

### Production env vars
Verify these are set in the production environment (not just local .env):
- `DATABASE_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `GCP_CREDENTIALS_JSON` — Google service account for Veo API access
- `NEXT_PUBLIC_SITE_URL`
- `OPENROUTER_API_KEY` — for Albert AI assistant

### Health check
- Endpoint: `GET /health` (or `GET /api/health`)
- Expected: `{"status": "healthy"}`
