from sqlalchemy.orm import Session
from models.database_models import Query, Feedback
from datetime import datetime
import json


def log_query(db: Session, user_id: str, question: str, response: str, documents_used: list = None, response_time: float = None):
    """Log a query and its response to the database."""
    query = Query(
        user_id=user_id,
        question=question,
        response=response,
        documents_used=json.dumps(documents_used) if documents_used else None,
        response_time=response_time,
        created_at=datetime.utcnow()
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


def log_feedback(db: Session, user_id: str, query_id: int, rating: int, is_helpful: bool, feedback_text: str = None):
    """Log user feedback for a query."""
    feedback = Feedback(
        user_id=user_id,
        query_id=query_id,
        rating=rating,
        is_helpful=is_helpful,
        feedback_text=feedback_text,
        created_at=datetime.utcnow()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_user_queries(db: Session, user_id: str, limit: int = 10):
    """Get recent queries for a user."""
    return db.query(Query).filter(Query.user_id == user_id).order_by(Query.created_at.desc()).limit(limit).all()


def get_query_feedback(db: Session, query_id: int):
    """Get feedback for a specific query."""
    return db.query(Feedback).filter(Feedback.query_id == query_id).first()
