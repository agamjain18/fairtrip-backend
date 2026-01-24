from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import Settlement, Trip, User
from schemas import Settlement as SettlementSchema, SettlementCreate, SettlementUpdate
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.get("/", response_model=List[SettlementSchema])
async def get_settlements(trip_id: Optional[str] = None, user_id: Optional[str] = None):
    """Get all settlements, optionally filtered by trip or user"""
    query = {}
    
    if trip_id:
        query["trip.$id"] = ObjectId(trip_id)
    
    if user_id:
        user_oid = ObjectId(user_id)
        # Get settlements where user is either sender or receiver
        settlements = await Settlement.find({
            "$or": [
                {"from_user.$id": user_oid},
                {"to_user.$id": user_oid}
            ]
        }).to_list()
    elif query:
        settlements = await Settlement.find(query).to_list()
    else:
        settlements = await Settlement.find_all().to_list()
    
    return settlements

@router.get("/{settlement_id}", response_model=SettlementSchema)
async def get_settlement(settlement_id: str):
    """Get a specific settlement"""
    settlement = await Settlement.get(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return settlement

@router.post("/", response_model=SettlementSchema, status_code=201)
async def create_settlement(settlement: SettlementCreate):
    """Create a new settlement record"""
    # Verify trip exists
    trip = await Trip.get(settlement.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verify users exist
    from_user = await User.get(settlement.from_user_id)
    to_user = await User.get(settlement.to_user_id)
    
    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_settlement = Settlement(
        trip=trip,
        from_user=from_user,
        to_user=to_user,
        amount=settlement.amount,
        currency=settlement.currency,
        payment_method=settlement.payment_method,
        payment_reference=settlement.payment_reference,
        notes=settlement.notes,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    
    await db_settlement.insert()
    return db_settlement

@router.put("/{settlement_id}", response_model=SettlementSchema)
async def update_settlement(settlement_id: str, settlement_update: SettlementUpdate):
    """Update settlement details (e.g., mark as completed)"""
    settlement = await Settlement.get(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    update_data = settlement_update.dict(exclude_unset=True)
    
    # If marking as completed, set settled_at timestamp
    if update_data.get("status") == "completed" and settlement.status != "completed":
        settlement.settled_at = datetime.now(timezone.utc)
    
    if update_data:
        await settlement.set(update_data)
        await settlement.save()
    
    return settlement

@router.delete("/{settlement_id}", status_code=204)
async def delete_settlement(settlement_id: str):
    """Delete a settlement"""
    settlement = await Settlement.get(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    await settlement.delete()
    return None

@router.get("/trip/{trip_id}/pending")
async def get_pending_settlements(trip_id: str):
    """Get all pending settlements for a trip"""
    settlements = await Settlement.find({
        "trip.$id": ObjectId(trip_id),
        "status": "pending"
    }).to_list()
    
    return settlements
