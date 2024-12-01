import os
import subprocess
from dotenv import load_dotenv

def run_sql_file(file_path, mysql_user, mysql_password, mysql_host, mysql_db):
    """Execute an SQL file using the MySQL CLI."""
    try:
        print(f"Executing SQL file: {file_path}")
        
        # Get the SQL directory path
        sql_dir = os.path.dirname(file_path)
        
        # Change to SQL directory for relative paths to work
        original_dir = os.getcwd()
        os.chdir(sql_dir)
        
        try:
            command = f"mysql -u {mysql_user} -p{mysql_password} -h {mysql_host} {mysql_db} < {os.path.basename(file_path)}"
            subprocess.run(command, shell=True, check=True)
            print(f"Executed {file_path} successfully.")
        finally:
            # Change back to original directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing {file_path}: {e}")
        raise

def reset_database():
    """Reset the database and initialize procedures."""
    load_dotenv()

    # Retrieve database credentials from environment
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_db = os.getenv("MYSQL_DATABASE", "real_estate")

    # Get absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_dir = os.path.join(base_dir, "sql")
    reset_script = os.path.join(sql_dir, "reset_db.sql")

    try:
        print("Starting database reset...")
        print(f"Using SQL directory: {sql_dir}")
        
        # Execute the reset script
        run_sql_file(reset_script, mysql_user, mysql_password, mysql_host, mysql_db)
        
        print("Database reset completed successfully!")

    except Exception as e:
        print(f"Error during database reset: {str(e)}")
        raise

if __name__ == "__main__":
    reset_database()
