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
def extract_metadata(request: UrlRequest):
    """
    Extract basic metadata (Title, Phone, Address) from a URL.
    Useful for auto-filling forms from Google Maps links.
    """
    import requests
    from bs4 import BeautifulSoup
    import re
    import traceback

    print(f"Extracting metadata for URL: {request.url}")

    try:
        # User-Agent is often required to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Follow redirects (often Google Maps short links redirect)
        session = requests.Session()
        response = session.get(request.url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Title/Name
        title_tag = soup.title.string if soup.title else ""
        name = ""
        
        # Google Maps specific title parsing
        if "Google Maps" in title_tag:
            name = title_tag.split(" - Google Maps")[0].split(" - ")[0].strip()
        else:
            name = title_tag.strip()
        
        # Open Graph tags (often cleaner)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
             name = og_title["content"].split("·")[0].split(" - ")[0].strip()

        # 2. Phone Extraction
        phone = ""
        # Try finding in meta tags first
        og_desc = soup.find("meta", property="og:description")
        description = og_desc["content"] if og_desc and og_desc.get("content") else ""
        
        # Regex for international phone numbers
        phone_regex = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        if description:
            phone_match = re.search(phone_regex, description)
            if phone_match:
                phone = phone_match.group(0).strip()

        if not phone:
             # Search in the whole body text
             phone_match = re.search(phone_regex, response.text)
             if phone_match:
                  phone = phone_match.group(0).strip()

        # 3. Address Extraction
        address = ""
        # Often in meta description for places
        if description and "·" in description:
            parts = description.split('·')
            # Heuristic: middle parts usually contains address
            if len(parts) >= 2:
                potential_address = parts[1].strip()
                if any(char.isdigit() for char in potential_address):
                    address = potential_address

        # Check for specific JSON-LD or meta tags if available
        meta_addr = soup.find("meta", property="business:contact_data:street_address")
        if meta_addr and meta_addr.get("content"):
            address = meta_addr["content"]

        print(f"Extracted: Name='{name}', Phone='{phone}', Address='{address}'")

        return {
            "name": name or "",
            "address": address or "",
            "contact_number": phone or "",
            "notes": f"Auto-filled from: {request.url}"
        }

    except Exception as e:
        print(f"Metadata extraction failed: {str(e)}")
        traceback.print_exc()
        return {
            "name": "", 
            "address": "", 
            "contact_number": "", 
            "notes": f"Extraction failed: {str(e)}"
        }
