
from database_sql import SessionLocal, City
import json

db = SessionLocal()
cities = db.query(City).all()
for city in cities:
    print(f"City: {city.name}")
    print(f"Spots: {city.popular_spots}")
    print("-" * 20)
db.close()
