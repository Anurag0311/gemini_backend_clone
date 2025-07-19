from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import os
load_dotenv()

SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")

sync_engine = create_engine(SYNC_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()