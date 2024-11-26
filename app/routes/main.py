from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os
from app.core.database import get_db
from app.models import Property, ResidentialProperty, CommercialProperty

router = APIRouter(tags=["main"])
templates = Jinja2Templates(directory="app/templates")


def is_db_empty(db: Session) -> bool:
    """Check if the database is empty."""
    return db.query(Property).count() == 0


@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    """Homepage route"""
    try:
        # Query properties with their details
        properties = (
            db.query(Property)
            .outerjoin(ResidentialProperty)
            .outerjoin(CommercialProperty)
            .all()
        )
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "properties": properties,
            }
        )
    except Exception as e:
        print(f"Error fetching properties: {str(e)}")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "properties": [],
                "error": "Failed to load properties"
            }
        )


@router.get("/about")
async def about(request: Request):
    """About page route"""
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/contact")
async def contact(request: Request):
    """Contact page route"""
    return templates.TemplateResponse("contact.html", {"request": request})


@router.get("/search")
async def search(
    request: Request,
    query: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Search properties route"""
    properties_query = (
        db.query(Property).outerjoin(ResidentialProperty).outerjoin(CommercialProperty)
    )

    if query:
        properties_query = properties_query.filter(
            Property.property_address.ilike(f"%{query}%")
        )

    if min_price:
        properties_query = properties_query.filter(Property.price >= min_price)

    if max_price:
        properties_query = properties_query.filter(Property.price <= max_price)

    properties = properties_query.all()

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/listings.html", {"request": request, "properties": properties}
        )

    return templates.TemplateResponse(
        "search.html", {"request": request, "properties": properties}
    )
