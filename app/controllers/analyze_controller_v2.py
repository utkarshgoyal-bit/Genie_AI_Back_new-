from fastapi import UploadFile, HTTPException, Depends, Request, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from app.services.analyze_service_FINAL_v4 import analyze_images
from ..models.detection_model import PlantDetection
from app.controllers.otp_controller import decode_access_token
from app.utils.s3_uploader import upload_to_s3
from app.config.db import get_db
from uuid import uuid4
import time
import asyncio
import os
import json

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

# We will schedule S3 uploads using asyncio.create_task(upload_to_s3(...))
# upload_to_s3 is async so scheduling it directly from this async handler is fine.

async def handle_analyze(
    images: List[UploadFile],
    request: Request,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Handles plant image analysis:
    1. Reads multiple images.
    2. Sends the best image to the AI service for analysis.
    3. Uploads ALL images to S3 in the background.
    4. Saves the complete analysis and all image URLs to the database.
    """
    start_time = time.time()

    # 1. Authentication (expect header: "Authorization: Bearer <token>")
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # 2. Read images into memory and preserve filenames/content types
    if not images:
        raise HTTPException(status_code=400, detail="No images were uploaded")

    image_bytes_list = []
    filenames = []
    content_types = []
    for idx, img in enumerate(images):
        data = await img.read()
        image_bytes_list.append(data)
        filenames.append(img.filename or f"upload_{idx}.jpg")
        content_types.append(img.content_type or "image/jpeg")

    # 3. Perform AI analysis using the best image (logic is in analyze_images)
    analysis_start_time = time.time()
    result = await analyze_images(image_bytes_list)
    print(f"🧠 AI analysis took: {time.time() - analysis_start_time:.2f}s")

    # Get the index of the image that was used for the analysis
    selected_idx = result.get("_metadata", {}).get("selected_image_index", 0)

    # 4. Upload ALL images to S3 (schedule async tasks immediately)
    detection_id = uuid4()
    s3_urls = []
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    aws_region = os.getenv("AWS_REGION")

    if not bucket_name or not aws_region:
        raise HTTPException(status_code=500, detail="S3 bucket name or region not configured")

    for i, image_bytes in enumerate(image_bytes_list):
        filename = f"{mobile}/{detection_id}_{i}.jpg"
        # Schedule async upload (fire-and-forget)
        try:
            asyncio.create_task(upload_to_s3(image_bytes, filename, content_types[i]))
        except Exception:
            # If scheduling fails, swallow and continue; upload may still be attempted later
            pass
        # Construct the URL immediately and store it for DB/response
        url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{filename}"
        s3_urls.append(url)

    print(f"🚀 All {len(s3_urls)} images scheduled for upload.")

    # 5. Save analysis result and ALL image URLs to the database
    # Map fields to PlantDetection model columns
    detection_data = {
        "mobile": mobile,
        "common_name": result.get("common_name", "Unknown Plant"),
        "scientific_name": result.get("scientific_name", "Species unknown"),
        "plant_confidence": result.get("plant_confidence", "0"),
        "disease": result.get("disease", []),
        "disease_scientific_name": result.get("disease_scientific_name", []),
        "disease_confidence": result.get("disease_confidence", []),
        "symptoms": result.get("symptoms", []),
        "cause": result.get("cause", []),
        "treatment": result.get("treatment", []),
        # store all image urls as comma-separated string to match existing usage elsewhere
        "image": ",".join(s3_urls),
    }

    if background_tasks:
        background_tasks.add_task(save_to_database_background, db, detection_data)
    else:
        # If BackgroundTasks not provided, run save in a background thread
        try:
            asyncio.create_task(asyncio.to_thread(save_to_database_background, db, detection_data))
        except Exception:
            # Fallback: call synchronously
            save_to_database_background(db, detection_data)

    # 6. Return the analysis result immediately to the client
    return result

