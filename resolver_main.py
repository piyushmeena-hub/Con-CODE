with open("backend/scholara-backend/main.py", "w") as f:
    f.write("""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine
import models
from routers import attendance, productivity, profile, auth

# Create database tables
models.Base.metadata.create_all(bind=engine)

# THIS IS THE "app" UVICORN IS LOOKING FOR:
app = FastAPI(title="Scholara Backend API")

# Allow Streamlit frontend to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the "uploads" directory so we can view the saved images
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(attendance.router)
app.include_router(productivity.router)
app.include_router(profile.router)
app.include_router(auth.router)

@app.get("/")
def health_check():
    return {"status": "Scholara API is running. Strict mode enabled."}
""")

with open("backend/scholara-backend/schemas.py", "w") as f:
    f.write("""from pydantic import BaseModel
from typing import Optional
from enum import Enum

class AttendanceStatus(str, Enum):
    ATTENDED = "ATTENDED"
    MISSED = "MISSED"
    OFF = "OFF"
    CLEAR = "CLEAR"

class MarkAttendanceRequest(BaseModel):
    subject: str
    date: str
    status: AttendanceStatus
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    face_image_path: Optional[str] = None

class ProofResponse(BaseModel):
    latitude: float
    longitude: float
    distance_m: float
    face_image_path: str
    timestamp: str

    class Config:
        from_attributes = True

class AttendanceResponse(BaseModel):
    id: int
    subject: str
    date: str
    status: AttendanceStatus
    proof: Optional[ProofResponse] = None

    class Config:
        from_attributes = True

class VerifyFaceResponse(BaseModel):
    match: bool
    message: str

class TaskSchema(BaseModel):
    id: str
    text: str
    completed: bool

class SessionSchema(BaseModel):
    date: str
    subject: str
    start_time: str
    end_time: str
    duration: str
""")

