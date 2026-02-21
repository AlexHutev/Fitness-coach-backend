from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse
)

router = APIRouter(tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get notifications for the current user"""
    notifications, unread_count, total_count = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )
    
    # Enrich notifications with related entity info
    enriched_notifications = [
        NotificationService.enrich_notification_response(n, db)
        for n in notifications
    ]
    
    return NotificationListResponse(
        notifications=enriched_notifications,
        unread_count=unread_count,
        total_count=total_count
    )


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread notifications"""
    count = NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark specific notifications as read"""
    marked_count = NotificationService.mark_as_read(
        db=db,
        user_id=current_user.id,
        notification_ids=request.notification_ids
    )
    return NotificationMarkReadResponse(success=True, marked_count=marked_count)


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read"""
    marked_count = NotificationService.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    return NotificationMarkReadResponse(success=True, marked_count=marked_count)


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a notification"""
    success = NotificationService.delete_notification(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/check-appointments")
def check_appointment_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check for upcoming appointments and create reminder notifications.
    This can be called periodically by the frontend or scheduled on the backend.
    """
    notifications = NotificationService.check_and_create_appointment_reminders(
        db=db,
        trainer_id=current_user.id
    )
    return {
        "created_count": len(notifications),
        "notifications": [
            NotificationService.enrich_notification_response(n, db)
            for n in notifications
        ]
    }


@router.post("/test/create-sample")
def create_sample_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create sample notifications for testing purposes.
    This endpoint is for development/testing only.
    """
    from app.models.client import Client
    
    # Get a client for this trainer
    client = db.query(Client).filter(Client.trainer_id == current_user.id).first()
    
    created = []
    
    # Sample workout completed notification
    notification1 = NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        notification_type=NotificationType.WORKOUT_COMPLETED,
        title="Workout Completed",
        message=f"{client.first_name} {client.last_name} completed Upper Body Day" if client else "Sample Client completed Upper Body Day",
        related_client_id=client.id if client else None
    )
    created.append(NotificationService.enrich_notification_response(notification1, db))
    
    # Sample upcoming appointment notification
    notification2 = NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        notification_type=NotificationType.APPOINTMENT_UPCOMING,
        title="Upcoming: Personal Training",
        message=f"Appointment with {client.first_name} {client.last_name} tomorrow at 10:00 AM" if client else "Appointment with Sample Client tomorrow at 10:00 AM",
        related_client_id=client.id if client else None
    )
    created.append(NotificationService.enrich_notification_response(notification2, db))
    
    # Another workout notification
    notification3 = NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        notification_type=NotificationType.WORKOUT_COMPLETED,
        title="Workout Completed",
        message=f"{client.first_name} {client.last_name} completed Leg Day" if client else "Sample Client completed Leg Day",
        related_client_id=client.id if client else None
    )
    created.append(NotificationService.enrich_notification_response(notification3, db))
    
    return {
        "message": "Sample notifications created",
        "created_count": len(created),
        "notifications": created
    }
