from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from app.models.schedule import AppointmentType

class AppointmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    appointment_type: str  # Changed from AppointmentType enum to string
    start_time: datetime
    end_time: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('End time must be after start time')
        return v

class AppointmentCreate(AppointmentBase):
    client_id: int
    status: str = "scheduled"  # Changed from AppointmentStatus enum to string

class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_type: Optional[str] = None  # Changed from AppointmentType enum to string
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # Changed from AppointmentStatus enum to string

class ClientBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None

class TrainerBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    first_name: str
    last_name: str
    email: str

class AppointmentResponse(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    trainer_id: int
    client_id: int
    status: str  # Changed from AppointmentStatus enum to string
    created_at: datetime
    updated_at: datetime
    
    # Related objects
    client: Optional[ClientBasic] = None
    trainer: Optional[TrainerBasic] = None

class AppointmentList(BaseModel):
    appointments: list[AppointmentResponse]
    total: int
    page: int
    size: int