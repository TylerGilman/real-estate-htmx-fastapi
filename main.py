from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, func
from sqlalchemy.dialects.postgresql import TSVECTOR
import random

from Levenshtein import distance as levenshtein_distance
from database import SessionLocal, engine
import models

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_db_empty(db: Session):
    return db.query(models.Listing).count() == 0

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    if is_db_empty(db):
        return templates.TemplateResponse("empty_db.html", {"request": request})
    listings = db.query(models.Listing).all()
    return templates.TemplateResponse("index.html", {"request": request, "listings": listings})

@app.get("/property/{property_id}")
def property_detail(request: Request, property_id: int, db: Session = Depends(get_db)):
    property = db.query(models.Listing).filter(models.Listing.id == property_id).first()
    if property is None:
        # Handle the case where the property is not found
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    
    template = "property_detail.html" if request.headers.get("HX-Request") else "property_detail_full.html"
    return templates.TemplateResponse(template, {"request": request, "property": property})

@app.post("/search")
async def search(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    search_query = form.get("search", "").lower()

    # Fetch all listings
    listings = db.query(models.Listing).all()

    # Calculate similarity based on Levenshtein distance
    def similarity_score(listing):
        title_distance = levenshtein_distance(listing.title.lower(), search_query)
        #price_distance = levenshtein_distance(str(listing.price), search_query)
        #return min(title_distance, price_distance)  # Use the smallest distance as similarity score
        return title_distance

    # Sort listings by similarity score (lower score means higher similarity)
    sorted_listings = sorted(listings, key=similarity_score)
    return templates.TemplateResponse("partials/listings.html", {
        "request": request,
        "listings": sorted_listings
    })


@app.post("/randomize")
async def randomize(request: Request, db: Session = Depends(get_db)):
    # Fetch all listings
    listings = db.query(models.Listing).all()
    random.shuffle(listings)
    return templates.TemplateResponse("partials/listings.html", {
        "request": request,
        "listings": listings
    })

@app.get("/admin")
def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
