
import asyncio
from sqlalchemy.orm import Session
from database_sql import SessionLocal, City
from utils.image_utils import get_city_tourist_spots_images

async def populate_city_spots(city_name: str):
    db = SessionLocal()
    try:
        # Normalize city name
        city = db.query(City).filter(City.name.ilike(city_name)).first()
        
        if not city:
            print(f"🏙️ Creating new city record for: {city_name}")
            city = City(name=city_name)
            db.add(city)
            db.commit()
            db.refresh(city)
        
        print(f"🔍 Fetching top 5 spots for {city_name}...")
        spot_images = await get_city_tourist_spots_images(city_name)
        
        print(f"✅ Found {len(spot_images)} images.")
        for i, url in enumerate(spot_images):
            print(f"  {i+1}. {url}")
            
        city.popular_spots = spot_images
        db.commit()
        print(f"💾 Saved to database for {city_name}.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # You can change 'Udaipur' to any city you want to populate
    asyncio.run(populate_city_spots("Udaipur"))
    asyncio.run(populate_city_spots("Paris"))
    asyncio.run(populate_city_spots("Tokyo"))
    asyncio.run(populate_city_spots("New Delhi"))
    asyncio.run(populate_city_spots("London"))
