from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
import shutil
import os
import uuid
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])

UPLOAD_DIR = "uploads/reference_faces"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/me")
def get_my_profile(db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": user.id,
        "email": user.email,
        "target_attendance": user.target_attendance,
        "reference_face_url": user.reference_face_url
    }

@router.post("/upload_face")
def upload_face(photo: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # If they already had a face, remove old one to save space (optional, but good practice)
    if user.reference_face_url and os.path.exists(user.reference_face_url):
        try:
            os.remove(user.reference_face_url)
        except:
            pass

    ext = os.path.splitext(photo.filename)[1]
    if not ext:
        ext = ".jpg"
    safe_filename = f"user_{user.id}_face_{uuid.uuid4().hex[:6]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
        
    user.reference_face_url = filepath
    db.commit()
    
    return {"status": "success", "reference_face_url": filepath}
