from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
import random
from Levenshtein import distance as levenshtein_distance
from ..core.database import get_db
from ..models import Property, ResidentialProperty, CommercialProperty

router = APIRouter(
    prefix="/properties",
    tags=["properties"]
)



templates = Jinja2Templates(directory="app/templates")


@router.get("/{tax_id}")
def property_detail(request: Request, tax_id: str, db: Session = Depends(get_db)):
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
        "property_detail.html"
        if request.headers.get("HX-Request")
        else "property_details_full.html"
    )
    
    return templates.TemplateResponse(
        template, {"request": request, "property": property}
    )

@router.post("/search")
async def search(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    search_query = form.get("search-text", "").lower()
    
    query = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
    )
    properties = query.all()
    
    if search_query:
        def similarity_score(property):
            return levenshtein_distance(property.property_address.lower(), search_query)
        properties = sorted(properties, key=similarity_score)
    
    return templates.TemplateResponse(
        "partials/listings.html", {"request": request, "properties": properties}
    )

@router.post("/randomize")
async def randomize(request: Request, db: Session = Depends(get_db)):
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
