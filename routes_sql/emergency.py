from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from database_sql import get_db, City, Trip
from typing import List, Dict, Any, Optional
import math

router = APIRouter(prefix="/emergency", tags=["emergency"])

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("/contacts/")
def get_emergency_contacts(trip_id: Optional[int] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, db: Session = Depends(get_db)):
    """Get emergency contacts for a trip or location"""
    # In a real app, this would fetch from a database table 'emergency_contacts'
    # linked to the trip or the city. For now, we return mock data based on city if trip_id provided.
    
    if trip_id:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if trip and trip.destination:
            # Try to find city by name
            dest = trip.destination.split(',')[0].strip()
            city = db.query(City).filter(City.name.ilike(f"%{dest}%")).first()
            if city:
                return [
                    {"name": "Local Police", "number": city.emergency_numbers.get("police", "112") if city.emergency_numbers else "112", "type": "police"},
                    {"name": "Local Ambulance", "number": city.emergency_numbers.get("ambulance", "112") if city.emergency_numbers else "112", "type": "medical"},
                    {"name": "Local Fire", "number": city.emergency_numbers.get("fire", "112") if city.emergency_numbers else "112", "type": "fire"}
                ]
                
    return [
        {"name": "Global Support", "number": "+1-800-FAIRTRIP", "type": "support"},
        {"name": "International Emergency", "number": "112", "type": "emergency"}
    ]

@router.get("/nearby")
def get_nearby_emergency_info(latitude: float, longitude: float, db: Session = Depends(get_db)):
    """
    Get emergency numbers and info for the nearest city based on user's current location.
    Also returns nearby services (calculated on client or via Places API in real app).
    """
    cities = db.query(City).all()
    if not cities:
        raise HTTPException(status_code=404, detail="No city data available")

    # Find nearest city efficiently (linear scan is fine for < 1000 cities)
    nearest_city = None
    min_distance = float('inf')

    for city in cities:
        if city.latitude and city.longitude:
            dist = haversine_distance(latitude, longitude, city.latitude, city.longitude)
            if dist < min_distance:
                min_distance = dist
                nearest_city = city

    if not nearest_city:
         # Fallback to national numbers if too far from any logged city
         return {
             "city_name": "Unknown",
             "distance_km": 0,
             "emergency_numbers": {"police": "112", "ambulance": "112", "fire": "101"},
             "message": "You are far from any tracked city. Providing national emergency numbers."
         }
    
    # Generic emergency logic if not specific numbers
    numbers = nearest_city.emergency_numbers or {"police": "100", "ambulance": "108", "fire": "101"}

    return {
        "city_name": nearest_city.name,
        "state": nearest_city.state,
        "distance_km": round(min_distance, 2),
        "emergency_numbers": numbers,
        "nearby_places_query": f"police station near {nearest_city.name}", # Hint for frontend to construct map queries
    }
