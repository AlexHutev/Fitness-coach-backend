from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class NotificationType(enum.Enum):
    WORKOUT_COMPLETED = "workout_completed"
    DAY_COMPLETED = "day_completed"
    EXERCISE_NOT_COMPLETED = "exercise_not_completed"
    APPOINTMENT_UPCOMING = "appointment_upcoming"
    APPOINTMENT_REMINDER = "appointment_reminder"
    # Future types for client notifications
    NEW_ASSIGNMENT = "new_assignment"
    WEEKLY_EXERCISE_UPDATE = "weekly_exercise_update"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who receives this notification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Related entities (optional, for linking to specific items)
    related_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    related_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    related_workout_log_id = Column(Integer, ForeignKey("workout_logs.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    related_client = relationship("Client", foreign_keys=[related_client_id])
    related_appointment = relationship("Appointment", foreign_keys=[related_appointment_id])
    related_workout_log = relationship("WorkoutLog", foreign_keys=[related_workout_log_id])
    
    def __repr__(self):
        return f"<Notification {self.id}: {self.notification_type.value} for user {self.user_id}>"
