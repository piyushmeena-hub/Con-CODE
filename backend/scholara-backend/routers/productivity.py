from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/v1/productivity", tags=["Productivity"])

# --- TASKS ---
@router.post("/tasks")
def add_task(task: schemas.TaskSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    new_task = models.Task(id=task.id, user_id=user.id, text=task.text, completed=task.completed)
    db.add(new_task)
    db.commit()
    return {"status": "success"}

@router.put("/tasks/{task_id}")
def toggle_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.completed = not task.completed
        db.commit()
    return {"status": "success"}

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db.query(models.Task).filter(models.Task.id == task_id).delete()
    db.commit()
    return {"status": "success"}

# --- STUDY SESSIONS ---
@router.post("/session")
def save_session(session: schemas.SessionSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    new_session = models.StudySession(
        user_id=user.id,
        date=session.date,
        subject=session.subject,
        start_time=session.start_time,
        end_time=session.end_time,
        duration=session.duration
    )
    db.add(new_session)
    db.commit()
    return {"status": "success"}