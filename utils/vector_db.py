import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import VARCHAR
from pgvector.sqlalchemy import Vector
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # Your Render PostgreSQL URL

print("DATABASE_URL in use:", DATABASE_URL)

Base = declarative_base()


class LegalChunk(Base):
    __tablename__ = "legal_chunks"
    id = sa.Column(sa.Integer, primary_key=True)
    text = sa.Column(sa.Text, nullable=False)
    source = sa.Column(VARCHAR(256), nullable=True)
    # 384 for MiniLM, adjust if you use another model
    embedding = sa.Column(Vector(384))


engine = sa.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Register the vector type with psycopg2
with engine.connect() as conn:
    raw_conn = conn.connection
    register_vector(raw_conn, "vector")

model = SentenceTransformer('all-MiniLM-L6-v2')  # Load model once


def create_tables():
    Base.metadata.create_all(engine)


def add_chunk(text, source=None):
    embedding = model.encode([text])[0]  # numpy array
    session = SessionLocal()
    chunk = LegalChunk(text=text, source=source, embedding=embedding)
    session.add(chunk)
    session.commit()
    session.close()


def search_chunks(query, k=5):
    embedding = model.encode([query])[0]  # numpy array, not list
    session = SessionLocal()
    results = session.execute(
        sa.text(
            "SELECT id, text, source FROM legal_chunks ORDER BY embedding <-> :embedding LIMIT :k"
        ),
        {"embedding": embedding, "k": k}
    ).fetchall()
    session.close()
    return results
