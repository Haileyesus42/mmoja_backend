from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_user_db  # Changed to use PostgreSQL database dependency
from schemas.schemas import UserResponse, UserUpdate, UserCreate
from routers.auth_routes import get_current_user
from models.user import User
from services.user_service import get_user_by_username
import hashlib

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_user_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password before storing
    hashed_password = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    # Create new user
    user = User(
        username=user_data.username,
        password=hashed_password,  # Store hashed password
        full_name=getattr(user_data, 'full_name', ''),
        address=getattr(user_data, 'address', ''),
        phone=getattr(user_data, 'phone', ''),
        email=getattr(user_data, 'email', ''),
        current_city=getattr(user_data, 'current_city', ''),
        current_country=getattr(user_data, 'current_country', ''),
        hotel_name=getattr(user_data, 'hotel_name', ''),
        current_location=getattr(user_data, 'current_location', ''),
        gps_latitude=getattr(user_data, 'gps_latitude', ''),
        gps_longitude=getattr(user_data, 'gps_longitude', '')
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "address": user.address,
            "phone": user.phone,
            "email": user.email,
            "current_city": user.current_city,
            "current_country": user.current_country,
            "hotel_name": user.hotel_name,
            "current_location": user.current_location,
            "gps_latitude": user.gps_latitude,
            "gps_longitude": user.gps_longitude
        }
    }

@router.get("/profile")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_user_db)  # Changed dependency
):
    """Get current user profile"""
    user = current_user  # Use the user from dependency injection
    
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "address": user.address,
        "phone": user.phone,
        "email": user.email,
        "current_city": user.current_city,
        "current_country": user.current_country,
        "hotel_name": user.hotel_name,
        "current_location": user.current_location,
        "gps_latitude": user.gps_latitude,
        "gps_longitude": user.gps_longitude
    }

@router.put("/profile")
def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_user_db)  # Changed dependency
):
    """Update user profile"""
    user = current_user  # Use the user from dependency injection
    
    # Update fields if provided
    if profile_data.full_name is not None:
        user.full_name = profile_data.full_name
    if profile_data.address is not None:
        user.address = profile_data.address
    if profile_data.phone is not None:
        user.phone = profile_data.phone
    if profile_data.email is not None:
        user.email = profile_data.email
    if profile_data.current_city is not None:
        user.current_city = profile_data.current_city
    if profile_data.current_country is not None:
        user.current_country = profile_data.current_country
    if profile_data.hotel_name is not None:
        user.hotel_name = profile_data.hotel_name
    if profile_data.current_location is not None:
        user.current_location = profile_data.current_location
    if profile_data.gps_latitude is not None:
        user.gps_latitude = profile_data.gps_latitude
    if profile_data.gps_longitude is not None:
        user.gps_longitude = profile_data.gps_longitude
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "address": user.address,
            "phone": user.phone,
            "email": user.email,
            "current_city": user.current_city,
            "current_country": user.current_country,
            "hotel_name": user.hotel_name,
            "current_location": user.current_location,
            "gps_latitude": user.gps_latitude,
            "gps_longitude": user.gps_longitude
        }
    }