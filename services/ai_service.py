import google.generativeai as genai
import json
import asyncio
from typing import Dict, List, Any
from database import Trip
from motor.motor_asyncio import AsyncIOMotorClient

# Configure Gemini
API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Database connection for caching images
DATABASE_URL = "mongodb://localhost:27017"
DATABASE_NAME = "fairshare"

async def get_images_collection():
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    return db["place_images"]

async def fetch_place_image(place_name: str) -> str:
    """
    Fetch an image for a place. Checks cache first, then asks Gemini/Web.
    """
    collection = await get_images_collection()
    
    # Check cache
    cached = await collection.find_one({"place_name": place_name})
    if cached and cached.get("image_url"):
        return cached["image_url"]

    # If not in cache, we need to find an image.
    # Since we can't search Google Images directly without an API key for Custom Search,
    # we will rely on Gemini to provide a known public URL if possible, or use a placeholder.
    # For a robust solution without a paid search API, we'll try to get Gemini to give us a Wikimedia/Unsplash URL.
    
    prompt = f"""
    Find a valid, public, direct image URL (jpg/png) for the tourist place: "{place_name}".
    Prefer Wikimedia Commons or Unsplash URLs.
    If you cannot find a specific URL, return "PLACEHOLDER".
    Return ONLY the URL string, nothing else.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        image_url = response.text.strip()
        
        if "PLACEHOLDER" in image_url or len(image_url) > 500 or not image_url.startswith("http"):
             # Fallback to a generic travel image service
             image_url = f"https://source.unsplash.com/800x600/?{place_name.replace(' ', ',')}"
        
        # Cache the result
        await collection.insert_one({
            "place_name": place_name,
            "image_url": image_url,
            "updated_at": datetime.now()
        })
        
        return image_url
    except Exception as e:
        print(f"Error fetching image for {place_name}: {e}")
        return f"https://source.unsplash.com/800x600/?travel,{place_name}"

async def generate_trip_itinerary(trip_id: str, destination: str, start_date: str, end_date: str, budget: float):
    """
    Generates a trip itinerary using Gemini and saves it to the database.
    """
    try:
        trip = await Trip.get(trip_id)
        if not trip:
            return

        # Update status to processing (10%)
        await trip.update({"$set": {"ai_status": "processing", "ai_progress": 10}})
        
        # Calculate duration
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        days = (end - start).days + 1
        
        prompt = f"""
        Create a detailed {days}-day itinerary for a trip to {destination} with a budget of {budget}.
        
        REQUIREMENTS:
        1. Find at least 5 top tourist places to visit.
        2. Create a day-by-day itinerary covering these places appropriately.
        3. Optimize for covering maximum places comfortably.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "top_places": [
                {{ "name": "Place Name", "description": "Short description" }}
            ],
            "itinerary": [
                {{
                    "day": 1,
                    "title": "Day Title",
                    "activities": [
                        {{ "time": "Morning", "activity": "...", "place": "Place Name" }}
                    ]
                }}
            ]
        }}
        """
        
        response = await model.generate_content_async(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(text)
        
        # 40% Progress - Text generated
        current_progress = 40
        await trip.update({"$set": {"ai_progress": current_progress}})

        # Process and enhance with images
        top_places = result.get("top_places", [])
        enhanced_places = []
        
        total_places = len(top_places)
        if total_places > 0:
            progress_step = 50 // total_places # Allocate 50% for images
        
        for i, place in enumerate(top_places):
            image_url = await fetch_place_image(place["name"])
            place["image_url"] = image_url
            enhanced_places.append(place)
            
            # Increment progress
            current_progress += progress_step
            await trip.update({"$set": {"ai_progress": min(95, current_progress)}})
            
        result["top_places"] = enhanced_places
        
        # Update trip with result and completed status (100%)
        await trip.update({
            "$set": {
                "itinerary_data": result,
                "ai_status": "completed",
                "ai_progress": 100
            }
        })
        print(f"✅ AI Itinerary generated and saved for trip {trip_id}")
            
    except Exception as e:
        print(f"❌ Error generating AI itinerary: {e}")
        # Update status to failed
        trip = await Trip.get(trip_id)
        if trip:
            await trip.update({"$set": {"ai_status": "failed"}})

from datetime import datetime
