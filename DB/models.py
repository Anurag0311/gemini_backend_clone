from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, TIMESTAMP, DateTime, Float, Enum, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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
    subscription_type = Column(String(10), default='basic')
    expiration_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Chatroom(Base):
    __tablename__ = "chatroom"

    id = Column(Integer, primary_key=True, index=True)
    chatroom_id = Column(String, nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("ChatroomHistory", back_populates="chatroom", cascade="all, delete")

class ChatroomHistory(Base):
    __tablename__ = "chatroom_history"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(ForeignKey("chatroom.id"), nullable=False)
    request_message = Column(Text, nullable=True)
    response_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    chatroom = relationship("Chatroom", back_populates="messages")


    