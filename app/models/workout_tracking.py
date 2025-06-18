from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Float, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class WorkoutLog(Base):
    """Individual workout session log"""
    __tablename__ = "workout_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("program_assignments.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Workout details
    workout_date = Column(DateTime, nullable=False, default=func.now())
    day_number = Column(Integer, nullable=False)  # Which day of the program (1, 2, 3...)
    workout_name = Column(String(200), nullable=True)
    
    # Performance metrics
    total_duration_minutes = Column(Integer, nullable=True)
    perceived_exertion = Column(Integer, nullable=True)  # 1-10 scale
    client_notes = Column(Text, nullable=True)
    trainer_feedback = Column(Text, nullable=True)
    
    # Status
    is_completed = Column(Boolean, default=True)
    is_skipped = Column(Boolean, default=False)
    skip_reason = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignment = relationship("ProgramAssignment", back_populates="workout_logs")
    client = relationship("Client")
    exercise_logs = relationship("ExerciseLog", back_populates="workout_log")
    
    def __repr__(self):
        return f"<WorkoutLog {self.id}: Day {self.day_number} on {self.workout_date}>"


class ExerciseLog(Base):
    """Individual exercise performance log within a workout"""
    __tablename__ = "exercise_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    workout_log_id = Column(Integer, ForeignKey("workout_logs.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)  # Reference to exercise
    
    # Exercise details (can be different from template)
    exercise_name = Column(String(200), nullable=False)
    exercise_order = Column(Integer, nullable=False, default=1)
    
    # Planned vs Actual
    planned_sets = Column(Integer, nullable=True)
    planned_reps = Column(String(50), nullable=True)  # "10" or "8-12"
    planned_weight = Column(String(50), nullable=True)  # "60kg" or "bodyweight"
    planned_rest_seconds = Column(Integer, nullable=True)
    
    # Actual performance (JSON array of sets)
    # Format: [{"set": 1, "reps": 10, "weight": "60kg", "completed": true, "notes": ""}]
    actual_sets = Column(JSON, nullable=True)
    
    # Exercise feedback
    difficulty_rating = Column(Integer, nullable=True)  # 1-10 scale
    exercise_notes = Column(Text, nullable=True)
    form_rating = Column(Integer, nullable=True)  # 1-10 scale for form quality
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workout_log = relationship("WorkoutLog", back_populates="exercise_logs")
    exercise = relationship("Exercise")
    
    def __repr__(self):
        return f"<ExerciseLog {self.exercise_name} in workout {self.workout_log_id}>"
