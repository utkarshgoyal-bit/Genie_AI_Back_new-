from sqlalchemy import Column, Integer, String, JSON, Float
from app.config.db import Base

class PlantDetection(Base):
    __tablename__ = "plant_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mobile = Column(String, nullable=False) 
    common_name = Column(String, nullable=False)
    scientific_name = Column(String, nullable=False)
    plant_confidence = Column(String, nullable=False)  # Keep as String (stores "90%")
    disease = Column(JSON, nullable=True)  # Keep as JSON
    disease_scientific_name = Column(JSON, nullable=True)  # Keep as JSON
    disease_confidence = Column(JSON, nullable=True)  # Keep as JSON
    symptoms = Column(JSON, nullable=True)
    cause = Column(JSON, nullable=True)
    treatment = Column(JSON, nullable=True)
    image = Column(String, nullable=True)
    
    # NEW columns we just added
    diagnosis_type = Column(String, nullable=True)
    prevention = Column(JSON, nullable=True)
    image_urls = Column(JSON, nullable=True)
    images_analyzed = Column(Integer, nullable=True)