from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import numpy as np
import cv2

# Use FastEmbed ONNX model to bypass macOS TensorFlow thread deadlocks
try:
    from fastembed import ImageEmbedding
    _image_model = None
except ImportError:
    pass

def get_image_model():
    global _image_model
    if _image_model is None:
        _image_model = ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision")
    return _image_model

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

# Initialize OpenCV Face Detector globally to save load time
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def crop_face(img_path):
    """Detects and crops to the largest face. Returns path to cropped temp image or original if no face found."""
    img = cv2.imread(img_path)
    if img is None:
        return img_path
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        return img_path # Fallback to full image if no face detected
        
    # Get largest face
    faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
    x, y, w, h = faces[0]
    
    # Expand bounding box slightly for context
    padding = int(w * 0.2)
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(img.shape[1], x + w + padding)
    y2 = min(img.shape[0], y + h + padding)
    
    cropped = img[y1:y2, x1:x2]
    
    # Save to a temp file
    cropped_path = img_path + "_cropped.jpg"
    cv2.imwrite(cropped_path, cropped)
    return cropped_path

@router.post("/verify_face", response_model=schemas.VerifyFaceResponse)
def verify_face(photo: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        user = models.User(email="student@scholara.edu")
        db.add(user)
        db.commit()

    # Save incoming photo
    temp_dir = "uploads/temp"
    os.makedirs(temp_dir, exist_ok=True)
    incoming_path = f"{temp_dir}/incoming_{datetime.utcnow().timestamp()}.jpg"
    
    with open(incoming_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
        
    try:
        # Check if reference face exists
        if not user.reference_face_url:
            return schemas.VerifyFaceResponse(match=False, message="face not enrolled. please upload in profile")

        # Verify using FastEmbed ONNX Model bypasses TensorFlow deadlock entirely
        model = get_image_model()
        
        # 1. Crop images strictly to faces using cv2
        cropped_incoming = crop_face(incoming_path)
        cropped_reference = crop_face(user.reference_face_url)
        
        # 2. Extract facial embeddings via Vision Model
        emb1 = next(model.embed([cropped_incoming]))
        emb2 = next(model.embed([cropped_reference]))
        
        # 3. Calculate Cosine Similarity
        similarity = float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        
        # A conservative threshold for identical faces using generic ViT model
        is_match = similarity > 0.88
        
        if is_match:
            message = "Face matched successfully."
        else:
            message = "face not recognise warning"
            
        # Clean up
        if os.path.exists(cropped_incoming) and cropped_incoming != incoming_path:
            os.remove(cropped_incoming)
        if os.path.exists(cropped_reference) and cropped_reference != user.reference_face_url:
            os.remove(cropped_reference)
            
        # Clean up
        if os.path.exists(incoming_path) and user.reference_face_url != incoming_path:
            os.remove(incoming_path)
            
        return schemas.VerifyFaceResponse(match=is_match, message=message)
        
    except Exception as e:
        return schemas.VerifyFaceResponse(match=False, message=f"Face detection failed: {str(e)}")

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