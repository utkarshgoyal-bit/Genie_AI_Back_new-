from sqlalchemy import Column, Integer, String, JSON, LargeBinary
from app.config.db import Base

class PlantDetection(Base):
    __tablename__ = "plant_detections"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, nullable=False) 
    common_name = Column(String, nullable=False)
    scientific_name = Column(String, nullable=False)
    plant_confidence = Column(String, nullable=False)
    disease = Column(JSON)  
    disease_scientific_name = Column(JSON)
    disease_confidence = Column(JSON)
    symptoms = Column(JSON)
    cause = Column(JSON)
    treatment = Column(JSON)
    image = Column(String, nullable=True)
    
