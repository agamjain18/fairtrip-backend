from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database_sql import get_db, Photo, Poll, PollOption, PollVote, BucketListItem, Accommodation, Flight, Notification
from schemas_sql import (
    Photo as PhotoSchema, PhotoCreate,
    Poll as PollSchema, PollCreate,
    BucketListItem as BucketListItemSchema, BucketListItemCreate,
    Accommodation as AccommodationSchema, AccommodationCreate,
    Flight as FlightSchema, FlightCreate,
    Notification as NotificationSchema, NotificationCreate
)
from datetime import datetime, timezone

router = APIRouter(prefix="/misc", tags=["miscellaneous"])

# Photos
@router.get("/photos/trip/{trip_id}", response_model=List[PhotoSchema])
def get_trip_photos(trip_id: int, db: Session = Depends(get_db)):
    """Get all photos for a trip"""
    photos = db.query(Photo).filter(Photo.trip_id == trip_id).order_by(Photo.uploaded_at.desc()).all()
    return photos

@router.post("/photos", response_model=PhotoSchema, status_code=status.HTTP_201_CREATED)
def create_photo(photo: PhotoCreate, db: Session = Depends(get_db)):
    """Upload a new photo"""
    db_photo = Photo(**photo.dict())
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo

@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """Delete a photo"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    db.delete(photo)
    db.commit()
    return None

# Polls
@router.get("/polls/trip/{trip_id}", response_model=List[PollSchema])
def get_trip_polls(trip_id: int, db: Session = Depends(get_db)):
    """Get all polls for a trip"""
    polls = db.query(Poll).filter(Poll.trip_id == trip_id).order_by(Poll.created_at.desc()).all()
    return polls

@router.get("/polls/{poll_id}", response_model=PollSchema)
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    """Get a specific poll"""
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll

@router.post("/polls", response_model=PollSchema, status_code=status.HTTP_201_CREATED)
def create_poll(poll: PollCreate, db: Session = Depends(get_db)):
    """Create a new poll"""
    poll_data = poll.dict(exclude={'options'})
    db_poll = Poll(**poll_data)
    
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)
    
    for option_create in poll.options:
        db_option = PollOption(poll_id=db_poll.id, text=option_create.text)
        db.add(db_option)
    
    db.commit()
    db.refresh(db_poll)
    return db_poll

@router.post("/polls/{poll_id}/vote")
def vote_on_poll(poll_id: int, option_id: int, user_id: int, db: Session = Depends(get_db)):
    """Vote on a poll option"""
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    if not poll.is_active:
        raise HTTPException(status_code=400, detail="Poll is not active")
    
    existing_vote = db.query(PollVote).filter(
        PollVote.poll_option_id == option_id,
        PollVote.user_id == user_id
    ).first()
    
    if existing_vote:
        raise HTTPException(status_code=400, detail="User has already voted")
    
    vote = PollVote(poll_option_id=option_id, user_id=user_id)
    db.add(vote)
    
    option = db.query(PollOption).filter(PollOption.id == option_id).first()
    option.votes_count += 1
    
    db.commit()
    return {"message": "Vote recorded successfully"}

# Bucket List
@router.get("/bucket-list/trip/{trip_id}", response_model=List[BucketListItemSchema])
def get_bucket_list(trip_id: int, db: Session = Depends(get_db)):
    """Get bucket list for a trip"""
    items = db.query(BucketListItem).filter(BucketListItem.trip_id == trip_id).all()
    return items

@router.post("/bucket-list", response_model=BucketListItemSchema, status_code=status.HTTP_201_CREATED)
def create_bucket_list_item(item: BucketListItemCreate, db: Session = Depends(get_db)):
    """Add item to bucket list"""
    db_item = BucketListItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.post("/bucket-list/{item_id}/complete")
def complete_bucket_list_item(item_id: int, db: Session = Depends(get_db)):
    """Mark bucket list item as completed"""
    item = db.query(BucketListItem).filter(BucketListItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Bucket list item not found")
    
    item.is_completed = True
    item.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/bucket-list/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bucket_list_item(item_id: int, db: Session = Depends(get_db)):
    """Delete bucket list item"""
    item = db.query(BucketListItem).filter(BucketListItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Bucket list item not found")
    
    db.delete(item)
    db.commit()
    return None

# Accommodations
@router.get("/accommodations/trip/{trip_id}", response_model=List[AccommodationSchema])
def get_accommodations(trip_id: int, db: Session = Depends(get_db)):
    """Get all accommodations for a trip"""
    accommodations = db.query(Accommodation).filter(Accommodation.trip_id == trip_id).all()
    return accommodations

@router.post("/accommodations", response_model=AccommodationSchema, status_code=status.HTTP_201_CREATED)
def create_accommodation(accommodation: AccommodationCreate, db: Session = Depends(get_db)):
    """Add accommodation"""
    db_accommodation = Accommodation(**accommodation.dict())
    db.add(db_accommodation)
    db.commit()
    db.refresh(db_accommodation)
    return db_accommodation

@router.delete("/accommodations/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_accommodation(accommodation_id: int, db: Session = Depends(get_db)):
    """Delete accommodation"""
    accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    db.delete(accommodation)
    db.commit()
    return None

# Flights
@router.get("/flights/trip/{trip_id}", response_model=List[FlightSchema])
def get_flights(trip_id: int, db: Session = Depends(get_db)):
    """Get all flights for a trip"""
    flights = db.query(Flight).filter(Flight.trip_id == trip_id).order_by(Flight.departure_time).all()
    return flights

@router.post("/flights", response_model=FlightSchema, status_code=status.HTTP_201_CREATED)
def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
    """Add flight"""
    db_flight = Flight(**flight.dict())
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight

@router.put("/flights/{flight_id}/status")
def update_flight_status(flight_id: int, status: str, db: Session = Depends(get_db)):
    """Update flight status"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    flight.status = status
    db.commit()
    db.refresh(flight)
    return flight

@router.delete("/flights/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight(flight_id: int, db: Session = Depends(get_db)):
    """Delete flight"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    db.delete(flight)
    db.commit()
    return None

# Notifications
@router.get("/notifications/user/{user_id}", response_model=List[NotificationSchema])
def get_notifications(user_id: int, unread_only: bool = False, db: Session = Depends(get_db)):
    """Get user notifications"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifications = query.order_by(Notification.created_at.desc()).all()
    return notifications

@router.post("/notifications", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    """Create a notification"""
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}

@router.post("/notifications/user/{user_id}/read-all")
def mark_all_notifications_read(user_id: int, db: Session = Depends(get_db)):
    """Mark all notifications as read for a user"""
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
