import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_enroll():
    """Test the enroll endpoint"""
    url = f"{BASE_URL}/enroll"
    
    # Prepare a sample image file for testing
    with open("test_image.jpg", "rb") as f:
        files = {"file": ("test_image.jpg", f, "image/jpeg")}
        data = {
            "user_id": "test_user_123",
            "name": "Test User"
        }
        
        response = requests.post(url, files=files, data=data)
        
    print("Enroll Response:", response.json())
    return response.json()

def test_verify():
    """Test the verify endpoint"""
    url = f"{BASE_URL}/verify"
    
    # Prepare a sample image file for testing
    with open("test_image.jpg", "rb") as f:
        files = {"file": ("test_image.jpg", f, "image/jpeg")}
        
        response = requests.post(url, files=files)
        
    print("Verify Response:", response.json())
    return response.json()

if __name__ == "__main__":
    print("Testing Face Recognition API...")
    
    # Note: These tests will fail if no image exists at test_image.jpg
    # and if the server is not running
    try:
        test_enroll()
        test_verify()
    except FileNotFoundError:
        print("Test image not found. Please place a test image named 'test_image.jpg' in the root directory.")
    except requests.exceptions.ConnectionError:
        print("Could not connect to the API server. Please make sure the server is running.")