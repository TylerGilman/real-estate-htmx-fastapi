from database import engine
from models import Base
import os


def init_db():
    # Remove existing database if it exists
    if os.path.exists("real_estate.db"):
        os.remove("real_estate.db")
        print("Removed existing database")

    print("Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
