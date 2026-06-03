import time
import base64
import io
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session
import logging

# Importing the backend directory using absolute path
try:
    from models.palm_models import (
        PalmEnrollmentRequest, 
        PalmVerificationRequest, 
        PalmRecognitionResult, 
        PalmEnrollmentResult, 
        PalmStatusResult
    )
    from services.palm_recognition_service import PalmRecognitionService
    from core.database import get_user_db
    from routers.auth_routes import get_current_user
    from models.palm_template import PalmTemplate  # Added PalmTemplate import
    from schemas.schemas import PalmAuthRequest  # Added PalmAuthRequest import
    from models.session import UserSession  # Added UserSession import
except ImportError:
    # Handle the case when the backend directory is not in the Python path
    import sys
    
    # Add the backend directory to the Python path
    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    
    # Now import the modules
    from models.palm_models import (
        PalmEnrollmentRequest, 
        PalmVerificationRequest, 
        PalmRecognitionResult, 
        PalmEnrollmentResult, 
        PalmStatusResult
    )
    from services.palm_recognition_service import PalmRecognitionService
    from core.database import get_user_db
    from routers.auth_routes import get_current_user
    from models.palm_template import PalmTemplate  # Added PalmTemplate import
    from schemas.schemas import PalmAuthRequest  # Added PalmAuthRequest import
    from models.session import UserSession  # Added UserSession import

router = APIRouter()  # Removed prefix to avoid duplication when included in main.py

# Initialize the palm recognition service
palm_service = PalmRecognitionService()

@router.get("/palm/status", response_model=PalmStatusResult)
def get_palm_recognition_status(db: Session = Depends(get_user_db)):
    """Get the status of the palm recognition service"""
    return PalmStatusResult(
        enrolled_count=palm_service.get_enrolled_count(db),
        enrolled_names=palm_service.get_enrolled_usernames(db),
        model_loaded=True
    )

