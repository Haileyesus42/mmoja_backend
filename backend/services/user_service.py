from sqlalchemy.orm import Session
from models.user import User
from schemas.schemas import UserCreate
import hashlib

def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    # Hash the input password to compare with stored hash
    hashed_input_password = hashlib.sha256(password.encode()).hexdigest()
    if user.password != hashed_input_password:
        return None
    return user

def create_mock_users(db: Session):
    """Create mock users if they don't exist"""
    # Check if users already exist
    if db.query(User).count() > 0:
        return
    
    # Create User 1: haile
    user1 = User(
        username="haile",
        password=hashlib.sha256("1234".encode()).hexdigest(),  # Hash the password
        full_name="Haile Selassie",
        address="123 Bole Road, Addis Ababa",
        phone="+251911234567",
        email="haile@example.com",
        current_city="Addis Ababa",
        current_country="Ethiopia",
        hotel_name="Sheraton Addis",
        current_location="Bale Mountains National Park",
        gps_latitude="6.6667",
        gps_longitude="39.8333"
    )
    
    # Create User 2: traveler1
    user2 = User(
        username="traveler1",
        password=hashlib.sha256("1234".encode()).hexdigest(),  # Hash the password
        full_name="John Traveler",
        address="456 Main Street, New York",
        phone="+12125551234",
        email="traveler1@example.com",
        current_city="New York",
        current_country="USA",
        hotel_name="Marriott Marquis",
        current_location="Central Park, New York",
        gps_latitude="40.7812",
        gps_longitude="-73.9665"
    )
    
    db.add(user1)
    db.add(user2)
    db.commit()