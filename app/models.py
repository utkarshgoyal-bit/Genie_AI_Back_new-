from sqlalchemy import Column, Integer, String, JSON, Text, Float
from app.utils import Base

# ============================================================================
# PLANT DETECTION MODEL
# ============================================================================
class PlantDetection(Base):
    __tablename__ = "plant_detections"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    mobile = Column(String, nullable=False)
    common_name = Column(String, nullable=True)
    scientific_name = Column(String, nullable=True)
    plant_confidence = Column(String, nullable=True)
    disease = Column(JSON, nullable=True)
    disease_scientific_name = Column(JSON, nullable=True)
    disease_confidence = Column(JSON, nullable=True)
    diagnosis_type = Column(String, nullable=True)
    symptoms = Column(JSON, nullable=True)
    cause = Column(JSON, nullable=True)
    treatment = Column(JSON, nullable=True)
    prevention = Column(JSON, nullable=True)
    image = Column(String, nullable=True)  # Backward compatibility
    image_urls = Column(JSON, nullable=True)
    images_analyzed = Column(Integer, nullable=True)


# ============================================================================
# OTP MODEL
# ============================================================================
class OTP(Base):
    __tablename__ = "otp"
    
    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, nullable=False)
    otp = Column(String, nullable=False)
    expiry = Column(Float, nullable=False)


# ============================================================================
# PRODUCT MODEL
# ============================================================================
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scientific_name = Column(String(255), nullable=True)
    disease = Column(String(255), nullable=True)
    disease_scientific_name = Column(String(255), nullable=True)
    product_link = Column(Text, nullable=True)
    product_name = Column(String(255), nullable=True)
    how_to_use = Column(Text, nullable=True)
    product_image = Column(Text, nullable=True)


# Export all models
__all__ = ["PlantDetection", "OTP", "Product"]
