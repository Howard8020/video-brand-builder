from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
from database import SessionLocal
from models import Client, Project
from auth import get_current_user
from services.prompts import generate_script, revise_script, revise_segment, generate_hooks, generate_scenes, revise_scenes, revise_scene, assemble_prompts, generate_caption
from services.lint import lint_claims

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now():
    return int(datetime.utcnow().timestamp() * 1000)


class ProjectCreate(BaseModel):
    client_id: str
    mode: str = "ai"
    source_script: Optional[str] = None
    brief: Dict[str, Any]
    settings: Optional[Dict[str, Any]] = None


class ProjectOut(BaseModel):
    id: str
    user_id: str
    client_id: Optional[str]
    status: str
    brief: Optional[Dict[str, Any]]
    script: Optional[Dict[str, Any]]
    continuity: Optional[Dict[str, Any]]
    scenes: Optional[Dict[str, Any]]
    prompts: Optional[Dict[str, Any]]
    versions: Optional[List[Dict[str, Any]]]
    source_script: Optional[str]
    adaptation_note: Optional[str]
    settings: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviseRequest(BaseModel):
    instruction: str
    segment_index: Optional[int] = None


class ApproveScriptRequest(BaseModel):
    draft_scenes: bool = True


class ApproveScenesRequest(BaseModel):
    instruction: Optional[str] = None


@router.get("/", response_model=List[ProjectOut])
def list_projects(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.user_id == user.id).order_by(Project.updated_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.post("/", response_model=ProjectOut)
def create_project(payload: ProjectCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = Project(
        id=f"p_{_now()}",
        user_id=user.id,
        client_id=payload.client_id,
        status="draft",
        brief=payload.brief,
        continuity=(payload.brief or {}).get("continuity") or {},
        source_script=payload.source_script,
        settings=payload.settings or {},
        versions=[],
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/generate", response_model=Dict[str, Any])
def generate_project(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        out = generate_script(proj.brief or {}, proj.settings or {}, proj.source_script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    proj.script = {"title": out.get("title"), "segments": out.get("segments", [])}
    proj.brief = {**(proj.brief or {}), **{k: v for k, v in out.items() if k in ("brief",)}}
    proj.status = "script_review"
    db.commit()
    db.refresh(proj)
    return {"script": proj.script, "brief": proj.brief, "adaptation_note": out.get("adaptation_note")}


@router.post("/{project_id}/revise", response_model=Dict[str, Any])
def revise_project(project_id: str, req: ReviseRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.script:
        raise HTTPException(status_code=404, detail="Project or script not found")
    try:
        if req.segment_index is not None:
            updated = revise_segment(proj.brief or {}, proj.script, req.segment_index, req.instruction)
            seg = proj.script["segments"][req.segment_index]
            seg.update(updated)
        else:
            updated = revise_script(proj.brief or {}, proj.script, req.instruction)
            proj.script = {"title": updated.get("title"), "segments": updated.get("segments", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revision failed: {str(e)}")
    db.commit()
    db.refresh(proj)
    return {"script": proj.script}


@router.post("/{project_id}/hooks", response_model=Dict[str, Any])
def refresh_hooks(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.script:
        raise HTTPException(status_code=404, detail="Project or script not found")
    try:
        hooks = generate_hooks(proj.brief or {}, proj.script)
        first_seg = proj.script["segments"][0]
        first_seg["spoken"] = hooks.get("hooks", [""])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hook generation failed: {str(e)}")
    db.commit()
    db.refresh(proj)
    return {"script": proj.script}


@router.post("/{project_id}/approve-script", response_model=Dict[str, Any])
def approve_script(project_id: str, req: ApproveScriptRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.script:
        raise HTTPException(status_code=404, detail="Project or script not found")
    proj.status = "scene_review"
    if req.draft_scenes:
        try:
            scenes = generate_scenes(proj.brief or {}, proj.script, proj.continuity or {})
            proj.scenes = scenes
        except Exception:
            proj.scenes = {"scenes": []}
    db.commit()
    db.refresh(proj)
    return {"status": proj.status, "scenes": proj.scenes}


@router.post("/{project_id}/scenes/revise", response_model=Dict[str, Any])
def revise_scenes_endpoint(project_id: str, req: ApproveScenesRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.scenes:
        raise HTTPException(status_code=404, detail="Project or scenes not found")
    try:
        updated = revise_scenes(proj.brief or {}, proj.script, proj.scenes, proj.continuity or {}, req.instruction or "Improve all scenes")
        proj.scenes = updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene revision failed: {str(e)}")
    db.commit()
    db.refresh(proj)
    return {"scenes": proj.scenes}


@router.post("/{project_id}/scenes/{scene_index}/revise", response_model=Dict[str, Any])
def revise_scene_endpoint(project_id: str, scene_index: int, req: ApproveScenesRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.scenes:
        raise HTTPException(status_code=404, detail="Project or scenes not found")
    try:
        updated = revise_scene(proj.brief or {}, proj.script, proj.scenes, proj.continuity or {}, scene_index, req.instruction or "Improve this scene")
        if "scenes" in updated:
            proj.scenes = updated
        else:
            scenes_list = list(proj.scenes.get("scenes", []))
            scenes_list[scene_index] = updated
            proj.scenes = {"scenes": scenes_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene revision failed: {str(e)}")
    db.commit()
    db.refresh(proj)
    return {"scenes": proj.scenes}


@router.post("/{project_id}/approve-scenes", response_model=Dict[str, Any])
def approve_scenes(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    prompts = assemble_prompts(proj.brief or {}, proj.script, proj.scenes or {}, proj.continuity or {}, proj.settings or {})
    proj.prompts = prompts
    proj.status = "approved"
    if proj.client_id:
        client = db.query(Client).filter(Client.id == proj.client_id).first()
        if client:
            client.saved_continuity = {"mode": (proj.continuity or {}).get("mode", "spokesperson"), "fields": proj.continuity or {}}
    db.commit()
    db.refresh(proj)
    return proj.prompts


@router.get("/{project_id}/prompts")
def get_prompts(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if proj.status != "approved" or not proj.prompts:
        raise HTTPException(status_code=400, detail="Prompts not ready. Approve scenes first.")
    return {
        "project": {
            "id": proj.id,
            "clientName": (proj.brief or {}).get("clientName"),
            "serviceLine": (proj.brief or {}).get("serviceLine"),
            "runtime": (proj.brief or {}).get("runtime"),
            "aspect": (proj.brief or {}).get("aspect"),
            "platform": (proj.brief or {}).get("platform"),
            "approvedAt": getattr(proj, "updated_at", None).isoformat() if getattr(proj, "updated_at", None) else None,
        },
        "prompts": proj.prompts.get("segments", []),
        "social": proj.prompts.get("social", {}),
    }


@router.post("/{project_id}/caption")
def refresh_caption(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.script:
        raise HTTPException(status_code=404, detail="Project or script not found")
    social = generate_caption(proj.brief or {}, proj.script)
    return social


@router.get("/{project_id}/lint")
def lint_project(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not proj or not proj.script:
        raise HTTPException(status_code=404, detail="Project or script not found")
    offer = (proj.brief or {}).get("offer", "")
    cta = (proj.brief or {}).get("cta", "")
    brand_notes = ""
    if proj.client_id:
        client = db.query(Client).filter(Client.id == proj.client_id).first()
        if client:
            brand_notes = client.brand_notes or ""
    flags = lint_claims(proj.script, offer, cta, brand_notes)
    return {"flags": flags}
