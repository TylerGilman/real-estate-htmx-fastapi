from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import random
from sqlalchemy import func, extract
from typing import Optional
from pydantic import BaseModel
import uuid
import os
import shutil
from database import get_db
from models import (
    Property,
    PropertyType,
    ResidentialProperty,
    CommercialProperty,
    Agent,
    AgentListing,
    AgentShowing,
    Brokerage,
)

# Initialize router with prefix
router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

# Constants
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Pydantic models
class AgentCreate(BaseModel):
    agent_name: str
    NRDS: str
    agent_phone: str
    SSN: str


def generate_unique_tax_id(db: Session) -> str:
    """Generate a unique tax ID that doesn't exist in the database."""
    while True:
        # Generate a random tax ID
        tax_id = f"TAX{random.randint(100000, 999999)}"
        # Check if it exists
        exists = db.query(Property).filter(Property.tax_id == tax_id).first()
        if not exists:
            return tax_id


# Routes
@router.get("")  # This will handle /admin
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard showing properties and agent statistics"""
    properties = (
        db.query(Property)
        .outerjoin(ResidentialProperty)
        .outerjoin(CommercialProperty)
        .all()
    )

    # Get agent statistics
    agents = db.query(Agent).all()
    total_agents = len(agents)

    # Calculate total active listings
    total_listings = (
        db.query(AgentListing)
        .join(Property)
        .filter(Property.status == "For Sale")
        .count()
    )

    # Calculate total sales (in millions)
    total_sales = (
        db.query(func.sum(Property.price))
        .join(AgentListing)
        .filter(Property.status == "For Sale")
        .scalar()
        or 0
    ) / 1000000

    # Calculate total showings
    total_showings = db.query(AgentShowing).count()

    # Get agents with their active listings count
    agents_with_stats = []
    for agent in agents:
        active_listings_count = (
            db.query(AgentListing)
            .join(Property)
            .filter(
                AgentListing.agent_nrds == agent.nrds, Property.status == "For Sale"
            )
            .count()
        )
        agents_with_stats.append(
            {
                "nrds": agent.nrds,
                "name": agent.agent_name,
                "phone": agent.agent_phone,
                "active_listings_count": active_listings_count,
            }
        )

    # Get list of agents for the property form
    available_agents = db.query(Agent).all()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "properties": properties,
            "agents": agents_with_stats,
            "available_agents": available_agents,
            "total_agents": total_agents,
            "total_listings": total_listings,
            "total_sales": total_sales,
            "total_showings": total_showings,
        },
    )


@router.post("/properties")
async def create_property(
    request: Request,
    db: Session = Depends(get_db),
    property_address: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    property_type: str = Form(...),
    agent_nrds: str = Form(...),
    image: UploadFile = File(...),
    bedrooms: Optional[int] = Form(None),
    bathrooms: Optional[float] = Form(None),
    r_type: Optional[str] = Form(None),
    sqft: Optional[float] = Form(None),
    industry: Optional[str] = Form(None),
    c_type: Optional[str] = Form(None),
):
    try:
        # Save image
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb+") as file_object:
            shutil.copyfileobj(image.file, file_object)

        # Generate tax_id
        tax_id = generate_unique_tax_id(db)

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

        # Create agent listing association (always as seller agent)
        agent_listing = AgentListing(
            tax_id=tax_id,
            property_address=property_address,
            agent_nrds=agent_nrds,
            l_agent_role=AgentRole.SELLER,  # Always a seller agent for new listings
            listing_date=datetime.utcnow(),
        )
        db.add(agent_listing)

        db.commit()

        # Get updated properties and stats
        return await admin_dashboard(request=request, db=db)

    except Exception as e:
        print(f"Error creating property: {str(e)}")
        db.rollback()
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)

        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "error",
                "message": f"Error creating property: {str(e)}",
            },
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


@router.post("/agents")
async def create_agent(
    request: Request,
    agent_name: str = Form(...),
    NRDS: str = Form(...),
    agent_phone: str = Form(...),
    SSN: str = Form(...),
    db: Session = Depends(get_db),
):
    """Create a new agent"""
    try:
        # Make sure we have a brokerage
        brokerage = db.query(Brokerage).first()
        if not brokerage:
            brokerage = Brokerage(
                broker_name="Cherokee Street Brokerage",
                broker_address="123 Cherokee St",
                broker_phone="555-123-4567",
            )
            db.add(brokerage)
            db.flush()

        db_agent = Agent(
            nrds=NRDS,
            agent_name=agent_name,
            agent_phone=agent_phone,
            ssn=SSN,
            broker_id=brokerage.broker_id,
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

        # Get updated statistics for the response
        # Reuse the admin dashboard logic
        return await admin_dashboard(request=request, db=db)

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "error",
                "message": f"Error adding agent: {str(e)}",
            },
        )


@router.get("/agents/{nrds}/details")
async def get_agent_details(request: Request, nrds: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific agent"""
    if not nrds:
        raise HTTPException(status_code=400, detail="NRDS number is required")

    agent = db.query(Agent).filter(Agent.nrds == nrds).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get agent's active listings
    active_listings = (
        db.query(Property)
        .join(AgentListing)
        .filter(AgentListing.agent_nrds == nrds, Property.status == "For Sale")
        .all()
    )

    # Get agent's showings this month
    current_month_showings = (
        db.query(AgentShowing)
        .filter(
            AgentShowing.agent_nrds == nrds,
            extract("month", AgentShowing.showing_date)
            == extract("month", func.current_date()),
        )
        .count()
    )

    # Calculate total sales
    total_sales = (
        db.query(func.sum(Property.price))
        .join(AgentListing)
        .filter(AgentListing.agent_nrds == nrds)
        .scalar()
        or 0
    )

    return templates.TemplateResponse(
        "partials/agent_details.html",
        {
            "request": request,
            "agent": {
                "nrds": agent.nrds,
                "name": agent.agent_name,
                "phone": agent.agent_phone,
                "active_listings_count": len(active_listings),
                "monthly_showings": current_month_showings,
                "total_sales": total_sales,
                "recent_listings": active_listings[:5],
            },
        },
    )


@router.delete("/agents/{nrds}")
async def delete_agent(request: Request, nrds: str, db: Session = Depends(get_db)):
    """Delete an agent and their related records"""
    try:
        print(f"Attempting to delete agent with NRDS: {nrds}")  # Debug print
        agent = db.query(Agent).filter(Agent.nrds == nrds).first()
        if not agent:
            print(f"Agent not found with NRDS: {nrds}")  # Debug print
            return templates.TemplateResponse(
                "partials/toast.html",
                {"request": request, "type": "error", "message": "Agent not found"},
                status_code=404,
            )

        # Delete related records first
        agent_listings = (
            db.query(AgentListing).filter(AgentListing.agent_nrds == nrds).delete()
        )
        agent_showings = (
            db.query(AgentShowing).filter(AgentShowing.agent_nrds == nrds).delete()
        )

        print(
            f"Deleted {agent_listings} listings and {agent_showings} showings"
        )  # Debug print

        # Delete the agent
        db.delete(agent)
        db.commit()
        print(f"Successfully deleted agent {nrds}")  # Debug print

        # Return an empty response with success message
        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "success",
                "message": "Agent deleted successfully",
            },
        )
    except Exception as e:
        print(f"Error deleting agent: {str(e)}")  # Debug print
        db.rollback()
        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "type": "error",
                "message": f"Error deleting agent: {str(e)}",
            },
            status_code=500,
        )
