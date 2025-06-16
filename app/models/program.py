from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Float, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ProgramType(enum.Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"
    FUNCTIONAL = "functional"
    SPORTS_SPECIFIC = "sports_specific"
    REHABILITATION = "rehabilitation"
    MIXED = "mixed"


class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Program(Base):
    __tablename__ = "programs"
    
    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Program details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    program_type = Column(SQLEnum(ProgramType), nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    duration_weeks = Column(Integer, nullable=True)
    sessions_per_week = Column(Integer, nullable=True)
    
    # Program structure (JSON)
    # Structure: [{"day": 1, "exercises": [{"name": "...", "sets": 3, "reps": 10, ...}]}]
    workout_structure = Column(JSON, nullable=True)
    
    # Tags and categories
    tags = Column(Text, nullable=True)  # Comma-separated tags
    equipment_needed = Column(Text, nullable=True)  # JSON list
    
    # Status
    is_template = Column(Boolean, default=True)  # Template or assigned to specific client
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trainer = relationship("User", back_populates="programs")
    
    def __repr__(self):
        return f"<Program {self.name}>"


class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Exercise details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    muscle_groups = Column(Text, nullable=True)  # JSON list
    equipment = Column(Text, nullable=True)  # JSON list
    difficulty_level = Column(String(20), nullable=True)
    
    # Media
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Exercise {self.name}>"


# Add relationships to User model
from app.models.user import User
User.programs = relationship("Program", back_populates="trainer")
User.exercises = relationship("Exercise", foreign_keys=[Exercise.created_by])
