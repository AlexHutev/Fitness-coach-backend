"""Legacy appointment endpoints (not currently mounted in app.api.api).

Kept for reference; the active router is `appointments_simple.py`.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schedule import AppointmentStatus
from app.models.user import User
from app.schemas.schedule import (
    AppointmentCreate,
    AppointmentList,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.services.appointment_service import AppointmentService
from app.utils.deps import get_current_trainer

router = APIRouter()


@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    return await service.create_appointment(appointment_data, current_user.id)


@router.get("/", response_model=AppointmentList)
async def get_appointments(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    today_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    if today_only:
        appointments = await service.get_todays_appointments(current_user.id)
        return AppointmentList(
            appointments=appointments, total=len(appointments), page=1, size=len(appointments)
        )

    appointments, total = await service.get_appointments(
        trainer_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        page=page,
        size=size,
    )
    return AppointmentList(appointments=appointments, total=total, page=page, size=size)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    appointment = await service.get_appointment(appointment_id, current_user.id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    appointment = await service.update_appointment(
        appointment_id, current_user.id, appointment_data
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: int,
    status: AppointmentStatus,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    appointment = await service.update_appointment_status(
        appointment_id, current_user.id, status
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db)
    success = await service.delete_appointment(appointment_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}
