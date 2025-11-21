from fastapi import APIRouter, UploadFile, File, Depends, Request, BackgroundTasks
from typing import List
from app.controllers.analyze_controller_FINAL import handle_analyze
from app.config.db import get_db  
from sqlalchemy.orm import Session
from unittest.mock import patch
import os

router = APIRouter(prefix="/analyze", tags=["Analyze"])

@router.post("/")
async def analyze_plant(
    request: Request,
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db), 
):
    
    return await handle_analyze(images, request, db, background_tasks)


@router.post("/test")
async def analyze_plant_test(
    request: Request,
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    TEST ONLY: Analyze without authentication
    WARNING: Remove this endpoint before production deployment
    """
    
    # Check if running in development mode
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return {"error": "Test endpoint disabled in production"}
    
    # Create a mock request with test authorization header
    class MockRequest:
        def __init__(self, original_request):
            self.headers = {"Authorization": "Bearer test_token"}
            self.state = original_request.state if hasattr(original_request, 'state') else None
    
    mock_request = MockRequest(request)
    
    # Mock the token decode to return test user
    with patch('app.controllers.analyze_controller_FINAL.decode_access_token') as mock_decode:
        mock_decode.return_value = {"sub": "+919999999999"}  # Test mobile number
        return await handle_analyze(images, mock_request, db, background_tasks)