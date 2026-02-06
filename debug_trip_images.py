
from database_sql import SessionLocal, Trip
import json

db = SessionLocal()
trips = db.query(Trip).all()
for trip in trips:
    print(f"ID: {trip.id}")
    print(f"Title: {trip.title}")
    print(f"Destination: {trip.destination}")
    print(f"Origin: {trip.start_location}")
    print(f"Dates: {trip.start_date} to {trip.end_date}")
    print(f"Budget: {trip.currency} {trip.total_budget}")
    print(f"Image: {trip.image_url}")
    print("-" * 20)
db.close()
