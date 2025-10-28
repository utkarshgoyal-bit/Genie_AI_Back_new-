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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.product_name,
            "scientific_name": self.scientific_name,
            "disease": self.disease,
            "disease_scientific_name": self.disease_scientific_name,
            "product_link": self.product_link,
            "how_to_use": self.how_to_use,
            "product_image": self.product_image
        }