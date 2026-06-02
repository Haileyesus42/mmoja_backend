#!/usr/bin/env python3
"""
Script to recreate all database tables for the FPAS application.
This will create the users, user_faces, emergency_contacts, and other required tables.
"""

import asyncio
from core.database import init_user_db_sync, init_face_db
from database.database import initialize_database
from services.user_service import create_mock_users
from services.contact_service import create_mock_emergency_contacts
from services.travel_service import create_mock_travel_history
from database.database import SessionLocal

async def recreate_face_db():
    """Async wrapper for face database initialization"""
    await init_face_db()

def recreate_all_tables():
    print("🔄 Initializing user database...")
    init_user_db_sync()
    print("✅ User database tables created!")
    
    print("\n🔄 Initializing face recognition database...")
    # Run the async function in an event loop
    asyncio.run(recreate_face_db())
    print("✅ Face recognition tables created!")
    
    print("\n🔄 Initializing main database...")
    initialize_database()
    print("✅ Main database tables created!")
    
    # Optionally, recreate mock data
    print("\n🔄 Creating mock users...")
    db = SessionLocal()
    try:
        create_mock_users(db)
        print("✅ Mock users created!")
        
        print("\n🔄 Creating mock emergency contacts...")
        create_mock_emergency_contacts(db)
        print("✅ Mock emergency contacts created!")
        
        print("\n🔄 Creating mock travel history...")
        create_mock_travel_history(db)
        print("✅ Mock travel history created!")
    finally:
        db.close()
    
    print("\n🎉 All tables have been successfully recreated!")
    print("\n📋 Tables created:")
    print("   - users (user accounts)")
    print("   - user_faces (face recognition data)")
    print("   - emergency_contacts")
    print("   - emergency_logs")
    print("   - travel_histories")
    print("   - user_sessions")
    print("   - palm_templates (palm recognition data)")
    print("\n💡 You can now enroll faces and use the application normally.")

if __name__ == "__main__":
    recreate_all_tables()