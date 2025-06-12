from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Clerk user ID
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    queries = relationship("Query", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    question = Column(Text)
    response = Column(Text)
    documents_used = Column(Text)  # JSON string of document references
    created_at = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float)  # in seconds

    # Relationships
    user = relationship("User", back_populates="queries")
    feedback = relationship("Feedback", back_populates="query")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    query_id = Column(Integer, ForeignKey("queries.id"))
    rating = Column(Integer)  # 1-5 stars
    is_helpful = Column(Boolean)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="feedback")
    query = relationship("Query", back_populates="feedback")
