from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class NotificationTypeEnum(str, Enum):
    WORKOUT_COMPLETED = "workout_completed"
    DAY_COMPLETED = "day_completed"
    EXERCISE_NOT_COMPLETED = "exercise_not_completed"
    APPOINTMENT_UPCOMING = "appointment_upcoming"
    APPOINTMENT_REMINDER = "appointment_reminder"
    NEW_ASSIGNMENT = "new_assignment"
    WEEKLY_EXERCISE_UPDATE = "weekly_exercise_update"


class NotificationBase(BaseModel):
    notification_type: NotificationTypeEnum
    title: str
    message: str
    related_client_id: Optional[int] = None
    related_appointment_id: Optional[int] = None
    related_workout_log_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    # Related entity names (populated by service)
    client_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    unread_count: int
    total_count: int


class NotificationMarkReadRequest(BaseModel):
    notification_ids: list[int]


class NotificationMarkReadResponse(BaseModel):
    success: bool
    marked_count: int
