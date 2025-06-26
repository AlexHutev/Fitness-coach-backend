# Weekly Exercise Assignment Model
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import date


class WeeklyExerciseStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class WeeklyExerciseAssignment(Base):
    """Individual exercise assignments broken down from program assignments"""
    __tablename__ = "weekly_exercise_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    program_assignment_id = Column(Integer, ForeignKey("program_assignments.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    # Schedule information
    assigned_date = Column(Date, nullable=False, default=func.current_date())
    due_date = Column(Date, nullable=True)
    week_number = Column(Integer, nullable=False)  # Which week of the program
    day_number = Column(Integer, nullable=False)   # Which day of the week (1-7)
    exercise_order = Column(Integer, nullable=False, default=1)  # Order within the day
    
    # Exercise parameters (from program structure)
    sets = Column(Integer, nullable=False)
    reps = Column(String(50), nullable=False)  # "10" or "8-12"
    weight = Column(String(50), nullable=True)  # "60kg" or "bodyweight"
    rest_seconds = Column(Integer, nullable=True)
    exercise_notes = Column(Text, nullable=True)
    
    # Assignment status
    status = Column(SQLEnum(WeeklyExerciseStatus), default=WeeklyExerciseStatus.PENDING)
    completed_date = Column(DateTime, nullable=True)
    
    # Performance tracking
    actual_sets_completed = Column(Integer, default=0)
    completion_percentage = Column(Integer, default=0)  # 0-100
    client_feedback = Column(Text, nullable=True)
    trainer_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    program_assignment = relationship("ProgramAssignment")
    client = relationship("Client")
    trainer = relationship("User")
    exercise = relationship("Exercise")
    
    def __repr__(self):
        return f"<WeeklyExerciseAssignment {self.exercise_id} for {self.client_id} on day {self.day_number}>"


# Add relationships to existing models
from app.models.program_assignment import ProgramAssignment
from app.models.client import Client
from app.models.user import User
from app.models.program import Exercise

# These relationships will be added when the models are imported together
