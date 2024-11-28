# app/core/database.py
from mysql.connector import connect, Error, pooling
from .config import settings
from .logging_config import logger
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": settings.MYSQL_HOST,
    "user": settings.MYSQL_USER,
    "password": settings.MYSQL_PASSWORD,
    "port": settings.MYSQL_PORT,
    "database": settings.MYSQL_DATABASE,
    "charset": "utf8mb4",
    "use_unicode": True,
    "get_warnings": True,
    "autocommit": False,  # We'll handle transactions explicitly
    "raise_on_warnings": True,
}

# Connection pool configuration
POOL_CONFIG = {"pool_name": "mypool", "pool_size": 5, "pool_reset_session": True}


def create_mysql_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect without database selected
        conn = connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
        )
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE}")
        logger.info(f"Database '{settings.MYSQL_DATABASE}' ensured.")

        # Create tables if they don't exist
        cursor.execute(f"USE {settings.MYSQL_DATABASE}")
        init_tables(cursor)

        conn.commit()
        logger.info("Database initialization completed successfully.")
    except Error as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


def init_tables(cursor):
    """Initialize database tables"""
    try:
        # Read and execute the SQL schema file
        schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
        with open(schema_path, "r") as f:
            schema = f.read()

        # Split and execute each statement
        for statement in schema.split(";"):
            if statement.strip():
                cursor.execute(statement)

        logger.info("Database tables initialized successfully.")
    except Error as e:
        logger.error(f"Error initializing tables: {e}")
        raise


# Create connection pool
try:
    pool = pooling.MySQLConnectionPool(**POOL_CONFIG, **DB_CONFIG)
    logger.info("Database connection pool created successfully.")
except Error as e:
    logger.error(f"Error creating connection pool: {e}")
    raise


@contextmanager
def get_db_connection():
    """Get a database connection from the pool"""
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
        conn.commit()
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_procedure(conn, procedure_name: str, params: tuple = ()):
    """Execute a stored procedure"""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(procedure_name, params)

        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())

        return results
    except Error as e:
        logger.error(f"Error executing procedure {procedure_name}: {e}")
        raise
    finally:
        cursor.close()


def execute_query(conn, query: str, params: tuple = ()):
    """Execute a SQL query"""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)

        if cursor.with_rows:
            return cursor.fetchall()
        return None
    except Error as e:
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        cursor.close()


def reset_db():
    """Reset the database (drop and recreate all tables)"""
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()

            # Read and execute the reset SQL file
            reset_path = os.path.join(
                os.path.dirname(__file__), "..", "sql", "reset.sql"
            )
            with open(reset_path, "r") as f:
                reset_sql = f.read()

            # Split and execute each statement
            for statement in reset_sql.split(";"):
                if statement.strip():
                    cursor.execute(statement)

            conn.commit()
            logger.info("Database reset successfully.")
        except Error as e:
            logger.error(f"Error resetting database: {e}")
            raise
        finally:
            cursor.close()


# Health check function
async def check_db_connection():
    """Check if database connection is healthy"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result is not None
    except Error:
        return False
