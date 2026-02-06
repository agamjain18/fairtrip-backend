from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from utils.email_service import send_trip_created_email, send_trip_invitation_email, send_trip_deleted_email
from utils.image_utils import update_trip_image_task
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Trip, User, trip_members, increment_trip_members_version, increment_user_version, DestinationImage
from .notifications import send_notification_sql
from .auth import get_current_user_sql
from schemas_sql import Trip as TripSchema, TripCreate, TripUpdate, User as UserSchema, InviteRequest
from datetime import datetime, timezone
from .expenses import get_user_balance_for_trip

router = APIRouter(prefix="/trips", tags=["trips"])

# Import Redis client
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis client not available for trips routes")

# Helper function to invalidate trip caches
async def invalidate_trip_cache(trip_id: int = None, user_id: int = None):
    """Invalidate trip-related caches"""
    if not REDIS_AVAILABLE:
        return
    
    try:
        # Invalidate specific trip cache
        if trip_id:
            await redis_client.delete(f"trip:details:{trip_id}")
            await redis_client.delete(f"trip:summary:{trip_id}")
            await redis_client.delete(f"trip:members:{trip_id}")
        
        # Invalidate user's trips list cache
        if user_id:
            await redis_client.delete(f"trips:user:{user_id}")
        
        # Invalidate all trips cache
        await redis_client.delete("trips:all")
        
        print(f"🗑️ Cache invalidated for trip_id={trip_id}, user_id={user_id}")
    except Exception as e:
        print(f"Error invalidating cache: {e}")

@router.get("/", response_model=List[TripSchema])
def get_trips(user_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all trips or trips for a specific user"""
    
    # Get from database
    if user_id:
        # Trips where user is a member
        trips = db.query(Trip).join(Trip.members).filter(User.id == user_id).offset(skip).limit(limit).all()
        # Also include trips created by user
        own_trips = db.query(Trip).filter(Trip.creator_id == user_id).offset(skip).limit(limit).all()
        # Combine and deduplicate
        all_trips = list({t.id: t for t in (trips + own_trips)}.values())
        
        # Calculate real-time balance and member count for each trip
        for trip in all_trips:
            trip.user_balance = get_user_balance_for_trip(db, trip.id, user_id)
            if trip.destination:
                imgs = db.query(DestinationImage).filter(DestinationImage.destination.like(f"{trip.destination}%")).all()
                trip.image_urls = [img.image_url for img in imgs] if imgs else []
            
        return all_trips
    else:
        trips = db.query(Trip).offset(skip).limit(limit).all()
    
    return trips


@router.get("/{trip_id}/", response_model=TripSchema)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """Get a specific trip"""
    
    # Get from database
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.destination:
        imgs = db.query(DestinationImage).filter(DestinationImage.destination.like(f"{trip.destination}%")).all()
        trip.image_urls = [img.image_url for img in imgs] if imgs else []
    
    return trip


@router.post("/", response_model=TripSchema, status_code=status.HTTP_201_CREATED)
def create_trip(trip: TripCreate, creator_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
    db.refresh(db_trip)
    
    # Send creation email with details
    if user.email:
        background_tasks.add_task(
            send_trip_created_email, 
            user.email, 
            user.full_name or user.username, 
            db_trip.title,
            destination=db_trip.destination,
            start_date=db_trip.start_date,
            end_date=db_trip.end_date,
            budget=db_trip.total_budget,
            currency=db_trip.currency,
            description=db_trip.description,
            use_ai=db_trip.use_ai,
            start_location=db_trip.start_location
        )
    
    # Fetch famous spot image if destination exists
    if db_trip.destination:
        try:
            from database_sql import SessionLocal
            from utils.image_utils import update_trip_image_task
            import asyncio

            async def run_image_task(trip_id, dest):
                new_db = SessionLocal()
                try:
                    await update_trip_image_task(trip_id, dest, new_db)
                except Exception as e:
                    print(f"Error in image background task: {e}")
                finally:
                    new_db.close()
            
            def start_async_task(trip_id, dest):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_image_task(trip_id, dest))
                loop.close()

            background_tasks.add_task(start_async_task, db_trip.id, db_trip.destination)
        except Exception as e:
            print(f"Error scheduling image task: {e}")
        
    return db_trip

@router.put("/{trip_id}/", response_model=TripSchema)
def update_trip(trip_id: int, trip_update: TripUpdate, db: Session = Depends(get_db)):
    """Update trip details"""
    db_trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    update_data = trip_update.dict(exclude_unset=True)
    print(f"DEBUG: update_trip data: {update_data}")
    for key, value in update_data.items():
        setattr(db_trip, key, value)
            
    db_trip.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_trip)
    
    # Real-time sync: notify all members
    increment_trip_members_version(db, trip_id)
    return db_trip

@router.delete("/{trip_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Delete a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    
    # Notify members about deletion before commit (fetching members first)
    members_to_notify = [(m.email, m.full_name or m.username) for m in trip.members if m.email]
    trip_title = trip.title
    
    db.commit()
    
    for email, name in members_to_notify:
        background_tasks.add_task(send_trip_deleted_email, email, name, trip_title)
        
    return None

@router.get("/{trip_id}/members/", response_model=List[UserSchema])
def get_trip_members(trip_id: int, db: Session = Depends(get_db)):
    """Get all members of a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.members

@router.post("/{trip_id}/members/{user_id}")
def add_trip_member(trip_id: int, user_id: int, background_tasks: BackgroundTasks, current_user_id: Optional[int] = None, db: Session = Depends(get_db)):
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
    
    # Notify added member
    inviter_name = "A friend"
    if current_user_id:
        inviter = db.query(User).filter(User.id == current_user_id).first()
        if inviter:
            inviter_name = inviter.full_name or inviter.username

    send_notification_sql(
        db,
        user_id=user_id,
        title="Added to Trip",
        message=f"{inviter_name} added you to the trip '{trip.title}'",
        notification_type="trip",
        action_url=f"/trip/{trip.id}"
    )

    if user.email:
        background_tasks.add_task(send_trip_invitation_email, user.email, inviter_name, trip.title, f"https://fairtrip.app/join-trip/{trip.id}")

    return {"message": "Member added successfully"}

@router.post("/{trip_id}/invite")
def invite_by_email(trip_id: int, request: InviteRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user_sql), db: Session = Depends(get_db)):
    """Invite a user to a trip by email"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Check if user already exists
    user = db.query(User).filter(User.email == request.email).first()
    
    inviter_name = current_user.full_name or current_user.username
    
    # Send invitation email with join link
    join_url = f"https://fairtrip.app/join-trip/{trip_id}"
    background_tasks.add_task(send_trip_invitation_email, request.email, inviter_name, trip.title, join_url)
    
    # If user exists, also send an in-app notification
    if user:
        send_notification_sql(
            db,
            user_id=user.id,
            title="Trip Invitation",
            message=f"{inviter_name} invited you to join '{trip.title}'",
            notification_type="trip",
            action_url=f"/join-trip/{trip.id}"
        )
        
    return {"message": f"Invitation sent to {request.email}"}

@router.post("/{trip_id}/join")
def join_trip(trip_id: int, current_user: User = Depends(get_current_user_sql), db: Session = Depends(get_db)):
    """Join a trip using a link/trip_id"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if current_user in trip.members:
        return {"message": "Already a member"}
        
    trip.members.append(current_user)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    increment_user_version(db, current_user.id)
    
    return {"message": "Joined trip successfully", "trip_id": trip.id}

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

@router.get("/{trip_id}/summary/")
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
