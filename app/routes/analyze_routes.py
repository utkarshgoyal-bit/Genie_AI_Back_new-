from fastapi import APIRouter, UploadFile, File, Depends, Request, BackgroundTasks
from typing import List
from app.controllers.analyze_controller import handle_analyze
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