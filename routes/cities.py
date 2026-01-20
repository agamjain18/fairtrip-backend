from fastapi import APIRouter, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/cities", tags=["cities"])

# Database connection
DATABASE_URL = "mongodb://localhost:27017"
DATABASE_NAME = "fairshare"

async def get_cities_collection():
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    return db["indian_cities"]

@router.get("/search")
async def search_cities(q: str = Query(..., min_length=1, description="Search query")):
    """Search Indian cities by name"""
    collection = await get_cities_collection()
    
    # Case-insensitive search
    cursor = collection.find(
        {"name": {"$regex": f"^{q}", "$options": "i"}},
        {"_id": 0}  # Exclude MongoDB _id field
    ).limit(10)
    
    cities = await cursor.to_list(length=10)
    return cities

@router.get("/")
async def get_all_cities(skip: int = 0, limit: int = 100):
    """Get all Indian cities"""
    collection = await get_cities_collection()
    
    cursor = collection.find(
        {},
        {"_id": 0}
    ).skip(skip).limit(limit)
    
    cities = await cursor.to_list(length=limit)
    return cities

@router.get("/{city_name}")
async def get_city_details(city_name: str):
    """Get details and emergency numbers for a specific city"""
    collection = await get_cities_collection()
    
    city = await collection.find_one(
        {"name": {"$regex": f"^{city_name}$", "$options": "i"}},
        {"_id": 0}
    )
    
    if not city:
        return {"error": "City not found"}
    
    return city
