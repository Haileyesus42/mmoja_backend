import time
from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Optional
import sys
from pathlib import Path

# Add the backend directory to the path to ensure imports work correctly
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from models.face_liveness_models import DetectionResult
from services.face_liveness_service import FaceLivenessService

router = APIRouter()  # Removed prefix to avoid duplication when included in main.py
detection_service = FaceLivenessService()

@router.get("/")
def read_root():
    """Root endpoint to verify the API is running"""
    return {"message": "Face Anti-Spoofing API is running"}

@router.post("/detect", response_model=DetectionResult)
async def detect_face_spoofing(image: UploadFile = File(...)):
    """
    Perform face liveness detection on an uploaded image
    
    Args:
        image: Uploaded image file (JPEG, PNG, etc.)
    
    Returns:
        DetectionResult: Contains spoofing detection results
    """
    try:
        # Read the uploaded image
        contents = await image.read()
        
        # Process the image using the service
        result = detection_service.detect_from_file(contents)
        
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/detect_base64", response_model=DetectionResult)
async def detect_face_spoofing_base64(base64_image: str):
    """
    Perform face liveness detection on a base64 encoded image
    
    Args:
        base64_image: Base64 encoded image string
    
    Returns:
        DetectionResult: Contains spoofing detection results
    """
    try:
        # Process the base64 image using the service
        result = detection_service.detect_from_base64(base64_image)
        
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")