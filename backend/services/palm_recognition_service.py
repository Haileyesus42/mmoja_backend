import os
import sys
import numpy as np
import cv2
import torch
import torchvision.models as models
import time
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import pickle
from datetime import datetime

# Add the backend directory to the path to ensure imports work correctly
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Import palm recognition modules from local palm_utils directory
from palm_utils.preprocessor import preprocess_image
from palm_utils.cosine_similarity import calculate_similarity

# Import database models
from models.user import User
from models.palm_template import PalmTemplate
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PalmRecognitionService:
    def __init__(self, model_path: str = "onnx/palmprint_encoder.pth"):
        """Initialize the palm recognition service with the trained model"""
        # Create the encoder model architecture (ResNet-18 without the final classification layer)
        resnet = models.resnet18(pretrained=True)
        self.encoder = torch.nn.Sequential(*list(resnet.children())[:-1])  # Remove the last FC layer

        # Load the trained encoder weights
        self.encoder.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        self.encoder.eval()  # Set to evaluation mode
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder.to(self.device)
        
        logger.info(f"Palm recognition service initialized on device: {self.device}")

    def extract_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extract features from a palm image using the trained encoder
        """
        # Preprocess the image
        preprocessed_roi = preprocess_image(image_path)
        
        if preprocessed_roi is None:
            return None
        
        # Add batch and channel dimensions
        preprocessed_roi = np.expand_dims(preprocessed_roi, axis=0)
        preprocessed_roi = torch.from_numpy(preprocessed_roi).float().repeat(1, 3, 1, 1).to(self.device)
        
        with torch.no_grad():
            features = self.encoder(preprocessed_roi)  # Get encoded features
            features = features.flatten(1)  # Flatten to get 512-dimensional vector
            features = features.cpu().numpy().flatten()  # Convert to numpy array
        
        return features

    def enroll_palm_for_user(self, db: Session, user_id: int, username: str, image_path: str) -> Tuple[bool, str]:
        """
        Enroll a palm for a specific user in the database
        """
        features = self.extract_features(image_path)
        
        if features is None:
            return False, "Could not extract features from the palm image"
        
        # Convert features to binary for storage
        features_binary = pickle.dumps(features)
        
        # Check if user already has a palm template
        existing_template = db.query(PalmTemplate).filter(PalmTemplate.user_id == user_id).first()
        
        if existing_template:
            # Update existing template
            existing_template.palm_features = features_binary
            existing_template.updated_at = datetime.utcnow().isoformat()
        else:
            # Create new palm template
            palm_template = PalmTemplate(
                user_id=user_id,
                palm_features=features_binary,
                created_at=datetime.utcnow().isoformat()
            )
            db.add(palm_template)
        
        db.commit()
        return True, f"Palm enrolled successfully for user: {username}"

    def verify_palm_for_user(self, db: Session, user_id: int, username: str, image_path: str, threshold: float = 0.82) -> Tuple[bool, float, str]:
        """
        Verify a palm specifically for a given user against the database
        """
        features = self.extract_features(image_path)
        
        if features is None:
            return False, 0.0, "Could not extract features from the palm image"
        
        # Get the enrolled palm template for this user
        palm_template = db.query(PalmTemplate).filter(PalmTemplate.user_id == user_id).first()
        
        if not palm_template:
            return False, 0.0, f"No palm enrolled for user: {username}"
        
        # Load stored features
        stored_features = pickle.loads(palm_template.palm_features)
        
        # Calculate similarity
        similarity_scores = calculate_similarity(features, stored_features.reshape(1, -1))
        score = similarity_scores[0]
        
        if score >= threshold:
            return True, score, f"Verified! Palm matches user: {username}"
        else:
            return False, score, f"Palm does not match enrolled palm for user: {username}"

    def verify_any_palm(self, db: Session, image_path: str, threshold: float = 0.82) -> Tuple[Optional[str], float, str, Optional[int]]:
        """
        Verify a palm against all enrolled palms in the database
        Returns the best match username, similarity score, status message, and user_id
        """
        features = self.extract_features(image_path)
        
        if features is None:
            return None, 0.0, "Could not extract features from the palm image", None
        
        # Get all palm templates from the database
        palm_templates = db.query(PalmTemplate).all()
        
        if not palm_templates:
            return None, 0.0, "No enrolled palms to verify against", None
        
        best_match_username = None
        best_match_user_id = None
        best_score = 0.0
        
        for template in palm_templates:
            # Load stored features
            stored_features = pickle.loads(template.palm_features)
            
            # Calculate similarity
            similarity_scores = calculate_similarity(features, stored_features.reshape(1, -1))
            score = similarity_scores[0]
            
            if score > best_score:
                best_score = score
                
                # Get the username for this user
                user = db.query(User).filter(User.id == template.user_id).first()
                if user:
                    best_match_username = user.username
                    best_match_user_id = template.user_id
        
        if best_score >= threshold:
            return best_match_username, best_score, f"Verified! Match found: {best_match_username}", best_match_user_id
        else:
            return None, best_score, f"No match found above threshold. Best candidate: Unknown palm", None

    def enroll_palm(self, name: str, image_path: str) -> Tuple[bool, str]:
        """
        Enroll a palm with the given name using the image file (legacy method)
        """
        features = self.extract_features(image_path)
        
        if features is None:
            return False, "Could not extract features from the palm image"
        
        self.enrolled_palms[name] = features
        return True, f"Palm enrolled successfully with name: {name}"

    def verify_palm(self, image_path: str, threshold: float = 0.82) -> Tuple[Optional[str], float, str]:
        """
        Verify a palm against enrolled palms (legacy method)
        Returns the best match name, similarity score, and status message
        """
        return self.verify_any_palm(image_path, threshold)

    def get_enrolled_count(self) -> int:
        """Get the number of enrolled palms"""
        return len(self.enrolled_palms)

    def get_enrolled_names(self) -> list:
        """Get a list of enrolled palm names"""
        return list(self.enrolled_palms.keys())