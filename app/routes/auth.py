# app/routes/auth.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import verify_password, get_password_hash
from ..models import User, UserRole
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # First check if it's the admin from .env
    if username == os.getenv("ADMIN_USERNAME") and password == os.getenv(
        "ADMIN_PASSWORD"
    ):
        request.session["username"] = username
        request.session["role"] = "admin"
        return RedirectResponse(url="/admin", status_code=303)

    # If not admin, check database users
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=400,
        )

    # Get user role
    role = db.query(UserRole).filter(UserRole.role_id == user.role_id).first()

    # Set session
    request.session["username"] = user.username
    request.session["role"] = role.role_name

    # Redirect based on role
    if role.role_name == "admin":
        return RedirectResponse(url="/admin", status_code=303)
    elif role.role_name == "agent":
        return RedirectResponse(url="/agent", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})
