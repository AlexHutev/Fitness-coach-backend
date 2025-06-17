from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.program_assignment import AssignmentStatus


# Base assignment schema
class ProgramAssignmentBase(BaseModel):
    program_id: int
    client_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_notes: Optional[str] = None
    trainer_notes: Optional[str] = None


# Schema for creating an assignment
class ProgramAssignmentCreate(ProgramAssignmentBase):
    pass


# Schema for updating an assignment
class ProgramAssignmentUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[AssignmentStatus] = None
    custom_notes: Optional[str] = None
    trainer_notes: Optional[str] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    sessions_completed: Optional[int] = Field(None, ge=0)
    total_sessions: Optional[int] = Field(None, ge=0)


# Schema for reading an assignment (full details)
class ProgramAssignment(ProgramAssignmentBase):
    id: int
    trainer_id: int
    assigned_date: datetime
    status: AssignmentStatus
    completion_percentage: int
    sessions_completed: int
    total_sessions: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Schema for assignment with related data
class ProgramAssignmentWithDetails(ProgramAssignment):
    program_name: str
    program_type: str
    program_difficulty: str
    client_name: str
    client_email: Optional[str]

    class Config:
        from_attributes = True


# Schema for listing assignments (minimal info)
class ProgramAssignmentList(BaseModel):
    id: int
    program_id: int
    program_name: str
    client_id: int
    client_name: str
    status: AssignmentStatus
    assigned_date: datetime
    start_date: Optional[datetime]
    completion_percentage: int

    class Config:
        from_attributes = True


# Schema for progress update
class ProgressUpdate(BaseModel):
    sessions_completed: int = Field(ge=0)
    completion_percentage: int = Field(ge=0, le=100)
    notes: Optional[str] = None


# Schema for bulk assignment
class BulkAssignmentCreate(BaseModel):
    program_id: int
    client_ids: List[int]
    start_date: Optional[datetime] = None
    custom_notes: Optional[str] = None

# Schema for assignment request (without program_id since it comes from URL)
class AssignmentRequest(BaseModel):
    client_ids: List[int]
    start_date: Optional[datetime] = None
    custom_notes: Optional[str] = None
