from fastapi import APIRouter, UploadFile, File, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.utils import get_db, upload_to_s3
from app.models import PlantDetection
from app.services.analyze_service import analyze_images_with_yolo, analyze_images_direct
from app.services.image_utils import optimize_image, detect_image_type, select_best_image
from app.domains.products import find_product_by_diagnosis
import asyncio
import time
from uuid import uuid4

# ============================================================================
# ROUTER DEFINITION
# ============================================================================
router = APIRouter(prefix="/analyze", tags=["Analyze"])


# ============================================================================
# BACKGROUND TASK HELPER
# ============================================================================
def save_to_database_background(db: Session, detection_data: dict):
    """Background task to save detection results to database"""
    try:
        detection = PlantDetection(**detection_data)
        db.add(detection)
        db.commit()
        print(f"✅ Detection {detection_data['id']} saved to database")
    except Exception as e:
        db.rollback()
        print(f"❌ Database save failed: {e}")


# ============================================================================
# CONTROLLER LOGIC: AUTHENTICATED ANALYSIS
# ============================================================================
async def handle_analyze(
    images: list[UploadFile],
    request: Request,
    db: Session,
    background_tasks: BackgroundTasks
):
    """
    Handle authenticated plant analysis with YOLO detection
    Requires Authorization header with JWT token
    """
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🔬 NEW ANALYSIS REQUEST (Authenticated)")
    print(f"{'='*60}")
    
    # Extract and validate JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    
    # Import here to avoid circular dependency
    from app.domains.auth import decode_access_token
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    print(f"👤 User: {mobile}")
    print(f"📸 Images received: {len(images)}")
    
    # Step 1: Read and validate images
    image_bytes_list = []
    for idx, img in enumerate(images):
        content = await img.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"Image {idx+1} is empty")
        image_bytes_list.append(content)
        print(f" ✓ Image {idx+1}: {len(content)} bytes")
    
    # Step 2: Select best image and analyze with YOLO + OpenAI
    print(f"\n🤖 Running AI analysis (YOLO + OpenAI)...")
    best_image, image_type, selected_idx = select_best_image(image_bytes_list)
    print(f" → Selected image {selected_idx+1} (type: {image_type})")
    
    diagnosis = await analyze_images_with_yolo([best_image])
    
    if not diagnosis.get("success"):
        raise HTTPException(status_code=500, detail=diagnosis.get("error", "Analysis failed"))
    
    print(f"✅ Analysis complete:")
    print(f" Plant: {diagnosis.get('plant_common_name')} ({diagnosis.get('plant_scientific_name')})")
    print(f" Disease: {diagnosis.get('disease')}")
    
    # Step 3: Upload ALL images to S3 in parallel
    print(f"\n☁️ Uploading {len(image_bytes_list)} images to S3...")
    detection_id = str(uuid4())
    upload_tasks = []
    
    for idx, img_bytes in enumerate(image_bytes_list):
        filename = f"authenticated/{detection_id}_image_{idx+1}.jpg"
        task = upload_to_s3(img_bytes, filename, "image/jpeg")
        upload_tasks.append(task)
    
    try:
        s3_urls = await asyncio.gather(*upload_tasks)
        print(f"✅ All images uploaded to S3:")
        for idx, url in enumerate(s3_urls):
            print(f" ✓ Image {idx+1}: {url}")
    except Exception as e:
        print(f"⚠️ S3 upload failed: {e}")
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
            print(f" Similarity: {matched_product.get('match_confidence'):.1%}")
        else:
            print(f"⚠️ No product match found (threshold not met)")
    except Exception as e:
        print(f"⚠️ Product matching failed: {e}")
        matched_product = None
    
    # Step 5: Prepare database record
    detection_data = {
        "id": detection_id,
        "mobile": mobile,
        "common_name": diagnosis.get("plant_common_name"),
        "scientific_name": diagnosis.get("plant_scientific_name"),
        "plant_confidence": diagnosis.get("plant_confidence"),
        "disease": diagnosis.get("disease"),
        "disease_scientific_name": diagnosis.get("disease_scientific_name"),
        "disease_confidence": diagnosis.get("disease_confidence"),
        "symptoms": diagnosis.get("symptoms", []),
        "cause": diagnosis.get("cause"),
        "treatment": diagnosis.get("treatment", []),
        "prevention": diagnosis.get("prevention", []),
        "image_urls": s3_urls,
        "images_analyzed": len(image_bytes_list)
    }
    
    # Step 6: Save to database (background)
    background_tasks.add_task(save_to_database_background, db, detection_data)
    print(f"📝 Database save scheduled (background)")
    
    # Step 7: Build response
    total_time = round(time.time() - start_time, 2)
    response = {
        "detection_id": detection_id,
        "mode": "authenticated",
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
            "yolo_time": diagnosis.get("yolo_time"),
            "openai_time": diagnosis.get("openai_time"),
            "total_time": total_time
        }
    }
    
    print(f"\n✅ REQUEST COMPLETE - Total time: {total_time}s")
    print(f"{'='*60}\n")
    return response


