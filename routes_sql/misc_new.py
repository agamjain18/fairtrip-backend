import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database_sql import Photo, Trip, User, get_db
from typing import List
from datetime import datetime, timezone
from routes_sql.auth import get_current_user_sql

router = APIRouter(prefix="/misc", tags=["Miscellanous"])

UPLOAD_DIRECTORY = "uploads"
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
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{trip_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)

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
            caption="Receipt",
            uploaded_at=datetime.now(timezone.utc)
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        return {"url": url, "id": receipt.id, "filename": filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/photos/upload/{trip_id}")
def upload_trip_photo(
    trip_id: int,
    file: UploadFile = File(...),
    caption: str = None,
    current_user: User = Depends(get_current_user_sql),
    db: Session = Depends(get_db)
):
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
            uploaded_at=datetime.now(timezone.utc)
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)

        return {"url": url, "id": photo.id, "filename": filename, "caption": photo.caption}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/receipts/{trip_id}")
def get_trip_receipts(trip_id: int, db: Session = Depends(get_db)):
    receipts = db.query(Photo).filter(Photo.trip_id == trip_id).order_by(Photo.uploaded_at.desc()).all()
    return receipts
