from fastapi import APIRouter
from ..routers.face_recognition import router as face_recognition_router

# Main API router that includes all sub-routers
api_router = APIRouter()

# Include all feature-specific routers
api_router.include_router(face_recognition_router, prefix="/v1", tags=["face-recognition"])

# Future routers can be added here:
# api_router.include_router(another_feature_router, prefix="/v1", tags=["another-feature"])