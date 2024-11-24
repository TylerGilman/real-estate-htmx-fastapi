from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models import Property, ResidentialProperty, CommercialProperty

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_db_empty(db: Session) -> bool:
    """Check if the database is empty."""
    return db.query(Property).count() == 0


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    if is_db_empty(db):
        return templates.TemplateResponse(
            "properties/empty_db.html", {"request": request}
        )

    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .all()
    )

    return templates.TemplateResponse(
        "index.html", {"request": request, "properties": properties}
    )
