from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Transport, Trip, increment_trip_members_version
from schemas_sql import Transport as TransportSchema, TransportCreate
from datetime import datetime, timezone
import os
import google.generativeai as genai
import tempfile
import json

router = APIRouter(prefix="/transports", tags=["transports"])

# Use the same API key as ai_service.py
API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

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
    
    # Real-time sync
    increment_trip_members_version(db, db_transport.trip_id)
    return db_transport

@router.post("/extract-pdf")
async def extract_pdf_metadata(file: UploadFile = File(...)):
    """
    Extract transport details from a PDF ticket using Gemini AI.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Create a temporary file to save the upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        try:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    try:
        # Upload to Gemini
        gemini_file = genai.upload_file(tmp_path, mime_type="application/pdf")
        
        prompt = """
        Extract transport details from this ticket/booking confirmation.
        Provide the following fields in JSON format:
        - type: (one of: flight, train, bus, car_rental, taxi, boat, other)
        - carrier: (e.g., Airline name, Train company)
        - flight_number: (e.g., Flight no, Train no, Bus no)
        - departure_location: (City/Airport code)
        - arrival_location: (City/Airport code)
        - departure_time: (ISO 8601 format if found, otherwise null)
        - arrival_time: (ISO 8601 format if found, otherwise null)
        - booking_reference: (PNR or reference)
        - seat_number: (if available)
        - cost: (numeric value if available, else 0)
        - notes: (any other important detail like terminal, gate, etc.)

        Respond ONLY with the JSON object.
        """

        response = model.generate_content([gemini_file, prompt])
        text = response.text.strip()
        
        # Robust JSON extraction
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            # Fallback if no JSON braces found
            text = text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text)

        return data

    except Exception as e:
        print(f"Gemini Extraction Error: {e}")
        # Clean up gemini file reference if possible? No need, it expires
        raise HTTPException(status_code=500, detail=f"Failed to extract info: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.delete("/{transport_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transport(transport_id: int, db: Session = Depends(get_db)):
    """Delete a transport"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    trip_id = transport.trip_id
    db.delete(transport)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    return None
