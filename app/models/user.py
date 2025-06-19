from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(enum.Enum):
    TRAINER = "trainer"
    CLIENT = "client"
    ADMIN = "admin"


class SpecializationType(enum.Enum):
    PERSONAL_TRAINING = "personal-training"
    STRENGTH_CONDITIONING = "strength-conditioning"
    WEIGHT_LOSS = "weight-loss"
    BODYBUILDING = "bodybuilding"
    FUNCTIONAL_FITNESS = "functional-fitness"
    SPORTS_SPECIFIC = "sports-specific"
    REHABILITATION = "rehabilitation"
    NUTRITION = "nutrition"
    OTHER = "other"


class ExperienceLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"
    EXPERT = "expert"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Professional details
    specialization = Column(SQLEnum(SpecializationType), nullable=True)
    experience = Column(SQLEnum(ExperienceLevel), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(SQLEnum(UserRole), default=UserRole.TRAINER)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="trainer")
    
    def __repr__(self):
        return f"<User {self.email}>"
