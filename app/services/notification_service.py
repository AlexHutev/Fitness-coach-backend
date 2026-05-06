from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select, update
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.notification import Notification, NotificationType
from app.models.schedule import Appointment
from app.models.workout_tracking import WorkoutLog


class NotificationService:
    """Service for managing notifications."""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_client_id: Optional[int] = None,
        related_appointment_id: Optional[int] = None,
        related_workout_log_id: Optional[int] = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_client_id=related_client_id,
            related_appointment_id=related_appointment_id,
            related_workout_log_id=related_workout_log_id,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> Tuple[List[Notification], int, int]:
        total_count = int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(Notification)
                    .where(Notification.user_id == user_id)
                )
            ).scalar_one()
        )
        unread_count = int(
            (
                await db.execute(
                    select(func.count())
                    .select_from(Notification)
                    .where(
                        Notification.user_id == user_id,
                        Notification.is_read.is_(False),
                    )
                )
            ).scalar_one()
        )

        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        notifications = list(result.scalars().all())

        return notifications, unread_count, total_count

    @staticmethod
    async def mark_as_read(
        db: AsyncSession, user_id: int, notification_ids: List[int]
    ) -> int:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                )
            )
            .values(is_read=True, read_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: int) -> int:
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                )
            )
            .values(is_read=True, read_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def delete_notification(
        db: AsyncSession, user_id: int, notification_id: int
    ) -> bool:
        stmt = (
            sql_delete(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(stmt)
        await db.commit()
        return (result.rowcount or 0) > 0

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                )
            )
        )
        return int((await db.execute(stmt)).scalar_one())

    # ==================== WORKOUT COMPLETION NOTIFICATIONS ====================

    @staticmethod
    async def create_workout_completed_notification(
        db: AsyncSession,
        trainer_id: int,
        client: Client,
        workout_log: WorkoutLog,
    ) -> Notification:
        client_name = f"{client.first_name} {client.last_name}"
        workout_name = workout_log.workout_name or f"Day {workout_log.day_number}"
        return await NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.WORKOUT_COMPLETED,
            title="Workout Completed",
            message=f"{client_name} completed {workout_name}",
            related_client_id=client.id,
            related_workout_log_id=workout_log.id,
        )

    # ==================== APPOINTMENT NOTIFICATIONS ====================

    @staticmethod
    async def create_upcoming_appointment_notification(
        db: AsyncSession,
        trainer_id: int,
        appointment: Appointment,
        client: Client,
        hours_before: int = 24,
    ) -> Notification:
        client_name = f"{client.first_name} {client.last_name}"
        time_str = appointment.start_time.strftime("%I:%M %p on %b %d")

        if hours_before <= 1:
            time_desc = "in 1 hour"
        elif hours_before < 24:
            time_desc = f"in {hours_before} hours"
        else:
            days = hours_before // 24
            time_desc = "tomorrow" if days == 1 else f"in {days} days"

        return await NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.APPOINTMENT_UPCOMING,
            title=f"Upcoming: {appointment.title}",
            message=f"Appointment with {client_name} {time_desc} at {time_str}",
            related_client_id=client.id,
            related_appointment_id=appointment.id,
        )

    @staticmethod
    async def check_and_create_appointment_reminders(
        db: AsyncSession,
        trainer_id: int,
        reminder_hours: List[int] = [24, 1],
    ) -> List[Notification]:
        created_notifications: List[Notification] = []
        now = datetime.utcnow()

        for hours in reminder_hours:
            window_start = now + timedelta(hours=hours - 0.5)
            window_end = now + timedelta(hours=hours + 0.5)

            appts_stmt = (
                select(Appointment)
                .where(
                    and_(
                        Appointment.trainer_id == trainer_id,
                        Appointment.start_time >= window_start,
                        Appointment.start_time <= window_end,
                        Appointment.status.in_(["scheduled", "confirmed", "pending"]),
                    )
                )
            )
            appointments = list((await db.execute(appts_stmt)).scalars().all())

            for appointment in appointments:
                existing_stmt = select(Notification).where(
                    and_(
                        Notification.user_id == trainer_id,
                        Notification.related_appointment_id == appointment.id,
                        Notification.notification_type == NotificationType.APPOINTMENT_UPCOMING,
                        Notification.created_at >= now - timedelta(hours=1),
                    )
                )
                existing = (await db.execute(existing_stmt)).scalar_one_or_none()

                if not existing and appointment.client:
                    notification = await NotificationService.create_upcoming_appointment_notification(
                        db=db,
                        trainer_id=trainer_id,
                        appointment=appointment,
                        client=appointment.client,
                        hours_before=hours,
                    )
                    created_notifications.append(notification)

        return created_notifications

    @staticmethod
    async def enrich_notification_response(
        notification: Notification, db: AsyncSession
    ) -> dict:
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
            "client_name": None,
        }

        if notification.related_client_id:
            client = (
                await db.execute(
                    select(Client).where(Client.id == notification.related_client_id)
                )
            ).scalar_one_or_none()
            if client:
                response["client_name"] = f"{client.first_name} {client.last_name}"

        return response

    # ==================== DAILY EXERCISE NOTIFICATIONS ====================

    @staticmethod
    async def create_day_completed_notification(
        db: AsyncSession,
        trainer_id: int,
        client: Client,
        day_name: str,
        exercises_completed: int,
        total_exercises: int,
    ) -> Notification:
        client_name = f"{client.first_name} {client.last_name}"
        return await NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.DAY_COMPLETED,
            title="Daily Workout Completed",
            message=f"{client_name} completed all {exercises_completed} exercises for {day_name}",
            related_client_id=client.id,
        )

    @staticmethod
    async def create_exercise_not_completed_notification(
        db: AsyncSession,
        trainer_id: int,
        client: Client,
        exercise_name: str,
        reason: str,
    ) -> Notification:
        client_name = f"{client.first_name} {client.last_name}"
        reason_preview = reason[:150] + "..." if len(reason) > 150 else reason
        return await NotificationService.create_notification(
            db=db,
            user_id=trainer_id,
            notification_type=NotificationType.EXERCISE_NOT_COMPLETED,
            title="Exercise Not Completed",
            message=f"{client_name} could not complete '{exercise_name}': {reason_preview}",
            related_client_id=client.id,
        )