@router.post("/palm/enroll_user", response_model=PalmEnrollmentResult)
async def enroll_palm_for_user(
    image: UploadFile = File(...),
    db: Session = Depends(get_user_db),
    current_user = Depends(get_current_user)
):
    """
    Enroll a palm for the currently authenticated user
    
    Args:
        image: Uploaded palm image file
        db: Database session
        current_user: The authenticated user from the token
    
    Returns:
        PalmEnrollmentResult: Contains enrollment result
    """
    try:
        # Validate file before reading it
        if not image.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size to prevent extremely large uploads
        contents = await image.read()
        
        # Check if file is actually empty
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Limit file size (e.g., 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large, max 10MB allowed")
        
        # Create a temporary file to store the image for preprocessing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
            
            try:
                # Perform enrollment for the specific user
                success, message = palm_service.enroll_palm_for_user(
                    db,
                    current_user.id, 
                    current_user.username, 
                    temp_path
                )
                
                return PalmEnrollmentResult(
                    success=success,
                    message=message,
                    enrolled_count=palm_service.get_enrolled_count(db)
                )
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logging.error(f"Palm enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail="User palm enrollment failed due to server error")

@router.post("/palm/verify_user", response_model=PalmRecognitionResult)
async def verify_palm_for_user(
    image: UploadFile = File(...),
    db: Session = Depends(get_user_db),
    current_user = Depends(get_current_user)
):
    """
    Verify palm specifically for the currently authenticated user
    
    Args:
        image: Uploaded palm image file for verification
        db: Database session
        current_user: The authenticated user from the token
    
    Returns:
        PalmRecognitionResult: Contains verification result
    """
    try:
        start_time = time.time()
        
        # Validate file before reading it
        if not image.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size to prevent extremely large uploads
        contents = await image.read()
        
        # Check if file is actually empty
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Limit file size (e.g., 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large, max 10MB allowed")
        
        # Create a temporary file to store the image for preprocessing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
            
            try:
                # Perform verification for the specific user
                success, confidence, message = palm_service.verify_palm_for_user(
                    db,
                    current_user.id, 
                    current_user.username, 
                    temp_path
                )
                
                processing_time = time.time() - start_time
                
                return PalmRecognitionResult(
                    success=success,
                    message=message,
                    matched_name=current_user.username if success else None,
                    confidence=confidence,
                    processing_time=processing_time,
                    enrolled_count=palm_service.get_enrolled_count(db)
                )
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logging.error(f"Palm verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="User palm verification failed due to server error")

@router.post("/palm/verify_any", response_model=PalmRecognitionResult)
async def verify_any_palm(
    image: UploadFile = File(...),
    db: Session = Depends(get_user_db)
):
    """
    Verify palm against any enrolled palm in the system
    
    Args:
        image: Uploaded palm image file for verification
        db: Database session
    
    Returns:
        PalmRecognitionResult: Contains verification result
    """
    try:
        start_time = time.time()
        
        # Validate file before reading it
        if not image.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size to prevent extremely large uploads
        contents = await image.read()
        
        # Check if file is actually empty
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Limit file size (e.g., 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large, max 10MB allowed")
        
        # Create a temporary file to store the image for preprocessing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
            
            try:
                # Perform verification against any enrolled palm
                matched_name, confidence, message, user_id = palm_service.verify_any_palm(
                    db,
                    temp_path
                )
                
                processing_time = time.time() - start_time
                
                return PalmRecognitionResult(
                    success=(matched_name is not None),
                    message=message,
                    matched_name=matched_name,
                    confidence=confidence,
                    processing_time=processing_time,
                    enrolled_count=palm_service.get_enrolled_count(db)
                )
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logging.error(f"General palm verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="General palm verification failed due to server error")

# Legacy endpoints for backward compatibility
@router.post("/palm/enroll", response_model=PalmEnrollmentResult)
async def enroll_palm_legacy(
    name: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Legacy endpoint - Enroll a palm using file upload via form data
    Note: This endpoint is deprecated in favor of user-specific enrollment
    Expected form data: name (str) and image (file)
    """
    from core.database import get_user_db
    from services.palm_recognition_service import PalmRecognitionService
    from models.user import User  # Import User model to check if user exists
    from models.palm_template import PalmTemplate  # Added PalmTemplate import
    import uuid
    
    # Create a database session manually since we can't use the normal dependency injection
    db_gen = get_user_db()
    db = next(db_gen)  # Get the session from the generator
    
    try:
        # First, check if the user exists, if not, create a user with the given name
        user = db.query(User).filter((User.username == name) | (User.full_name == name)).first()
        if user is None:
            # Create a new user if one doesn't exist
            user = User(
                username=name,
                full_name=name,
                email=f"{name}@example.com",  # Default email
                phone="",  # Empty phone initially
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Validate file before reading it
        if not image.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size to prevent extremely large uploads
        contents = await image.read()
        
        # Check if file is actually empty
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Limit file size (e.g., 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large, max 10MB allowed")
        
        # Create a temporary file to store the image for preprocessing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
            
            try:
                palm_service = PalmRecognitionService()
                
                success, message = palm_service.enroll_palm_for_user(
                    db,
                    user.id,  # Use actual user id instead of 0
                    name,
                    temp_path
                )
                
                # Get enrolled count from the database instead of the potentially buggy in-memory counter
                enrolled_count = db.query(PalmTemplate).count()
                
                return PalmEnrollmentResult(
                    success=success,
                    message=message,
                    enrolled_count=enrolled_count
                )
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Legacy palm enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Legacy palm enrollment failed due to server error")
    finally:
        # Close the database session
        db.close()

@router.post("/palm/login-with-palm")
async def palm_login_legacy(
    palm_image: str = Form(None),  # Accept base64 image from form data
    image: UploadFile = File(None)  # Or accept raw image file
):
    """
    Legacy endpoint - Authenticate user using palm recognition
    Note: This endpoint handles both base64 JSON data and raw file uploads
    """
    from core.database import get_user_db
    from services.palm_recognition_service import PalmRecognitionService
    from models.user import User
    from models.session import UserSession
    from datetime import datetime, timedelta
    import tempfile
    import base64
    
    # Create a database session
    db_gen = get_user_db()
    db = next(db_gen)
    
    # Generate a secure token function (this should match the one in auth_routes)
    def generate_token():
        import secrets
        return secrets.token_urlsafe(32)
    
    try:
        # Determine the source of the image data
        img_data = None
        
        if palm_image is not None:
            # Handle base64 encoded image from form data
            try:
                img_data = base64.b64decode(palm_image)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid base64 image data")
        elif image is not None:
            # Handle raw file upload
            img_data = await image.read()
            if len(img_data) == 0:
                raise HTTPException(status_code=400, detail="Uploaded image file is empty")
        else:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Create a temporary file to store the image for preprocessing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(img_data)
            temp_path = temp_file.name
            
            try:
                palm_service = PalmRecognitionService()
                
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
                        "hotel_name": user.hotel_name,
                        "gps_latitude": user.gps_latitude,
                        "gps_longitude": user.gps_longitude,
                        "current_location": user.current_location
                    }
                }
            finally:
                # Clean up temporary file
                import os
                os.unlink(temp_path)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Legacy palm login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Palm authentication failed due to server error")
    finally:
        db.close()

@router.post("/palm/enroll_file", response_model=PalmEnrollmentResult)
async def enroll_palm_file_legacy(name: str, image: UploadFile = File(...)):
    """
    Legacy endpoint - Enroll a palm using an uploaded image file
    Note: This endpoint is deprecated in favor of user-specific enrollment
    """
    raise HTTPException(status_code=501, detail="This endpoint is deprecated. Use /palm/enroll_user instead.")

@router.post("/palm/verify", response_model=PalmRecognitionResult)
async def verify_palm_legacy(verification_request: PalmVerificationRequest):
    """
    Legacy endpoint - Verify a palm using base64 encoded image data
    Note: This endpoint is deprecated in favor of user-specific verification
    """
    raise HTTPException(status_code=501, detail="This endpoint is deprecated. Use /palm/verify_any instead.")

@router.post("/palm/verify_file", response_model=PalmRecognitionResult)
async def verify_palm_file_legacy(image: UploadFile = File(...)):
    """
    Legacy endpoint - Verify a palm using an uploaded image file
    Note: This endpoint is deprecated in favor of user-specific verification
    """
    raise HTTPException(status_code=501, detail="This endpoint is deprecated. Use /palm/verify_any instead.")

@router.get("/palm/enrolled")
def get_enrolled_palms(db: Session = Depends(get_user_db)):
    """Get a list of usernames with enrolled palms"""
    return {
        "enrolled_users": palm_service.get_enrolled_usernames(db), 
        "count": palm_service.get_enrolled_count(db)
    }