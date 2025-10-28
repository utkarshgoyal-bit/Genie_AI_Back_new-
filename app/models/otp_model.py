from sqlalchemy import Column, Integer, String, Float
from app.config.db import Base

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, index=True, nullable=False)
    otp = Column(String, nullable=False)        
    expiry = Column(Float, nullable=False)
