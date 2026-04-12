#!/usr/bin/env python3
"""
Register a reference face image for the primary user (used by /api/v1/attendance/verify_face).

Usage (from backend/scholara-backend):
  python enroll_face.py /absolute/path/to/your_photo.jpg

This copies the image into uploads/reference_faces/ and sets users.reference_face_url.
Verification compares new photos to this reference via CLIP embeddings + cosine similarity
(same pipeline as verify_face) — different people score lower than the threshold.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import uuid

# Ensure imports work when run as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models


UPLOAD_DIR = os.path.join("uploads", "reference_faces")


def enroll_from_path(image_path: str, db: Session) -> str:
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    user = db.query(models.User).first()
    if not user:
        user = models.User(email="student@scholara.edu")
        db.add(user)
        db.flush()

    if user.reference_face_url and os.path.exists(user.reference_face_url):
        try:
            os.remove(user.reference_face_url)
        except OSError:
            pass

    ext = os.path.splitext(image_path)[1] or ".jpg"
    safe_name = f"user_{user.id}_face_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)
    shutil.copy2(image_path, dest)

    user.reference_face_url = dest
    db.commit()
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Enroll reference face from an image file.")
    parser.add_argument(
        "image",
        nargs="?",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "student.jpeg",
        ),
        help="Path to reference photo (default: repo root student.jpeg)",
    )
    args = parser.parse_args()

    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        path = enroll_from_path(os.path.abspath(args.image), db)
        print(f"Enrolled reference face: {path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
