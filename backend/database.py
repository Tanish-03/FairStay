import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

url = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password="Tanish@123",      # raw password ok here
    host="localhost",
    port=5432,
    database="FairStayServer",    
)

engine = create_engine(url, pool_pre_ping=True,future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()