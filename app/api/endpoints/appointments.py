from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.utils.deps import get_current_trainer
from app.models.user import User
from app.schemas.schedule import (
    AppointmentCreate, 
    AppointmentUpdate, 
    AppointmentResponse, 
    AppointmentList
)
from app.services.appointment_service import AppointmentService

router = APIRouter()

@router.post("/", response_model=AppointmentResponse)
def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Create a new appointment"""
    service = AppointmentService(db)
    appointment = service.create_appointment(appointment_data, current_user.id)
    return appointment

@router.get("/", response_model=AppointmentList)
def get_appointments(
    date_from: Optional[date] = Query(None, description="Filter appointments from this date"),
    date_to: Optional[date] = Query(None, description="Filter appointments to this date"),
    status: Optional[str] = Query(None, description="Filter by appointment status"),
    today_only: bool = Query(False, description="Get only today's appointments"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get appointments with optional filtering"""
    service = AppointmentService(db)
    
    # Handle today_only filter
    if today_only:
        # Let's return a simple hard-coded response to test
        return {
            "appointments": [],
            "total": 0,
            "page": 1,
            "size": 0,
            "debug": "Hard-coded response"
        }
    
    appointments, total = service.get_appointments(
        trainer_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        page=page,
        size=size
    )
    
    return AppointmentList(
        appointments=appointments,
        total=total,
        page=page,
        size=size
    )

# Remove the problematic /today route and keep the existing /{appointment_id} route

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get a specific appointment"""
    service = AppointmentService(db)
    appointment = service.get_appointment(appointment_id, current_user.id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment

@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update an appointment"""
    service = AppointmentService(db)
    appointment = service.update_appointment(appointment_id, current_user.id, appointment_data)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status: AppointmentStatus,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update appointment status"""
    service = AppointmentService(db)
    appointment = service.update_appointment_status(appointment_id, current_user.id, status)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment

@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Delete an appointment"""
    service = AppointmentService(db)
    success = service.delete_appointment(appointment_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": "Appointment deleted successfully"}