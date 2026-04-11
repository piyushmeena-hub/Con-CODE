from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import AttendanceStatus

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