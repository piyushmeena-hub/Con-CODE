from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class AttendanceStatus(str, enum.Enum):
    ATT = "att"
    MISS = "miss"
    OFF = "off"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # Replaced email with username
    hashed_password = Column(String)
    role = Column(String, default="student") # 'student' or 'teacher'
    target_attendance = Column(Float, default=75.0)
    
    attendances = relationship("Attendance", back_populates="user")

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String, index=True)
    date = Column(String, index=True) # Stored as YYYY-MM-DD
    status = Column(Enum(AttendanceStatus))
    
    user = relationship("User", back_populates="attendances")
    proof = relationship("AttendanceProof", back_populates="attendance", uselist=False)

class AttendanceProof(Base):
    __tablename__ = "attendance_proofs"
    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(Integer, ForeignKey("attendances.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    accuracy = Column(Float)
    address = Column(String)
    photo_url = Column(String) # URL to S3, NOT the base64 string
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    attendance = relationship("Attendance", back_populates="proof")

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean

# ... [Keep your existing User, Attendance, and AttendanceProof classes here] ...

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True) # String because Streamlit uses time.time()
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(String)
    completed = Column(Boolean, default=False)

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String)
    subject = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    duration = Column(String)