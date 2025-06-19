from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import HTTPException

from app.models.schedule import Appointment, AppointmentType
from app.models.client import Client
from app.models.user import User
from app.schemas.schedule import AppointmentCreate, AppointmentUpdate

class AppointmentService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_appointment(self, appointment_data: AppointmentCreate, trainer_id: int) -> Appointment:
        """Create a new appointment"""
        
        # Verify client belongs to trainer
        client = self.db.query(Client).filter(
            and_(Client.id == appointment_data.client_id, Client.trainer_id == trainer_id)
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found or not assigned to this trainer")
        
        # Check for time conflicts
        existing_appointment = self.db.query(Appointment).filter(
            and_(
                Appointment.trainer_id == trainer_id,
                Appointment.status != AppointmentStatus.CANCELLED,
                or_(
                    and_(
                        Appointment.start_time <= appointment_data.start_time,
                        Appointment.end_time > appointment_data.start_time
                    ),
                    and_(
                        Appointment.start_time < appointment_data.end_time,
                        Appointment.end_time >= appointment_data.end_time
                    ),
                    and_(
                        Appointment.start_time >= appointment_data.start_time,
                        Appointment.end_time <= appointment_data.end_time
                    )
                )
            )
        ).first()
        
        if existing_appointment:
            raise HTTPException(
                status_code=400, 
                detail=f"Time conflict with existing appointment at {existing_appointment.start_time}"
            )
        
        # Create appointment
        appointment = Appointment(
            trainer_id=trainer_id,
            **appointment_data.model_dump()
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    def get_appointments(self, trainer_id: int, date_from: Optional[date] = None, 
                        date_to: Optional[date] = None, status: Optional[str] = None,
                        page: int = 1, size: int = 50) -> tuple[List[Appointment], int]:
        """Get appointments with optional filtering"""
        
        query = self.db.query(Appointment).options(
            joinedload(Appointment.client),
            joinedload(Appointment.trainer)
        ).filter(Appointment.trainer_id == trainer_id)
        
        if date_from:
            query = query.filter(Appointment.start_time >= datetime.combine(date_from, datetime.min.time()))
        
        if date_to:
            query = query.filter(Appointment.start_time < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))
        
        if status:
            query = query.filter(Appointment.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and order
        appointments = query.order_by(asc(Appointment.start_time)).offset((page - 1) * size).limit(size).all()
        
        return appointments, total
    
    def get_todays_appointments(self, trainer_id: int) -> List[Appointment]:
        """Get today's appointments for a trainer"""
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        appointments = self.db.query(Appointment).options(
            joinedload(Appointment.client),
            joinedload(Appointment.trainer)
        ).filter(
            and_(
                Appointment.trainer_id == trainer_id,
                Appointment.start_time >= datetime.combine(today, datetime.min.time()),
                Appointment.start_time < datetime.combine(tomorrow, datetime.min.time()),
                Appointment.status != "cancelled"
            )
        ).order_by(asc(Appointment.start_time)).all()
        
        return appointments
    
    def get_appointment(self, appointment_id: int, trainer_id: int) -> Optional[Appointment]:
        """Get a specific appointment"""
        
        return self.db.query(Appointment).options(
            joinedload(Appointment.client),
            joinedload(Appointment.trainer)
        ).filter(
            and_(Appointment.id == appointment_id, Appointment.trainer_id == trainer_id)
        ).first()
    
    def update_appointment(self, appointment_id: int, trainer_id: int, 
                          appointment_data: AppointmentUpdate) -> Optional[Appointment]:
        """Update an appointment"""
        
        appointment = self.get_appointment(appointment_id, trainer_id)
        if not appointment:
            return None
        
        # Update fields
        update_data = appointment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)
        
        appointment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    def delete_appointment(self, appointment_id: int, trainer_id: int) -> bool:
        """Delete an appointment"""
        
        appointment = self.get_appointment(appointment_id, trainer_id)
        if not appointment:
            return False
        
        self.db.delete(appointment)
        self.db.commit()
        
        return True
    
    def update_appointment_status(self, appointment_id: int, trainer_id: int, 
                                 status: AppointmentStatus) -> Optional[Appointment]:
        """Update appointment status"""
        
        appointment = self.get_appointment(appointment_id, trainer_id)
        if not appointment:
            return None
        
        appointment.status = status
        appointment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment