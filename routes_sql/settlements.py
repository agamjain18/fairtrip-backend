from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from utils.email_service import send_settlement_email
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database_sql import Settlement, Trip, User, get_db, increment_trip_members_version
from .notifications import send_notification_sql
from schemas_sql import Settlement as SettlementSchema, SettlementCreate, SettlementUpdate
from datetime import datetime, timezone
from utils.timezone_utils import get_ist_now

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.get("/", response_model=List[SettlementSchema])
def get_settlements(trip_id: Optional[int] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all settlements, optionally filtered by trip or user"""
    query = db.query(Settlement)
    
    if trip_id:
        query = query.filter(Settlement.trip_id == trip_id)
    
    if user_id:
        query = query.filter(or_(Settlement.from_user_id == user_id, Settlement.to_user_id == user_id))
    
    settlements = query.all()
    return settlements

@router.get("/{settlement_id}", response_model=SettlementSchema)
def get_settlement(settlement_id: int, db: Session = Depends(get_db)):
    """Get a specific settlement"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return settlement

@router.post("/", response_model=SettlementSchema, status_code=status.HTTP_201_CREATED)
def create_settlement(settlement: SettlementCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new settlement record"""
    trip = db.query(Trip).filter(Trip.id == settlement.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    from_user = db.query(User).filter(User.id == settlement.from_user_id).first()
    to_user = db.query(User).filter(User.id == settlement.to_user_id).first()
    
    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_settlement = Settlement(
        trip_id=settlement.trip_id,
        from_user_id=settlement.from_user_id,
        to_user_id=settlement.to_user_id,
        amount=settlement.amount,
        currency=settlement.currency,
        payment_method=settlement.payment_method,
        payment_reference=settlement.payment_reference,
        notes=settlement.notes,
        status=settlement.status or "pending",
        created_at=get_ist_now()
    )
    
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    
    # Real-time sync
    increment_trip_members_version(db, db_settlement.trip_id)
        
    # Notify Receiver
    if to_user.email:
        background_tasks.add_task(send_settlement_email, to_user.email, from_user.full_name or from_user.username, settlement.amount, settlement.currency, trip.title)
    
    # In-app notification
    send_notification_sql(
        db,
        user_id=settlement.to_user_id,
        title="Payment Recorded",
        message=f"{from_user.full_name or from_user.username} recorded a payment of {settlement.amount} {settlement.currency} for '{trip.title}'",
        notification_type="settlement",
        action_url=f"/trip/{trip.id}/expenses"
    )
        
    return db_settlement

@router.put("/{settlement_id}", response_model=SettlementSchema)
def update_settlement(settlement_id: int, settlement_update: SettlementUpdate, db: Session = Depends(get_db)):
    """Update settlement details (e.g., mark as completed)"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    update_data = settlement_update.dict(exclude_unset=True)
    
    was_pending = settlement.status == "pending"
    is_now_completed = update_data.get("status") == "completed"

    if is_now_completed and was_pending:
        settlement.settled_at = get_ist_now()
        
        # Notify the Payer that it's been approved
        to_user = db.query(User).filter(User.id == settlement.to_user_id).first()
        trip = db.query(Trip).filter(Trip.id == settlement.trip_id).first()
        
        send_notification_sql(
            db,
            user_id=settlement.from_user_id,
            title="Settlement Approved",
            message=f"{to_user.full_name or to_user.username} approved your payment of {settlement.amount} {settlement.currency} for '{trip.title if trip else 'Trip'}'",
            notification_type="settlement",
            action_url=f"/trip/{settlement.trip_id}/expenses"
        )
    
    for key, value in update_data.items():
        setattr(settlement, key, value)
        
    db.commit()
    db.refresh(settlement)
    
    # Real-time sync
    increment_trip_members_version(db, settlement.trip_id)
    return settlement

@router.delete("/{settlement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_settlement(settlement_id: int, db: Session = Depends(get_db)):
    """Delete a settlement"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    trip_id = settlement.trip_id
    db.delete(settlement)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    return None

@router.get("/trip/{trip_id}/pending", response_model=List[SettlementSchema])
def get_pending_settlements(trip_id: int, db: Session = Depends(get_db)):
    """Get all pending settlements for a trip"""
    settlements = db.query(Settlement).filter(
        Settlement.trip_id == trip_id,
        Settlement.status == "pending"
    ).all()
    
    return settlements
