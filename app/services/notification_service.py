from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.notification import Notification, NotificationType
from app.models.client import Client
from app.models.schedule import Appointment
from app.models.workout_tracking import WorkoutLog
from app.schemas.notification import NotificationCreate, NotificationResponse


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_client_id: Optional[int] = None,
        related_appointment_id: Optional[int] = None,
        related_workout_log_id: Optional[int] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_client_id=related_client_id,
            related_appointment_id=related_appointment_id,
            related_workout_log_id=related_workout_log_id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> tuple[List[Notification], int, int]:
        """
        Get notifications for a user
        Returns: (notifications, unread_count, total_count)
        """
        base_query = db.query(Notification).filter(Notification.user_id == user_id)
        
        # Get total count
        total_count = base_query.count()
        
        # Get unread count
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        # Apply unread filter if requested
        if unread_only:
            base_query = base_query.filter(Notification.is_read == False)
        
        # Order by created_at descending and apply pagination
        notifications = base_query.order_by(Notification.created_at.desc())\
            .offset(offset).limit(limit).all()
        
        return notifications, unread_count, total_count
    
    @staticmethod
    def mark_as_read(db: Session, user_id: int, notification_ids: List[int]) -> int:
        """Mark notifications as read. Returns count of updated notifications."""
        result = db.query(Notification).filter(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        }, synchronize_session=False)
        db.commit()
        return result
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        result = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        }, synchronize_session=False)
        db.commit()
        return result

    @staticmethod
    def delete_notification(db: Session, user_id: int, notification_id: int) -> bool:
        """Delete a notification"""
        result = db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).delete(synchronize_session=False)
        db.commit()
        return result > 0
    
    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Get count of unread notifications"""
        return db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).count()
    
    # ==================== WORKOUT COMPLETION NOTIFICATIONS ====================
    
    @staticmethod
    def create_workout_completed_notification(
        db: Session,
        trainer_id: int,
        client: Client,
        workout_log: WorkoutLog
    ) -> Notification:
        """Create a notification when a client completes a workout"""
        client_name = f"{client.first_name} {client.last_name}"
        workout_name = workout_log.workout_name or f"Day {workout_log.day_number}"
        
        return NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.WORKOUT_COMPLETED,
            title="Workout Completed",
            message=f"{client_name} completed {workout_name}",
            related_client_id=client.id,
            related_workout_log_id=workout_log.id
        )

    # ==================== APPOINTMENT NOTIFICATIONS ====================
    
    @staticmethod
    def create_upcoming_appointment_notification(
        db: Session,
        trainer_id: int,
        appointment: Appointment,
        client: Client,
        hours_before: int = 24
    ) -> Notification:
        """Create a notification for an upcoming appointment"""
        client_name = f"{client.first_name} {client.last_name}"
        time_str = appointment.start_time.strftime("%I:%M %p on %b %d")
        
        if hours_before <= 1:
            time_desc = "in 1 hour"
        elif hours_before < 24:
            time_desc = f"in {hours_before} hours"
        else:
            days = hours_before // 24
            time_desc = f"tomorrow" if days == 1 else f"in {days} days"
        
        return NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.APPOINTMENT_UPCOMING,
            title=f"Upcoming: {appointment.title}",
            message=f"Appointment with {client_name} {time_desc} at {time_str}",
            related_client_id=client.id,
            related_appointment_id=appointment.id
        )
    
    @staticmethod
    def check_and_create_appointment_reminders(
        db: Session,
        trainer_id: int,
        reminder_hours: List[int] = [24, 1]
    ) -> List[Notification]:
        """
        Check for upcoming appointments and create reminder notifications.
        Default: 24 hours and 1 hour before.
        """
        created_notifications = []
        now = datetime.utcnow()
        
        for hours in reminder_hours:
            window_start = now + timedelta(hours=hours - 0.5)
            window_end = now + timedelta(hours=hours + 0.5)
            
            # Find appointments in this window
            appointments = db.query(Appointment).filter(
                and_(
                    Appointment.trainer_id == trainer_id,
                    Appointment.start_time >= window_start,
                    Appointment.start_time <= window_end,
                    Appointment.status.in_(["scheduled", "confirmed", "pending"])
                )
            ).all()
            
            for appointment in appointments:
                # Check if we already created a notification for this
                existing = db.query(Notification).filter(
                    and_(
                        Notification.user_id == trainer_id,
                        Notification.related_appointment_id == appointment.id,
                        Notification.notification_type == NotificationType.APPOINTMENT_UPCOMING,
                        Notification.created_at >= now - timedelta(hours=1)
                    )
                ).first()
                
                if not existing and appointment.client:
                    notification = NotificationService.create_upcoming_appointment_notification(
                        db=db,
                        trainer_id=trainer_id,
                        appointment=appointment,
                        client=appointment.client,
                        hours_before=hours
                    )
                    created_notifications.append(notification)
        
        return created_notifications
    
    @staticmethod
    def enrich_notification_response(
        notification: Notification,
        db: Session
    ) -> dict:
        """Add related entity information to notification response"""
        response = {
            "id": notification.id,
            "user_id": notification.user_id,
            "notification_type": notification.notification_type.value,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "read_at": notification.read_at,
            "created_at": notification.created_at,
            "related_client_id": notification.related_client_id,
            "related_appointment_id": notification.related_appointment_id,
            "related_workout_log_id": notification.related_workout_log_id,
            "client_name": None
        }
        
        # Add client name if available
        if notification.related_client_id:
            client = db.query(Client).filter(
                Client.id == notification.related_client_id
            ).first()
            if client:
                response["client_name"] = f"{client.first_name} {client.last_name}"
        
        return response

    # ==================== DAILY EXERCISE NOTIFICATIONS ====================
    
    @staticmethod
    def create_day_completed_notification(
        db: Session,
        trainer_id: int,
        client: Client,
        day_name: str,
        exercises_completed: int,
        total_exercises: int
    ) -> Notification:
        """Create a notification when a client completes all exercises for a day"""
        client_name = f"{client.first_name} {client.last_name}"
        
        return NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.DAY_COMPLETED,
            title="Daily Workout Completed",
            message=f"{client_name} completed all {exercises_completed} exercises for {day_name}",
            related_client_id=client.id
        )
    
    @staticmethod
    def create_exercise_not_completed_notification(
        db: Session,
        trainer_id: int,
        client: Client,
        exercise_name: str,
        reason: str
    ) -> Notification:
        """Create a notification when a client marks an exercise as not completed"""
        client_name = f"{client.first_name} {client.last_name}"
        
        # Truncate reason if too long for preview
        reason_preview = reason[:150] + "..." if len(reason) > 150 else reason
        
        return NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.EXERCISE_NOT_COMPLETED,
            title="Exercise Not Completed",
            message=f"{client_name} could not complete '{exercise_name}': {reason_preview}",
            related_client_id=client.id
        )
