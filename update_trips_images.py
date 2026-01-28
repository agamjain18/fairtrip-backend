
import asyncio
from sqlalchemy.orm import Session
from database_sql import SessionLocal, Trip
from utils.image_utils import update_trip_image_task

async def update_all_trips():
    db = SessionLocal()
    try:
        trips = db.query(Trip).all()
        print(f"Found {len(trips)} trips to process.")
        
        for trip in trips:
            if trip.destination:
                print(f"Updating image for trip {trip.id}: {trip.title} ({trip.destination})...")
                await update_trip_image_task(trip.id, trip.destination, db)
            else:
                print(f"Skipping trip {trip.id} (No destination).")
                
        print("\n✅ All existing trips have been updated with new images!")
    except Exception as e:
        print(f"❌ Error updating trips: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(update_all_trips())
