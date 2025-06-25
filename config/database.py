from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Sanity check for debugging
if DATABASE_URL is None:
    raise ValueError("❌ DATABASE_URL is not set. Please check your .env file.")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a sessionmaker factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declaring ORM models
Base = declarative_base()

# Dependency for getting a DB session in other modules
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()






# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Get database URL from environment variable
# DATABASE_URL = os.getenv("DATABASE_URL")

# # Create SQLAlchemy engine with explicit PostgreSQL dialect
# engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# # Create SessionLocal class
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Create Base class
# Base = declarative_base()

# # Dependency to get DB session


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
