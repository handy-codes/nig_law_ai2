from config.database import Base, engine
from models.database_models import User, Query, Feedback

if __name__ == "__main__":
    print("Creating all tables (users, Query, Feedback) in the database...")
    Base.metadata.create_all(engine)
    print("All tables created successfully!")
