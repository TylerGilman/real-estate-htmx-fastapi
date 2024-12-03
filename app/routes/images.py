from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
from ..core.database import get_db_connection, execute_procedure
from ..core.security import get_current_admin, get_current_agent
from ..core.image_utils import (
    validate_image,
    save_property_image,
    delete_property_images,
    setup_image_directories,
)
from ..core.logging_config import logger

router = APIRouter(tags=["images"])

# Ensure image directories exist
setup_image_directories()


@router.post("/properties/{property_id}/images")
async def upload_property_image(
    property_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    current_user: dict = Depends(get_current_agent),  # Allows both agents and admins
    conn=Depends(get_db_connection),
):
    """Upload a new property image"""
    try:
        # Validate image
        if not validate_image(file):
            raise HTTPException(
                status_code=400,
                detail="Invalid image. Must be JPG, PNG or WebP under 5MB",
            )

        # Save image and create thumbnail
        main_path, thumb_path = await save_property_image(file, property_id)

        # Add to database
        execute_procedure(
            conn, "add_property_image", (property_id, main_path, is_primary)
        )

        return JSONResponse(
            {
                "message": "Image uploaded successfully",
                "file_path": main_path,
                "thumbnail_path": thumb_path,
            }
        )

    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading image")


@router.get("/properties/{property_id}/images")
async def get_property_images(property_id: int, conn=Depends(get_db_connection)):
    """Get all images for a property"""
    try:
        images = execute_procedure(conn, "get_property_images", (property_id,))
        return {"images": images}
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching images")


@router.put("/properties/images/{image_id}/primary")
async def set_primary_image(
    image_id: int,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """Set an image as the primary image for its property"""
    try:
        execute_procedure(conn, "set_primary_image", (image_id,))
        return {"message": "Primary image updated successfully"}
    except Exception as e:
        logger.error(f"Error setting primary image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error setting primary image")


@router.delete("/properties/images/{image_id}")
async def delete_image(
    image_id: int,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """Delete a property image"""
    try:
        # Get image path before deleting
        images = execute_procedure(conn, "get_property_images", (image_id,))

        if not images:
            raise HTTPException(status_code=404, detail="Image not found")

        # Delete from database
        execute_procedure(conn, "delete_property_image", (image_id,))

        # Delete physical files
        delete_property_images([images[0]["file_path"]])

        return {"message": "Image deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting image")
