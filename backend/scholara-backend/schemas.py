from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import AttendanceStatus

# Add this at the top with your other imports
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
# --- Responses ---
class ProofResponse(BaseModel):
    latitude: float
    longitude: float
    accuracy: float
    address: str
    photo_url: str
    timestamp: datetime

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