# create_auth_tables.py
import mysql.connector
from dotenv import load_dotenv
import os


def create_auth_tables():
    load_dotenv()

    config = {
        "host": os.getenv("MYSQL_HOST"),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Read and execute the SQL file
        with open("sql/create_auth_tables.sql", "r") as file:
            sql_commands = file.read()

        # Split and execute multiple commands if necessary
        for command in sql_commands.split(";"):
            if command.strip():
                cursor.execute(command)

        conn.commit()
        print("Authentication tables created successfully")

    except Exception as e:
        print(f"Error creating tables: {e}")

    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    create_auth_tables()
