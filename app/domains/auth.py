import time
import random
import os
import requests
from jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils import get_db
from app.models import OTP, PlantDetection

# ============================================================================
# CONFIGURATION
# ============================================================================
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

# OTP SMS Configuration
E2A_API_KEY = os.getenv("E2A_API_KEY")
E2A_SENDER_ID = os.getenv("E2A_SENDER_ID")
E2A_API_URL = os.getenv("E2A_API_URL")
E2A_ENTITY_ID = os.getenv("E2A_ENTITY_ID")
E2A_TEMPLATE_ID = os.getenv("E2A_TEMPLATE_ID")


# ============================================================================
# JWT TOKEN HANDLERS
# ============================================================================
def create_access_token(data: dict):
    """Persistent JWT token without expiry."""
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


# ============================================================================
# OTP CONTROLLER LOGIC
# ============================================================================
class OTPController:
    @staticmethod
    def send_otp(mobile: str, db: Session):
        try:
            otp = random.randint(1000, 9999)
            otp_str = str(otp)
            
            # Test mobile number bypass
            if mobile == "+919999999999":
                otp_str = "0000"
            
            message = f"Welcome to Garden Genie. Your OTP for verification is {otp_str}. Enjoy Gardening!"
            
            params = {
                "key": E2A_API_KEY,
                "to": mobile,
                "from": E2A_SENDER_ID,
                "body": message,
                "entityid": E2A_ENTITY_ID,
                "templateid": E2A_TEMPLATE_ID,
            }
            
            response = requests.get(E2A_API_URL, params=params, timeout=10)
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to send OTP")
            
            # Save OTP in database
            otp_entry = OTP(mobile=mobile, otp=otp_str, expiry=time.time() + 300)
            db.add(otp_entry)
            db.commit()
            
            return {"message": "OTP sent successfully", "otp": otp_str}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def verify_otp(mobile: str, otp: str, db: Session):
        otp_entry = (
            db.query(OTP)
            .filter(OTP.mobile == mobile)
            .order_by(OTP.id.desc())
            .first()
        )
        
        if not otp_entry:
            raise HTTPException(status_code=400, detail="OTP not sent")
        
        if time.time() > otp_entry.expiry:
            raise HTTPException(status_code=400, detail="OTP expired")
        
        if otp_entry.otp == otp:
            db.delete(otp_entry)
            db.commit()
            
            # Generate JWT token
            token = create_access_token({"sub": mobile})
            
            return {
                "message": "OTP verified successfully",
                "token": token,
                "mobile": mobile
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================
class MobileRequest(BaseModel):
    mobile: str


class OtpVerifyRequest(BaseModel):
    mobile: str
    otp: str


# ============================================================================
# ROUTER DEFINITION
# ============================================================================
router = APIRouter(prefix="/auth", tags=["OTP"])


# ============================================================================
# API ROUTES
# ============================================================================
@router.post("/send_otp")
def send_otp(data: MobileRequest, db: Session = Depends(get_db)):
    """Send OTP to mobile number"""
    return OTPController.send_otp(data.mobile, db)


@router.post("/verify_otp")
def verify_otp(data: OtpVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and return JWT token"""
    return OTPController.verify_otp(data.mobile, data.otp, db)


@router.get("/profile")
def get_profile(request: Request, db: Session = Depends(get_db)):
    """
    Get user profile from JWT token
    Returns the user's mobile number
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {"mobile": mobile}


@router.delete("/delete_account")
def delete_account(request: Request, db: Session = Depends(get_db)):
    """
    Delete user account and all associated data
    - Deletes all diagnosis history
    - Deletes OTP records
    - Removes all user data from database
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    mobile = payload.get("sub")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    try:
        # Delete all diagnosis history for this user
        deleted_detections = db.query(PlantDetection).filter(PlantDetection.mobile == mobile).delete()
        
        # Delete all OTP records for this user (cleanup)
        deleted_otps = db.query(OTP).filter(OTP.mobile == mobile).delete()
        
        # Commit the changes
        db.commit()
        
        print(f"✅ Account deleted for {mobile}: {deleted_detections} detections, {deleted_otps} OTPs")
        
        return {
            "message": "Account successfully deleted",
            "deleted_records": {
                "diagnosis_history": deleted_detections,
                "otp_records": deleted_otps
            }
        }
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to delete account for {mobile}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")
