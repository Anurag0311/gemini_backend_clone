from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, TIMESTAMP, DateTime, Float, Enum, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Authentication
    mobile = Column(String(15), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # only needed for change password
    # Optional Info
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    # Account State
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # set True after OTP verify
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())




    