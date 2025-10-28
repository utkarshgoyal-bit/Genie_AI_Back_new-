from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.db import get_db
from app.models.detection_model import PlantDetection
from app.controllers.otp_controller import decode_access_token

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("/")
def get_detection_history(token: str, db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    history = db.query(PlantDetection).filter(PlantDetection.mobile == mobile).all()

    return {"history": [dict(
        id=item.id,
        mobile=item.mobile,
        common_name=item.common_name,
        scientific_name=item.scientific_name,
        plant_confidence=item.plant_confidence,
        disease=item.disease,
        disease_scientific_name=item.disease_scientific_name,
        disease_confidence=item.disease_confidence,
        symptoms=item.symptoms,
        cause=item.cause,
        treatment=item.treatment,
        image=item.image
    ) for item in history]}