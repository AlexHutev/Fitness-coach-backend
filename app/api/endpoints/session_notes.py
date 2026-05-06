from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.session_note import SessionNote
from app.models.user import User
from app.utils.deps import get_current_trainer, get_current_user

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


async def _verify_client(client_id: int, trainer_id: int, db: AsyncSession) -> Client:
    stmt = select(Client).where(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    )
    client = (await db.execute(stmt)).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/clients/{client_id}/notes", response_model=List[NoteResponse])
async def get_notes(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = (
        select(SessionNote)
        .where(SessionNote.client_id == client_id)
        .order_by(SessionNote.note_date.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post(
    "/clients/{client_id}/notes", response_model=NoteResponse, status_code=201
)
async def create_note(
    client_id: int,
    data: NoteCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    note = SessionNote(
        client_id=client_id, trainer_id=current_user.id, **data.dict()
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.put(
    "/clients/{client_id}/notes/{note_id}", response_model=NoteResponse
)
async def update_note(
    client_id: int,
    note_id: int,
    data: NoteUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(SessionNote).where(
        and_(
            SessionNote.id == note_id,
            SessionNote.client_id == client_id,
            SessionNote.trainer_id == current_user.id,
        )
    )
    note = (await db.execute(stmt)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(note, field, value)
    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/clients/{client_id}/notes/{note_id}", status_code=204)
async def delete_note(
    client_id: int,
    note_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(SessionNote).where(
        and_(
            SessionNote.id == note_id,
            SessionNote.client_id == client_id,
            SessionNote.trainer_id == current_user.id,
        )
    )
    note = (await db.execute(stmt)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()


@router.get("/my/notes", response_model=List[NoteResponse])
async def get_my_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client self-view — only non-private notes."""
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return []
    stmt = (
        select(SessionNote)
        .where(
            and_(
                SessionNote.client_id == client.id,
                SessionNote.is_private.is_(False),
            )
        )
        .order_by(SessionNote.note_date.desc())
    )
    return list((await db.execute(stmt)).scalars().all())
