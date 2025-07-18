from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, TIMESTAMP, DateTime, Float, Enum, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class UserDetails(Base):
    __tablename__= 'user_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    subscription_type = Column(String, nullable = False, default='basic')
    updated_at = Column(DateTime, onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    


    