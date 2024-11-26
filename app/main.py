from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.models import Property, ResidentialProperty, CommercialProperty
from app.routes.admin import router as admin_router
from app.routes.properties import router as properties_router
from app.routes.main import router as main_router
from app.routes.auth import router as auth_router

app = FastAPI(title="Real Estate Management System")

# Get the current directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key"),
    same_site="lax",
    https_only=False  # Set to True in production
)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

# Include routers with prefixes
app.include_router(auth_router, tags=["auth"])
app.include_router(admin_router, prefix="/admin")
app.include_router(properties_router, prefix="/properties")
app.include_router(main_router)  # No prefix for main routes

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
