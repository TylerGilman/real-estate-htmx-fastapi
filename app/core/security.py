# app/core/security.py
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from mysql.connector import Error

from app.database import get_db_connection, execute_procedure
from ..core.logging_config import logger
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import jwt

load_dotenv()

# Initialize security settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class SecurityError(Exception):
    """Custom security exception"""

    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user(
    request: Request, conn=Depends(get_db_connection)
) -> Optional[Dict[str, Any]]:
    """Get current user using stored procedures"""
    try:
        # Check session authentication
        username = request.session.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        # Handle admin from environment
        if username == os.getenv("ADMIN_USERNAME"):
            admin_role = await execute_procedure(conn, "get_or_create_admin_role", ())
            if not admin_role:
                raise HTTPException(
                    status_code=500, detail="Failed to get or create admin role"
                )

            return {
                "username": username,
                "role_id": admin_role[0]["role_id"],
                "role_name": "admin",
                "agent_id": None,
            }

        # Get user details and verify
        user = await call_procedure(conn, "get_user_by_username", (username,))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Log access
        await call_procedure(
            conn, "log_user_access", (user[0]["user_id"], request.client.host)
        )

        return user[0]

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn=Depends(get_db_connection),
) -> Dict[str, Any]:
    """Get current admin user with role verification"""
    try:
        # Check env admin
        if current_user["username"] == os.getenv("ADMIN_USERNAME"):
            return current_user

        # Verify admin role
        is_admin = await call_procedure(
            conn, "check_user_role", (current_user["username"], "admin")
        )

        if not is_admin or not is_admin[0].get("is_role"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        # Log admin access
        await call_procedure(
            conn, "log_admin_access", (current_user["user_id"], request.client.host)
        )

        return current_user

    except Exception as e:
        logger.error(f"Admin verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access verification failed",
        )


async def get_current_agent(
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn=Depends(get_db_connection),
) -> Dict[str, Any]:
    """Get current agent user with details"""
    try:
        # Verify agent role
        is_agent = await call_procedure(
            conn, "check_user_role", (current_user["username"], "agent")
        )

        if not is_agent or not is_agent[0].get("is_role"):
            return RedirectResponse(url="/login", status_code=303)

        # Get agent details
        agent_details = await call_procedure(
            conn, "get_agent_details", (current_user["user_id"],)
        )

        if not agent_details:
            return RedirectResponse(url="/login", status_code=303)

        # Check license expiration
        agent = agent_details[0]
        if (
            agent.get("license_expiration")
            and agent["license_expiration"] < datetime.now().date()
        ):
            logger.warning(f"Agent {agent['agent_id']} license expired")
            return RedirectResponse(url="/login?error=license_expired", status_code=303)

        return {"user": current_user, "agent": agent}

    except Exception as e:
        logger.error(f"Agent verification error: {str(e)}")
        return RedirectResponse(url="/login", status_code=303)


async def create_admin_user(conn) -> None:
    """Create admin user from environment variables"""
    try:
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_username or not admin_password:
            raise ValueError("Admin credentials not found in environment variables")

        hashed_password = get_password_hash(admin_password)
        await call_procedure(
            conn, "create_admin_user", (admin_username, hashed_password)
        )

    except Exception as e:
        logger.error(f"Admin user creation error: {str(e)}")
        raise


async def validate_session(request: Request, conn=Depends(get_db_connection)) -> bool:
    """Validate user session"""
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            return False

        session = await call_procedure(
            conn, "validate_session", (session_id, request.client.host)
        )

        return bool(session and session[0].get("is_valid"))

    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return False


async def check_permissions(
    user_id: int, permission: str, conn=Depends(get_db_connection)
) -> bool:
    """Check user permissions"""
    try:
        result = await call_procedure(
            conn, "check_user_permission", (user_id, permission)
        )

        return bool(result and result[0].get("has_permission"))

    except Exception as e:
        logger.error(f"Permission check error: {str(e)}")
        return False


async def log_security_event(
    event_type: str,
    user_id: Optional[int],
    details: str,
    conn=Depends(get_db_connection),
) -> None:
    """Log security-related events"""
    try:
        await call_procedure(conn, "log_security_event", (event_type, user_id, details))
    except Exception as e:
        logger.error(f"Security event logging error: {str(e)}")
