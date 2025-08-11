from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func 
from .database import Base

class Complaint(Base):
    __tablename__="complaints"
    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(String,index=True,nullable=True)
    complaint_text= Column(Text,nullable=False)
    category= Column(String,nullable=True)
    severity_score=Column(Integer,nullable=True)
    generated_summary=Column(Text,nullable=True)
    submitted_at = Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)
    