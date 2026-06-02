#!/usr/bin/env python3
"""
Test script for the AdaFace ONNX model.
Run this from the project root where 'models/' directory exists.
Usage: python test_model.py [optional path to a face image (112x112)]
"""

import sys
import numpy as np
import onnxruntime as ort
from pathlib import Path

MODEL_PATH = Path("models/adaface_ir18.onnx")

def load_and_inspect_model(model_path):
    """Load the ONNX model and print its input/output details."""
    print(f"Loading model from: {model_path.absolute()}")
    if not model_path.exists():
        print("❌ Model file not found. Please check the path.")
        sys.exit(1)
    
    try:
        session = ort.InferenceSession(str(model_path))
        print("✅ Model loaded successfully.\n")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        sys.exit(1)
    
    # Print inputs
    print("Model Inputs:")
    for inp in session.get_inputs():
        print(f"  Name: {inp.name}, Shape: {inp.shape}, Type: {inp.type}")
    
    # Print outputs
    print("\nModel Outputs:")
    for out in session.get_outputs():
        print(f"  Name: {out.name}, Shape: {out.shape}, Type: {out.type}")
    
    return session

def preprocess_dummy_image(height=160, width=160):
    """Create a dummy RGB image and preprocess it to the model's expected format.
    Returns: numpy array of shape (1, 3, H, W), float32, normalized to [-1, 1]."""
    # Create a random image (3, H, W) with values 0-255
    dummy = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    # Convert to float and normalize to [-1, 1]
    dummy = dummy.astype(np.float32) / 127.5 - 1.0
    # Transpose to CHW and add batch dimension
    dummy = np.transpose(dummy, (2, 0, 1))
    dummy = np.expand_dims(dummy, axis=0)
    return dummy

def preprocess_image_from_file(image_path, target_size=(112, 112)):
    """Load an image from file and preprocess it for the model."""
    try:
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not read image from {image_path}")
            sys.exit(1)
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Resize to target size
        img = cv2.resize(img, target_size)
        # Normalize to [-1, 1]
        img = img.astype(np.float32) / 127.5 - 1.0
        # Transpose and add batch dim
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img
    except ImportError:
        print("❌ opencv-python is required for loading images. Install with: pip install opencv-python")
        sys.exit(1)

def test_inference(session, input_tensor):
    """Run the model with the given input tensor and return the embedding."""
    inputs = session.get_inputs()
    output_name = session.get_outputs()[0].name
    feed_dict = {inputs[0].name: input_tensor}
    
    # Some ONNX models have a second input for batch size
    if len(inputs) > 1:
        # Try to detect batch input (often an int64 scalar)
        for inp in inputs[1:]:
            if inp.name.lower() in ["batch", "batch_size"] or inp.type == "tensor(int64)":
                feed_dict[inp.name] = np.array([input_tensor.shape[0]], dtype=np.int64)
                print(f"  Adding batch input: {inp.name} = {feed_dict[inp.name]}")
                break
    
    outputs = session.run([output_name], feed_dict)
    embedding = outputs[0]
    return embedding

if __name__ == "__main__":
    # 1. Load model and display info
    session = load_and_inspect_model(MODEL_PATH)
    
    # 2. Prepare input
    if len(sys.argv) > 1:
        # Use provided image file (ensure it's a face image)
        print(f"\nUsing image: {sys.argv[1]}")
        input_tensor = preprocess_image_from_file(sys.argv[1])
    else:
        print("\nNo image provided, using a random dummy image...")
        input_tensor = preprocess_dummy_image()
    
    print(f"Input tensor shape: {input_tensor.shape}, dtype: {input_tensor.dtype}")
    
    # 3. Run inference
    try:
        print("\nRunning inference...")
        embedding = test_inference(session, input_tensor)
        print("✅ Inference successful!")
        print(f"Embedding shape: {embedding.shape}")
        print(f"Embedding dtype: {embedding.dtype}")
        # Normalize and check
        norm = np.linalg.norm(embedding[0])
        print(f"Norm of first embedding: {norm:.4f}")
        print(f"First 5 values: {embedding[0][:5]}")
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)