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
    - S3 upload runs in background (ALL images uploaded)
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

    # 4. Prepare S3 filenames for ALL images
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    region = os.getenv("AWS_REGION")
    
    s3_filenames = []
    for filename in filenames:
        s3_filename = f"plant_detections/{uuid4()}_{filename}"
        s3_filenames.append(s3_filename)
    
    # Get selected image URL for database
    selected_idx = result.get('_metadata', {}).get('selected_image_index', 0)
    selected_s3_filename = s3_filenames[selected_idx]
    image_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{selected_s3_filename}"
    
    # 5. Upload ALL images to S3 in background (non-blocking)
    async def upload_all_in_background():
        upload_tasks = []
        for i, (img_bytes, s3_filename, content_type) in enumerate(
            zip(image_bytes_list, s3_filenames, content_types)
        ):
            upload_tasks.append(upload_to_s3(img_bytes, s3_filename, content_type))
        
        try:
            await asyncio.gather(*upload_tasks)
            print(f"✅ All {len(upload_tasks)} images uploaded to S3")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
    
    # Fire and forget
    asyncio.create_task(upload_all_in_background())
    
    # 6. Database save in background
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
        'note': f'All {len(images)} images uploaded to S3 in background, DB save in background'
    }
    
    return {"message": "Detection saved", "data": {**result, "image": image_url}}