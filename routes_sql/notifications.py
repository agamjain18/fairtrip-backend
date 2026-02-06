from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session
from database_sql import Notification, User, get_db
from schemas_sql import Notification as NotificationSchema, NotificationCreate
from datetime import datetime, timezone
from utils.timezone_utils import get_ist_now

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationSchema])
def get_notifications(user_id: int, is_read: Optional[bool] = None, limit: int = 50, db: Session = Depends(get_db)):
    """Get notifications for a user"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifications

@router.get("/{notification_id}", response_model=NotificationSchema)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """Get a specific notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    """Create a new notification"""
    user = db.query(User).filter(User.id == notification.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_notification = Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        action_url=notification.action_url,
        is_read=False,
        created_at=get_ist_now()
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.put("/{notification_id}/read", response_model=NotificationSchema)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

@router.put("/user/{user_id}/read-all")
def mark_all_read(user_id: int, db: Session = Depends(get_db)):
    """Mark all notifications as read for a user"""
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return {"message": "All notifications marked as read"}

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete a notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return None

@router.get("/user/{user_id}/unread-count")
def get_unread_count(user_id: int, db: Session = Depends(get_db)):
    """Get count of unread notifications for a user"""
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}

# Helper function to send notifications
def send_notification_sql(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "system",
    action_url: Optional[str] = None
):
    """Helper function to create a notification and send push if available"""
    try:
        # 1. Save to database for in-app history
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            action_url=action_url,
            is_read=False,
            created_at=get_ist_now()
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # 2. Send Push Notification via Firebase
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.fcm_token and user.push_notifications:
            from services.firebase_service import FirebaseService
            FirebaseService.send_push_notification(
                token=user.fcm_token,
                title=title,
                body=message,
                data={
                    "type": notification_type,
                    "action_url": action_url or "",
                    "notification_id": str(notification.id)
                }
            )

        return notification
    except Exception as e:
        print(f"Error sending notification: {e}")
        return None
