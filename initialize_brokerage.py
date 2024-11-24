import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os


def initialize_brokerage():
    # Load environment variables from .env file
    load_dotenv()

    # Database connection configuration from .env file
    config = {
        "host": os.getenv("MYSQL_HOST"),
        "port": os.getenv("MYSQL_PORT"),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }

    # Brokerage information
    brokerage_data = {
        "broker_name": "Cherokee Street Real Estate",
        "broker_address": "25 Cherokee St, Boston, MA",
        "broker_phone": "555-123-4567",
        "broker_email": "contact@cherokeerealestate.com",
        "broker_license": "LIC-2023-001",
    }

    try:
        # Connect to the database
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            print("Connected to the database")

            cursor = connection.cursor()

            # Insert brokerage record
            brokerage_insert_query = """
                INSERT INTO Brokerage (broker_name, broker_address, broker_phone, broker_email, broker_license)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(brokerage_insert_query, tuple(brokerage_data.values()))
            connection.commit()

            print("Brokerage initialized successfully. ID:", cursor.lastrowid)

    except Error as e:
        print("Error:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")


# Run the initialization
initialize_brokerage()
