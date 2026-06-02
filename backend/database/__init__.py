from database.database import Base, engine

def init_db():
    """Initialize database by creating all tables"""
    # Import models inside the function to avoid circular imports
    from models.user import User
    from models.emergency_contact import EmergencyContact
    from models.travel_history import TravelHistory
    from models.session import UserSession
    from models.emergency_log import EmergencyLog
    Base.metadata.create_all(bind=engine)