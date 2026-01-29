
import asyncio
from sqlalchemy.orm import Session
from database_sql import SessionLocal, Trip
import google.generativeai as genai
from utils.ai_client import generate_content_with_fallback

# Configure Gemini
# API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel('gemini-1.5-flash')

async def geocode_trips():
    db = SessionLocal()
    try:
        trips = db.query(Trip).all()
        print(f"Checking {len(trips)} trips for coordinates...")
        
        for trip in trips:
            if trip.destination and (trip.latitude is None or trip.longitude is None):
                print(f"📍 Geocoding '{trip.destination}' for trip {trip.id}...")
                try:
                    coord_prompt = f"Return ONLY the latitude and longitude of '{trip.destination}' as 'lat,lng'. No other text."
                    # Use fallback client
                    resp = await asyncio.to_thread(generate_content_with_fallback, coord_prompt)
                    bits = resp.text.strip().split(',')
                    if len(bits) == 2:
                        trip.latitude = float(bits[0].strip())
                        trip.longitude = float(bits[1].strip())
                        print(f"  ✅ Saved: {trip.latitude}, {trip.longitude}")
                except Exception as e:
                    print(f"  ❌ Failed: {e}")
        
        db.commit()
        print("\n✅ All trips processed!")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(geocode_trips())
