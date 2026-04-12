<<<<<<< HEAD
"""
Faculty Dashboard API — SQLAlchemy + SQLite backend
Solves:
  1. Relational master data  (Students, Courses, Enrollments)
  2. Dynamic timetable       (Rooms, TimetableSessions)
  3. Audit trail             (GradeAuditLog on every score change)

Run:
    pip install fastapi uvicorn pydantic sqlalchemy
    python app.py
    # Swagger UI → http://localhost:8000/docs
"""
=======
import streamlit as st
import os
from langchain_groq import ChatGroq 
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA 
import sqlite3

# --- 1. INITIAL SETUP ---
# This sets the page title and the local JSON database for attendance
st.set_page_config(page_title="Learner's FREE AI Hub", layout="wide")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "concode.db")
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

>>>>>>> 01aa913d88921740c9e4c6737bcba4f8bb8766f2

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Table, create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# ══════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ══════════════════════════════════════════════════════════════════════

SQLALCHEMY_DATABASE_URL = "sqlite:///./faculty_dashboard.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ══════════════════════════════════════════════════════════════════════
# ORM MODELS
# ══════════════════════════════════════════════════════════════════════

# ── Many-to-many join table: students ↔ courses ──────────────────────
enrollment_table = Table(
    "enrollments",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id",  Integer, ForeignKey("courses.id"),  primary_key=True),
)


class Student(Base):
    __tablename__ = "students"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String,  nullable=False, index=True)
    enrollment_number = Column(String,  unique=True, nullable=False, index=True)
    total_classes     = Column(Integer, default=0)
    attended_classes  = Column(Integer, default=0)

    courses = relationship("Course", secondary=enrollment_table, back_populates="students")
    marks   = relationship("Mark",   back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String,  nullable=False)
    faculty_id = Column(Integer, nullable=False, index=True)

    students  = relationship("Student",          secondary=enrollment_table, back_populates="courses")
    sessions  = relationship("TimetableSession", back_populates="course")


class Room(Base):
    __tablename__ = "rooms"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String,  unique=True, nullable=False)
    capacity = Column(Integer, default=30)

    sessions = relationship("TimetableSession", back_populates="room")


class TimetableSession(Base):
    __tablename__ = "timetable_sessions"

    id          = Column(Integer, primary_key=True, index=True)
    course_id   = Column(Integer, ForeignKey("courses.id"), nullable=False)
    room_id     = Column(Integer, ForeignKey("rooms.id"),   nullable=False)
    day_of_week = Column(String,  nullable=False)   # e.g. "Monday"
    time_slot   = Column(String,  nullable=False)   # e.g. "09:00-10:00"

    course = relationship("Course", back_populates="sessions")
    room   = relationship("Room",   back_populates="sessions")


class Mark(Base):
    __tablename__ = "marks"

    id              = Column(Integer, primary_key=True, index=True)
    student_id      = Column(Integer, ForeignKey("students.id"), nullable=False)
    assessment_type = Column(String,  nullable=False)
    score           = Column(Float,   nullable=False)

    student    = relationship("Student",       back_populates="marks")
    audit_logs = relationship("GradeAuditLog", back_populates="mark")


class GradeAuditLog(Base):
    """Immutable record of every score change — academic integrity trail."""
    __tablename__ = "grade_audit_logs"

    id         = Column(Integer,  primary_key=True, index=True)
    mark_id    = Column(Integer,  ForeignKey("marks.id"), nullable=False)
    faculty_id = Column(Integer,  nullable=False)
    old_score  = Column(Float,    nullable=True)   # None on first entry
    new_score  = Column(Float,    nullable=False)
    timestamp  = Column(DateTime, default=datetime.utcnow, nullable=False)

    mark = relationship("Mark", back_populates="audit_logs")


# Create all tables (idempotent — safe to call on every startup)
Base.metadata.create_all(bind=engine)

