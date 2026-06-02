import time
import base64
import io
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session

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
        # Read the uploaded image
        contents = await image.read()
        
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
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User palm enrollment failed: {str(e)}")

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
        
        # Read the uploaded image
        contents = await image.read()
        
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
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User palm verification failed: {str(e)}")

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
        
        # Read the uploaded image
        contents = await image.read()
        
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
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"General palm verification failed: {str(e)}")

# Legacy endpoints for backward compatibility
@router.post("/palm/enroll", response_model=PalmEnrollmentResult)
async def enroll_palm_legacy(enrollment_request: PalmEnrollmentRequest):
    """
    Legacy endpoint - Enroll a palm using base64 encoded image data
    Note: This endpoint is deprecated in favor of user-specific enrollment
    """
    raise HTTPException(status_code=501, detail="This endpoint is deprecated. Use /palm/enroll_user instead.")

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