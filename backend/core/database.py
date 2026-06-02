from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .config import settings  # Fix import path

# User database engine (PostgreSQL) - async engine (changed from SQLite)
user_engine = create_async_engine(settings.USER_DB_URL)

# Synchronous engines for user database (needed for non-async operations)
sync_user_engine = create_engine(settings.USER_DB_URL.replace("postgresql+asyncpg://", "postgresql://"))  
user_sync_session = sessionmaker(autocommit=False, autoflush=False, bind=sync_user_engine)

# Face recognition database engine (PostgreSQL) - async engine
face_engine = create_async_engine(settings.FACE_DB_URL)

# Synchronous engines for face recognition service (needed for the pgvector operations)
sync_face_engine = create_engine(settings.FACE_DB_URL.replace("postgresql+asyncpg://", "postgresql://"))  
sync_face_session = sessionmaker(autocommit=False, autoflush=False, bind=sync_face_engine)


def get_user_db():
    db = user_sync_session()
    try:
        yield db
    finally:
        db.close()


async def get_face_db():
    async with AsyncSession(face_engine, expire_on_commit=False) as session:
        yield session


def get_sync_face_db():
    db = sync_face_session()
    try:
        yield db
    finally:
        db.close()


async def init_user_db():
    """Initialize the user database and create tables (async version)"""
    from models import user, emergency_contact, travel_history, session, emergency_log, palm_template  # Import all user-related models to register them
    from database.database import Base  # Use the same Base as models
    async with user_engine.begin() as conn:
        from sqlalchemy import text
        # Create tables
        await conn.run_sync(lambda conn: Base.metadata.create_all(conn))


def init_user_db_sync():
    """Initialize the user database and create tables (sync version)"""
    from models import user, emergency_contact, travel_history, session, emergency_log, palm_template  # Import all user-related models to register them
    from database.database import Base  # Use the same Base as models
    Base.metadata.create_all(bind=sync_user_engine)


async def init_face_db():
    """Initialize the face recognition database and create tables"""
    from models.user_face import FaceBase  # Import face-specific Base
    async with face_engine.begin() as conn:
        from pgvector.sqlalchemy import Vector  # Import here to ensure pgvector is loaded
        from sqlalchemy import text
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create tables
        await conn.run_sync(lambda conn: FaceBase.metadata.create_all(conn))