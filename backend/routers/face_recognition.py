from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel
import logging
from services.face_recognition_service import FaceRecognitionService
from dependencies.database import get_face_db_dep
from core.database import get_user_db  # Import the user database dependency
from sqlalchemy.orm import Session
from models.user import User  # Import the User model
from models.session import UserSession  # Import the UserSession model
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/face-recognition", tags=["face-recognition"])
logger = logging.getLogger(__name__)

# Initialize service lazily to avoid startup issues
_face_service = None

def get_face_service():
    global _face_service
    if _face_service is None:
        _face_service = FaceRecognitionService()
    return _face_service

def generate_token():
    """Generate a secure random token"""
    return f"session_{secrets.token_urlsafe(32)}"

class EnrollRequest(BaseModel):
    user_id: str
    name: str


class VerifyResponse(BaseModel):
    user_id: str
    name: str
    similarity: float
    is_match: bool


@router.post("/enroll")
async def enroll_face(
    user_id: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_face_db_dep)
) -> Dict[str, Any]:
    """Enroll a new face by extracting and storing its embedding"""
    try:
        image_bytes = await file.read()
        face_service = get_face_service()
        result = await face_service.enroll_face(user_id, name, image_bytes, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")


@router.post("/verify", response_model=VerifyResponse)
async def verify_face(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_face_db_dep)
) -> Dict[str, Any]:
    """Verify a face against enrolled faces"""
    try:
        image_bytes = await file.read()
        face_service = get_face_service()
        result = await face_service.verify_face(image_bytes, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/login-with-face")
async def login_with_face(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_face_db_dep),
    user_db: Session = Depends(get_user_db)  # Add user database dependency
) -> Dict[str, Any]:
    """Login with face recognition - verifies face and creates session if successful"""
    try:
        image_bytes = await file.read()
        face_service = get_face_service()
        verification_result = await face_service.verify_face(image_bytes, db)
        
        logger.info(f"Face verification result: {verification_result}")
        
        if not verification_result.get("is_match"):
            logger.info("Face not recognized, raising 401")
            raise HTTPException(
                status_code=401,
                detail="Face not recognized. Please enroll first."
            )
        
        # Log the recognized user ID for debugging
        recognized_user_id = verification_result.get("user_id")
        recognized_name = verification_result.get("name")
        logger.info(f"Recognized user_id: {recognized_user_id}, name: {recognized_name}")
        
        # Find the user in the user database
        # Try multiple matching strategies to find the corresponding user account
        user = None
        
        # Strategy 1: Try to find by user_id (exact match)
        if recognized_user_id:
            logger.info(f"Searching for user with username: {recognized_user_id}")
            user = user_db.query(User).filter(User.username == recognized_user_id).first()
            if user:
                logger.info(f"Found user by username: {user.username}")
        
        # Strategy 2: If not found by user_id, try to find by name
        if not user and recognized_name:
            logger.info(f"Searching for user with full_name: {recognized_name}")
            user = user_db.query(User).filter(User.full_name == recognized_name).first()
            if user:
                logger.info(f"Found user by full_name: {user.username}")
        
        # Strategy 3: Try partial matches with user_id
        if not user and recognized_user_id:
            logger.info(f"Searching for user with partial match for: {recognized_user_id}")
            user = user_db.query(User).filter(
                (User.username.ilike(f"%{recognized_user_id}%")) |
                (User.full_name.ilike(f"%{recognized_user_id}%"))
            ).first()
            if user:
                logger.info(f"Found user by partial match: {user.username}")
        
        # Strategy 4: Try partial matches with name
        if not user and recognized_name:
            logger.info(f"Searching for user with partial match for name: {recognized_name}")
            user = user_db.query(User).filter(
                (User.full_name.ilike(f"%{recognized_name}%")) |
                (User.username.ilike(f"%{recognized_name}%"))
            ).first()
            if user:
                logger.info(f"Found user by partial name match: {user.username}")
        
        if not user:
            # Query all usernames for debugging purposes (only in development)
            all_users = user_db.query(User.username, User.full_name).all()
            logger.info(f"All registered users: {[{'username': u[0], 'fullname': u[1]} for u in all_users]}")
            
            # If we still can't find the user, provide a more informative error
            # indicating what was found during face recognition vs what's in the user database
            recognized_identity = recognized_user_id or recognized_name or "unknown"
            logger.info(f"No registered user found for recognized identity: {recognized_identity}")
            raise HTTPException(
                status_code=404,
                detail=f"No registered user found for the recognized face '{recognized_identity}'. "
                       f"The face was recognized but is not linked to an existing account. "
                       f"Please ensure your face is enrolled under a registered username."
            )
        
        # Generate a secure token
        token = generate_token()
        
        # Create session record in database with 24-hour expiration
        session = UserSession(
            token=token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour session
        )
        user_db.add(session)
        user_db.commit()
        
        # Return the same format as the regular login endpoint
        return {
            "message": "Face login successful",
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Face login failed: {str(e)}")


@router.get("/user/{user_id}/has-face-enrollment")
async def check_face_enrollment(
    user_id: str,
    db: AsyncSession = Depends(get_face_db_dep)
) -> Dict[str, bool]:
    """Check if a user has face enrollment data"""
    try:
        face_service = get_face_service()
        has_enrollment = await face_service.has_face_enrollment(user_id, db)
        return {"has_enrollment": has_enrollment}
    except Exception as e:
        logger.error(f"Check face enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Check face enrollment failed: {str(e)}")
