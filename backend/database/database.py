from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from core.config import settings  # Import settings to get the PostgreSQL URL

# Changed from SQLite to PostgreSQL database
SQLALCHEMY_DATABASE_URL = settings.USER_DB_URL  # Now uses PostgreSQL URL from config

engine = create_engine(
    SQLALCHEMY_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),  # Sync engine for sessionmaker
    connect_args={}  # Removed SQLite-specific args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_database():
    """Initialize database with proper schema"""
    # Import all models to ensure they are registered with Base metadata
    from models import user, emergency_contact, travel_history, session, user_face, emergency_log, palm_template

    # Create all tables according to models (PostgreSQL version)
    Base.metadata.create_all(bind=engine)

    # PostgreSQL doesn't need PRAGMA operations like SQLite
    # Schema modifications for PostgreSQL would be handled differently if needed
    print("Database initialized with PostgreSQL")