from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AssignmentStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ProgramAssignment(Base):
    __tablename__ = "program_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Assignment details
    assigned_date = Column(DateTime(timezone=True), server_default=func.now())
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(AssignmentStatus), default=AssignmentStatus.ACTIVE)
    
    # Client access credentials (for client login)
    client_access_email = Column(String(255), nullable=True)  # Optional separate client email
    client_hashed_password = Column(String(255), nullable=True)  # For client login
    
    # Customization
    custom_notes = Column(Text, nullable=True)
    trainer_notes = Column(Text, nullable=True)
    assignment_notes = Column(Text, nullable=True)
    trainer_feedback = Column(Text, nullable=True)
    
    # Progress tracking
    completion_percentage = Column(Integer, default=0)  # 0-100
    sessions_completed = Column(Integer, default=0)
    total_sessions = Column(Integer, nullable=True)
    total_workouts = Column(Integer, default=0)
    completed_workouts = Column(Integer, default=0)
    last_workout_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    program = relationship("Program")
    client = relationship("Client")
    trainer = relationship("User")
    workout_logs = relationship("WorkoutLog", back_populates="assignment")
    
    def __repr__(self):
        return f"<ProgramAssignment {self.program_id} -> {self.client_id}>"


# Add relationships to existing models
from app.models.program import Program
from app.models.client import Client
from app.models.user import User

# These will be added when imported