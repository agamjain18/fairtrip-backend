from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db, ItineraryDay, Activity
from schemas import ItineraryDay as ItineraryDaySchema, ItineraryDayCreate, Activity as ActivitySchema, ActivityCreate
from datetime import datetime

router = APIRouter(prefix="/itinerary", tags=["itinerary"])

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
    db_day = ItineraryDay(**day.dict())
    db.add(db_day)
    db.commit()
    db.refresh(db_day)
    return db_day

@router.put("/days/{day_id}", response_model=ItineraryDaySchema)
def update_itinerary_day(day_id: int, day_update: ItineraryDayCreate, db: Session = Depends(get_db)):
    """Update itinerary day"""
    day = db.query(ItineraryDay).filter(ItineraryDay.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    
    update_data = day_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(day, field, value)
    
    day.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(day)
    return day

@router.delete("/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itinerary_day(day_id: int, db: Session = Depends(get_db)):
    """Delete an itinerary day"""
    day = db.query(ItineraryDay).filter(ItineraryDay.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    
    db.delete(day)
    db.commit()
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
    db_activity = Activity(**activity.dict())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.put("/activities/{activity_id}", response_model=ActivitySchema)
def update_activity(activity_id: int, activity_update: ActivityCreate, db: Session = Depends(get_db)):
    """Update activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    update_data = activity_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)
    
    activity.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(activity)
    return activity

@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    """Delete an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db.delete(activity)
    db.commit()
    return None
