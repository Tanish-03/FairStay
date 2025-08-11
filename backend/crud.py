from sqlalchemy.orm import Session 
from . import models, schemas

def create_complaint(db: Session, complaint_in: schemas.ComplaintCreate, ai_payload: dict):
    obj = models.Complaint(
        user_id=complaint_in.user_id,
        complaint_text=complaint_in.complaint_text,
        category=ai_payload.get("category"),
        severity_score=ai_payload.get("severity"),
        generated_summary=ai_payload.get("summary"),        
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_complaint(db: Session,complaint_id:int):
    return db.get(models.Complaint,complaint_id)    

def list_recent(db: Session, limit: int = 20):
    return (
        db.query(models.Complaint)
        .order_by(models.Complaint.id.desc())
        .limit(limit)
        .all()
    )
