from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
)
from app.services.notification_service import NotificationService
from app.utils.deps import get_current_active_user

router = APIRouter(tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    notifications, unread_count, total_count = await NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    enriched = [
        await NotificationService.enrich_notification_response(n, db) for n in notifications
    ]
    return NotificationListResponse(
        notifications=enriched, unread_count=unread_count, total_count=total_count
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    marked = await NotificationService.mark_as_read(
        db=db, user_id=current_user.id, notification_ids=request.notification_ids
    )
    return NotificationMarkReadResponse(success=True, marked_count=marked)


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    marked = await NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return NotificationMarkReadResponse(success=True, marked_count=marked)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    success = await NotificationService.delete_notification(
        db=db, user_id=current_user.id, notification_id=notification_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/check-appointments")
async def check_appointment_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Scan upcoming appointments and create reminder notifications."""
    notifications = await NotificationService.check_and_create_appointment_reminders(
        db=db, trainer_id=current_user.id
    )
    enriched = [
        await NotificationService.enrich_notification_response(n, db) for n in notifications
    ]
    return {"created_count": len(notifications), "notifications": enriched}


@router.post("/test/create-sample")
async def create_sample_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create sample notifications for development/testing only."""
    client = (
        await db.execute(select(Client).where(Client.trainer_id == current_user.id))
    ).scalars().first()

    titles_messages = [
        (
            NotificationType.WORKOUT_COMPLETED,
            "Workout Completed",
            f"{client.first_name} {client.last_name} completed Upper Body Day"
            if client
            else "Sample Client completed Upper Body Day",
        ),
        (
            NotificationType.APPOINTMENT_UPCOMING,
            "Upcoming: Personal Training",
            f"Appointment with {client.first_name} {client.last_name} tomorrow at 10:00 AM"
            if client
            else "Appointment with Sample Client tomorrow at 10:00 AM",
        ),
        (
            NotificationType.WORKOUT_COMPLETED,
            "Workout Completed",
            f"{client.first_name} {client.last_name} completed Leg Day"
            if client
            else "Sample Client completed Leg Day",
        ),
    ]

    created = []
    for notification_type, title, message in titles_messages:
        n = await NotificationService.create_notification(
            db=db,
            user_id=current_user.id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_client_id=client.id if client else None,
        )
        created.append(await NotificationService.enrich_notification_response(n, db))

    return {
        "message": "Sample notifications created",
        "created_count": len(created),
        "notifications": created,
    }
