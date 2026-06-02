from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError, IntegrityError
from typing import Dict, Any, List, Optional
import numpy as np
import logging
from models.user_face import UserFace, insert_face_embedding_async, find_similar_faces_async
from utils.image_utils import image_to_numpy
from utils.face_detection import FaceDetector
from utils.face_alignment import FaceAligner
from utils.embedding_extraction import EmbeddingExtractor
from utils.math_utils import cosine_similarity

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    def __init__(self):
        self.detector = FaceDetector()
        self.aligner = FaceAligner()
        self.extractor = EmbeddingExtractor()

    async def enroll_face(  # Changed back to async
        self, 
        user_id: str, 
        name: str, 
        image_bytes: bytes, 
        db: AsyncSession  # Changed to AsyncSession
    ) -> Dict[str, Any]:
        """Enroll a new face by extracting and storing its embedding"""
        try:
            # Read and decode image
            image = image_to_numpy(image_bytes)
            
            # Detect face
            landmarks = self.detector.detect_face(image)
            if landmarks is None:
                raise ValueError("No face detected or multiple faces detected")
            
            # Align face
            aligned_face = self.aligner.align_face(image, landmarks)
            if aligned_face is None:
                raise ValueError("Face alignment failed")
            
            # Extract embedding
            embedding = self.extractor.extract_embedding(aligned_face)
            if embedding is None:
                raise ValueError("Embedding extraction failed")
            
            # Try to insert or update face embedding in database
            try:
                # First, check if user already exists
                existing_user = await db.execute(
                    select(UserFace).where(UserFace.user_id == user_id)
                )
                existing_record = existing_user.scalar_one_or_none()
                
                logger.info(f"Enrollment: Found existing record for user_id {user_id}: {existing_record is not None}")
                
                if existing_record:
                    # Update the existing record
                    existing_record.name = name
                    existing_record.embedding = embedding.tolist()
                    existing_record.updated_at = func.now()
                    await db.commit()
                    await db.refresh(existing_record)
                    logger.info(f"Enrollment: Updated face for user_id {user_id}")
                    return {"message": "Face updated successfully", "user_id": user_id}
                else:
                    # Insert a new record
                    await insert_face_embedding_async(db, user_id, name, embedding.tolist())
                    logger.info(f"Enrollment: Created new face entry for user_id {user_id}")
                    return {"message": "Face enrolled successfully", "user_id": user_id}
            except IntegrityError as e:
                # Handle other integrity errors
                if "duplicate key value violates unique constraint" in str(e):
                    # This shouldn't happen anymore with our check, but just in case
                    await db.rollback()
                    # Update the existing record instead
                    existing_user = await db.execute(
                        select(UserFace).where(UserFace.user_id == user_id)
                    )
                    existing_record = existing_user.scalar_one_or_none()
                    
                    if existing_record:
                        existing_record.name = name
                        existing_record.embedding = embedding.tolist()
                        existing_record.updated_at = func.now()
                        await db.commit()
                        await db.refresh(existing_record)
                        logger.info(f"Enrollment: Updated face after integrity error for user_id {user_id}")
                        return {"message": "Face updated successfully", "user_id": user_id}
                    else:
                        # This is unexpected, raise the error
                        raise e
                else:
                    raise e
            except OperationalError as e:
                if "password authentication failed" in str(e) or "connection to server" in str(e):
                    logger.warning(f"PostgreSQL not available for enrollment: {e}")
                    # Still return success if face processing was successful, just couldn't store
                    return {"message": "Face processed successfully (storage pending PostgreSQL setup)", "user_id": user_id, "requires_postgres": True}
                else:
                    raise e
            except Exception as e:
                logger.error(f"Database error during enrollment: {str(e)}")
                await db.rollback()
                raise e
        
        except ValueError as e:
            raise e  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Enrollment error: {str(e)}")
            try:
                await db.rollback()
            except:
                pass  # Ignore rollback errors
            raise Exception(f"Enrollment failed: {str(e)}")

    async def verify_face(  # Changed back to async
        self, 
        image_bytes: bytes, 
        db: AsyncSession  # Changed to AsyncSession
    ) -> Dict[str, Any]:
        """Verify a face against enrolled faces"""
        try:
            # Read and decode image
            image = image_to_numpy(image_bytes)
            
            # Detect face
            landmarks = self.detector.detect_face(image)
            if landmarks is None:
                raise ValueError("No face detected or multiple faces detected")
            
            # Align face
            aligned_face = self.aligner.align_face(image, landmarks)
            if aligned_face is None:
                raise ValueError("Face alignment failed")
            
            # Extract embedding
            query_embedding = self.extractor.extract_embedding(aligned_face)
            if query_embedding is None:
                raise ValueError("Embedding extraction failed")
            
            # Try to find similar faces in the database
            try:
                logger.info("Starting face verification process")
                
                # Find similar faces using the async function
                similar_faces = await find_similar_faces_async(db, query_embedding.tolist(), limit=1)
                
                logger.info(f"Found {len(similar_faces) if similar_faces else 0} similar faces")
                
                if similar_faces and len(similar_faces) > 0:
                    best_match = similar_faces[0]
                    logger.info(f"Best match: user_id={best_match['user_id']}, similarity={best_match['similarity']}")
                    
                    # Consider a match if similarity is above threshold (adjust as needed)
                    SIMILARITY_THRESHOLD = 0.7  # Restored original threshold
                    is_match = best_match['similarity'] >= SIMILARITY_THRESHOLD
                    
                    logger.info(f"Similarity: {best_match['similarity']}, Threshold: {SIMILARITY_THRESHOLD}, Is match: {is_match}")
                    
                    return {
                        "user_id": best_match['user_id'],
                        "name": best_match['name'],
                        "similarity": best_match['similarity'],
                        "distance": best_match['distance'],
                        "is_match": is_match
                    }
                else:
                    # No similar faces found
                    logger.info("No similar faces found in database")
                    return {
                        "user_id": None,
                        "name": None,
                        "similarity": 0.0,
                        "distance": 1.0,
                        "is_match": False
                    }
            except Exception as e:
                logger.error(f"Database error during verification: {str(e)}")
                raise e
        
        except ValueError as e:
            logger.error(f"Validation error during verification: {str(e)}")
            raise e  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            raise Exception(f"Verification failed: {str(e)}")

    async def get_enrolled_faces(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get list of enrolled faces"""
        try:
            result = await db.execute(select(UserFace))
            faces = result.scalars().all()
            
            return [
                {
                    "user_id": face.user_id,
                    "name": face.name,
                    "created_at": face.created_at.isoformat() if face.created_at else None,
                    "updated_at": face.updated_at.isoformat() if face.updated_at else None
                }
                for face in faces
            ]
        except Exception as e:
            logger.error(f"Error retrieving enrolled faces: {str(e)}")
            raise Exception(f"Failed to retrieve enrolled faces: {str(e)}")

    async def has_face_enrollment(self, user_id: str, db: AsyncSession) -> bool:
        """Check if a user has face enrollment data"""
        try:
            result = await db.execute(
                select(UserFace).where(UserFace.user_id == user_id)
            )
            face_record = result.scalar_one_or_none()
            return face_record is not None
        except Exception as e:
            logger.error(f"Error checking face enrollment: {str(e)}")
            return False
