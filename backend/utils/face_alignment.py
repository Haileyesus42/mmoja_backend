import cv2
import numpy as np
from typing import Tuple, Optional

class FaceAligner:
    def __init__(self, target_size: Tuple[int, int] = (112, 112)):
        self.target_size = target_size
        # Define standard 5-point facial landmark positions for alignment
        self.standard_landmarks = np.array([
            [30.2946, 51.6963],  # Left eye
            [65.5318, 51.5014],  # Right eye
            [48.0252, 71.7366],  # Nose
            [33.5493, 92.3655],  # Left mouth corner
            [62.7299, 92.2041]   # Right mouth corner
        ], dtype=np.float32)
        
        # Scale to target size
        scale_x = target_size[0] / 96.0
        scale_y = target_size[1] / 112.0
        self.standard_landmarks[:, 0] *= scale_x
        self.standard_landmarks[:, 1] *= scale_y

    def align_face(self, image: np.ndarray, landmarks: np.ndarray) -> Optional[np.ndarray]:
        """
        Align face using affine transformation
        Args:
            image: Input image
            landmarks: Detected facial landmarks (5 points)
        Returns:
            Aligned face image of target size or None if alignment fails
        """
        if landmarks.shape[0] != 5:
            raise ValueError("Exactly 5 landmarks are required for alignment")
            
        # Calculate affine transformation matrix
        transform_matrix = cv2.estimateAffinePartial2D(landmarks, self.standard_landmarks)[0]
        
        if transform_matrix is None:
            return None  # Could not calculate transformation
            
        # Apply transformation to align the face
        aligned_face = cv2.warpAffine(
            image, 
            transform_matrix, 
            self.target_size,
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return aligned_face