import os
import subprocess
from dotenv import load_dotenv


def run_sql_file(file_path, mysql_user, mysql_password, mysql_host, mysql_db):
    """Execute an SQL file using the MySQL CLI."""
    try:
        print(f"Executing SQL file: {file_path}")
        sql_dir = os.path.dirname(file_path)  # Ensure correct working directory
        command = f"mysql -u {mysql_user} -p{mysql_password} -h {mysql_host} {mysql_db} < {file_path}"
        subprocess.run(command, shell=True, check=True, cwd=sql_dir)
        print(f"Executed {file_path} successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {file_path}: {e}")


def reset_database():
    """Reset the database and initialize procedures."""
    load_dotenv()

    # Retrieve database credentials from environment
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_db = os.getenv("MYSQL_DATABASE", "real_estate")

    # Paths to SQL directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reset_script = os.path.join(base_dir, "../sql/reset_db.sql")
    procedures_dir = os.path.join(base_dir, "../sql/procedures")

    try:
        print("Resetting database...")
        # Execute the main reset script
        run_sql_file(reset_script, mysql_user, mysql_password, mysql_host, mysql_db)
        print("Database reset completed successfully.")

        # Execute all procedure SQL files
        if os.path.isdir(procedures_dir):
            for sql_file in sorted(os.listdir(procedures_dir)):
                if sql_file.endswith(".sql"):
                    file_path = os.path.join(procedures_dir, sql_file)
                    run_sql_file(
                        file_path, mysql_user, mysql_password, mysql_host, mysql_db
                    )
            print("All procedures initialized successfully.")
        else:
            print(f"Procedures directory not found: {procedures_dir}")

    except Exception as e:
        print(f"Unexpected error during database reset: {e}")


if __name__ == "__main__":
    reset_database()
