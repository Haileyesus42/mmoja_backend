import cv2
import numpy as np
import os
import onnxruntime as ort
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MiniFASNetDemo:
    def __init__(self, model_dir: str = "onnx"):
        """Initialize the face anti-spoofing detector with ONNX models"""
        self.model_dir = model_dir
        self.session = None
        self.min_face_size = 20  # Minimum face size for detection
        self.confidence_threshold = 0.5  # Confidence threshold for face detection
        
        # Initialize ONNX models for face anti-spoofing
        self._load_models()
    
    def _load_models(self):
        """Load the ONNX models for face anti-spoofing detection"""
        # Find the appropriate model file
        model_files = []
        for file in os.listdir(self.model_dir):
            if file.endswith('.onnx') and 'MiniFASNet' in file:
                model_files.append(file)
        
        if not model_files:
            raise FileNotFoundError(f"No MiniFASNet ONNX model found in {self.model_dir}")
        
        # Use the first available model
        model_path = os.path.join(self.model_dir, model_files[0])
        logger.info(f"Loading face anti-spoofing model: {model_path}")
        
        # Load ONNX model with onnxruntime
        self.session = ort.InferenceSession(model_path)
        logger.info("Face anti-spoofing model loaded successfully")
    
    def detect_face(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect a face in the image using OpenCV Haar cascades
        
        Args:
            image: Input image (BGR format)
        
        Returns:
            Bounding box (x, y, w, h) of the detected face, or None if no face detected
        """
        # Convert BGR to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use Haar cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(self.min_face_size, self.min_face_size),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) > 0:
            # Return the first detected face (largest if sorted by area)
            # Sort by area (w*h) in descending order and return the first one
            faces_sorted = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
            return tuple(faces_sorted[0])
        
        return None
    
    def predict(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Predict if the face in the bounding box is real or fake
        
        Args:
            image: Input image (BGR format)
            bbox: Bounding box (x, y, w, h) containing the face
        
        Returns:
            Dictionary with prediction results
        """
        x, y, w, h = bbox
        
        # Extract face region from the image
        face_roi = image[y:y+h, x:x+w]
        
        if face_roi.size == 0:
            return {
                "is_real": False,
                "confidence": 0.0,
                "label": 1,  # Fake
                "label_text": "Fake (No face ROI)"
            }
        
        # Resize face to model input size (typically 80x80 for MiniFASNet)
        face_resized = cv2.resize(face_roi, (80, 80))
        
        # Preprocess the face image for the model
        # Normalize to [0, 1] and convert to RGB
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        face_normalized = face_rgb.astype(np.float32) / 255.0
        
        # Transpose to (channels, height, width) format
        face_input = np.transpose(face_normalized, (2, 0, 1))
        
        # Add batch dimension
        face_input = np.expand_dims(face_input, axis=0)
        
        try:
            # Get input and output names
            input_name = self.session.get_inputs()[0].name
            output_name = self.session.get_outputs()[0].name
            
            # Run inference
            result = self.session.run([output_name], {input_name: face_input})
            
            # Process the result
            output = result[0][0]  # Get the first output
            
            # Apply softmax to get probabilities if needed
            exp_output = np.exp(output - np.max(output))  # Subtract max for numerical stability
            probabilities = exp_output / np.sum(exp_output)
            
            # Get the predicted label and confidence
            predicted_label = int(np.argmax(probabilities))
            confidence = float(np.max(probabilities))
            
            # Determine if it's real or fake based on your specific model
            # Based on your feedback that label 2 with high confidence should be "Real",
            # it seems your specific model has different label semantics
            # If label 2 consistently appears for real faces, we may need to adjust the logic
            is_real = (predicted_label == 2)  # Changed: assuming label 2 means real for your model
            label_text = "Real" if is_real else "Fake"
            
            return {
                "is_real": is_real,
                "confidence": confidence,
                "label": predicted_label,
                "label_text": label_text
            }
            
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            # In case of error, default to considering it as fake for security
            return {
                "is_real": False,
                "confidence": 0.0,
                "label": 1,  # Fake
                "label_text": "Fake (Inference Error)"
            }
    
    def detect_and_predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect face and predict if it's real or fake in one step
        
        Args:
            image: Input image (BGR format)
        
        Returns:
            Dictionary with detection and prediction results
        """
        # First, detect face
        bbox = self.detect_face(image)
        
        if bbox is None:
            return {
                "is_real": False,
                "confidence": 0.0,
                "label": -1,  # No face detected
                "label_text": "No face detected",
                "bbox": None
            }
        
        # If face is detected, run anti-spoofing prediction
        prediction = self.predict(image, bbox)
        prediction["bbox"] = bbox
        
        return prediction