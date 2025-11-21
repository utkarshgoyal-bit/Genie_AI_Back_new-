from fastapi import UploadFile, HTTPException, Depends, Request, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from app.services.analyze_service_FINAL import analyze_images
from ..models.detection_model import PlantDetection
from app.controllers.otp_controller import decode_access_token
from app.controllers.product_controller_FINAL import find_product_by_diagnosis
from app.services.analyze_service_FINAL import analyze_images, analyze_images_direct
from app.config.db import SessionLocal
from app.utils.s3_uploader import upload_to_s3
from app.config.db import get_db
from uuid import uuid4
import time
import asyncio
import os
import json

def save_to_database_background(db: Session, detection_data: dict):
    """Background task to save detection to database.

    NOTE: The incoming `db` from the request is request-scoped and will be
    closed before background tasks run. Create a fresh session here instead
    to avoid using a closed session.
    """
    session = None
    try:
        session = SessionLocal()
        detection = PlantDetection(**detection_data)
        session.add(detection)
        session.commit()
        print("✅ Detection saved to database (background)")
    except Exception as e:
        print(f"❌ Background DB save failed: {e}")
        if session:
            session.rollback()
    finally:
        if session:
            session.close()

async def handle_analyze(
    images: List[UploadFile],
    request: Request,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    FINAL VERSION: Multi-image analysis with product matching
    - All images analyzed by AI
    - All images uploaded to S3
    - Fuzzy matching to find product recommendation
    """
    start_time = time.time()

    # Step 1: Extract JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    print(f"\n{'='*60}")
    print(f"🚀 ANALYZE REQUEST - User: {mobile}")
    print(f"{'='*60}")
    print(f"📸 Received {len(images)} image(s)")

    # Step 2: Read all images
    image_bytes_list = []
    for idx, img in enumerate(images):
        content = await img.read()
        image_bytes_list.append(content)
        print(f"  ✓ Image {idx+1}: {len(content)} bytes")

    # Step 3: AI Analysis (all images)
    print(f"\n🤖 Starting AI analysis...")
    try:
        diagnosis = await analyze_images(image_bytes_list)

        if not diagnosis.get("success"):
            raise HTTPException(status_code=400, detail=diagnosis.get("error", "Analysis failed"))

        print(f"✅ Diagnosis complete:")
        print(f"  Plant: {diagnosis.get('plant_common_name')} ({diagnosis.get('plant_scientific_name')})")
        print(f"  Issue: {diagnosis.get('disease')}")
        print(f"  Type: {diagnosis.get('diagnosis_type')}")

    except Exception as e:
        print(f"❌ AI Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Step 4: Upload ALL images to S3 in parallel
    print(f"\n☁️  Uploading {len(image_bytes_list)} images to S3...")
    detection_id = str(uuid4())

    upload_tasks = []
    s3_urls = []

    for idx, img_bytes in enumerate(image_bytes_list):
        filename = f"{detection_id}_image_{idx+1}.jpg"
        task = upload_to_s3(img_bytes, filename, "image/jpeg")
        upload_tasks.append(task)

    try:
        s3_urls = await asyncio.gather(*upload_tasks)
        print(f"✅ All images uploaded to S3:")
        for idx, url in enumerate(s3_urls):
            print(f"  ✓ Image {idx+1}: {url}")
    except Exception as e:
        print(f"⚠️  S3 upload failed: {e}")
        s3_urls = []

    # Step 5: Fuzzy match product recommendation
    print(f"\n🔍 Searching for product recommendation...")
    try:
        matched_product = find_product_by_diagnosis(
            plant_scientific_name=diagnosis.get('plant_scientific_name'),
            plant_common_name=diagnosis.get('plant_common_name'),
            disease_name=diagnosis.get('disease'),
            db=db
        )

        if matched_product:
            print(f"✅ Product matched: {matched_product.get('product_name')}")
            print(f"  Similarity: {matched_product.get('match_confidence'):.1%}")
        else:
            print(f"⚠️  No product match found (threshold not met)")

    except Exception as e:
        print(f"⚠️  Product matching failed: {e}")
        matched_product = None

    # Step 6: Prepare database record
    detection_data = {
        "id": detection_id,
        "mobile": mobile,
        "common_name": diagnosis.get("plant_common_name"),
        "scientific_name": diagnosis.get("plant_scientific_name"),
        "plant_confidence": diagnosis.get("plant_confidence"),
        "disease": diagnosis.get("disease"),
        "disease_scientific_name": diagnosis.get("disease_scientific_name"),
        "disease_confidence": diagnosis.get("disease_confidence"),
        "diagnosis_type": diagnosis.get("diagnosis_type"),
        "symptoms": json.dumps(diagnosis.get("symptoms", [])),
        "cause": diagnosis.get("cause"),
        "treatment": json.dumps(diagnosis.get("treatment", [])),
        "prevention": json.dumps(diagnosis.get("prevention", [])),
        "image_urls": json.dumps(s3_urls),  # Store all image URLs
        "images_analyzed": len(image_bytes_list)
    }

    # Step 7: Save to database (background)
    if background_tasks:
        background_tasks.add_task(save_to_database_background, db, detection_data)
        print(f"📝 Database save scheduled (background)")

    # Step 8: Build response
    total_time = round(time.time() - start_time, 2)

    response = {
        "detection_id": detection_id,
        "plant": {
            "common_name": diagnosis.get("plant_common_name"),
            "scientific_name": diagnosis.get("plant_scientific_name"),
            "confidence": diagnosis.get("plant_confidence")
        },
        "diagnosis": {
            "disease": diagnosis.get("disease"),
            "disease_scientific_name": diagnosis.get("disease_scientific_name"),
            "confidence": diagnosis.get("disease_confidence"),
            "type": diagnosis.get("diagnosis_type"),
            "symptoms": diagnosis.get("symptoms", []),
            "cause": diagnosis.get("cause"),
            "treatment": diagnosis.get("treatment", []),
            "prevention": diagnosis.get("prevention", [])
        },
        "images": {
            "uploaded": len(s3_urls),
            "urls": s3_urls
        },
        "recommended_product": matched_product,  # Append product recommendation
        "timing": {
            "yolo_time": diagnosis.get("yolo_time"),
            "openai_time": diagnosis.get("openai_time"),
            "total_time": total_time
        }
    }

    print(f"\n✅ REQUEST COMPLETE - Total time: {total_time}s")
    print(f"{'='*60}\n")

    return response
async def handle_analyze_direct(
    images: List[UploadFile],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    DIRECT VERSION: No JWT authentication, no YOLO detection.
    - OpenAI identifies plant + diagnoses disease
    - All images uploaded to S3
    - Database save (with mobile="guest")
    - Product matching included
    """
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"🚀 ANALYZE DIRECT REQUEST (No Auth)")
    print(f"{'='*60}")
    print(f"📸 Received {len(images)} image(s)")

    # Step 1: Read all images
    image_bytes_list = []
    for idx, img in enumerate(images):
        content = await img.read()
        image_bytes_list.append(content)
        print(f"  ✓ Image {idx+1}: {len(content)} bytes")

    # Step 2: AI Analysis (direct - no YOLO)
    print(f"\n🤖 Starting direct AI analysis...")
    try:
        diagnosis = await analyze_images_direct(image_bytes_list)

        if not diagnosis.get("success"):
            raise HTTPException(status_code=400, detail=diagnosis.get("error", "Analysis failed"))

        print(f"✅ Diagnosis complete:")
        print(f"  Plant: {diagnosis.get('plant_common_name')} ({diagnosis.get('plant_scientific_name')})")
        print(f"  Issue: {diagnosis.get('disease')}")
        print(f"  Type: {diagnosis.get('diagnosis_type')}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ AI Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Step 3: Upload ALL images to S3 in parallel
    print(f"\n☁️  Uploading {len(image_bytes_list)} images to S3...")
    detection_id = str(uuid4())

    upload_tasks = []
    s3_urls = []

    for idx, img_bytes in enumerate(image_bytes_list):
        filename = f"direct/{detection_id}_image_{idx+1}.jpg"
        task = upload_to_s3(img_bytes, filename, "image/jpeg")
        upload_tasks.append(task)

    try:
        s3_urls = await asyncio.gather(*upload_tasks)
        print(f"✅ All images uploaded to S3:")
        for idx, url in enumerate(s3_urls):
            print(f"  ✓ Image {idx+1}: {url}")
    except Exception as e:
        print(f"⚠️  S3 upload failed: {e}")
        s3_urls = []

    # Step 4: Fuzzy match product recommendation
    print(f"\n🔍 Searching for product recommendation...")
    try:
        matched_product = find_product_by_diagnosis(
            plant_scientific_name=diagnosis.get('plant_scientific_name'),
            plant_common_name=diagnosis.get('plant_common_name'),
            disease_name=diagnosis.get('disease'),
            db=db
        )

        if matched_product:
            print(f"✅ Product matched: {matched_product.get('product_name')}")
            print(f"  Similarity: {matched_product.get('match_confidence'):.1%}")
        else:
            print(f"⚠️  No product match found (threshold not met)")

    except Exception as e:
        print(f"⚠️  Product matching failed: {e}")
        matched_product = None

    # Step 5: Prepare database record (mobile="guest" for unauthenticated)
    detection_data = {
        "id": detection_id,
        "mobile": "guest",
        "common_name": diagnosis.get("plant_common_name"),
        "scientific_name": diagnosis.get("plant_scientific_name"),
        "plant_confidence": diagnosis.get("plant_confidence"),
        "disease": diagnosis.get("disease"),
        "disease_scientific_name": diagnosis.get("disease_scientific_name"),
        "disease_confidence": diagnosis.get("disease_confidence"),
        "diagnosis_type": diagnosis.get("diagnosis_type"),
        "symptoms": json.dumps(diagnosis.get("symptoms", [])),
        "cause": diagnosis.get("cause"),
        "treatment": json.dumps(diagnosis.get("treatment", [])),
        "prevention": json.dumps(diagnosis.get("prevention", [])),
        "image_urls": json.dumps(s3_urls),
        "images_analyzed": len(image_bytes_list)
    }

    # Step 6: Save to database (background)
    if background_tasks:
        background_tasks.add_task(save_to_database_background, db, detection_data)
        print(f"📝 Database save scheduled (background)")

    # Step 7: Build response
    total_time = round(time.time() - start_time, 2)

    response = {
        "detection_id": detection_id,
        "mode": "direct",
        "plant": {
            "common_name": diagnosis.get("plant_common_name"),
            "scientific_name": diagnosis.get("plant_scientific_name"),
            "confidence": diagnosis.get("plant_confidence")
        },
        "diagnosis": {
            "disease": diagnosis.get("disease"),
            "disease_scientific_name": diagnosis.get("disease_scientific_name"),
            "confidence": diagnosis.get("disease_confidence"),
            "type": diagnosis.get("diagnosis_type"),
            "symptoms": diagnosis.get("symptoms", []),
            "cause": diagnosis.get("cause"),
            "treatment": diagnosis.get("treatment", []),
            "prevention": diagnosis.get("prevention", [])
        },
        "images": {
            "uploaded": len(s3_urls),
            "urls": s3_urls
        },
        "recommended_product": matched_product,
        "timing": {
            "yolo_time": 0,
            "openai_time": diagnosis.get("openai_time"),
            "total_time": total_time
        }
    }

    print(f"\n✅ REQUEST COMPLETE - Total time: {total_time}s")
    print(f"{'='*60}\n")

    return response