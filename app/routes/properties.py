from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
import random
from Levenshtein import distance as levenshtein_distance
from app.core.database import get_db
from app.models import Property, ResidentialProperty, CommercialProperty

router = APIRouter(prefix="/properties", tags=["properties"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def properties_list(
    request: Request, page: int = 1, limit: int = 12, db: Session = Depends(get_db)
):
    """List all properties with pagination"""
    offset = (page - 1) * limit

    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = db.query(Property).count()
    total_pages = (total + limit - 1) // limit

    return templates.TemplateResponse(
        "properties/list.html",
        {
            "request": request,
            "properties": properties,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.get("/{tax_id}")
async def property_detail(request: Request, tax_id: str, db: Session = Depends(get_db)):
    """Get property details"""
    property = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .filter(Property.tax_id == tax_id)
        .first()
    )

    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")

    template = (
        "properties/detail.html"
        if not request.headers.get("HX-Request")
        else "partials/property_detail.html"
    )

    return templates.TemplateResponse(
        template, {"request": request, "property": property}
    )


@router.post("/search")
async def search_properties(request: Request, db: Session = Depends(get_db)):
    """Search properties"""
    form = await request.form()
    search_query = form.get("search-text", "").lower()

    query = (
        db.query(Property).outerjoin(ResidentialProperty).outerjoin(CommercialProperty)
    )

    if search_query:
        query = query.filter(
            or_(
                Property.property_address.ilike(f"%{search_query}%"),
                Property.tax_id.ilike(f"%{search_query}%"),
            )
        )

    properties = query.all()

    return templates.TemplateResponse(
        "partials/listings.html", {"request": request, "properties": properties}
    )


@router.post("/randomize")
async def randomize_properties(request: Request, db: Session = Depends(get_db)):
    """Randomize property listing order"""
    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .all()
    )

    properties_list = list(properties)
    random.shuffle(properties_list)

    return templates.TemplateResponse(
        "partials/listings.html", {"request": request, "properties": properties_list}
    )
