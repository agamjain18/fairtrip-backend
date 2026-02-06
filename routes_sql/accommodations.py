from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Accommodation, Trip, increment_trip_members_version
from schemas_sql import Accommodation as AccommodationSchema, AccommodationCreate
from datetime import datetime, timezone
from utils.timezone_utils import get_ist_now

router = APIRouter(prefix="/accommodations", tags=["accommodations"])

@router.get("/", response_model=List[AccommodationSchema])
def get_accommodations(trip_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all accommodations or accommodations for a specific trip"""
    query = db.query(Accommodation)
    if trip_id:
        query = query.filter(Accommodation.trip_id == trip_id)
    accommodations = query.offset(skip).limit(limit).all()
    return accommodations

@router.get("/{accommodation_id}", response_model=AccommodationSchema)
def get_accommodation(accommodation_id: int, db: Session = Depends(get_db)):
    """Get a specific accommodation"""
    accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return accommodation

# Directory to save booking confirmations
import os
import uuid
import shutil
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKINGS_DIR = os.path.join(BASE_DIR, "uploads", "bookings")
if not os.path.exists(BOOKINGS_DIR):
    os.makedirs(BOOKINGS_DIR)

from fastapi import UploadFile, File

@router.post("/upload-booking")
async def upload_booking(file: UploadFile = File(...)):
    """Upload a booking confirmation PDF/Image and return its static URL"""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.png', '.jpg', '.jpeg']:
        raise HTTPException(status_code=400, detail="Only PDF and images are supported")
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(BOOKINGS_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return the relative URL served by StaticFiles
    return {"url": f"/static/bookings/{filename}"}

@router.post("/", response_model=AccommodationSchema, status_code=status.HTTP_201_CREATED)
def create_accommodation(accommodation: AccommodationCreate, db: Session = Depends(get_db)):
    """Create a new accommodation"""
    trip = db.query(Trip).filter(Trip.id == accommodation.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db_accommodation = Accommodation(
        trip_id=accommodation.trip_id,
        name=accommodation.name,
        type=accommodation.type,
        address=accommodation.address,
        check_in=accommodation.check_in,
        check_out=accommodation.check_out,
        booking_reference=accommodation.booking_reference,
        cost=accommodation.cost,
        contact_number=accommodation.contact_number,
        notes=accommodation.notes,
        google_maps_url=accommodation.google_maps_url,
        latitude=accommodation.latitude,
        longitude=accommodation.longitude,
        confirmation_url=accommodation.confirmation_url,
        created_at=get_ist_now()
    )
    
    db.add(db_accommodation)
    db.commit()
    db.refresh(db_accommodation)
    
    # Real-time sync
    increment_trip_members_version(db, db_accommodation.trip_id)
    return db_accommodation

@router.put("/{accommodation_id}", response_model=AccommodationSchema)
def update_accommodation(accommodation_id: int, accommodation: AccommodationCreate, db: Session = Depends(get_db)):
    """Update an existing accommodation"""
    db_accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not db_accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    # Update fields
    db_accommodation.name = accommodation.name
    db_accommodation.type = accommodation.type
    db_accommodation.address = accommodation.address
    db_accommodation.check_in = accommodation.check_in
    db_accommodation.check_out = accommodation.check_out
    db_accommodation.booking_reference = accommodation.booking_reference
    db_accommodation.cost = accommodation.cost
    db_accommodation.contact_number = accommodation.contact_number
    db_accommodation.notes = accommodation.notes
    db_accommodation.google_maps_url = accommodation.google_maps_url
    db_accommodation.latitude = accommodation.latitude
    db_accommodation.longitude = accommodation.longitude
    db_accommodation.confirmation_url = accommodation.confirmation_url
    
    db.commit()
    db.refresh(db_accommodation)
    
    # Real-time sync
    increment_trip_members_version(db, db_accommodation.trip_id)
    return db_accommodation

@router.delete("/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_accommodation(accommodation_id: int, db: Session = Depends(get_db)):
    """Delete an accommodation"""
    accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    trip_id = accommodation.trip_id
    db.delete(accommodation)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    return None

@router.get("/trip/{trip_id}/", response_model=List[AccommodationSchema])
def get_trip_accommodations(trip_id: int, db: Session = Depends(get_db)):
    """Get all accommodations for a specific trip"""
    accommodations = db.query(Accommodation).filter(Accommodation.trip_id == trip_id).all()
    return accommodations

from pydantic import BaseModel
class UrlRequest(BaseModel):
    url: str

@router.post("/extract-metadata")
async def extract_metadata(request: UrlRequest):
    """
    Extract basic metadata (Title, Phone, Address) from a URL.
    Uses Gemini AI for high accuracy with dynamic Google Maps links.
    """
    import requests
    from bs4 import BeautifulSoup
    import re
    import json

    print(f"Extracting metadata for URL: {request.url}")

    try:
        # User-Agent to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        session = requests.Session()
        response = session.get(request.url, headers=headers, timeout=12, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Try to get name from Title
        title = soup.title.string if soup.title else ""
        name = ""
        if title:
            # Google Maps titles usually look like "Hotel Name - Google Maps" or "Hotel Name · Address"
            if " - Google Maps" in title:
                name = title.split(" - Google Maps")[0].strip()
            elif " · " in title:
                name = title.split(" · ")[0].strip()
            else:
                name = title.strip()

        # 2. Try to get address from Meta tags
        address = ""
        meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            desc_content = meta_desc.get("content", "")
            # Often address is in the description
            # If it's a map link, description often starts with address or type
            address = desc_content.strip()
        
        # 3. Contact number search (simple regex)
        contact_number = ""
        phone_match = re.search(r'(\+?\d{1,4}[\s\-]?)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}', response.text)
        if phone_match:
            contact_number = phone_match.group(0).strip()

        return {
            "name": name,
            "address": address[:200] if address else "",
            "contact_number": contact_number,
            "notes": f"Scraped via deterministic rules: {get_ist_now().strftime('%Y-%m-%d %H:%M')}"
        }

    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        # Fallback to a very basic scrape if Gemini fails
        return {"name": "", "address": "", "contact_number": "", "notes": f"Auto-fill failed: {str(e)}"}
