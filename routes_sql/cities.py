from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from database_sql import City, DestinationImage, get_db
import json

router = APIRouter(prefix="/cities", tags=["cities"])

# Import Redis client
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis client not available for cities routes")

@router.get("/featured-images")
async def get_featured_images(db: Session = Depends(get_db)):
    """Get all destination images for the home screen slider"""
    cache_key = "featured_images:all"
    
    # Try cache first
    if REDIS_AVAILABLE:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                print(f"✅ Cache HIT: {cache_key}")
                return cached
        except Exception as e:
            print(f"Redis GET error: {e}")
    
    # Get from database
    images = db.query(DestinationImage).all()
    result = [
        {
            "id": img.id,
            "city_name": img.city_name,
            "image_url": img.image_url,
            "description": img.description
        }
        for img in images
    ]
    
    # Cache for 1 hour (3600 seconds)
    if REDIS_AVAILABLE:
        try:
            await redis_client.set(cache_key, result, expire=3600)
            print(f"💾 Cached: {cache_key}")
        except Exception as e:
            print(f"Redis SET error: {e}")
    
    return result

@router.get("/search")
async def search_cities(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search cities by name"""
    cache_key = f"cities:search:{q.lower()}"
    
    # Try cache first
    if REDIS_AVAILABLE:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                print(f"✅ Cache HIT: {cache_key}")
                return cached
        except Exception as e:
            print(f"Redis GET error: {e}")
    
    # Get from database
    cities = db.query(City).filter(City.name.ilike(f"{q}%")).limit(10).all()
    result = [
        {
            "id": city.id,
            "name": city.name,
            "state": city.state,
            "country": city.country,
            "latitude": city.latitude,
            "longitude": city.longitude,
            "image_url": city.image_url
        }
        for city in cities
    ]
    
    # Cache for 5 minutes (300 seconds)
    if REDIS_AVAILABLE:
        try:
            await redis_client.set(cache_key, result, expire=300)
            print(f"💾 Cached: {cache_key}")
        except Exception as e:
            print(f"Redis SET error: {e}")
    
    return result

@router.get("/")
async def get_all_cities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all cities"""
    cache_key = f"cities:all:skip{skip}:limit{limit}"
    
    # Try cache first
    if REDIS_AVAILABLE:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                print(f"✅ Cache HIT: {cache_key}")
                return cached
        except Exception as e:
            print(f"Redis GET error: {e}")
    
    # Get from database
    cities = db.query(City).offset(skip).limit(limit).all()
    result = [
        {
            "id": city.id,
            "name": city.name,
            "state": city.state,
            "latitude": city.latitude,
            "longitude": city.longitude,
            "emergency_numbers": city.emergency_numbers,
            "popular_spots": city.popular_spots
        }
        for city in cities
    ]
    
    # Cache for 30 minutes (1800 seconds)
    if REDIS_AVAILABLE:
        try:
            await redis_client.set(cache_key, result, expire=1800)
            print(f"💾 Cached: {cache_key}")
        except Exception as e:
            print(f"Redis SET error: {e}")
    
    return result

@router.get("/{city_name}")
async def get_city_details(city_name: str, db: Session = Depends(get_db)):
    """Get details for a specific city"""
    cache_key = f"cities:details:{city_name.lower()}"
    
    # Try cache first
    if REDIS_AVAILABLE:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                print(f"✅ Cache HIT: {cache_key}")
                return cached
        except Exception as e:
            print(f"Redis GET error: {e}")
    
    # Get from database
    city = db.query(City).filter(City.name.ilike(city_name)).first()
    if not city:
        return {"error": "City not found"}
    
    result = {
        "id": city.id,
        "name": city.name,
        "state": city.state,
        "country": city.country,
        "latitude": city.latitude,
        "longitude": city.longitude,
        "image_url": city.image_url
    }
    
    # Cache for 1 hour (3600 seconds)
    if REDIS_AVAILABLE:
        try:
            await redis_client.set(cache_key, result, expire=3600)
            print(f"💾 Cached: {cache_key}")
        except Exception as e:
            print(f"Redis SET error: {e}")
    
    return result
