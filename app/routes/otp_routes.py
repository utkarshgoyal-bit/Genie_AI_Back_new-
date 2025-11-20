from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.controllers.otp_controller import OTPController, get_db
from sqlalchemy.orm import Session
from dotenv import load_dotenv
router = APIRouter()

class MobileRequest(BaseModel):
    mobile: str

class OtpVerifyRequest(BaseModel):
    mobile: str
    otp: str

router = APIRouter(prefix="/auth", tags=["OTP"])

@router.post("/send_otp")
def send_otp(data: MobileRequest, db: Session = Depends(get_db)):
    return OTPController.send_otp(data.mobile, db)

@router.post("/verify_otp")
def verify_otp(data: OtpVerifyRequest, db: Session = Depends(get_db)):
    return OTPController.verify_otp(data.mobile, data.otp, db)
