from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.schedule import Appointment
from app.models.user import User
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class ClientBasic(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


class AppointmentResponse(BaseModel):
    id: int
    trainer_id: int
    client_id: int
    title: str
    description: Optional[str] = None
    appointment_type: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    client: Optional[ClientBasic] = None

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    client_id: int
    title: str
    description: Optional[str] = None
    appointment_type: str = "Personal Training"
    start_time: datetime
    end_time: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    notes: Optional[str] = None
    status: str = "scheduled"

    @validator("end_time")
    def end_after_start(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class AppointmentUpdate(BaseModel):
    client_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_appointment_or_404(
    appointment_id: int, trainer_id: int, db: AsyncSession
) -> Appointment:
    stmt = select(Appointment).where(
        and_(Appointment.id == appointment_id, Appointment.trainer_id == trainer_id)
    )
    appt = (await db.execute(stmt)).scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


# ── Static routes (registered before dynamic /{id}) ──────────────────────────

@router.get("/today", response_model=List[AppointmentResponse])
async def get_today_appointments(
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    day_start = datetime(today.year, today.month, today.day, 0, 0, 0)
    day_end = datetime(today.year, today.month, today.day, 23, 59, 59)
    stmt = (
        select(Appointment)
        .where(
            and_(
                Appointment.trainer_id == current_user.id,
                Appointment.start_time >= day_start,
                Appointment.start_time <= day_end,
            )
        )
        .order_by(Appointment.start_time.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.get("/my", response_model=List[AppointmentResponse])
async def get_my_appointments(
    upcoming_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client-facing: appointments for the logged-in client."""
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return []
    stmt = select(Appointment).where(Appointment.client_id == client.id)
    if upcoming_only:
        stmt = stmt.where(Appointment.start_time >= datetime.utcnow())
    stmt = stmt.order_by(Appointment.start_time.asc())
    return list((await db.execute(stmt)).scalars().all())


@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Appointment).where(Appointment.trainer_id == current_user.id)
    if date_from:
        stmt = stmt.where(Appointment.start_time >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.start_time <= date_to)
    if status:
        stmt = stmt.where(Appointment.status == status)
    stmt = stmt.order_by(Appointment.start_time.asc()).offset(skip).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    client = (
        await db.execute(
            select(Client).where(
                and_(Client.id == data.client_id, Client.trainer_id == current_user.id)
            )
        )
    ).scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=404, detail="Client not found or does not belong to you"
        )

    title = (
        data.title.strip()
        if data.title.strip()
        else f"{data.appointment_type} - {client.first_name} {client.last_name}"
    )
    appt = Appointment(
        trainer_id=current_user.id,
        client_id=data.client_id,
        title=title,
        description=data.description,
        appointment_type=data.appointment_type,
        status=data.status,
        start_time=data.start_time,
        end_time=data.end_time,
        duration_minutes=data.duration_minutes,
        location=data.location,
        notes=data.notes,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt


# ── Dynamic /{appointment_id} routes ─────────────────────────────────────────

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    return await _get_appointment_or_404(appointment_id, current_user.id, db)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    appt = await _get_appointment_or_404(appointment_id, current_user.id, db)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(appt, field, value)
    appt.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(appt)
    return appt


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_status(
    appointment_id: int,
    data: StatusUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    appt = await _get_appointment_or_404(appointment_id, current_user.id, db)
    appt.status = data.status
    appt.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(appt)
    return appt


@router.delete("/{appointment_id}", status_code=204)
async def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    appt = await _get_appointment_or_404(appointment_id, current_user.id, db)
    await db.delete(appt)
    await db.commit()
