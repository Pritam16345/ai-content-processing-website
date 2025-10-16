# backend/models.py (User Accounts Update)

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    sources = relationship("ContentSource", back_populates="owner")

class ContentSource(Base):
    __tablename__ = "content_sources"
    id = Column(Integer, primary_key=True, index=True)
    source_identifier = Column(String, index=True)
    title = Column(String, nullable=True)
    source_type = Column(String)
    content = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="sources")