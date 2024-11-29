# app/core/security.py
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from mysql.connector import Error, MySQLConnection
from .database import get_db_connection, execute_procedure
from .logging_config import logger
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Initialize security settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(
    request: Request,
    conn: MySQLConnection = Depends(get_db_connection)
) -> Optional[Dict[str, Any]]:
    """Get current user using stored procedures"""
    try:
        # Check if user is authenticated via session
        username = request.session.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Handle admin from environment
        if username == os.getenv("ADMIN_USERNAME"):
            admin_role = execute_procedure(conn, 'get_or_create_admin_role')
            if admin_role:
                return {
                    "username": username,
                    "role_name": "admin",
                    "role_id": admin_role[0]['role_id'],
                    "agent_id": None
                }

        # Get database user
        user = execute_procedure(conn, 'get_user_by_username', (username,))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user[0]

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: MySQLConnection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Get current admin user"""
    try:
        # First check if it's the env admin
        if current_user["username"] == os.getenv("ADMIN_USERNAME"):
            return current_user
        
        # Otherwise check database role
        role = execute_procedure(conn, 'check_user_role', (current_user["username"], "admin"))
        if not role or not role[0].get("is_role"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return current_user
    except Exception as e:
        logger.error(f"Admin verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access verification failed"
        )

async def get_current_agent(
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: MySQLConnection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Get current agent user"""
    try:
        # Check agent role
        role = execute_procedure(conn, 'check_user_role', (current_user["username"], "agent"))
        if not role or not role[0].get("is_role"):
            return RedirectResponse(url="/login", status_code=303)

        # Get agent details
        agent_details = execute_procedure(conn, 'get_agent_details', (current_user["user_id"],))
        if not agent_details:
            return RedirectResponse(url="/login", status_code=303)

        return {
            "user": current_user,
            "agent": agent_details[0]
        }
    except Exception as e:
        logger.error(f"Agent verification error: {str(e)}")
        return RedirectResponse(url="/login", status_code=303)
