from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, func, extract
import random
from Levenshtein import distance as levenshtein_distance
from database import SessionLocal, engine, get_db
from routes import admin
from models import (
    Property,
    ResidentialProperty,
    CommercialProperty,
    PropertyType,
    Agent,
    AgentListing,
    AgentShowing,
    Brokerage,
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(admin.router)


def is_db_empty(db: Session) -> bool:
    """Check if the database is empty."""
    return db.query(Property).count() == 0


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    if is_db_empty(db):
        return templates.TemplateResponse("empty_db.html", {"request": request})

    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .all()
    )

    print("Properties" + str(properties))

    return templates.TemplateResponse(
        "index.html", {"request": request, "properties": properties}
    )


@app.get("/property/{tax_id}")
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


@app.post("/search")
async def search(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    search_query = form.get("search-text", "").lower()

    query = (
        db.query(Property).outerjoin(ResidentialProperty).outerjoin(CommercialProperty)
    )

    properties = query.all()

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
