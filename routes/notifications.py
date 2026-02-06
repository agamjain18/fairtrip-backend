from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from database import Notification, User
from schemas import Notification as NotificationSchema, NotificationCreate
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationSchema])
async def get_notifications(user_id: str, is_read: Optional[bool] = None, limit: int = 50):
    """Get notifications for a user"""
    query = {"user.$id": ObjectId(user_id)}
    
    if is_read is not None:
        query["is_read"] = is_read
    
    notifications = await Notification.find(query).sort("-created_at").limit(limit).to_list()
    return notifications

@router.get("/{notification_id}", response_model=NotificationSchema)
async def get_notification(notification_id: str):
    """Get a specific notification"""
    notification = await Notification.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/", response_model=NotificationSchema, status_code=201)
async def create_notification(notification: NotificationCreate):
    """Create a new notification"""
    user = await User.get(notification.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_notification = Notification(
        user=user,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        action_url=notification.action_url,
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    
    await db_notification.insert()
    return db_notification

@router.put("/{notification_id}/read", response_model=NotificationSchema)
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    notification = await Notification.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    await notification.save()
    return notification

@router.put("/user/{user_id}/read-all")
async def mark_all_read(user_id: str):
    """Mark all notifications as read for a user"""
    notifications = await Notification.find({
        "user.$id": ObjectId(user_id),
        "is_read": False
    }).to_list()
    
    for notification in notifications:
        notification.is_read = True
        await notification.save()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}

@router.delete("/{notification_id}", status_code=204)
async def delete_notification(notification_id: str):
    """Delete a notification"""
    notification = await Notification.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await notification.delete()
    return None

@router.get("/user/{user_id}/unread-count")
async def get_unread_count(user_id: str):
    """Get count of unread notifications for a user"""
    count = await Notification.find({
        "user.$id": ObjectId(user_id),
        "is_read": False
    }).count()
    
    return {"unread_count": count}

# Helper function to send notifications (can be called from other routes)
async def send_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "system",
    action_url: Optional[str] = None
):
    """Helper function to send a notification to a user"""
    try:
        user = await User.get(user_id)
        if not user:
            return None
        
        notification = Notification(
            user=user,
            title=title,
            message=message,
            type=notification_type,
            action_url=action_url,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        
        await notification.insert()
        return notification
    except Exception as e:
        print(f"Error sending notification: {e}")
        return None
