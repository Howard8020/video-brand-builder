from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import SessionLocal
from models import Client
from auth import get_current_user

router = APIRouter(prefix="/api/clients", tags=["clients"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ClientCreate(BaseModel):
    name: str
    category: str
    brand_notes: Optional[str] = ""
    saved_continuity: Optional[dict] = None


class ClientOut(BaseModel):
    id: str
    name: str
    category: str
    brand_notes: Optional[str]
    saved_continuity: Optional[dict]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ClientOut])
def list_clients(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Client).filter(Client.user_id == user.id).all()


@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = Client(
        id=f"c_{user.id}_{payload.name.lower().replace(' ', '_')}",
        user_id=user.id,
        name=payload.name,
        category=payload.category,
        brand_notes=payload.brand_notes or "",
        saved_continuity=payload.saved_continuity,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: str, payload: ClientCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.name = payload.name
    client.category = payload.category
    client.brand_notes = payload.brand_notes or client.brand_notes
    if payload.saved_continuity is not None:
        client.saved_continuity = payload.saved_continuity
    db.commit()
    db.refresh(client)
    return client
