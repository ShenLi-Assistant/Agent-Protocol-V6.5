import os
import subprocess
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime

# --- DATABASE SETUP ---
DB_URL = "sqlite:///./production.db"
Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    budget = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- APP SETUP ---
app = FastAPI(title="Agent Protocol Production")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

# Mount static for images
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- ROUTES ---
@app.get("/")
async def home(): return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/app")
async def dashboard(): return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/docs-ui")
async def docs(): return FileResponse(os.path.join(FRONTEND_DIR, "docs.html"))

@app.get("/whitepaper")
async def wp(): return FileResponse(os.path.join(FRONTEND_DIR, "whitepaper.html"))

@app.get("/roadmap")
async def roadmap(): return FileResponse(os.path.join(FRONTEND_DIR, "roadmap.html"))

@app.post("/jobs/post")
async def post_job(data: dict, db: Session = Depends(get_db)):
    new_job = Job(title=data.get('title'), budget=float(data.get('budget', 0)))
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return {"status": "posted", "job_id": new_job.id}

@app.get("/api/jobs")
async def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.id.desc()).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
