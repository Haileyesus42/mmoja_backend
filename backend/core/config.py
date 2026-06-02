import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Changed from SQLite to PostgreSQL for user data
    USER_DB_URL = os.getenv("USER_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition")
    FACE_DB_URL = os.getenv("FACE_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition")  # Restore asyncpg
    MODEL_PATH = os.getenv("MODEL_PATH", "models/adaface_ir18.onnx")
    EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE", "512"))
    IMAGE_SIZE = tuple(map(int, os.getenv("IMAGE_SIZE", "160,160").split(",")))
    FACE_DETECTION_THRESHOLD = float(os.getenv("FACE_DETECTION_THRESHOLD", "0.7"))

settings = Settings()