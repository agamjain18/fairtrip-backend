from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database_sql import get_db, ItineraryDay, Activity, Trip, increment_trip_members_version
from schemas_sql import ItineraryDay as ItineraryDaySchema, ItineraryDayCreate, Activity as ActivitySchema, ActivityCreate
from datetime import datetime, timezone
from utils.timezone_utils import get_ist_now

router = APIRouter(prefix="/itinerary", tags=["itinerary"])

@router.get("/trip/{trip_id}/", response_model=List[ItineraryDaySchema])
def get_trip_itinerary(trip_id: int, db: Session = Depends(get_db)):
    """Get full itinerary for a trip (all days with activities)"""
    days = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip_id).order_by(ItineraryDay.day_number).all()
    return days

@router.get("/trip/{trip_id}/days", response_model=List[ItineraryDaySchema])
def get_itinerary_days(trip_id: int, db: Session = Depends(get_db)):
    """Get all itinerary days for a trip"""
    days = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip_id).order_by(ItineraryDay.day_number).all()
    return days

@router.get("/days/{day_id}", response_model=ItineraryDaySchema)
def get_itinerary_day(day_id: int, db: Session = Depends(get_db)):
    """Get a specific itinerary day"""
    day = db.query(ItineraryDay).filter(ItineraryDay.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    return day

@router.post("/days", response_model=ItineraryDaySchema, status_code=status.HTTP_201_CREATED)
def create_itinerary_day(day: ItineraryDayCreate, db: Session = Depends(get_db)):
    """Create a new itinerary day"""
    trip = db.query(Trip).filter(Trip.id == day.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db_day = ItineraryDay(
        trip_id=day.trip_id,
        day_number=day.day_number,
        date=day.date,
        title=day.title,
        description=day.description,
        created_at=get_ist_now(),
        updated_at=get_ist_now()
    )
    db.add(db_day)
    db.commit()
    db.refresh(db_day)
    
    # Real-time sync
    increment_trip_members_version(db, db_day.trip_id)
    return db_day

@router.put("/days/{day_id}", response_model=ItineraryDaySchema)
def update_itinerary_day(day_id: int, day_update: ItineraryDayCreate, db: Session = Depends(get_db)):
    """Update itinerary day"""
    day = db.query(ItineraryDay).filter(ItineraryDay.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    
    update_data = day_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(day, key, value)
        
    day.updated_at = get_ist_now()
    db.commit()
    db.refresh(day)
    
    # Real-time sync
    increment_trip_members_version(db, day.trip_id)
    return day

@router.delete("/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itinerary_day(day_id: int, db: Session = Depends(get_db)):
    """Delete an itinerary day"""
    day = db.query(ItineraryDay).filter(ItineraryDay.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    
    db.delete(day)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    return None

# Activity routes
@router.get("/days/{day_id}/activities", response_model=List[ActivitySchema])
def get_activities(day_id: int, db: Session = Depends(get_db)):
    """Get all activities for a day"""
    activities = db.query(Activity).filter(Activity.day_id == day_id).order_by(Activity.start_time).all()
    return activities

@router.get("/activities/{activity_id}", response_model=ActivitySchema)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """Get a specific activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.post("/activities", response_model=ActivitySchema, status_code=status.HTTP_201_CREATED)
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    """Create a new activity"""
    day = db.query(ItineraryDay).filter(ItineraryDay.id == activity.day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")

    db_activity = Activity(
        day_id=activity.day_id,
        title=activity.title,
        description=activity.description,
        type=activity.type,
        location=activity.location,
        address=activity.address,
        start_time=activity.start_time,
        end_time=activity.end_time,
        duration_minutes=activity.duration_minutes,
        cost=activity.cost,
        booking_url=activity.booking_url,
        booking_reference=activity.booking_reference,
        notes=activity.notes,
        latitude=activity.latitude,
        longitude=activity.longitude,
        created_at=get_ist_now(),
        updated_at=get_ist_now()
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    # Real-time sync
    day = db.query(ItineraryDay).filter(ItineraryDay.id == db_activity.day_id).first()
    if day:
        increment_trip_members_version(db, day.trip_id)
        
    return db_activity

@router.put("/activities/{activity_id}", response_model=ActivitySchema)
def update_activity(activity_id: int, activity_update: ActivityCreate, db: Session = Depends(get_db)):
    """Update activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    update_data = activity_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(activity, key, value)
        
    activity.updated_at = get_ist_now()
    db.commit()
    db.refresh(activity)
    
    # Real-time sync
    day = db.query(ItineraryDay).filter(ItineraryDay.id == activity.day_id).first()
    if day:
        increment_trip_members_version(db, day.trip_id)
        
    return activity

@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    """Delete an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    day_id = activity.day_id
    db.delete(activity)
    db.commit()
    
    # Real-time sync
    day = db.query(ItineraryDay).filter(ItineraryDay.id == day_id).first()
    if day:
        increment_trip_members_version(db, day.trip_id)
        
    return None