# ══════════════════════════════════════════════════════════════════════
# SEED DATA  (runs once; skipped if data already exists)
# ══════════════════════════════════════════════════════════════════════

def _seed():
    db = SessionLocal()
    try:
        if db.query(Student).first():
            return  # already seeded

        # Rooms
        lab201   = Room(name="Lab 201",   capacity=40)
        room104  = Room(name="Room 104",  capacity=60)
        db.add_all([lab201, room104])
        db.flush()

        # Courses
        ml = Course(name="Machine Learning", faculty_id=1)
        ds = Course(name="Data Structures",  faculty_id=1)
        db.add_all([ml, ds])
        db.flush()

        # Students
        seed_students = [
            ("Aarav Sharma",  "2024CS101", 40, 32),
            ("Priya Patel",   "2024CS102", 40, 38),
            ("Rohan Mehta",   "2024CS103", 38, 28),
            ("Neha Singh",    "2024CS104", 40, 36),
            ("Karan Joshi",   "2024CS105", 40, 30),
            ("Ananya Gupta",  "2024CS106", 40, 35),
        ]
        students = []
        for name, enroll, total, attended in seed_students:
            s = Student(name=name, enrollment_number=enroll,
                        total_classes=total, attended_classes=attended)
            s.courses = [ml, ds]
            students.append(s)
        db.add_all(students)
        db.flush()

        # Seed marks (5 historical scores per student)
        seed_scores = {
            "2024CS101": [80, 85, 90, 82, 90.5],
            "2024CS102": [90, 95, 92, 89, 94],
            "2024CS103": [70, 68, 75, 72, 71],
            "2024CS104": [85, 90, 88, 91, 88],
            "2024CS105": [75, 80, 78, 82, 80],
            "2024CS106": [88, 92, 90, 94, 91],
        }
        assessment_labels = ["Quiz 1", "Quiz 2", "Midterm", "Assignment", "Quiz 3"]
        for s in students:
            for label, score in zip(assessment_labels, seed_scores[s.enrollment_number]):
                mark = Mark(student_id=s.id, assessment_type=label, score=score)
                db.add(mark)
                db.flush()
                db.add(GradeAuditLog(
                    mark_id=mark.id, faculty_id=1,
                    old_score=None, new_score=score,
                ))

        # Timetable sessions
        schedule = [
            (ml, lab201,  "Monday",    "09:00-10:00"),
            (ds, room104, "Monday",    "11:00-12:00"),
            (ml, lab201,  "Monday",    "14:00-15:00"),
            (ml, lab201,  "Tuesday",   "10:00-11:00"),
            (ds, room104, "Tuesday",   "12:00-13:00"),
            (ds, room104, "Tuesday",   "15:00-16:00"),
            (ds, room104, "Wednesday", "09:00-10:00"),
            (ml, lab201,  "Wednesday", "10:00-11:00"),
            (ml, lab201,  "Thursday",  "11:00-12:00"),
            (ds, room104, "Thursday",  "12:00-13:00"),
            (ds, room104, "Friday",    "09:00-10:00"),
            (ml, lab201,  "Friday",    "14:00-15:00"),
        ]
        for course, room, day, slot in schedule:
            db.add(TimetableSession(
                course_id=course.id, room_id=room.id,
                day_of_week=day, time_slot=slot,
            ))

        db.commit()
        print("✅ Database seeded.")
    except Exception as e:
        db.rollback()
        print(f"⚠️  Seed failed: {e}")
    finally:
        db.close()


_seed()

# ══════════════════════════════════════════════════════════════════════
# DB SESSION DEPENDENCY
# ══════════════════════════════════════════════════════════════════════

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ══════════════════════════════════════════════════════════════════════
# AUTH DEPENDENCY  (teammate will replace with JWT decode)
# ══════════════════════════════════════════════════════════════════════

def get_current_faculty_id() -> int:
    return 1  # Dr. Smith

def get_current_faculty() -> dict:
    return {"id": 1, "name": "Dr. Smith", "faculty_id": "FAC-CS-2024"}

