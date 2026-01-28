from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from database_sql import City, DestinationImage, get_db
import json

router = APIRouter(prefix="/cities", tags=["cities"])

@router.get("/featured-images")
def get_featured_images(db: Session = Depends(get_db)):
    """Get all destination images for the home screen slider"""
    return db.query(DestinationImage).all()

@router.get("/search")
def search_cities(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search cities by name"""
    cities = db.query(City).filter(City.name.ilike(f"{q}%")).limit(10).all()
    return cities

@router.get("/")
def get_all_cities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all cities"""
    cities = db.query(City).offset(skip).limit(limit).all()
    return cities

@router.get("/{city_name}")
def get_city_details(city_name: str, db: Session = Depends(get_db)):
    """Get details for a specific city"""
    city = db.query(City).filter(City.name.ilike(city_name)).first()
    if not city:
        return {"error": "City not found"}
    return city
