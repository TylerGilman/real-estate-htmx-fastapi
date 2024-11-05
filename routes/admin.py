import random
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import os
import shutil
from database import get_db
from models import Property, PropertyType, ResidentialProperty, CommercialProperty

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def generate_unique_tax_id(db: Session) -> str:
    """Generate a unique tax ID that doesn't exist in the database."""
    while True:
        # Generate a random tax ID
        tax_id = f"TAX{random.randint(100000, 999999)}"
        # Check if it exists
        exists = db.query(Property).filter(Property.tax_id == tax_id).first()
        if not exists:
            return tax_id


@router.get("/admin")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .all()
    )
    return templates.TemplateResponse(
        "admin.html", {"request": request, "properties": properties}
    )


@router.delete("/admin/properties/{tax_id}")
async def delete_property(request: Request, tax_id: str, db: Session = Depends(get_db)):
    try:
        # First delete the specific property type
        residential = (
            db.query(ResidentialProperty)
            .filter(ResidentialProperty.tax_id == tax_id)
            .first()
        )
        if residential:
            db.delete(residential)

        commercial = (
            db.query(CommercialProperty)
            .filter(CommercialProperty.tax_id == tax_id)
            .first()
        )
        if commercial:
            db.delete(commercial)

        # Then delete the base property
        property = db.query(Property).filter(Property.tax_id == tax_id).first()
        if not property:
            return templates.TemplateResponse(
                "partials/toast.html",
                {"request": request, "type": "error", "message": "Property not found"},
            )

        # Delete the image file
        if property.image_url:
            image_path = os.path.join("static", property.image_url.lstrip("/static/"))
            if os.path.exists(image_path):
                os.remove(image_path)

        db.delete(property)
        db.commit()

        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "success",
                "message": "Property deleted successfully",
            },
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "error",
                "message": f"Error deleting property: {str(e)}",
            },
        )


@router.post("/admin/properties")
async def create_property(
    request: Request,
    db: Session = Depends(get_db),
    property_address: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    property_type: str = Form(...),
    image: UploadFile = File(...),
    bedrooms: Optional[int] = Form(None),
    bathrooms: Optional[float] = Form(None),
    r_type: Optional[str] = Form(None),
    sqft: Optional[float] = Form(None),
    industry: Optional[str] = Form(None),
    c_type: Optional[str] = Form(None),
):
    try:
        # Save the uploaded file
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb+") as file_object:
            shutil.copyfileobj(image.file, file_object)

        # Generate tax_id
        tax_id = f"TAX{random.randint(100000, 999999)}"

        # Create base property
        property = Property(
            tax_id=tax_id,
            property_address=property_address,
            price=price,
            status=status,
            property_type=PropertyType[property_type],
            image_url=f"/static/uploads/{file_name}",
        )
        db.add(property)
        db.flush()

        # Add type-specific details
        if property_type == "RESIDENTIAL":
            residential = ResidentialProperty(
                tax_id=tax_id,
                property_address=property_address,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                r_type=r_type,
            )
            db.add(residential)
        else:
            commercial = CommercialProperty(
                tax_id=tax_id,
                property_address=property_address,
                sqft=sqft,
                industry=industry,
                c_type=c_type,
            )
            db.add(commercial)

        db.commit()

        # Get updated properties list
        properties = (
            db.query(Property)
            .outerjoin(ResidentialProperty)
            .outerjoin(CommercialProperty)
            .all()
        )

        # Return the full admin page with toast
        response = templates.TemplateResponse(
            "admin.html", {"request": request, "properties": properties}
        ).body.decode()

        toast = templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "success",
                "message": "Property created successfully",
            },
        ).body.decode()

        return HTMLResponse(response + toast)

    except Exception as e:
        print(f"Error creating property: {str(e)}")
        db.rollback()
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)

        # Get the current properties list for the error response
        properties = (
            db.query(Property)
            .outerjoin(ResidentialProperty)
            .outerjoin(CommercialProperty)
            .all()
        )

        response = templates.TemplateResponse(
            "admin.html", {"request": request, "properties": properties}
        ).body.decode()

        toast = templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "error",
                "message": f"Error creating property: {str(e)}",
            },
        ).body.decode()

        return HTMLResponse(response + toast)
