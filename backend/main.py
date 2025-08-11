# backend/main.py
from .database import engine, Base, SessionLocal
from . import models , schemas, crud  
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session     
Base.metadata.create_all(bind=engine)
from .ai_agent import classify_and_summarize

from fastapi import FastAPI

app = FastAPI(title="FairSaty API",version="0.1")

@app.get("/health")
def health():
    return {"status":"ok"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/complaints/{complaint_id}",response_model=schemas.ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    obj = crud.get_complaint(db, complaint_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj 

@app.get("/complaints", response_model=list[schemas.ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    return db.query(models.Complaint).all()

def submit_complaint(payload: schemas.ComplaintCreate, db: Session = Depends(get_db)):
    if not payload.complaint_text or not payload.complaint_text.strip():
        raise HTTPException(status_code=400, detail="complaint_text is required")
    ai_result = classify_and_summarize(payload.complaint_text)
    return crud.create_complaint(db, payload, ai_result)

from typing import List

@app.get("/complaints", response_model=list[schemas.ComplaintOut])
def list_complaints(limit: int = 20, db: Session = Depends(get_db)):
    return crud.list_recent(db, limit=limit)
