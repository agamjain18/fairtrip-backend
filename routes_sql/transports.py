from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import shutil
import uuid
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Transport, Trip, increment_trip_members_version
from schemas_sql import Transport as TransportSchema, TransportCreate
from datetime import datetime, timezone
import os
# import google.generativeai as genai
import tempfile
import json
from pypdf import PdfReader

router = APIRouter(prefix="/transports", tags=["transports"])

# Directory to save tickets
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKETS_DIR = os.path.join(BASE_DIR, "uploads", "tickets")
if not os.path.exists(TICKETS_DIR):
    os.makedirs(TICKETS_DIR)

@router.post("/upload-ticket")
async def upload_ticket(file: UploadFile = File(...)):
    """Upload a ticket PDF/Image and return its static URL"""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.png', '.jpg', '.jpeg']:
        raise HTTPException(status_code=400, detail="Only PDF and images are supported")
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(TICKETS_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return the relative URL served by StaticFiles
    # Since StaticFiles is mounted at /static to UPLOAD_DIRECTORY (backend/uploads)
    # The URL should be /static/tickets/{filename}
    return {"url": f"/static/tickets/{filename}", "ticket_url": f"/static/tickets/{filename}"}

# Use the same API key as ai_service.py
# API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
# genai.configure(api_key=API_KEY)

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
        # Save the file permanently as well
        file_ext = os.path.splitext(file.filename)[1].lower()
        saved_filename = f"{uuid.uuid4()}{file_ext}"
        saved_file_path = os.path.join(TICKETS_DIR, saved_filename)
        
        # We need to seek back to start since we already read it for extraction
        await file.seek(0)
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        ticket_url = f"/static/tickets/{saved_filename}"

        # Use the new deterministic PDFAnalysisService
        from services.pdf_service import PDFAnalysisService
        pdf_service = PDFAnalysisService()
        result = pdf_service.analyze_pdf(tmp_path)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        data = result["data"]
        
        # Combine date and time into ISO 8601 strings
        dep_date_str = data.get("date")
        dep_time_str = data.get("departure_time") # HH:mm
        arr_time_str = data.get("arrival_time")   # HH:mm

        iso_departure = None
        iso_arrival = None
        arrival_date_str = dep_date_str
        
        if dep_date_str and dep_time_str:
            try:
                # Ensure time is HH:mm:ss
                t = dep_time_str if ":" in dep_time_str else f"{dep_time_str}:00"
                if len(t.split(":")[0]) == 1: t = f"0{t}"
                iso_departure = f"{dep_date_str}T{t}:00"
            except: pass

        if dep_date_str and arr_time_str:
            try:
                # Handle next-day arrival
                if dep_time_str:
                    dep_h = int(dep_time_str.split(':')[0])
                    arr_h = int(arr_time_str.split(':')[0])
                    if arr_h < dep_h:
                        from datetime import datetime, timedelta
                        d = datetime.strptime(dep_date_str, "%Y-%m-%d")
                        arrival_date_str = (d + timedelta(days=1)).strftime("%Y-%m-%d")
                
                t = arr_time_str if ":" in arr_time_str else f"{arr_time_str}:00"
                if len(t.split(":")[0]) == 1: t = f"0{t}"
                iso_arrival = f"{arrival_date_str}T{t}:00"
            except: pass

        response_data = {
            "type": data.get("type", "flight"),
            "carrier": data.get("carrier"),
            "flight_number": data.get("flight_number"),
            "departure_location": data.get("from_location"),
            "arrival_location": data.get("to_location"),
            "departure_time": iso_departure,
            "arrival_time": iso_arrival,
            "departure_date": dep_date_str,
            "arrival_date": arrival_date_str,
            "departure_time_raw": dep_time_str,
            "arrival_time_raw": arr_time_str,
            "booking_reference": data.get("booking_reference"),
            "seat_number": data.get("seat_number"),
            "cost": data.get("total_amount", 0),
            "passengers": data.get("passengers", []),
            "notes": f"Extracted via deterministic rules. {len(data.get('passengers', []))} passengers found.",
            "ticket_url": ticket_url
        }
        
        print(f"DEBUG: Final Response Data -> {json.dumps(response_data, indent=2)}")
        return response_data

    except Exception as e:
        print(f"Extraction Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract info: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/trip/{trip_id}/", response_model=List[TransportSchema])
def get_trip_transports(trip_id: int, db: Session = Depends(get_db)):
    """Get all transports for a specific trip"""
    transports = db.query(Transport).filter(Transport.trip_id == trip_id).all()
    return transports
@router.delete("/{transport_id}")
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
