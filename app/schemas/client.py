from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from app.models.client import Gender, ActivityLevel, GoalType


# Base schemas
class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    body_fat_percentage: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    primary_goal: Optional[GoalType] = None
    secondary_goals: Optional[str] = None  # JSON string
    medical_conditions: Optional[str] = None
    injuries: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    custom_password: Optional[str] = None  # For account creation


class ClientCreate(ClientBase):
    @validator('height')
    def validate_height(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError('Height must be between 50 and 300 cm')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and (v < 20 or v > 500):
            raise ValueError('Weight must be between 20 and 500 kg')
        return v
    
    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Body fat percentage must be between 0 and 100')
        return v


class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    primary_goal: Optional[GoalType] = None
    secondary_goals: Optional[str] = None
    medical_conditions: Optional[str] = None
    injuries: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ClientInDB(ClientBase):
    id: int
    trainer_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Client(ClientInDB):
    pass


class ClientAccountCreate(BaseModel):
    email: EmailStr
    custom_password: Optional[str] = None  # If not provided, will generate temporary password


class ClientSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    primary_goal: Optional[GoalType] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Progress tracking schemas
class ProgressEntry(BaseModel):
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    measurements: Optional[dict] = None  # Body measurements
    notes: Optional[str] = None
    date: datetime = datetime.now()


class ProgressCreate(ProgressEntry):
    client_id: int


class ProgressInDB(ProgressEntry):
    id: int
    client_id: int
    trainer_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
