from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .config import settings
import logging
import mysql.connector
from mysql.connector import Error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mysql_database():
    """Create the database if it doesn't exist"""
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE}")
        logger.info(f"Database '{settings.MYSQL_DATABASE}' ensured.")
        
        conn.close()
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise

# Database URL
DATABASE_URL = (
    f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database"""
    try:
        # Create database if it doesn't exist
        create_mysql_database()
        
        # Import all models here
        from app.models.base import Base
        from app.models.property import Property, ResidentialProperty, CommercialProperty
        from app.models.agent import Agent, Brokerage
        from app.models.client import Client, ClientRoles
        from app.models.transaction import AgentListing, AgentShowing, Contract, Transaction
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def reset_db():
    """Reset the database (drop all tables and recreate)"""
    try:
        # Import all models
        from app.models.base import Base
        from app.models.property import Property, ResidentialProperty, CommercialProperty
        from app.models.agent import Agent, Brokerage
        from app.models.client import Client, ClientRoles
        from app.models.transaction import AgentListing, AgentShowing, Contract, Transaction
        
        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully.")
        
        # Recreate all tables
        logger.info("Recreating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables recreated successfully.")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise
