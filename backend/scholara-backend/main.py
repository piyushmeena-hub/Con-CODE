from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine
import models
<<<<<<< HEAD
from routers import attendance, productivity, profile
=======
from routers import attendance, productivity, auth
>>>>>>> 36ed83e833aa2a501a5fa6f307d02166683aba0d

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
<<<<<<< HEAD
app.include_router(profile.router)
=======
app.include_router(auth.router)
>>>>>>> 36ed83e833aa2a501a5fa6f307d02166683aba0d

@app.get("/")
def health_check():
    return {"status": "Scholara API is running. Strict mode enabled."}