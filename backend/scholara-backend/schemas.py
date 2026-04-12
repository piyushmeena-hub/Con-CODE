from pydantic import BaseModel
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

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str
    role: str
