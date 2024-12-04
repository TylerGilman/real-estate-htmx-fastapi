# In app/core/image_utils.py

import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from uuid import uuid4

# Define constants
UPLOAD_DIR = Path("app/static/property_images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def setup_image_directories():
    """Ensure upload directories exist"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_image(file: UploadFile) -> bool:
    """Validate image file type and size"""
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset file pointer

    return size <= MAX_FILE_SIZE


async def save_uploaded_image(file: UploadFile, property_id: int) -> str:
    """Save uploaded image and return relative path"""
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    filename = f"{property_id}_{uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename

    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return relative path from static directory
    return f"property_images/{filename}"


def delete_property_image(file_path: str) -> bool:
    """Delete image file from filesystem"""
    try:
        full_path = Path("app/static") / file_path
        if full_path.exists():
            full_path.unlink()
            return True
    except Exception:
        pass
    return False
