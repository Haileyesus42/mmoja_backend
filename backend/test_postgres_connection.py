#!/usr/bin/env python3
"""
Test script to verify PostgreSQL connectivity after migration
"""

import asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import text  # Import text for raw SQL queries
from core.config import settings
from core.database import init_user_db_sync

def test_postgres_connection():
    """Test basic PostgreSQL connectivity"""
    print("Testing PostgreSQL connection...")
    
    # Create sync engine for testing
    sync_engine = create_engine(
        settings.USER_DB_URL.replace("postgresql+asyncpg://", "postgresql://"),
        connect_args={}
    )
    
    try:
        # Test the connection
        with sync_engine.connect() as connection:
            print("✅ Successfully connected to PostgreSQL database")
            
            # Execute a simple query using text()
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"PostgreSQL version: {version[:50]}...")
        
        # Test creating a session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        db = SessionLocal()
        
        # Try to count users (should work if tables exist)
        from models.user import User
        user_count = db.query(User).count()
        print(f"✅ Found {user_count} users in the database")
        
        db.close()
        print("✅ PostgreSQL connection test completed successfully")
        
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_user_data():
    """Test that user data exists in PostgreSQL"""
    print("\nTesting user data access...")
    
    sync_engine = create_engine(
        settings.USER_DB_URL.replace("postgresql+asyncpg://", "postgresql://"),
        connect_args={}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db = SessionLocal()
    
    try:
        # Test accessing users
        from models.user import User
        users = db.query(User).all()
        print(f"✅ Retrieved {len(users)} users from PostgreSQL")
        
        for user in users:
            print(f"  - User: {user.username} ({user.full_name})")
        
        # Test accessing emergency contacts
        from models.emergency_contact import EmergencyContact
        contacts = db.query(EmergencyContact).all()
        print(f"✅ Retrieved {len(contacts)} emergency contacts from PostgreSQL")
        
        # Test accessing travel history
        from models.travel_history import TravelHistory
        travels = db.query(TravelHistory).all()
        print(f"✅ Retrieved {len(travels)} travel history records from PostgreSQL")
        
        db.close()
        print("✅ User data access test completed successfully")
        
    except Exception as e:
        print(f"❌ Error accessing user data: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False
    
    return True

if __name__ == "__main__":
    print("PostgreSQL Connection Test")
    print("="*30)
    
    success = test_postgres_connection()
    if success:
        success = test_user_data()
    
    if success:
        print("\n🎉 All tests passed! PostgreSQL migration is working correctly.")
    else:
        print("\n❌ Tests failed! Please check your PostgreSQL configuration.")