from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from Levenshtein import distance as levenshtein_distance
import random
import os
from app.database import SessionLocal, engine
from app.models import Base, AgentListing  # Changed from Listing to AgentListing

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Get the current directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")

# Setup templates with absolute path
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_db_empty(db: Session):
    return db.query(AgentListing).count() == 0  # Changed from Listing to AgentListing

@app.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    if is_db_empty(db):
        return templates.TemplateResponse("empty_db.html", {"request": request})
    listings = db.query(AgentListing).all()  # Changed from Listing to AgentListing
    return templates.TemplateResponse(
        "index.html", {"request": request, "listings": listings}
    )

@app.get("/property/{property_id}")
async def property_detail(
    request: Request, property_id: int, db: Session = Depends(get_db)
):
    property = db.query(AgentListing).filter(AgentListing.id == property_id).first()  # Changed from Listing to AgentListing
    if property is None:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
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
    listings = db.query(AgentListing).all()  # Changed from Listing to AgentListing

    def similarity_score(listing):
        return levenshtein_distance(listing.title.lower(), search_query)

    sorted_listings = sorted(listings, key=similarity_score)
    return templates.TemplateResponse(
        "partials/listings.html", {"request": request, "listings": sorted_listings}
    )

@app.post("/randomize")
async def randomize(request: Request, db: Session = Depends(get_db)):
    listings = db.query(AgentListing).all()  # Changed from Listing to AgentListing
    random.shuffle(listings)
    return templates.TemplateResponse(
        "partials/listings.html", {"request": request, "listings": listings}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
