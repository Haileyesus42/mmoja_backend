from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select                    
from typing import Dict, Any
import uuid
import numpy as np
import logging
from database import get_db, UserFace, insert_face_embedding, find_similar_faces
from face_detection import FaceDetector
from face_alignment import FaceAligner
from embedding_extraction import EmbeddingExtractor
from utils import image_to_numpy, cosine_similarity
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize components
detector = FaceDetector()
aligner = FaceAligner()
extractor = EmbeddingExtractor()

# Optional pydantic models (not used in multipart, but can stay)
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
    db: AsyncSession = Depends(get_db)
):
    """Enroll a new face by extracting and storing its embedding"""
    try:
        # Validate file before reading it
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size to prevent extremely large uploads
        # Note: We can't check content length directly from UploadFile, so we'll read in chunks if needed
        image_bytes = await file.read()
        
        # Check if file is actually empty
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Limit file size (e.g., 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large, max 10MB allowed")
        
        # Try to convert image to numpy array to validate it's a proper image
        try:
            image = image_to_numpy(image_bytes)
        except Exception as img_error:
            logger.error(f"Image conversion error: {str(img_error)}")
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect face
        landmarks = detector.detect_face(image)
        if landmarks is None:
            raise HTTPException(status_code=400, detail="No face detected or multiple faces detected")
        
        # Align face
        aligned_face = aligner.align_face(image, landmarks)
        if aligned_face is None:
            raise HTTPException(status_code=400, detail="Face alignment failed")
        
        # Extract embedding
        embedding = extractor.extract_embedding(aligned_face)
        if embedding is None:
            raise HTTPException(status_code=400, detail="Embedding extraction failed")
        
        # Check if user already exists by the string user_id field, NOT the primary key
        result = await db.execute(
            select(UserFace).where(UserFace.user_id == user_id)
        )
        existing_user = result.scalars().first()

        if existing_user:
            # Update existing user
            existing_user.embedding = embedding.tolist()
            existing_user.name = name
        else:
            # Create new user
            user_face = UserFace(
                user_id=user_id,
                name=name,
                embedding=embedding.tolist()
            )
            db.add(user_face)
        
        await db.commit()
        
        return {"message": "Face enrolled successfully", "user_id": user_id}
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Enrollment failed due to server error")


@router.post("/verify", response_model=VerifyResponse)
async def verify_face(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Verify a face against enrolled faces"""
    try:
        # Validate file before reading it
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size to prevent extremely large uploads
        image_bytes = await file.read()
        
        # Check if file is actually empty
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Limit file size (e.g., 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large, max 10MB allowed")
        
        # Try to convert image to numpy array to validate it's a proper image
        try:
            image = image_to_numpy(image_bytes)
        except Exception as img_error:
            logger.error(f"Image conversion error: {str(img_error)}")
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect face
        landmarks = detector.detect_face(image)
        if landmarks is None:
            raise HTTPException(status_code=400, detail="No face detected or multiple faces detected")
        
        # Align face
        aligned_face = aligner.align_face(image, landmarks)
        if aligned_face is None:
            raise HTTPException(status_code=400, detail="Face alignment failed")
        
        # Extract embedding
        query_embedding = extractor.extract_embedding(aligned_face)
        if query_embedding is None:
            raise HTTPException(status_code=400, detail="Embedding extraction failed")
        
        # Find similar faces in the database
        similar_faces = await find_similar_faces(db, query_embedding.tolist(), limit=1)
        
        if not similar_faces:
            raise HTTPException(status_code=404, detail="No enrolled faces found")
        
        # Get the best match
        best_match = similar_faces[0]
        
        # Determine if it's a match (threshold could be configurable)
        is_match = best_match["similarity"] > 0.4  # Threshold for verification
        
        return {
            "user_id": best_match["user_id"],
            "name": best_match["name"],
            "similarity": best_match["similarity"],
            "is_match": is_match
        }
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed due to server error")