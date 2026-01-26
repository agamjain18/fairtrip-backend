from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Trip, User, trip_members, increment_trip_members_version, increment_user_version
from schemas_sql import Trip as TripSchema, TripCreate, TripUpdate, User as UserSchema
from datetime import datetime, timezone

router = APIRouter(prefix="/trips", tags=["trips"])

@router.get("/", response_model=List[TripSchema])
def get_trips(user_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all trips or trips for a specific user"""
    if user_id:
        # Trips where user is a member
        trips = db.query(Trip).join(Trip.members).filter(User.id == user_id).offset(skip).limit(limit).all()
        # Also include trips created by user
        own_trips = db.query(Trip).filter(Trip.creator_id == user_id).offset(skip).limit(limit).all()
        # Combine and deduplicate
        all_trips = list({t.id: t for t in (trips + own_trips)}.values())
        return all_trips
    else:
        trips = db.query(Trip).offset(skip).limit(limit).all()
    return trips

@router.get("/{trip_id}", response_model=TripSchema)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """Get a specific trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.post("/", response_model=TripSchema, status_code=status.HTTP_201_CREATED)
def create_trip(trip: TripCreate, creator_id: int, db: Session = Depends(get_db)):
    """Create a new trip"""
    user = db.query(User).filter(User.id == creator_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Creator not found")
        
    db_trip = Trip(
        **trip.dict(),
        creator_id=creator_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Add creator as the first member
    db_trip.members.append(user)
    
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.put("/{trip_id}", response_model=TripSchema)
def update_trip(trip_id: int, trip_update: TripUpdate, db: Session = Depends(get_db)):
    """Update trip details"""
    db_trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    update_data = trip_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_trip, key, value)
            
    db_trip.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    """Delete a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    return None

@router.get("/{trip_id}/members", response_model=List[UserSchema])
def get_trip_members(trip_id: int, db: Session = Depends(get_db)):
    """Get all members of a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.members

@router.post("/{trip_id}/members/{user_id}")
def add_trip_member(trip_id: int, user_id: int, db: Session = Depends(get_db)):
    """Add a member to a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in trip.members:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    trip.members.append(user)
    db.commit()
    
    # Real-time sync: notify all members
    increment_trip_members_version(db, trip_id)
    
    return {"message": "Member added successfully"}

@router.delete("/{trip_id}/members/{user_id}")
def remove_trip_member(trip_id: int, user_id: int, db: Session = Depends(get_db)):
    """Remove a member from a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user not in trip.members:
        raise HTTPException(status_code=404, detail="User is not a member of this trip")
    
    trip.members.remove(user)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    increment_user_version(db, user_id) # Notify the removed user too
    
    return {"message": "Member removed successfully"}

@router.get("/{trip_id}/summary")
def get_trip_summary(trip_id: int, db: Session = Depends(get_db)):
    """Get a summary of trip details and stats"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    from database_sql import Expense, ItineraryDay, ChecklistItem, Photo
    
    expense_count = db.query(Expense).filter(Expense.trip_id == trip_id).count()
    itinerary_days = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip_id).count()
    checklist_items = db.query(ChecklistItem).filter(ChecklistItem.trip_id == trip_id).count()
    photos_count = db.query(Photo).filter(Photo.trip_id == trip_id).count()
    
    return {
        "id": trip.id,
        "title": trip.title,
        "total_budget": trip.total_budget,
        "total_spent": trip.total_spent,
        "budget_remaining": trip.total_budget - trip.total_spent,
        "budget_used_percentage": trip.budget_used_percentage,
        "member_count": len(trip.members),
        "expense_count": expense_count,
        "itinerary_days": itinerary_days,
        "checklist_items": checklist_items,
        "photos_count": photos_count
    }
