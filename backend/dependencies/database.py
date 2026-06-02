from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_face_db

# Export the async face database dependency
async def get_face_db_dep():
    async for db in get_face_db():
        yield db