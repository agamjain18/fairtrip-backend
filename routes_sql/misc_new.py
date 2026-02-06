import shutil
import os
from datetime import datetime, timezone
import traceback
from utils.timezone_utils import get_ist_now
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from database_sql import Photo, Trip, User, get_db
from typing import List
from routes_sql.auth import get_current_user_sql

router = APIRouter(prefix="/misc", tags=["Miscellanous"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "uploads")

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    
@router.post("/upload-receipt/{trip_id}")
def upload_receipt(
    trip_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    try:
        # Validate file
        print(f"Receipt Content-Type: {file.content_type}")
        if not file.content_type.startswith('image/') and file.content_type != 'application/octet-stream':
            raise HTTPException(status_code=400, detail=f"File must be an image, got {file.content_type}")

        # Create unique filename
        timestamp = get_ist_now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{trip_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        print(f"DEBUG: Saving file to: {os.path.abspath(file_path)}")

        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate URL
        url = f"/static/{filename}"

        # Create Photo record in DB
        receipt = Photo(
            trip_id=trip_id,
            uploaded_by_id=current_user.id,
            url=url,
            caption="Bills",
            uploaded_at=get_ist_now()
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        return {"url": url, "id": receipt.id, "filename": filename}

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/photos/upload/{trip_id}")
def upload_trip_photo(
    trip_id: int,
    file: UploadFile = File(...),
    caption: str = Form(None),
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    try:
        # Validate file
        print(f"Photo Content-Type: {file.content_type}")
        if not file.content_type.startswith('image/') and file.content_type != 'application/octet-stream':
            raise HTTPException(status_code=400, detail=f"File must be an image, got {file.content_type}")

        # Create unique filename
        timestamp = get_ist_now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{trip_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)

        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate URL
        url = f"/static/{filename}"

        # Create Photo record in DB
        photo = Photo(
            trip_id=trip_id,
            uploaded_by_id=current_user.id,
            url=url,
            caption=caption or "Trip Photo",
            uploaded_at=get_ist_now()
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)

        return {"url": url, "id": photo.id, "filename": filename, "caption": photo.caption}

    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/receipts/{trip_id}")
def get_trip_receipts(trip_id: int, db: Session = Depends(get_db)):
    # Legacy endpoint
    return db.query(Photo).filter(Photo.trip_id == trip_id).order_by(Photo.uploaded_at.desc()).all()

@router.get("/photos/{trip_id}")
@router.get("/photos/trip/{trip_id}")
def get_trip_photos(trip_id: int, db: Session = Depends(get_db)):
    """Fetch all photos for a specific trip with uploader info"""
    photos = db.query(Photo).filter(Photo.trip_id == trip_id).order_by(Photo.uploaded_at.desc()).all()
    
    # Enrich with uploader name
    result = []
    for photo in photos:
        p_dict = {
            "id": photo.id,
            "url": photo.url,
            "caption": photo.caption,
            "uploaded_at": photo.uploaded_at,
            "uploaded_by_id": photo.uploaded_by_id,
            "uploader_name": photo.uploaded_by.full_name if photo.uploaded_by else "Unknown"
        }
        result.append(p_dict)
        
    return result

@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int, 
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    """Delete a photo record and its associated file"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    # Check permissions: only uploader can delete
    if photo.uploaded_by_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to delete this photo")

    # Try to delete file from disk
    try:
        if photo.url and photo.url.startswith("/static/"):
            filename = photo.url.replace("/static/", "")
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error removing file {photo.url}: {e}")
        # Continue to delete DB record even if file deletion fails

    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}
