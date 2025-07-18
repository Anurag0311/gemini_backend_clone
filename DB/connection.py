from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL =  os.getenv("DATABASE_URL")


engine = create_async_engine(DATABASE_URL, echo=True)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# db_dependency = Annotated[AsyncSession, Depends(get_db)]