from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/v1/attendance", tags=["Attendance"])

# Mock function for S3 Upload
def upload_to_storage(file: UploadFile) -> str:
    """In production, upload to AWS S3 here and return the URL."""
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return a fake URL for now
    return f"http://localhost:8000/{file_path}"

@router.post("/mark", response_model=schemas.AttendanceResponse)
def mark_attendance_with_proof(
    subject: str = Form(...),
    date: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    accuracy: float = Form(...),
    address: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Hardcoded user for this example (Normally extracted from JWT Token)
    user = db.query(models.User).first()
    if not user:
        user = models.User(email="student@scholara.edu")
        db.add(user)
        db.commit()

    # 2. Upload the file to our "S3" storage
    photo_url = upload_to_storage(photo)

    # 3. Create the database records
    new_attendance = models.Attendance(
        user_id=user.id,
        subject=subject,
        date=date,
        status=models.AttendanceStatus.ATT
    )
    db.add(new_attendance)
    db.flush() # Get the new_attendance ID without committing yet

    new_proof = models.AttendanceProof(
        attendance_id=new_attendance.id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        address=address,
        photo_url=photo_url
    )
    db.add(new_proof)
    db.commit()
    db.refresh(new_attendance)

    return new_attendance

@router.get("/{date}", response_model=list[schemas.AttendanceResponse])
def get_attendance_for_day(date: str, db: Session = Depends(get_db)):
    # Again, assuming a hardcoded user for the skeleton
    user = db.query(models.User).first()
    if not user: return []
    
    records = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id,
        models.Attendance.date == date
    ).all()

    
    return records
@router.get("/", response_model=list[schemas.AttendanceResponse])
def get_all_attendance(db: Session = Depends(get_db)):
    # Grab the hardcoded user we created earlier
    user = db.query(models.User).first()
    if not user: return []
    
    # Fetch all records and their associated proofs
    records = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id
    ).all()
    
    return records