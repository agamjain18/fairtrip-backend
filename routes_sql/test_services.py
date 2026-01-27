from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from database_sql import get_db, User
from routes_sql.auth import get_current_user_sql, send_welcome_email
from routes_sql.notifications import send_notification_sql
from utils.email_service import (
    send_trip_created_email,
    send_trip_invitation_email,
    send_friend_added_email,
    send_settlement_email,
    send_trip_deleted_email
)

router = APIRouter(prefix="/test-services", tags=["Test Services"])

@router.post("/push-notification")
def test_push_notification(
    title: str = "Test Notification",
    message: str = "This is a test push notification from FairTrip!",
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    """Test push notification service for the current user"""
    notification = send_notification_sql(
        db,
        user_id=current_user.id,
        title=title,
        message=message,
        notification_type="test"
    )
    if notification:
        return {"status": "success", "message": "Notification sent"}
    return {"status": "error", "message": "Failed to send notification. Ensure FCM Token is set and Firebase Admin is initialized."}

@router.post("/email/welcome")
def test_welcome_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sql)
):
    """Test welcome email"""
    background_tasks.add_task(send_welcome_email, current_user.email, current_user.full_name or current_user.username)
    return {"status": "success", "message": "Welcome email queued"}

@router.post("/email/trip-created")
def test_trip_created_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sql)
):
    """Test trip created email"""
    background_tasks.add_task(send_trip_created_email, current_user.email, current_user.full_name or current_user.username, "Summer Vacation 2026")
    return {"status": "success", "message": "Trip created email queued"}

@router.post("/email/invitation")
def test_invitation_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sql)
):
    """Test trip invitation email"""
    background_tasks.add_task(send_trip_invitation_email, current_user.email, "John Doe", "Euro Trip")
    return {"status": "success", "message": "Invitation email queued"}

@router.post("/email/friend-added")
def test_friend_added_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sql)
):
    """Test friend added email"""
    background_tasks.add_task(send_friend_added_email, current_user.email, "Alice Smith")
    return {"status": "success", "message": "Friend added email queued"}

@router.post("/email/settlement")
def test_settlement_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sql)
):
    """Test settlement email"""
    background_tasks.add_task(send_settlement_email, current_user.email, "Bob Wilson", 150.0, "USD", "Ski Trip")
    return {"status": "success", "message": "Settlement email queued"}

@router.post("/email/trip-deleted")
def test_trip_deleted_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sql)
):
    """Test trip deleted email"""
    background_tasks.add_task(send_trip_deleted_email, current_user.email, current_user.full_name or current_user.username, "Old Trip")
    return {"status": "success", "message": "Trip deleted email queued"}
