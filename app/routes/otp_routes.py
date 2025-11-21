from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from app.controllers.otp_controller import OTPController, get_db, decode_access_token
from sqlalchemy.orm import Session
from dotenv import load_dotenv

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

@router.get("/profile")
def get_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {"mobile": mobile}
