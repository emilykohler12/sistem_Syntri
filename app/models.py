from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())
    
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="messages")
    deliveries = relationship("MessageDelivery", back_populates="message")

class MessageDelivery(Base):
    __tablename__ = "message_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    service = Column(String, nullable=False)
    status = Column(String, default="pending")
    provider_response = Column(Text)
    
    message = relationship("Message", back_populates="deliveries")