from sqlalchemy import Column, Integer, String, Text
from app.config.db import Base

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