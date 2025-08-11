# schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ComplaintCreate(BaseModel):
    user_id: Optional[str] = None
    complaint_text: str
    category: Optional[str] = None
    severity_score: Optional[int] = None

class ComplaintUpdate(BaseModel):
    user_id: Optional[str] = None
    complaint_text: Optional[str] = None
    category: Optional[str] = None
    severity_score: Optional[int] = None
    generated_summary: Optional[str] = None

class ComplaintOut(BaseModel):
    id: int
    user_id: Optional[str] = None
    complaint_text: str
    category: Optional[str] = None
    severity_score: Optional[int] = None
    generated_summary: Optional[str] = None
    submitted_at: datetime

    # Pydantic v2 equivalent of orm_mode=True
    model_config = ConfigDict(from_attributes=True)
