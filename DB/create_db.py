import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
