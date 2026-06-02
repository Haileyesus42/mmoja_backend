import onnxruntime as ort
import numpy as np
import cv2
from typing import Optional
from core.config import settings

class EmbeddingExtractor:
    def __init__(self, model_path: str = settings.MODEL_PATH):
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face embedding using AdaFace ONNX model
        Args:
            face_image: Aligned face image (112x112)
        Returns:
            Normalized embedding vector or None if extraction fails
        """
        try:
            # Preprocess the image
            input_tensor = self._preprocess(face_image)
            
            # Run inference
            embedding = self.session.run([self.output_name], {self.input_name: input_tensor})[0][0]
            
            # Normalize the embedding
            normalized_embedding = embedding / np.linalg.norm(embedding)
            
            return normalized_embedding.astype(np.float32)
        except Exception as e:
            print(f"Error extracting embedding: {str(e)}")
            return None
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the image for the model"""
        # Ensure the image is in RGB format and resize if needed
        if image.shape[:2] != settings.IMAGE_SIZE:
            image = cv2.resize(image, settings.IMAGE_SIZE)
            
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # Normalize pixel values to [-1, 1] range (common for face recognition models)
        image = image.astype(np.float32) / 127.5 - 1.0
        
        # Transpose to CHW format (channels first)
        image = np.transpose(image, (2, 0, 1))
        
        # Add batch dimension
        image = np.expand_dims(image, axis=0)
        
        return image
    
    def __del__(self):
        if hasattr(self, 'session'):
            del self.session