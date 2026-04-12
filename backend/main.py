"""
Faculty Dashboard API — Unified backend
Merges teammate's Faculty/Student/Timetable models with
audit trail, enrollment, and full CRUD endpoints.

Run:
    pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib[bcrypt]
    python main.py
    # Swagger UI → http://localhost:8000/docs
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey,
    Integer, String, JSON, Table, create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# ══════════════════════════════════════════════════════════════════════
# JWT CONFIG
# ══════════════════════════════════════════════════════════════════════

SECRET_KEY  = "scholara-secret-key-change-in-production"
ALGORITHM   = "HS256"
TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash(password: str) -> str:
    return pwd_context.hash(password)

def _verify(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _create_token(data: dict, expires_days: int = TOKEN_EXPIRE_DAYS) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=expires_days)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

SQLALCHEMY_DATABASE_URL = "sqlite:///./faculty_dashboard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ══════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════

# Many-to-many: students ↔ courses
enrollment_table = Table(
    "enrollments", Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id",  Integer, ForeignKey("courses.id"),  primary_key=True),
)


class Faculty(Base):
    __tablename__ = "faculty"
    id     = Column(Integer, primary_key=True)
    name   = Column(String,  nullable=False)
    dept   = Column(String,  nullable=False)
    fac_id = Column(String,  unique=True, nullable=False)
    email  = Column(String,  nullable=False)
    phone  = Column(String,  nullable=False)


class Student(Base):
    __tablename__ = "students"
    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String,  nullable=False, index=True)
    enrollment_number = Column(String, unique=True, nullable=False, index=True)
    total_classes    = Column(Integer, default=40)
    attended_classes = Column(Integer, default=0)

    courses = relationship("Course", secondary=enrollment_table, back_populates="students")
    marks   = relationship("Mark",   back_populates="student")


class Course(Base):
    __tablename__ = "courses"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String,  nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False, index=True)

    students = relationship("Student",          secondary=enrollment_table, back_populates="courses")
    sessions = relationship("TimetableSession", back_populates="course")
    faculty  = relationship("Faculty")


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
    day_of_week = Column(String,  nullable=False)
    time_slot   = Column(String,  nullable=False)

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
    """Immutable record of every score change."""
    __tablename__ = "grade_audit_logs"
    id         = Column(Integer,  primary_key=True, index=True)
    mark_id    = Column(Integer,  ForeignKey("marks.id"), nullable=False)
    faculty_id = Column(Integer,  nullable=False)
    old_score  = Column(Float,    nullable=True)
    new_score  = Column(Float,    nullable=False)
    timestamp  = Column(DateTime, default=datetime.utcnow, nullable=False)

    mark = relationship("Mark", back_populates="audit_logs")


class User(Base):
    """Auth accounts — linked to either a Faculty or Student record."""
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String,  unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role          = Column(String,  nullable=False)   # "teacher" | "student"


Base.metadata.create_all(bind=engine)

# ══════════════════════════════════════════════════════════════════════
# SEED DATA
# ══════════════════════════════════════════════════════════════════════

def _seed():
    db = SessionLocal()
    try:
        # If faculty table exists but is empty, or was never seeded, run seed
        if db.query(Faculty).first():
            return  # already seeded

        print("🌱 Seeding database...")

        # Faculty
        dr_smith = Faculty(
            name="Dr. Smith", dept="COMPUTER SCIENCE",
            fac_id="FAC-CS-2024", email="dr.smith@scholara.edu",
            phone="+91 98765 43210",
        )
        db.add(dr_smith)
        db.flush()

        # Rooms
        lab201  = Room(name="Lab 201",  capacity=40)
        room104 = Room(name="Room 104", capacity=60)
        db.add_all([lab201, room104])
        db.flush()

        # Courses
        ml = Course(name="Machine Learning", faculty_id=dr_smith.id)
        ds = Course(name="Data Structures",  faculty_id=dr_smith.id)
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
        seed_scores = {
            "2024CS101": [80, 85, 90, 82, 90.5],
            "2024CS102": [90, 95, 92, 89, 94],
            "2024CS103": [70, 68, 75, 72, 71],
            "2024CS104": [85, 90, 88, 91, 88],
            "2024CS105": [75, 80, 78, 82, 80],
            "2024CS106": [88, 92, 90, 94, 91],
        }
        assessment_labels = ["Quiz 1", "Quiz 2", "Midterm", "Assignment", "Quiz 3"]

        for sname, enroll, total, attended in seed_students:
            s = Student(name=sname, enrollment_number=enroll,
                        total_classes=total, attended_classes=attended)
            s.courses = [ml, ds]
            db.add(s)
            db.flush()
            for label, score in zip(assessment_labels, seed_scores[enroll]):
                mark = Mark(student_id=s.id, assessment_type=label, score=score)
                db.add(mark)
                db.flush()
                db.add(GradeAuditLog(
                    mark_id=mark.id, faculty_id=dr_smith.id,
                    old_score=None, new_score=score,
                ))

        # Timetable
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

        # Default teacher account
        db.add(User(
            username="drsmith",
            hashed_password=_hash("faculty123"),
            role="teacher",
        ))

        db.commit()
        print("✅ Database seeded successfully.")
        print("   Default login → username: drsmith  password: faculty123  role: teacher")
    except Exception as e:
        db.rollback()
        print(f"⚠️  Seed failed: {e}")
        raise
    finally:
        db.close()

_seed()

# ══════════════════════════════════════════════════════════════════════
# DEPENDENCIES
# ══════════════════════════════════════════════════════════════════════

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_faculty(db: Session = Depends(get_db)) -> Faculty:
    """
    Returns the first faculty record.
    If none exists (stale DB), drops all tables, recreates, and re-seeds.
    """
    fac = db.query(Faculty).first()
    if not fac:
        # Stale DB — nuke and rebuild
        print("⚠️  No faculty found — dropping stale DB and re-seeding...")
        db.close()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        _seed()
        new_db = SessionLocal()
        try:
            fac = new_db.query(Faculty).first()
        finally:
            new_db.close()
        if not fac:
            raise HTTPException(status_code=500, detail="Seed failed — check server logs")
    return fac

# ══════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════

VALID_ASSESSMENT_TYPES = {
    "Quiz", "Quiz 1", "Quiz 2", "Quiz 3",
    "Midterm", "End-term", "Assignment",
}


class StudentCreate(BaseModel):
    name: str
    total_classes: int = 40


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
            raise ValueError(f"Must be one of {VALID_ASSESSMENT_TYPES}")
        return v


class AuditLogOut(BaseModel):
    id:         int
    mark_id:    int
    faculty_id: int
    old_score:  Optional[float]
    new_score:  float
    timestamp:  datetime
    model_config = {"from_attributes": True}


# ── Auth schemas ──────────────────────────────────────────────────────
class AuthPayload(BaseModel):
    username: str
    password: str
    role: str   # "teacher" | "student"

# ══════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Faculty Dashboard API",
    version="2.0.0",
    description="Unified SQLAlchemy backend with audit trail.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _build_student_out(student: Student, db: Session) -> dict:
    scores = [
        m.score for m in
        db.query(Mark).filter(Mark.student_id == student.id).order_by(Mark.id).all()
    ]
    pct  = round(student.attended_classes / student.total_classes * 100, 1) \
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
    return {"status": "ok", "version": "2.0.0"}


# ══════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS  (consumed by login_page.py Flask app)
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/v1/auth/signup")
def signup(payload: AuthPayload, db: Session = Depends(get_db)):
    """Create a new user account."""
    if payload.role not in ("teacher", "student"):
        raise HTTPException(status_code=400, detail="role must be 'teacher' or 'student'")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    db.add(User(
        username=payload.username,
        hashed_password=_hash(payload.password),
        role=payload.role,
    ))
    db.commit()
    return {"message": f"Account created for '{payload.username}'"}


@app.post("/api/v1/auth/login")
def login(payload: AuthPayload, db: Session = Depends(get_db)):
    """Verify credentials and return a JWT access token."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not _verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.role != payload.role:
        raise HTTPException(status_code=403, detail=f"Account is not a {payload.role} account")
    token = _create_token({"sub": user.username, "role": user.role, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@app.get("/api/v1/auth/verify")
def verify_token(token: str, db: Session = Depends(get_db)):
    """Streamlit calls this to validate the cookie token on page load."""
    try:
        data = _decode_token(token)
        user = db.query(User).filter(User.username == data["sub"]).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"valid": True, "username": user.username, "role": user.role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Faculty profile ───────────────────────────────────────────────────
@app.get("/api/v1/faculty/me")
def get_faculty_profile(fac: Faculty = Depends(get_current_faculty)):
    return {
        "id":    fac.id,
        "name":  fac.name,
        "dept":  fac.dept,
        "fac_id": fac.fac_id,
        "email": fac.email,
        "phone": fac.phone,
    }


# ── Dashboard ─────────────────────────────────────────────────────────
@app.get("/api/v1/faculty/me/dashboard")
def get_dashboard(
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
    students = (
        db.query(Student)
        .join(enrollment_table, Student.id == enrollment_table.c.student_id)
        .join(Course, Course.id == enrollment_table.c.course_id)
        .filter(Course.faculty_id == fac.id)
        .distinct()
        .all()
    )
    return [_build_student_out(s, db) for s in students]


# ── Single student ────────────────────────────────────────────────────
@app.get("/api/v1/students/{student_id}")
def get_student(
    student_id: int,
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return _build_student_out(s, db)


# ── Register new student ──────────────────────────────────────────────
@app.post("/api/v1/students")
def add_student(
    payload: StudentCreate,
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
    # Auto-generate enrollment number
    count = db.query(Student).count()
    enroll = f"2024CS{count + 101:03d}"
    s = Student(
        name=payload.name,
        enrollment_number=enroll,
        total_classes=payload.total_classes,
        attended_classes=0,
    )
    # Enroll in all courses taught by this faculty
    courses = db.query(Course).filter(Course.faculty_id == fac.id).all()
    s.courses = courses
    db.add(s)
    db.commit()
    return {"message": f"Student '{payload.name}' registered successfully!", "enrollment_number": enroll}


# ── Students in a course ──────────────────────────────────────────────
@app.get("/api/v1/courses/{course_id}/students")
def get_enrolled_students(
    course_id: int,
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return [
        {"id": s.id, "name": s.name, "enrollment_number": s.enrollment_number}
        for s in course.students
    ]


# ── Timetable ─────────────────────────────────────────────────────────
@app.get("/api/v1/faculty/me/timetable")
def get_timetable(
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
    sessions = (
        db.query(TimetableSession)
        .join(Course, Course.id == TimetableSession.course_id)
        .filter(Course.faculty_id == fac.id)
        .all()
    )

    DAYS  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    SLOTS = [
        "09:00-10:00", "10:00-11:00", "11:00-12:00",
        "12:00-13:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
    ]
    timetable: Dict[str, Dict[str, Optional[dict]]] = {
        day: {slot: None for slot in SLOTS} for day in DAYS
    }
    for s in sessions:
        if s.day_of_week in timetable and s.time_slot in timetable[s.day_of_week]:
            timetable[s.day_of_week][s.time_slot] = {
                "course": s.course.name,
                "room":   s.room.name,
            }
    return timetable


# ── Bulk marks with audit trail ───────────────────────────────────────
@app.post("/api/v1/assessments/marks/bulk")
def submit_marks(
    payload: BulkMarksEntry,
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
    ids       = [e.student_id for e in payload.marks]
    found_ids = {s.id for s in db.query(Student.id).filter(Student.id.in_(ids)).all()}
    unknown   = [i for i in ids if i not in found_ids]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown student IDs: {unknown}")

    audit_count = 0
    for entry in payload.marks:
        existing = (
            db.query(Mark)
            .filter(Mark.student_id == entry.student_id,
                    Mark.assessment_type == payload.assessment_type)
            .first()
        )
        old_score: Optional[float] = None

        if existing:
            if existing.score == entry.score:
                continue  # unchanged — skip
            old_score      = existing.score
            existing.score = entry.score
            mark_id        = existing.id
        else:
            new_mark = Mark(
                student_id=entry.student_id,
                assessment_type=payload.assessment_type,
                score=entry.score,
            )
            db.add(new_mark)
            db.flush()
            mark_id = new_mark.id

        db.add(GradeAuditLog(
            mark_id=mark_id, faculty_id=fac.id,
            old_score=old_score, new_score=entry.score,
        ))
        audit_count += 1

    db.commit()
    return {
        "message":    "Marks updated and audit logs recorded successfully.",
        "course_id":  payload.course_id,
        "audit_rows": audit_count,
    }


# ── Audit log for a mark ──────────────────────────────────────────────
@app.get("/api/v1/marks/{mark_id}/audit", response_model=List[AuditLogOut])
def get_audit_log(
    mark_id: int,
    db:  Session = Depends(get_db),
    fac: Faculty = Depends(get_current_faculty),
):
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
