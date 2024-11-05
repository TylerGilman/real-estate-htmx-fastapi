from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, func
from sqlalchemy.dialects.postgresql import TSVECTOR
import random
from Levenshtein import distance as levenshtein_distance
from database import SessionLocal, engine, get_db, is_db_empty
from routes import admin
from models import Property, ResidentialProperty, CommercialProperty, PropertyType

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(admin.router)


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    if is_db_empty(db):
        return templates.TemplateResponse("empty_db.html", {"request": request})

    # Query properties with their details
    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .all()
    )

    # Debug print
    print(f"Found {len(properties)} properties")
    for prop in properties:
        print(f"Property {prop.tax_id}: {prop.property_address}, {prop.price}")
        if prop.property_type == PropertyType.RESIDENTIAL and prop.residential_details:
            print(
                f"  Residential: {prop.residential_details.bedrooms} beds, {prop.residential_details.bathrooms} baths"
            )
        elif prop.property_type == PropertyType.COMMERCIAL and prop.commercial_details:
            print(
                f"  Commercial: {prop.commercial_details.sqft} sqft, {prop.commercial_details.industry}"
            )

    return templates.TemplateResponse(
        "index.html", {"request": request, "properties": properties}
    )


@app.get("/property/{tax_id}")
def property_detail(request: Request, tax_id: str, db: Session = Depends(get_db)):
    # Query property with its details using tax_id
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


@app.post("/search")
async def search(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    search_query = form.get("search-text", "").lower()
    property_type = form.get("search-style", "All")
    min_price = form.get("search-min-price")
    max_price = form.get("search-max-price")

    # Start with base query
    query = (
        db.query(Property).outerjoin(ResidentialProperty).outerjoin(CommercialProperty)
    )

    """
    # Apply filters
    if search_query:
        query = query.filter(Property.property_address.ilike(f"%{search_query}%"))

    if property_type != "All":
        query = query.filter(Property.property_type == PropertyType[property_type])

    if min_price and min_price.isdigit():
        query = query.filter(Property.price >= float(min_price))

    if max_price and max_price.isdigit():
        query = query.filter(Property.price <= float(max_price))
    """

    properties = query.all()
    # Sort by similarity if there's a search query
    if search_query:

        def similarity_score(property):
            return levenshtein_distance(property.property_address.lower(), search_query)

        properties = sorted(properties, key=similarity_score)

    return templates.TemplateResponse(
        "partials/listings.html", {"request": request, "properties": properties}
    )


@app.post("/randomize")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
