from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Connection pool settings for stable PostgreSQL connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Test connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_size=5,             # Keep 5 connections in pool
    max_overflow=10,         # Allow 10 extra connections if needed
    echo=False,              # Don't log SQL queries
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()