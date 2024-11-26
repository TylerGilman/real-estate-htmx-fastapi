# app/core/security.py
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models import User, UserRole, Agent
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    # Check if user is authenticated via session
    username = request.session.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Handle admin from .env
    if username == os.getenv("ADMIN_USERNAME"):
        # Create a synthetic admin user
        admin_role = db.query(UserRole).filter(UserRole.role_name == "admin").first()
        if not admin_role:
            admin_role = UserRole(role_name="admin")
            db.add(admin_role)
            db.commit()
            
        return User(
            username=username,
            role_id=admin_role.role_id,
            agent_id=None
        )
    
    # Handle database users
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    # First check if it's the env admin
    if current_user.username == os.getenv("ADMIN_USERNAME"):
        return current_user
    
    # Otherwise check database role
    role = db.query(UserRole).filter(UserRole.role_id == current_user.role_id).first()
    if not role or role.role_name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_agent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    # Get the role
    role = db.query(UserRole).filter(UserRole.role_id == current_user.role_id).first()
    
    if not role or role.role_name != "agent":
        return RedirectResponse(url="/login", status_code=303)
    
    # Get agent info
    agent = db.query(Agent).filter(Agent.agent_id == current_user.agent_id).first()
    if not agent:
        return RedirectResponse(url="/login", status_code=303)
    
    return {"user": current_user, "agent": agent}

def create_admin_user(db: Session) -> None:
    """Create admin user from environment variables if it doesn't exist"""
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_username or not admin_password:
        raise ValueError("Admin credentials not found in environment variables")
    
    # Check if admin role exists
    admin_role = db.query(UserRole).filter(UserRole.role_name == "admin").first()
    if not admin_role:
        admin_role = UserRole(role_name="admin")
        db.add(admin_role)
        db.commit()
    
    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == admin_username).first()
    if not admin_user:
        admin_user = User(
            username=admin_username,
            password_hash=get_password_hash(admin_password),
            role_id=admin_role.role_id
        )
        db.add(admin_user)
        db.commit()
