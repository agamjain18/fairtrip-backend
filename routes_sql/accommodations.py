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
        
        soup = BeautifulSoup(response.text, 'html.parser')
        name, address, phone = "", "", ""

        # 1. Title Parsing
        title_tag = soup.title.string if soup.title else ""
        if title_tag:
            name = title_tag.split(" - Google Maps")[0].split(" - ")[0].split("·")[0].strip()

        # 2. Meta Description Parsing
        og_desc = soup.find("meta", property="og:description")
        description = og_desc["content"] if og_desc and og_desc.get("content") else ""
        
        if description and "·" in description:
            parts = [p.strip() for p in description.split('·')]
            phone_regex = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            for part in parts:
                if re.search(phone_regex, part):
                    phone = part
                elif any(char.isdigit() for char in part) and len(part) > 8:
                    if not address: address = part

        # 3. JSON-LD fallback
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") in ["Hotel", "LodgingBusiness", "Place", "LocalBusiness"]:
                        if not name: name = data.get("name")
                        if not phone: phone = data.get("telephone")
                        if not address:
                            addr = data.get("address")
                            if isinstance(addr, dict):
                                address = f"{addr.get('streetAddress', '')}, {addr.get('addressLocality', '')}"
                            elif isinstance(addr, str):
                                address = addr
            except: continue

        return {
            "name": name or "",
            "address": address or "",
            "contact_number": phone or "",
            "notes": f"Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }

    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        return {"name": "", "address": "", "contact_number": "", "notes": f"Auto-fill failed: {str(e)}"}
