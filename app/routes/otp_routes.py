from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.controllers.otp_controller import OTPController, get_db, decode_access_token
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()
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

@router.get("/profile")
def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {"mobile": mobile}

@router.delete("/delete_account")
def delete_account(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return OTPController.delete_account(mobile, db)
