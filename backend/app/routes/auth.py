from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlmodel import Session, select
from ..database import get_session
from ..models import User, DriverDocument
from ..utils.hashing import hash_password, verify_password
from ..utils.jwt_handler import create_access_token, get_current_user
from ..utils.audit import log_action
from ..utils.otp_sender import send_otp
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import os

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "passenger"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class OtpLoginRequest(BaseModel):
    email: EmailStr

class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/register")
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    
    if existing and existing.is_active:
        raise HTTPException(400, "Email already exists")

    otp = send_otp(payload.email)
    
    if existing: # User exists but isn't active, update their details
        user = existing
        user.name = payload.name
        user.password = hash_password(payload.password)
        user.role = payload.role
    else:
        user = User(name=payload.name, email=payload.email,
                    password=hash_password(payload.password), 
                    role=payload.role, is_active=False)
    
    user.otp = otp
    user.otp_expires = datetime.utcnow() + timedelta(minutes=5)
    
    session.add(user); session.commit(); session.refresh(user)
    log_action(payload.email, "REGISTER_ATTEMPT", f"role={payload.role}")
    
    return {"message": "User registered. Please verify OTP (check console)."}

@router.post("/verify_otp")
def verify_otp(payload: OtpVerifyRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_active:
        raise HTTPException(400, "User already verified")
    if user.otp != payload.otp:
        raise HTTPException(400, "Invalid OTP")
    if user.otp_expires < datetime.utcnow():
        raise HTTPException(400, "OTP expired")
        
    user.is_active = True
    user.otp = None
    user.otp_expires = None
    session.add(user); session.commit()
    log_action(user.email, "REGISTER_SUCCESS", "")
    
    return {"message": "User verified successfully"}

@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    
    if not user:
        raise HTTPException(401, "Invalid credentials")
        
    if not user.is_active:
        raise HTTPException(403, "Account not active. Please verify your OTP.")

    if not verify_password(payload.password, user.password):
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.is_active = False # Lock account
            log_action(user.email, "ACCOUNT_LOCKED", "5 failed attempts")
        session.add(user); session.commit()
        raise HTTPException(401, "Invalid credentials")
        
    user.failed_attempts = 0
    session.add(user); session.commit()
    
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    log_action(user.email, "LOGIN_SUCCESS", "")
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login/otp_request")
def login_otp_request(payload: OtpLoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not user.is_active:
        raise HTTPException(404, "Active user not found")
    
    otp = send_otp(user.email)
    user.otp = otp
    user.otp_expires = datetime.utcnow() + timedelta(minutes=5)
    
    session.add(user); session.commit()
    log_action(payload.email, "LOGIN_OTP_REQUEST", "")
    return {"message": "OTP sent (check console)"}

@router.post("/login/otp_verify")
def login_otp_verify(payload: OtpVerifyRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    
    if not user or not user.is_active:
        raise HTTPException(404, "Active user not found")
    if user.otp != payload.otp:
        raise HTTPException(400, "Invalid OTP")
    if user.otp_expires < datetime.utcnow():
        raise HTTPException(400, "OTP expired")

    user.otp = None
    user.otp_expires = None
    session.add(user); session.commit()
    
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    log_action(user.email, "LOGIN_OTP_SUCCESS", "")
    return {"access_token": token, "token_type": "bearer"}

@router.post("/upload_docs")
def upload_driver_docs(
    email: EmailStr = Form(...), 
    doc_type: str = Form(...), 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user)):
    
    if payload.get("sub") != email:
        raise HTTPException(403, "You can only upload documents for your own account")
        
    user = session.exec(select(User).where(User.email == email, User.role == "driver")).first()
    if not user:
        raise HTTPException(404, "Driver not found")
    
    dest_dir = "uploaded_docs"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Sanitize filename
    safe_filename = f"{user.id}_{doc_type.lower().replace(' ','_')}.pdf"
    dest = os.path.join(dest_dir, safe_filename)
    
    with open(dest, "wb") as f:
        f.write(file.file.read())
        
    doc = DriverDocument(user_id=user.id, doc_type=doc_type, file_path=dest, approved=False)
    session.add(doc); session.commit(); session.refresh(doc)
    log_action(email, "UPLOAD_DOC", doc_type)
    return {"status": "uploaded", "doc_id": doc.id, "path": dest}

@router.put("/driver/location")
def update_driver_location(
    loc: LocationUpdateRequest, 
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user)):
    
    if payload.get("role") != "driver":
        raise HTTPException(403, "Only drivers can update their location")
        
    driver = session.get(User, payload.get("id"))
    if not driver:
        raise HTTPException(404, "Driver not found")
        
    driver.latitude = loc.latitude
    driver.longitude = loc.longitude
    session.add(driver); session.commit()
    log_action(driver.email, "UPDATE_LOCATION", f"lat={loc.latitude}, lon={loc.longitude}")
    return {"status": "location updated"}