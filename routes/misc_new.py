import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from database import Photo, Trip, User
from typing import List
from datetime import datetime, timezone
from beanie import PydanticObjectId
from routes.auth import get_current_user

router = APIRouter(prefix="/misc", tags=["Miscellanous"])

UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    
@router.post("/upload-receipt/{trip_id}")
async def upload_receipt(
    trip_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{trip_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)

        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate URL (In a real app, this would be a cloud storage URL)
        # For now, we'll return a path that needs to be served by a static file handler
        url = f"/static/{filename}"

        # Create Photo record in DB
        receipt = Photo(
            trip=PydanticObjectId(trip_id),
            uploaded_by=current_user.id,
            url=url,
            caption="Receipt",
            uploaded_at=datetime.now(timezone.utc)
        )
        await receipt.save()

        return {"url": url, "id": str(receipt.id), "filename": filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/receipts/{trip_id}")
async def get_trip_receipts(trip_id: str):
    receipts = await Photo.find(Photo.trip == PydanticObjectId(trip_id)).sort(-Photo.uploaded_at).to_list()
    return receipts

@router.get("/maps/fleet_dashboard")
async def get_fleet_dashboard_map():
    # Example data; replace with database query
    return {
        "mapUrl": "https://maps.googleapis.com/maps/api/staticmap?center=LAX&zoom=14&size=600x300&maptype=roadmap&key=YOUR_API_KEY"
    }

@router.get("/maps/visa_entry_info")
async def get_visa_entry_info_map():
    # Example data; replace with database query
    return {
        "mapUrl": "https://maps.googleapis.com/maps/api/staticmap?center=Tokyo&zoom=9&size=600x300&maptype=terrain&key=YOUR_API_KEY"
    }
