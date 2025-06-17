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
    
    # Customization
    custom_notes = Column(Text, nullable=True)
    trainer_notes = Column(Text, nullable=True)
    
    # Progress tracking
    completion_percentage = Column(Integer, default=0)  # 0-100
    sessions_completed = Column(Integer, default=0)
    total_sessions = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    program = relationship("Program", backref="assignments")
    client = relationship("Client", backref="program_assignments")
    trainer = relationship("User", backref="program_assignments")
    
    def __repr__(self):
        return f"<ProgramAssignment {self.program_id} -> {self.client_id}>"


# Add relationships to existing models
from app.models.program import Program
from app.models.client import Client
from app.models.user import User

# These will be added when imported
