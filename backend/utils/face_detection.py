import cv2
import numpy as np
from typing import Tuple, Optional
from core.config import settings

try:
    # Try the newer MediaPipe API first
    import mediapipe as mp
    from mediapipe.tasks import vision
    USE_NEW_API = True
except ImportError:
    # Fall back to the older API
    import mediapipe as mp
    USE_NEW_API = False


class FaceDetector:
    def __init__(self):
        if USE_NEW_API:
            # New MediaPipe API
            base_options = vision.RunningMode.IMAGE
            self.detector = vision.FaceDetector.create_from_options(
                vision.FaceDetectorOptions(base_options=base_options)
            )
        else:
            # Old MediaPipe API
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,  # Only detect one face
                min_detection_confidence=settings.FACE_DETECTION_THRESHOLD
            )
            self.mp_drawing = mp.solutions.drawing_utils
        
    def detect_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect a single face in the image and return landmarks
        Returns: landmarks or None if no face detected
        """
        if USE_NEW_API:
            # Use new API
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            
            detection_result = self.detector.detect(mp_image)
            
            if not detection_result.detections:
                return None  # No face detected
                
            if len(detection_result.detections) > 1:
                return None  # Multiple faces detected - reject
                
            # For the new API, we need to get face landmarks differently
            # This is simplified since the new API doesn't directly provide face mesh
            detection = detection_result.detections[0]
            bbox = detection.bounding_box
            x, y, w, h = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height
            
            # For simplicity in this case, return bounding box center points
            # In a real implementation, you'd need to use FaceGeometry or similar
            center_x, center_y = x + w//2, y + h//2
            # Approximate 5 landmark points based on bounding box
            landmarks = np.array([
                [x + w * 0.3, y + h * 0.3],  # Left eye
                [x + w * 0.7, y + h * 0.3],  # Right eye  
                [center_x, center_y + h * 0.1],  # Nose
                [x + w * 0.3, y + h * 0.7],  # Mouth left
                [x + w * 0.7, y + h * 0.7]   # Mouth right
            ], dtype=np.float32)
            
            return landmarks
        else:
            # Old MediaPipe API
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_image)
            
            if not results.multi_face_landmarks:
                return None  # No face detected
                
            if len(results.multi_face_landmarks) > 1:
                return None  # Multiple faces detected - reject
                
            # Get the first (and only) face
            landmarks = results.multi_face_landmarks[0]
            
            # Extract key facial landmarks (5-point model: eyes, nose, mouth corners)
            landmark_points = []
            for idx in [33, 263, 1, 61, 291]:  # Left eye, right eye, nose, left mouth, right mouth
                landmark = landmarks.landmark[idx]
                x = int(landmark.x * image.shape[1])
                y = int(landmark.y * image.shape[0])
                landmark_points.append((x, y))
                
            return np.array(landmark_points, dtype=np.float32)
    
    def __del__(self):
        if not USE_NEW_API and hasattr(self, 'face_mesh'):
            self.face_mesh.close()