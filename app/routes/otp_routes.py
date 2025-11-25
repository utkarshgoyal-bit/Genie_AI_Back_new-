from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.controllers.otp_controller import OTPController, get_db, decode_access_token
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

# ✅ NEW ENDPOINT - Get User Profile
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

# ✅ NEW ENDPOINT - Delete User Account
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
        # Import PlantDetection model
        from app.models.detection_model import PlantDetection
        from app.models.otp_model import OTP
        
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