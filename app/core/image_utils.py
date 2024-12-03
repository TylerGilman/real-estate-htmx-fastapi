import os
import shutil
from fastapi import UploadFile
from pathlib import Path
from uuid import uuid4
from PIL import Image
from ..core.logging_config import logger

# Define image constants
IMAGES_DIR = Path("app/static/property_images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
THUMBNAIL_SIZE = (300, 300)


def setup_image_directories():
    """Create necessary image directories if they don't exist"""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    (IMAGES_DIR / "thumbnails").mkdir(exist_ok=True)


def validate_image(file: UploadFile) -> bool:
    """Validate image file type and size"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset file pointer

    return size <= MAX_IMAGE_SIZE


async def save_property_image(file: UploadFile, property_id: int) -> tuple[str, str]:
    """
    Save property image and create thumbnail
    Returns tuple of (main_path, thumbnail_path)
    """
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid4()}{file_ext}"

    # Create file paths
    main_path = IMAGES_DIR / unique_filename
    thumb_path = IMAGES_DIR / "thumbnails" / unique_filename

    try:
        # Save original file
        with open(main_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create thumbnail
        with Image.open(main_path) as img:
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(thumb_path)

        return str(main_path.relative_to("app/static")), str(
            thumb_path.relative_to("app/static")
        )

    except Exception as e:
        logger.error(f"Error saving image for property {property_id}: {str(e)}")
        # Clean up any partially created files
        if main_path.exists():
            main_path.unlink()
        if thumb_path.exists():
            thumb_path.unlink()
        raise


def delete_property_images(file_paths: list[str]):
    """Delete property images and their thumbnails"""
    for path in file_paths:
        try:
            full_path = Path("app/static") / path
            thumb_path = full_path.parent.parent / "thumbnails" / full_path.name

            if full_path.exists():
                full_path.unlink()
            if thumb_path.exists():
                thumb_path.unlink()

        except Exception as e:
            logger.error(f"Error deleting image {path}: {str(e)}")
