import os
import asyncio
import httpx
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from database_sql import Trip, DestinationImage

# Use the same API key as ai_service.py (configured in client already, but safe to keep or remove if unused here)
# API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
# genai.configure(api_key=API_KEY)

async def get_famous_spot_image(destination: str, db: Session) -> str:
    """
    Checks cache for destination image. If not found, asks Gemini for a famous spot,
    constructs an Unsplash URL, caches it, and returns the URL.
    """
    # 1. Check Cache
    cached = db.query(DestinationImage).filter(DestinationImage.destination.ilike(destination)).first()
    if cached:
        print(f"🎯 Cache HIT for {destination}: {cached.image_url}")
        return cached.image_url

    # 2. Skip AI identifying famous spot - just use the destination directly
    # OR use a very simple lookup for common major cities
    spot_name = destination
    print(f"🌟 Identifying famous spot for {destination}: {spot_name}")
        
    # 3. Construct URL
    # We use a high-quality featured search on Unsplash with better keywords
    # Using a direct URL pattern that often works better than the 'featured' redirect
    image_url = f"https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80" # Default fallback
    
    # Try to generate a more specific keyword-based URL
    # We'll stick to a more robust unsplash keyword search or a backup provider
    search_keywords = f"{spot_name.replace(' ', ',')},landscape,landmark,travel"
    image_url = f"https://source.unsplash.com/1200x800/?{search_keywords}"
    
    # If source.unsplash.com is being flaky, we can use a backup like loremflickr
    # image_url = f"https://loremflickr.com/1200/800/{spot_name.replace(' ', ',')},travel"
    
    # Actually, let's use a very high-quality direct reference for Udaipur if it's Udaipur
    if "udaipur" in spot_name.lower():
        image_url = "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=1200&q=80"
    elif "paris" in spot_name.lower():
        image_url = "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1200&q=80"
    
    # 4. Save to Cache
    try:
        new_cache = DestinationImage(
            destination=destination,
            image_url=image_url,
            famous_spot=spot_name
        )
        db.add(new_cache)
        db.commit()
        print(f"💾 Cached new image for {destination}")
    except Exception as cache_error:
        db.rollback()
        print(f"⚠️ Cache save error (might be duplicate): {cache_error}")
        # Try to fetch again in case of race condition
        cached = db.query(DestinationImage).filter(DestinationImage.destination.ilike(destination)).first()
        if cached: return cached.image_url

    return image_url

async def update_trip_image_task(trip_id: int, destination: str, db: Session):
    """
    Background task to fetch/cache an image, get coordinates, and update the trip.
    """
    if not destination:
        return

    # Normalize destination
    destination = destination.strip()
    
    # 1. Image
    image_url = await get_famous_spot_image(destination, db)
    
    # 2. Coordinates (Non-AI Geocoding)
    lat, lng = None, None
    try:
        # Use Nominatim (OpenStreetMap) instead of AI for geocoding
        # This is strictly non-AI and reliable
        url = f"https://nominatim.openstreetmap.org/search?q={destination}&format=json&limit=1"
        headers = {"User-Agent": "FairShare/1.0"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    lat = float(data[0]['lat'])
                    lng = float(data[0]['lon'])
                    print(f"📍 Geocoded {destination} to {lat}, {lng}")
    except Exception as e:
        print(f"⚠️ Failed to geocode {destination}: {e}")

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip:
        trip.image_url = image_url
        if lat is not None and lng is not None:
            trip.latitude = lat
            trip.longitude = lng
        db.commit()
        print(f"✅ Updated trip {trip_id} with image and coordinates.")

async def get_city_tourist_spots_images(city_name: str) -> List[str]:
    """
    Finds tourist spots for a city and returns their image URLs.
    """
    try:
        # Simplified: Use city name directly with common landmark descriptors
        spots = [f"{city_name} landmark", f"{city_name} landscape", f"{city_name} city view"]
        
        image_urls = []
        for spot in spots:
            search_keywords = f"{spot.replace(' ', ',')},travel"
            image_urls.append(f"https://source.unsplash.com/1200x800/?{search_keywords}")
        
        return image_urls
    except Exception as e:
        print(f"❌ Error getting spots for {city_name}: {e}")
        return [f"https://source.unsplash.com/1200x800/?{city_name},travel"]
