from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database_sql import get_db, User, Notification, Trip
from .auth import get_current_user_sql
from typing import Optional

router = APIRouter(prefix="/sync", tags=["sync"])

@router.get("/version-check/")
def sync_version_check(
    last_version: int = 0,
    trip_id: Optional[int] = None,
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    """Alias for /sync/"""
    return sync_check(last_version, trip_id, current_user, db)

@router.get("/")
def sync_check(
    last_version: int = 0,
    trip_id: Optional[int] = None,
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    """
    Fast lightweight endpoint to check if anything has changed.
    Reduced response time by avoiding heavy data fetching.
    """
    # Check if user data version has increased
    needs_refresh = (current_user.data_version or 0) > last_version
    
    # Check unread notifications
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    response = {
        "current_version": current_user.data_version or 0,
        "needs_refresh": needs_refresh,
        "unread_notifications": unread_count,
    }
    
    # If on a trip page, check trip-specific status if needed
    # Actually, data_version is incremented for trip updates too (via increment_trip_members_version)
    
    return response
