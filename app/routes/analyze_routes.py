from fastapi import APIRouter, UploadFile, File, Depends, Request, BackgroundTasks
from typing import List
from app.controllers.analyze_controller import handle_analyze  # ← Changed this line
from app.config.db import get_db  
from sqlalchemy.orm import Session

router = APIRouter(prefix="/analyze", tags=["Analyze"])

@router.post("/")
async def analyze_plant(
    request: Request,
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db), 
):
    return await handle_analyze(images, request, db, background_tasks)


@router.post("/test-analyze")
async def test_analyze_no_auth(
    images: list[UploadFile] = File(...),
    version: str = "FINAL_V2"
):
    """
    TEST ENDPOINT - No authentication required
    
    Usage:
    1. Go to http://localhost:8000/docs
    2. Find POST /analyze/test-analyze
    3. Click "Try it out"
    4. Upload images
    5. Optional: Change version parameter (FINAL_V2, FINAL, v2, v4)
    6. Click "Execute"
    
    Returns: Complete analysis without auth, S3 upload, or DB save
    """
    print(f"\n{'='*60}")
    print(f"🧪 TEST MODE - Using analyze_service_{version}")
    print(f"{'='*60}")
    
    # Read images
    image_bytes_list = []
    for idx, img in enumerate(images):
        content = await img.read()
        image_bytes_list.append(content)
        print(f"📸 Image {idx+1}: {len(content)} bytes ({img.filename})")
    
    # Import the correct version dynamically
    try:
        if version == "FINAL_V2":
            from app.services.analyze_service_FINAL_V2 import analyze_images
        elif version == "FINAL":
            from app.services.analyze_service_FINAL import analyze_images
        elif version == "v2":
            from app.services.analyze_service_v2 import analyze_images
        elif version == "v4":
            from app.services.analyze_service_v4 import analyze_images
        else:
            return {
                "error": f"Unknown version: {version}",
                "available_versions": ["FINAL_V2", "FINAL", "v2", "v4"]
            }
    except ImportError as e:
        return {
            "error": f"Failed to import analyze_service_{version}",
            "details": str(e),
            "available_versions": ["FINAL_V2", "FINAL", "v2", "v4"]
        }
    
    # Run analysis
    print(f"🤖 Starting analysis with version: {version}")
    result = await analyze_images(image_bytes_list)
    
    print(f"✅ Analysis complete")
    print(f"{'='*60}\n")
    
    return {
        "test_mode": True,
        "version_used": version,
        "authentication": "bypassed",
        "s3_upload": "skipped",
        "database_save": "skipped",
        "result": result
    }