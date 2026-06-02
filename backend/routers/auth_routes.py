from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from core.database import get_user_db  # Changed to use PostgreSQL database dependency
from schemas.schemas import UserLogin, UserResponse, PalmAuthRequest
from services.user_service import authenticate_user
from models.session import UserSession
from datetime import datetime, timedelta
import secrets

# Import palm recognition service
from services.palm_recognition_service import PalmRecognitionService
import base64
import tempfile
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize palm recognition service
palm_service = PalmRecognitionService()

def generate_token():
    """Generate a secure random token"""
    return f"session_{secrets.token_urlsafe(32)}"

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_user_db)):  # Changed dependency
    """Login with username and password"""
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Generate a secure token
    token = generate_token()
    
    # Create session record in database with 24-hour expiration
    session = UserSession(
        token=token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour session
    )
    db.add(session)
    db.commit()
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "address": user.address,
            "phone": user.phone,
            "email": user.email,
            "current_city": user.current_city,
            "current_country": user.current_country,
            "hotel_name": user.hotel_name
        }
    }

@router.post("/palm-auth")
def palm_login(palm_auth_data: PalmAuthRequest, db: Session = Depends(get_user_db)):
    """Authenticate user using palm recognition"""
    try:
        # Decode base64 palm image
        img_data = base64.b64decode(palm_auth_data.palm_image)
        
        # Create a temporary file to store the image for preprocessing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(img_data)
            temp_path = temp_file.name
            
            try:
                # Perform palm verification against all enrolled palms in the database
                matched_username, confidence, message, user_id = palm_service.verify_any_palm(
                    db,
                    temp_path
                )
                
                if matched_username is None:
                    raise HTTPException(
                        status_code=401,
                        detail=f"Palm authentication failed: {message}"
                    )
                
                # Find user in database based on matched username
                from models.user import User
                user = db.query(User).filter(User.username == matched_username).first()
                
                if not user:
                    raise HTTPException(
                        status_code=401,
                        detail=f"User not found for palm match: {matched_username}"
                    )
                
                # Generate a secure token
                token = generate_token()
                
                # Create session record in database with 24-hour expiration
                session = UserSession(
                    token=token,
                    user_id=user.id,
                    expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour session
                )
                db.add(session)
                db.commit()
                
                return {
                    "message": "Palm authentication successful",
                    "token": token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "address": user.address,
                        "phone": user.phone,
                        "email": user.email,
                        "current_city": user.current_city,
                        "current_country": user.current_country,
                        "hotel_name": user.hotel_name
                    },
                    "confidence": confidence
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Palm authentication error: {str(e)}"
        )

@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_user_db)):  # Changed dependency
    """Logout and clear session"""
    # Get token from headers
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header[len("Bearer "):]  # Remove "Bearer " prefix
    
    # Find and delete the session from database
    session = db.query(UserSession).filter(UserSession.token == token).first()
    if session:
        db.delete(session)
        db.commit()
    
    return {"message": "Logout successful"}

def get_current_user(request: Request, db: Session = Depends(get_user_db)):  # Changed dependency
    """Get current user from session token in request headers"""
    # Get token from headers and extract the actual token from "Bearer <token>" format
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated - no authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header[len("Bearer "):]  # Remove "Bearer " prefix
    
    # Look up session in database
    session = db.query(UserSession).filter(UserSession.token == token).first()
    
    if not session:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated - invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if session has expired
    if session.expires_at < datetime.utcnow():
        # Clean up expired session
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated - session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from models.user import User
    user = db.query(User).filter(User.id == session.user_id).first()
    
    if not user:
        # Clean up session if user doesn't exist
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=404, detail="User not found")
    
    return user