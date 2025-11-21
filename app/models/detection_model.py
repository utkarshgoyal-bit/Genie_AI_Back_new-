from sqlalchemy import Column, Integer, String, JSON, Text
from app.config.db import Base

class PlantDetection(Base):
    __tablename__ = "plant_detections"

    id = Column(String, primary_key=True, index=True)  # Changed to String for UUID
    mobile = Column(String, nullable=False)
    common_name = Column(String, nullable=True)
    scientific_name = Column(String, nullable=True)
    plant_confidence = Column(String, nullable=True)
    disease = Column(JSON, nullable=True)
    disease_scientific_name = Column(JSON, nullable=True)
    disease_confidence = Column(JSON, nullable=True)
    diagnosis_type = Column(String, nullable=True)  # NEW
    symptoms = Column(JSON, nullable=True)
    cause = Column(JSON, nullable=True)
    treatment = Column(JSON, nullable=True)
    prevention = Column(JSON, nullable=True)  # NEW
    image = Column(String, nullable=True)  # Keep for backward compatibility
    image_urls = Column(JSON, nullable=True)  # NEW - stores all image URLs
    images_analyzed = Column(Integer, nullable=True)  # NEW