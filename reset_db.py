# reset_db.py
import mysql.connector
from dotenv import load_dotenv
import os


def reset_database():
    """Reset the database using MySQL command line"""
    load_dotenv()

    # Get credentials from env
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_host = os.getenv("MYSQL_HOST")

    try:
        # Execute the reset script
        os.system(
            f"mysql -u {mysql_user} -p{mysql_password} -h {mysql_host} < sql/reset_db.sql"
        )
        print("Database reset successfully")
    except Exception as e:
        print(f"Error resetting database: {e}")


if __name__ == "__main__":
    reset_database()
