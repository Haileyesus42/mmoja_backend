import numpy as np
import cv2
from PIL import Image
import io
from typing import Tuple


def image_to_numpy(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to numpy array"""
    image = Image.open(io.BytesIO(image_bytes))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return image


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
        
    return float(dot_product / (norm_vec1 * norm_vec2))


def normalize_vector(vec: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length"""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm