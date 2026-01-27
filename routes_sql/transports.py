from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Transport, Trip
from schemas_sql import Transport as TransportSchema, TransportCreate
from datetime import datetime, timezone

router = APIRouter(prefix="/transports", tags=["transports"])

@router.get("/", response_model=List[TransportSchema])
def get_transports(trip_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all transports or transports for a specific trip"""
    query = db.query(Transport)
    if trip_id:
        query = query.filter(Transport.trip_id == trip_id)
    transports = query.offset(skip).limit(limit).all()
    return transports

@router.get("/{transport_id}", response_model=TransportSchema)
def get_transport(transport_id: int, db: Session = Depends(get_db)):
    """Get a specific transport"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    return transport

@router.post("/", response_model=TransportSchema, status_code=status.HTTP_201_CREATED)
def create_transport(transport: TransportCreate, db: Session = Depends(get_db)):
    """Create a new transport"""
    trip = db.query(Trip).filter(Trip.id == transport.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db_transport = Transport(
        trip_id=transport.trip_id,
        type=transport.type,
        carrier=transport.carrier,
        flight_number=transport.flight_number,
        departure_location=transport.departure_location,
        arrival_location=transport.arrival_location,
        departure_time=transport.departure_time,
        arrival_time=transport.arrival_time,
        booking_reference=transport.booking_reference,
        ticket_url=transport.ticket_url,
        seat_number=transport.seat_number,
        status=transport.status,
        cost=transport.cost,
        notes=transport.notes,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db.add(db_transport)
    db.commit()
    db.refresh(db_transport)
    return db_transport

@router.delete("/{transport_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transport(transport_id: int, db: Session = Depends(get_db)):
    """Delete a transport"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    db.delete(transport)
    db.commit()
    return None
