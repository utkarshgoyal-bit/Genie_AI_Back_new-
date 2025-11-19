from fastapi import UploadFile, HTTPException, Depends, Request, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from app.services.analyze_service import analyze_images
from ..models.detection_model import PlantDetection
from app.controllers.otp_controller import decode_access_token
from app.utils.s3_uploader import upload_to_s3
from app.config.db import get_db
from uuid import uuid4
import time
import asyncio
import os


def save_to_database_background(db: Session, detection_data: dict):
    """Background task to save detection to database"""
    try:
        detection = PlantDetection(**detection_data)
        db.add(detection)
        db.commit()
        print("✅ Detection saved to database (background)")
    except Exception as e:
        print(f"❌ Background DB save failed: {e}")
        db.rollback()


async def handle_analyze(
    images: List[UploadFile], 
    request: Request, 
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    OPTIMIZED: Parallel processing for faster response
    - AI analysis runs first (priority)
    - S3 upload runs in background
    - Database save runs in background
    """
    
    start_time = time.time()
    
    # 1. Authentication
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    
    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(401, "Invalid token payload")

    if not 1 <= len(images) <= 2:
        raise HTTPException(400, "Upload 1-2 images")

    auth_time = time.time() - start_time

    # 2. Read images into memory
    read_start = time.time()
    image_bytes_list = []
    filenames = []
    content_types = []
    
    for img in images:
        if img.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(400, f"Invalid type: {img.content_type}")
        
        data = await img.read()
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 10MB)")
        
        image_bytes_list.append(data)
        filenames.append(img.filename)
        content_types.append(img.content_type)
    
    read_time = time.time() - read_start

    # 3. Run AI analysis (PRIORITY - don't wait for S3)
    analysis_start = time.time()
    result = await analyze_images(image_bytes_list)
    
    if "error" in result:
        raise HTTPException(500, result["error"])
    
    analysis_time = time.time() - analysis_start

    # 4. S3 upload in background (non-blocking)
    selected_idx = result.get('_metadata', {}).get('selected_image_index', 0)
    selected_image_bytes = image_bytes_list[selected_idx]
    selected_filename = filenames[selected_idx]
    selected_content_type = content_types[selected_idx]
    
    filename = f"plant_detections/{uuid4()}_{selected_filename}"
    
    # Placeholder URL (S3 upload happens in background)
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    region = os.getenv("AWS_REGION")
    image_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"
    
    # Start S3 upload asynchronously (don't wait)
    async def upload_in_background():
        try:
            await upload_to_s3(selected_image_bytes, filename, selected_content_type)
            print(f"✅ S3 upload completed: {filename}")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
    
    # Fire and forget
    asyncio.create_task(upload_in_background())
    
    # 5. Database save in background
    detection_data = {
        "mobile": mobile,
        "common_name": result.get("common_name"),
        "scientific_name": result.get("scientific_name"),
        "plant_confidence": result.get("plant_confidence"),
        "disease": result.get("disease"),
        "disease_scientific_name": result.get("disease_scientific_name"),
        "disease_confidence": result.get("disease_confidence"),
        "symptoms": result.get("symptoms"),
        "cause": result.get("cause"),
        "treatment": result.get("treatment"),
        "image": image_url
    }
    
    if background_tasks:
        background_tasks.add_task(save_to_database_background, db, detection_data)
    else:
        # Fallback: save synchronously
        save_to_database_background(db, detection_data)
    
    total_time = time.time() - start_time
    
    # Add timing to response
    result['_timing'] = {
        'total_seconds': round(total_time, 2),
        'auth': round(auth_time, 2),
        'image_read': round(read_time, 2),
        'ai_analysis': round(analysis_time, 2),
        'note': 'S3 upload and DB save run in background'
    }
    
    return {"message": "Detection saved", "data": {**result, "image": image_url}}