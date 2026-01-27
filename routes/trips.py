from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from database import Trip, User, Expense
from schemas import Trip as TripSchema, TripCreate, TripUpdate, User as UserSchema
from datetime import datetime, timezone
from services.ai_service import generate_trip_itinerary
from beanie import PydanticObjectId, Link

router = APIRouter(prefix="/trips", tags=["trips"])

@router.get("/", response_model=List[TripSchema])
async def get_trips(skip: int = 0, limit: int = 100, user_id: Optional[str] = None):
    """Get all trips or trips for a specific user"""
    if user_id:
        # Find trips where members list contains a link with this ID
        trips = await Trip.find(Trip.members.id == user_id).skip(skip).limit(limit).to_list()
    else:
        trips = await Trip.find_all().skip(skip).limit(limit).to_list()
    return trips

@router.get("/{trip_id}", response_model=TripSchema)
async def get_trip(trip_id: str):
    """Get a specific trip"""
    try:
        if not PydanticObjectId.is_valid(trip_id):
             raise HTTPException(status_code=400, detail="Invalid Trip ID format")
             
        trip = await Trip.get(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        return trip
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/", response_model=TripSchema, status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripCreate, creator_id: str, background_tasks: BackgroundTasks):
    """Create a new trip"""
    creator = await User.get(creator_id)
    if not creator:
         raise HTTPException(status_code=404, detail="Creator user not found")

    db_trip = Trip(
        title=trip.title,
        description=trip.description,
        destination=trip.destination,
        start_location=trip.start_location,
        image_url=trip.image_url,
        start_date=trip.start_date,
        end_date=trip.end_date,
        total_budget=trip.total_budget,
        budget_type=trip.budget_type,
        currency=trip.currency,
        timezone=trip.timezone,
        is_public=trip.is_public,
        use_ai=trip.use_ai,
        creator=creator,
        members=[creator] # Add creator as member
    )
    
    await db_trip.insert()

    # Trigger AI generation if requested
    if trip.use_ai and trip.destination:
        # Format dates safe for passing
        s_date = trip.start_date.isoformat() if trip.start_date else datetime.now().isoformat()
        e_date = trip.end_date.isoformat() if trip.end_date else s_date
        
        background_tasks.add_task(
            generate_trip_itinerary, 
            str(db_trip.id), # PydanticObjectId to str
            trip.destination, 
            s_date, 
            e_date, 
            trip.total_budget or 0.0
        )

    return db_trip

@router.put("/{trip_id}", response_model=TripSchema)
async def update_trip(trip_id: str, trip_update: TripUpdate):
    """Update trip details"""
    trip = await Trip.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    update_data = trip_update.dict(exclude_unset=True)
    if update_data:
        await trip.set(update_data)
        trip.updated_at = datetime.now(timezone.utc)
        await trip.save()
        
    return trip

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: str):
    """Delete a trip"""
    trip = await Trip.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    await trip.delete()
    return None

@router.post("/{trip_id}/members/{user_id}")
async def add_trip_member(trip_id: str, user_id: str):
    """Add a member to a trip"""
    trip = await Trip.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already member
    # trip.members is list of Link[User]
    if user.id in [m.id for m in trip.members]:
         raise HTTPException(status_code=400, detail="User is already a member")

    trip.members.append(user)
    await trip.save()
    return {"message": "Member added successfully"}

@router.delete("/{trip_id}/members/{user_id}")
async def remove_trip_member(trip_id: str, user_id: str):
    """Remove a member from a trip"""
    trip = await Trip.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Remove by ID
    original_len = len(trip.members)
    trip.members = [m for m in trip.members if str(m.id) != user_id]
    
    if len(trip.members) == original_len:
         raise HTTPException(status_code=400, detail="User is not a member")

    await trip.save()
    return {"message": "Member removed successfully"}

@router.get("/{trip_id}/members", response_model=List[UserSchema])
async def get_trip_members(trip_id: str):
    """Get all members of a trip"""
    try:
        if not PydanticObjectId.is_valid(trip_id):
             raise HTTPException(status_code=400, detail="Invalid Trip ID format")

        trip = await Trip.get(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        members = []
        # Robustly fetch members
        for member_link in trip.members:
            try:
                # Check if it's already a User object (Beanie sometimes fetches automatically)
                if isinstance(member_link, User):
                    members.append(member_link)
                    continue
                
                # If it's a Link, access .id or .ref
                # Beanie Links can be tricky. Safest is to try to fetch using the ID if available
                member_id = None
                if isinstance(member_link, Link):
                    # Link object
                    member_id = member_link.ref.id
                elif hasattr(member_link, 'id'):
                     member_id = member_link.id
                
                if member_id:
                     m = await User.get(member_id)
                     if m:
                         members.append(m)
            except Exception as e:
                print(f"Error resolving member link in trip {trip_id}: {e}")
                continue
                
        return members
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching trip members {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/{trip_id}/summary")
async def get_trip_summary(trip_id: str):
    """Get trip summary with financial data"""
    trip = await Trip.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Count expenses
    expense_count = await Expense.find(Expense.trip.id == trip_id).count()
    
    return {
        "id": str(trip.id),
        "title": trip.title,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "status": trip.status,
        "total_budget": trip.total_budget,
        "total_spent": trip.total_spent,
        "budget_remaining": trip.total_budget - trip.total_spent,
        "budget_used_percentage": trip.budget_used_percentage,
        "member_count": len(trip.members),
        "expense_count": expense_count,
        "itinerary_days": 0, # TODO: implement itinerary count
        "checklist_items": 0, # TODO: implement checklist count
        "photos_count": 0 # TODO: implement photos count
    }
