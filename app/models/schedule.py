from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime

class AppointmentType(str, enum.Enum):
    PERSONAL_TRAINING = "Personal Training"
    PROGRAM_REVIEW = "Program Review"
    INITIAL_ASSESSMENT = "Initial Assessment"
    CONSULTATION = "Consultation"
    GROUP_SESSION = "Group Session"
    FOLLOW_UP = "Follow-up"

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Appointment details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    appointment_type = Column(String(50), nullable=False)  # Use String instead of Enum
    status = Column(String(20), default="scheduled")  # Use String instead of Enum
    
    # Time details
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    
    # Additional info
    location = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trainer = relationship("User", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment(id={self.id}, client={self.client.name if self.client else 'Unknown'}, start_time={self.start_time})>"