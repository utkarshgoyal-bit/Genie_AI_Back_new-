import os
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException

load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL")

# Connection pool settings to prevent SSL timeout errors
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Test connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_size=5,             # Keep 5 connections in pool
    max_overflow=10,         # Allow 10 extra connections if needed
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
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# S3 UPLOADER
# ============================================================================
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)


async def upload_to_s3(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Upload file bytes to S3 and return public URL"""
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
        )
        return f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{filename}"
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
