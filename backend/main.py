"""Video Brand Builder API - backend entry point."""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import SessionLocal, init_db
from routes import auth_router, clients_router, projects_router, albert_router, payments_router, render_router, profile_router
from models import User, Client


SEED_CLIENTS = [
    {
        "name": "Apple Blossom",
        "category": "Apparel",
        "brand_notes": "Clean Punch brand: white/black serif, pink accent #D63384.",
        "continuity": {"mode": "spokesperson", "spokesperson": "friendly founder", "delivery": "warm, upbeat, and animated", "setting": "studio with soft natural light", "lighting": "soft key + fill", "brand": "clean whitespace, pink accent"},
    },
    {
        "name": "Spotlight",
        "category": "Contractor",
        "brand_notes": "Spotlight Contractor. Bold, confident, local-trust.",
        "continuity": {"mode": "spokesperson", "spokesperson": "field crew leader", "delivery": "direct, confident", "setting": "jobsite or warehouse", "lighting": "hard daylight-style", "brand": "high-contrast, logo lower-third"},
    },
    {
        "name": "MVP Transformation",
        "category": "Fitness",
        "brand_notes": "MVP Transformation. High-energy, transformation story.",
        "continuity": {"mode": "product", "delivery": "high-energy coach", "setting": "gym", "lighting": "dramatic gym lighting", "brand": "logo watermark, bold type"},
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if os.getenv("VBB_SEED_ADMIN", "").lower() == "true":
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.email == "admin@example.com").first()
            if not admin:
                from auth import hash_password
                admin_password = os.getenv("VBB_SEED_ADMIN_PASSWORD")
                if not admin_password:
                    raise RuntimeError("VBB_SEED_ADMIN=true requires VBB_SEED_ADMIN_PASSWORD to be set")
                admin = User(id="u_admin", email="admin@example.com", hashed_password=hash_password(admin_password))
                db.add(admin)
                db.flush()
                for seed in SEED_CLIENTS:
                    c = Client(
                        id=f"c_admin_{seed['name'].lower().replace(' ', '_')}",
                        user_id=admin.id,
                        name=seed["name"],
                        category=seed["category"],
                        brand_notes=seed.get("brand_notes", ""),
                        saved_continuity=seed.get("continuity"),
                    )
                    db.add(c)
            db.commit()
        finally:
            db.close()
    yield


app = FastAPI(
    title="Video Brand Builder API",
    description="Script-to-Flow-prompt workstation",
    version="0.1.0",
    lifespan=lifespan,
)

CORS_ORIGINS = os.getenv("VBB_CORS_ORIGINS", "http://localhost:3000").split(",")
# Force reload: register all routers including payments + render + albert
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(projects_router)
app.include_router(albert_router)
app.include_router(profile_router)
app.include_router(payments_router)
app.include_router(render_router)

from services.storage import generated_dir

_generated_dir = generated_dir()
print(f"[startup] {os.path.basename(__file__)}: generated dir = {_generated_dir}")
app.mount("/generated", StaticFiles(directory=str(_generated_dir)), name="generated")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "healthy", "version": "0.1.0", "service": "Video Brand Builder API"}
