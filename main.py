from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from database import SessionLocal, engine
import models

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Drop existing table and recreate with new schema
def init_db():
    try:
        # Try to select from the table
        with engine.connect() as conn:
            conn.execute(text("SELECT image_url FROM listings LIMIT 1"))
    except OperationalError:
        # If the column doesn't exist, recreate the table
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS listings"))
        models.Base.metadata.create_all(bind=engine)
        print("Database initialized with new schema.")
    else:
        print("Database schema is up to date.")


# Call this function to initialize the database
init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_empty(db: Session) -> bool:
    return db.query(models.Listing).count() == 0


@app.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    if is_db_empty(db):
        return templates.TemplateResponse("empty_db.html", {"request": request})
    listings = db.query(models.Listing).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "listings": listings}
    )

@app.get("/property/{property_id}")
async def property_detail(request: Request, property_id: int, db: Session = Depends(get_db)):
    is_htmx = request.headers.get("HX-Request") == "true"
    property = db.query(models.Listing).filter(models.Listing.id == property_id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    context = {"request": request, "property": property}
    
    if is_htmx:
        print("htmx")
        return templates.TemplateResponse("property_detail.html", context)
    else:

        print("not htmx")
        return templates.TemplateResponse("property_details_full.html", context)

@app.get("/admin")
async def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.post("/admin/add")
async def add_property(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    image_url: str = Form(...),
    db: Session = Depends(get_db),
):
    new_listing = models.Listing(
        title=title, description=description, price=price, image_url=image_url
    )
    db.add(new_listing)
    db.commit()
    return templates.TemplateResponse(
        "admin.html", {"request": request, "message": "Property added successfully!"}
    )


@app.get("/property/{property_id}")
async def property_detail(
    request: Request, property_id: int, db: Session = Depends(get_db)
):
    property = db.query(models.Listing).filter(models.Listing.id == property_id).first()
    return templates.TemplateResponse(
        "property_detail.html", {"request": request, "property": property}
    )


if __name__ == "__main__":
    init_db()  # Initialize the database when running the script directly
