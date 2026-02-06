from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import ItineraryDay, Activity, Trip
from schemas import ItineraryDay as ItineraryDaySchema, ItineraryDayCreate, Activity as ActivitySchema, ActivityCreate
from datetime import datetime, timezone
from beanie import PydanticObjectId

router = APIRouter(prefix="/itinerary", tags=["itinerary"])

@router.get("/trip/{trip_id}/days", response_model=List[ItineraryDaySchema])
async def get_itinerary_days(trip_id: str):
    """Get all itinerary days for a trip"""
    days = await ItineraryDay.find(ItineraryDay.trip.id == PydanticObjectId(trip_id)).sort(ItineraryDay.day_number).to_list()
    return days

@router.get("/days/{day_id}", response_model=ItineraryDaySchema)
async def get_itinerary_day(day_id: str):
    """Get a specific itinerary day"""
    day = await ItineraryDay.get(day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    return day

@router.post("/days", response_model=ItineraryDaySchema, status_code=status.HTTP_201_CREATED)
async def create_itinerary_day(day: ItineraryDayCreate):
    """Create a new itinerary day"""
    trip = await Trip.get(day.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db_day = ItineraryDay(
        trip=trip,
        day_number=day.day_number,
        date=day.date,
        title=day.title,
        description=day.description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await db_day.insert()
    return db_day

@router.put("/days/{day_id}", response_model=ItineraryDaySchema)
async def update_itinerary_day(day_id: str, day_update: ItineraryDayCreate):
    """Update itinerary day"""
    day = await ItineraryDay.get(day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    
    update_data = day_update.dict(exclude_unset=True)
    if update_data:
        if 'trip_id' in update_data:
            trip = await Trip.get(update_data['trip_id'])
            if trip:
                day.trip = trip
            del update_data['trip_id']
            
        await day.set(update_data)
        day.updated_at = datetime.now(timezone.utc)
        await day.save()
    
    return day

@router.delete("/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary_day(day_id: str):
    """Delete an itinerary day"""
    day = await ItineraryDay.get(day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")
    
    await day.delete()
    return None

# Activity routes
@router.get("/days/{day_id}/activities", response_model=List[ActivitySchema])
async def get_activities(day_id: str):
    """Get all activities for a day"""
    activities = await Activity.find(Activity.day.id == PydanticObjectId(day_id)).sort(Activity.start_time).to_list()
    return activities

@router.get("/activities/{activity_id}", response_model=ActivitySchema)
async def get_activity(activity_id: str):
    """Get a specific activity"""
    activity = await Activity.get(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.post("/activities", response_model=ActivitySchema, status_code=status.HTTP_201_CREATED)
async def create_activity(activity: ActivityCreate):
    """Create a new activity"""
    day = await ItineraryDay.get(activity.day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Itinerary day not found")

    db_activity = Activity(
        day=day,
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await db_activity.insert()
    return db_activity

@router.put("/activities/{activity_id}", response_model=ActivitySchema)
async def update_activity(activity_id: str, activity_update: ActivityCreate):
    """Update activity"""
    activity = await Activity.get(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    update_data = activity_update.dict(exclude_unset=True)
    if update_data:
        if 'day_id' in update_data:
            day = await ItineraryDay.get(update_data['day_id'])
            if day:
                activity.day = day
            del update_data['day_id']

        await activity.set(update_data)
        activity.updated_at = datetime.now(timezone.utc)
        await activity.save()
    
    return activity

@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(activity_id: str):
    """Delete an activity"""
    activity = await Activity.get(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    await activity.delete()
    return None
