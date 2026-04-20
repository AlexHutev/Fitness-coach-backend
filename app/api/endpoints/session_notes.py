from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.utils.deps import get_current_trainer, get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.session_note import SessionNote

router = APIRouter()


class NoteCreate(BaseModel):
    note_date: date
    title: Optional[str] = None
    content: str
    is_private: bool = False
    appointment_id: Optional[int] = None


class NoteUpdate(BaseModel):
    note_date: Optional[date] = None
    title: Optional[str] = None
    content: Optional[str] = None
    is_private: Optional[bool] = None


class NoteResponse(BaseModel):
    id: int
    client_id: int
    trainer_id: int
    appointment_id: Optional[int]
    note_date: date
    title: Optional[str]
    content: str
    is_private: bool

    class Config:
        from_attributes = True


def verify_client(client_id: int, trainer_id: int, db: Session) -> Client:
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/clients/{client_id}/notes", response_model=List[NoteResponse])
def get_notes(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    return db.query(SessionNote).filter(
        SessionNote.client_id == client_id
    ).order_by(SessionNote.note_date.desc()).all()


@router.post("/clients/{client_id}/notes", response_model=NoteResponse, status_code=201)
def create_note(
    client_id: int,
    data: NoteCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    note = SessionNote(client_id=client_id, trainer_id=current_user.id, **data.dict())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/clients/{client_id}/notes/{note_id}", response_model=NoteResponse)
def update_note(
    client_id: int,
    note_id: int,
    data: NoteUpdate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    note = db.query(SessionNote).filter(
        and_(SessionNote.id == note_id, SessionNote.client_id == client_id,
             SessionNote.trainer_id == current_user.id)
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/clients/{client_id}/notes/{note_id}", status_code=204)
def delete_note(
    client_id: int,
    note_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    note = db.query(SessionNote).filter(
        and_(SessionNote.id == note_id, SessionNote.client_id == client_id,
             SessionNote.trainer_id == current_user.id)
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()


@router.get("/my/notes", response_model=List[NoteResponse])
def get_my_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client self-view — only non-private notes."""
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        return []
    return db.query(SessionNote).filter(
        and_(SessionNote.client_id == client.id, SessionNote.is_private == False)
    ).order_by(SessionNote.note_date.desc()).all()