# ============================================================================
# CONTROLLER LOGIC: DIRECT ANALYSIS (UNAUTHENTICATED)
# ============================================================================
async def handle_analyze_direct(
    images: list[UploadFile],
    db: Session,
    background_tasks: BackgroundTasks
):
    """
    Handle unauthenticated plant analysis (direct mode)
    Skips YOLO detection, OpenAI identifies plant + diagnoses
    """
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🔬 NEW ANALYSIS REQUEST (Direct Mode - No Auth)")
    print(f"{'='*60}")
    print(f"📸 Images received: {len(images)}")
    
    # Step 1: Read and validate images
    image_bytes_list = []
    for idx, img in enumerate(images):
        content = await img.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"Image {idx+1} is empty")
        image_bytes_list.append(content)
        print(f" ✓ Image {idx+1}: {len(content)} bytes")
    
    # Step 2: Analyze with OpenAI (direct mode - no YOLO)
    print(f"\n🤖 Running AI analysis (Direct Mode - OpenAI only)...")
    diagnosis = await analyze_images_direct(image_bytes_list)
    
    if not diagnosis.get("success"):
        raise HTTPException(status_code=500, detail=diagnosis.get("error", "Analysis failed"))
    
    print(f"✅ Analysis complete:")
    print(f" Plant: {diagnosis.get('plant_common_name')} ({diagnosis.get('plant_scientific_name')})")
    print(f" Disease: {diagnosis.get('disease')}")
    
    # Step 3: Upload ALL images to S3 in parallel
    print(f"\n☁️ Uploading {len(image_bytes_list)} images to S3...")
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
            print(f" ✓ Image {idx+1}: {url}")
    except Exception as e:
        print(f"⚠️ S3 upload failed: {e}")
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
            print(f" Similarity: {matched_product.get('match_confidence'):.1%}")
        else:
            print(f"⚠️ No product match found (threshold not met)")
    except Exception as e:
        print(f"⚠️ Product matching failed: {e}")
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
        "symptoms": diagnosis.get("symptoms", []),
        "cause": diagnosis.get("cause"),
        "treatment": diagnosis.get("treatment", []),
        "prevention": diagnosis.get("prevention", []),
        "image_urls": s3_urls,
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


# ============================================================================
# API ROUTES
# ============================================================================
@router.post("/")
async def analyze_plant(
    request: Request,
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Authenticated plant analysis endpoint"""
    return await handle_analyze(images, request, db, background_tasks)


@router.post("/direct")
async def analyze_plant_direct(
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Direct analysis endpoint - no authentication required.
    Skips YOLO detection, OpenAI identifies plant + diagnoses.
    """
    return await handle_analyze_direct(images, db, background_tasks)