# ══════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════

VALID_ASSESSMENT_TYPES = {"Quiz", "Midterm", "End-term", "Assignment",
                          "Quiz 1", "Quiz 2", "Quiz 3"}


class MarkEntry(BaseModel):
    student_id: int
    score: float = Field(..., ge=0, le=100)


class BulkMarksEntry(BaseModel):
    assessment_type: str
    course_id: int
    marks: List[MarkEntry]

    @field_validator("assessment_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_ASSESSMENT_TYPES:
            raise ValueError(f"assessment_type must be one of {VALID_ASSESSMENT_TYPES}")
        return v


class StudentOut(BaseModel):
    student_id:           int
    name:                 str
    enrollment_number:    str
    total_classes:        int
    attended_classes:     int
    attendance_percentage: float
    performance_score:    float
    score_history:        List[float]

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id:         int
    mark_id:    int
    faculty_id: int
    old_score:  Optional[float]
    new_score:  float
    timestamp:  datetime

    model_config = {"from_attributes": True}

# ══════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Faculty Dashboard API",
    version="2.0.0",
    description="SQLAlchemy-backed API with audit trail for the Faculty Dashboard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to Streamlit origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _build_student_out(student: Student, db: Session) -> dict:
    scores = [m.score for m in db.query(Mark)
              .filter(Mark.student_id == student.id)
              .order_by(Mark.id)
              .all()]
    pct = round(student.attended_classes / student.total_classes * 100, 1) \
          if student.total_classes else 0.0
    perf = round(sum(scores) / len(scores), 1) if scores else 0.0
    return {
        "student_id":            student.id,
        "name":                  student.name,
        "enrollment_number":     student.enrollment_number,
        "total_classes":         student.total_classes,
        "attended_classes":      student.attended_classes,
        "attendance_percentage": pct,
        "performance_score":     perf,
        "score_history":         scores,
    }

# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "ok", "api": "Faculty Dashboard API", "version": "2.0.0"}


# ── Faculty profile ───────────────────────────────────────────────────
@app.get("/api/v1/faculty/me")
def get_faculty_profile(faculty: dict = Depends(get_current_faculty)):
    return faculty


# ── Dashboard: all students for this faculty's courses ───────────────
@app.get("/api/v1/faculty/me/dashboard", response_model=List[StudentOut])
def get_dashboard_data(
    db: Session = Depends(get_db),
    faculty_id: int = Depends(get_current_faculty_id),
):
    """
    Returns every student enrolled in any course taught by this faculty,
    with live attendance % and performance score computed from the DB.
    """
    students = (
        db.query(Student)
        .join(enrollment_table, Student.id == enrollment_table.c.student_id)
        .join(Course, Course.id == enrollment_table.c.course_id)
        .filter(Course.faculty_id == faculty_id)
        .distinct()
        .all()
    )
    return [_build_student_out(s, db) for s in students]


# ── Single student ────────────────────────────────────────────────────
@app.get("/api/v1/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_faculty),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return _build_student_out(student, db)


# ── Students enrolled in a specific course ───────────────────────────
@app.get("/api/v1/courses/{course_id}/students")
def get_enrolled_students(
    course_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_faculty),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return [
        {"id": s.id, "name": s.name, "enrollment_number": s.enrollment_number}
        for s in course.students
    ]


# ── Timetable: built dynamically from DB ─────────────────────────────
@app.get("/api/v1/faculty/me/timetable")
def get_timetable(
    db: Session = Depends(get_db),
    faculty_id: int = Depends(get_current_faculty_id),
):
    """
    Queries TimetableSession → Course → Room and returns the nested
    {day: {slot: {course, room}}} structure the Streamlit UI expects.
    """
    sessions = (
        db.query(TimetableSession)
        .join(Course, Course.id == TimetableSession.course_id)
        .filter(Course.faculty_id == faculty_id)
        .all()
    )

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    slots = [
        "09:00-10:00", "10:00-11:00", "11:00-12:00",
        "12:00-13:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
    ]
    timetable: Dict[str, Dict[str, Optional[dict]]] = {
        day: {slot: None for slot in slots} for day in days
    }
    for s in sessions:
        if s.day_of_week in timetable and s.time_slot in timetable[s.day_of_week]:
            timetable[s.day_of_week][s.time_slot] = {
                "course": s.course.name,
                "room":   s.room.name,
            }
    return timetable


# ── Bulk marks submission with audit trail ────────────────────────────
@app.post("/api/v1/assessments/marks/bulk")
def submit_marks(
    payload: BulkMarksEntry,
    db: Session = Depends(get_db),
    faculty_id: int = Depends(get_current_faculty_id),
):
    """
    Upserts marks and writes a GradeAuditLog row for every score that
    is new or changed. Unchanged scores are silently skipped.
    """
    # Validate all student IDs exist in one query
    ids = [e.student_id for e in payload.marks]
    found_ids = {s.id for s in db.query(Student.id).filter(Student.id.in_(ids)).all()}
    unknown = [i for i in ids if i not in found_ids]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown student IDs: {unknown}")

    audit_count = 0
    for entry in payload.marks:
        existing = (
            db.query(Mark)
            .filter(
                Mark.student_id      == entry.student_id,
                Mark.assessment_type == payload.assessment_type,
            )
            .first()
        )

<<<<<<< HEAD
        old_score: Optional[float] = None

        if existing:
            if existing.score == entry.score:
                continue  # nothing changed — skip audit
            old_score       = existing.score
            existing.score  = entry.score
            mark_id         = existing.id
=======
with tab2:
    st.header("📝 Quick Attendance Logger")
    st.write("Log your study sessions or team attendance here.")
    
    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("Student ID (e.g., ECE-001)")
    with col2:
        status = st.selectbox("Status", ["Present", "Late"])
        
    if st.button("Submit Attendance"):
        if student_id:
            conn = get_db_connection()
            conn.execute("INSERT INTO student_logs (student_id, status) VALUES (?, ?)", (student_id, status))
            conn.commit()
            conn.close()
            st.success(f"Successfully logged attendance for {student_id}!")
>>>>>>> 01aa913d88921740c9e4c6737bcba4f8bb8766f2
        else:
            new_mark = Mark(
                student_id=entry.student_id,
                assessment_type=payload.assessment_type,
                score=entry.score,
            )
            db.add(new_mark)
            db.flush()          # get new_mark.id before commit
            mark_id = new_mark.id

<<<<<<< HEAD
        db.add(GradeAuditLog(
            mark_id=mark_id,
            faculty_id=faculty_id,
            old_score=old_score,
            new_score=entry.score,
        ))
        audit_count += 1

    db.commit()
    return {
        "message":     "Marks updated and audit logs recorded successfully.",
        "course_id":   payload.course_id,
        "audit_rows":  audit_count,
    }


# ── Audit log for a specific mark ─────────────────────────────────────
@app.get("/api/v1/marks/{mark_id}/audit", response_model=List[AuditLogOut])
def get_audit_log(
    mark_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_faculty),
):
    """Returns the full change history for a single mark record."""
    logs = (
        db.query(GradeAuditLog)
        .filter(GradeAuditLog.mark_id == mark_id)
        .order_by(GradeAuditLog.timestamp)
        .all()
    )
    if not logs:
        raise HTTPException(status_code=404, detail=f"No audit logs for mark {mark_id}")
    return logs


# ══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
=======
    st.divider()
    st.subheader("Recent Logs")
    # Show the last 5 entries in the database
    conn = get_db_connection()
    logs = conn.execute("SELECT student_id, status, timestamp FROM student_logs ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    
    if logs:
        st.table([dict(row) for row in logs])
    else:
        st.write("No logs found yet.")
>>>>>>> 01aa913d88921740c9e4c6737bcba4f8bb8766f2
