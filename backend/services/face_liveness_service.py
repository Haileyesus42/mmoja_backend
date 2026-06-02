import os
import sys
import numpy as np
import cv2
import time
import logging
from typing import Tuple, Optional
from pathlib import Path

# Add the project root directory to the path to import test.py correctly
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from test import MiniFASNetDemo

# Import using sys.path addition
sys.path.append(str(Path(__file__).resolve().parent.parent))
from models.face_liveness_models import DetectionResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceLivenessService:
    def __init__(self, model_dir: str = "onnx"):
        """Initialize the detection service with the face anti-spoofing model"""
        self.detector = MiniFASNetDemo(model_dir=model_dir)

    def detect_from_file(self, image_contents: bytes) -> DetectionResult:
        start_time = time.time()
        
        # Decode the image
        nparr = np.frombuffer(image_contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Invalid image file")
        
        # Detect face in the image
        bbox = self.detector.detect_face(frame)
        
        if not bbox:
            raise ValueError("No face detected in the image")
        
        # Perform liveness detection
        result = self.detector.predict(frame, bbox)
        
        processing_time = time.time() - start_time
        
        # Log the raw result for debugging
        logger.info(f"Liveness detection result: {result}")
        
        # Apply post-processing to adjust prediction based on confidence if needed
        # This is to handle cases where the model might have been trained differently
        processed_result = self._post_process_result(result)
        
        # Convert numpy types to native Python types for serialization
        return DetectionResult(
            is_real=bool(processed_result["is_real"]),
            confidence=float(processed_result["confidence"]),
            label=int(processed_result["label"]),  # Convert numpy.int32 to Python int
            label_text=str(processed_result["label_text"]),
            processing_time=float(processing_time),
            bbox=[float(coord) for coord in bbox] if bbox else None
        )

    def detect_from_base64(self, base64_image: str) -> DetectionResult:
        """
        Perform face liveness detection on a base64 encoded image
        
        Args:
            base64_image: Base64 encoded image string
        
        Returns:
            DetectionResult: Contains spoofing detection results
        """
        start_time = time.time()
        
        import base64
        
        # Decode base64 image
        img_data = base64.b64decode(base64_image)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Invalid base64 image")
        
        # Detect face in the image
        bbox = self.detector.detect_face(frame)
        
        if not bbox:
            raise ValueError("No face detected in the image")
        
        # Perform liveness detection
        result = self.detector.predict(frame, bbox)
        
        processing_time = time.time() - start_time
        
        # Log the raw result for debugging
        logger.info(f"Liveness detection result: {result}")
        
        # Apply post-processing to adjust prediction based on confidence if needed
        # This is to handle cases where the model might have been trained differently
        processed_result = self._post_process_result(result)
        
        # Convert numpy types to native Python types for serialization
        return DetectionResult(
            is_real=bool(processed_result["is_real"]),
            confidence=float(processed_result["confidence"]),
            label=int(processed_result["label"]),  # Convert numpy.int32 to Python int
            label_text=str(processed_result["label_text"]),
            processing_time=float(processing_time),
            bbox=[float(coord) for coord in bbox] if bbox else None
        )
    
    def _post_process_result(self, result: dict) -> dict:
        """
        Post-process the result to adjust for potential model differences.
        This method can be customized based on how your specific model behaves.
        """
        # For now, return the result as is
        # In the future, this could contain logic to adjust results based on confidence thresholds
        # or other heuristics if needed
        return result