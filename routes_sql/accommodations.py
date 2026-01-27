from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Accommodation, Trip
from schemas_sql import Accommodation as AccommodationSchema, AccommodationCreate
from datetime import datetime, timezone

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
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(db_accommodation)
    db.commit()
    db.refresh(db_accommodation)
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
    
    db.commit()
    db.refresh(db_accommodation)
    return db_accommodation

@router.delete("/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_accommodation(accommodation_id: int, db: Session = Depends(get_db)):
    """Delete an accommodation"""
    accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    db.delete(accommodation)
    db.commit()
    return None

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
    import google.generativeai as genai

    # Use the same API key as transports.py and ai_service.py
    API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

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
        
        # Get raw text and some HTML for context
        # Google Maps pages are large, we'll take the head and some of the body
        html_content = response.text[:50000] # Increased context
        
        prompt = f"""
        Extract the following information for a place (Hotel/Stay/Business) from this Google Maps / Website HTML source.
        URL: {request.url}
        HTML Snippet: {html_content[:20000]}

        Provide the following fields in JSON format:
        - name: (The name of the hotel or place)
        - address: (The full address)
        - contact_number: (The phone number in international format if possible)
        - notes: (A very brief summary or "Scraped via AI")

        Respond ONLY with the JSON object. 
        If a field is not found, use an empty string.
        """

        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)

        return {
            "name": data.get("name") or "",
            "address": data.get("address") or "",
            "contact_number": data.get("contact_number") or "",
            "notes": f"Magic Fill: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        }

    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        # Fallback to a very basic scrape if Gemini fails
        return {"name": "", "address": "", "contact_number": "", "notes": f"Auto-fill failed: {str(e)}"}
