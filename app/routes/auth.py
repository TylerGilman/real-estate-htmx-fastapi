# app/routes/auth.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.security import verify_password, get_password_hash
from ..core.logging_config import logger
from ..core.database import get_db_connection, execute_procedure
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class AuthError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

async def authenticate_user(username: str, password: str, conn = Depends(get_db_connection)) -> dict:
    """Authenticate user and return user details"""
    # Check env admin first
    if username == os.getenv("ADMIN_USERNAME"):
        if password == os.getenv("ADMIN_PASSWORD"):
            return {
                "username": username,
                "role_name": "admin",
                "is_env_admin": True
            }
        raise AuthError("Invalid credentials", 400)

    # Get user from database
    user_result = execute_procedure(conn, 'get_user_by_username', (username,))
    if not user_result or not verify_password(password, user_result[0]['password_hash']):
        raise AuthError("Invalid credentials", 400)

    # Get complete user details
    user = user_result[0]
    user_info = execute_procedure(conn, 'get_user_role_and_details', (user['user_id'],))
    
    if not user_info:
        raise AuthError("User role not found", 500)
    
    # Log successful login
    execute_procedure(
        conn, 
        'log_user_login',
        (user['user_id'], user_info[0]['role_name'])
    )
    
    return user_info[0]

@router.get("/logout")
async def logout(request: Request):
    """Log out the current user"""
    try:
        username = request.session.get("username")
        if username:
            logger.info(f"User logged out: {username}")
            request.session.clear()
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return RedirectResponse(url="/", status_code=303)

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    conn = Depends(get_db_connection)
):
    """Handle user login"""
    try:
        # Authenticate user
        user_details = await authenticate_user(conn, username, password)
        
        # Set session data
        request.session["username"] = username
        request.session["role"] = user_details["role_name"]
        
        # Add additional session security
        request.session["authenticated"] = True
        request.session["last_activity"] = str(datetime.now())
        
        # Log successful login
        logger.info(f"Successful login for user: {username}")
        
        # Redirect based on role
        if user_details["role_name"] == "admin":
            return RedirectResponse(url="/admin", status_code=303)
        elif user_details["role_name"] == "agent":
            return RedirectResponse(url="/agent", status_code=303)
        else:
            raise AuthError("Invalid role", 500)
            
    except AuthError as e:
        logger.warning(f"Authentication failed for user {username}: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": e.message
            },
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "An unexpected error occurred"
            },
            status_code=500
        )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page"""
    try:
        # Check if user is already logged in
        if request.session.get("authenticated"):
            role = request.session.get("role")
            if role == "admin":
                return RedirectResponse(url="/admin", status_code=303)
            elif role == "agent":
                return RedirectResponse(url="/agent", status_code=303)
                
        return templates.TemplateResponse("auth/login.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html", 
            {
                "request": request,
                "error": "An error occurred"
            }
        )
