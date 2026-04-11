from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import uvicorn

# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./faculty_dashboard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    total_classes = Column(Integer, default=40)
    attended_classes = Column(Integer, default=0)
    score_history = Column(JSON, default=[]) 

class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True)
    day = Column(String)
    time_slot = Column(String)
    course = Column(String)
    room = Column(String)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS ---
class StudentCreate(BaseModel):
    name: str
    total_classes: int

app = FastAPI()

# --- SEED DATA ---
def seed_data():
    db = SessionLocal()
    if db.query(Student).count() == 0:
        db.add_all([
            Student(name="Aarav Sharma", total_classes=40, attended_classes=35, score_history=[85, 90, 78]),
            Student(name="Priya Patel", total_classes=40, attended_classes=28, score_history=[92, 88, 95])
        ])
        db.add_all([
            Timetable(day="Monday", time_slot="09:00-10:00", course="Machine Learning", room="Lab 201"),
            Timetable(day="Tuesday", time_slot="10:00-11:00", course="Data Structures", room="Room 104")
        ])
        db.commit()
    db.close()

seed_data()

# --- ENDPOINTS ---

@app.get("/api/v1/faculty/me/dashboard")
def get_dashboard(db: Session = Depends(lambda: SessionLocal())):
    students = db.query(Student).all()
    return [
        {
            "student_id": s.id, "name": s.name, "total_classes": s.total_classes,
            "attended_classes": s.attended_classes,
            "attendance_percentage": round((s.attended_classes / s.total_classes) * 100, 1) if s.total_classes > 0 else 0,
            "performance_score": round(sum(s.score_history)/len(s.score_history), 1) if s.score_history else 0,
            "score_history": s.score_history
        } for s in students
    ]

@app.get("/api/v1/faculty/me/timetable")
def get_timetable(db: Session = Depends(lambda: SessionLocal())):
    entries = db.query(Timetable).all()
    res = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    for e in entries:
        if e.day in res:
            res[e.day][e.time_slot] = {"course": e.course, "room": e.room}
    return res

@app.post("/api/v1/assessments/marks/bulk")
def update_marks(payload: dict, db: Session = Depends(lambda: SessionLocal())):
    for entry in payload['marks']:
        student = db.query(Student).filter(Student.id == entry['student_id']).first()
        if student:
            h = list(student.score_history)
            h.append(entry['score'])
            student.score_history = h
    db.commit()
    return {"message": "Marks updated successfully"}

@app.post("/api/v1/students")
def add_new_student(payload: StudentCreate, db: Session = Depends(lambda: SessionLocal())):
    new_student = Student(name=payload.name, total_classes=payload.total_classes, attended_classes=0, score_history=[])
    db.add(new_student)
    db.commit()
    return {"message": f"Student '{payload.name}' registered successfully!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)