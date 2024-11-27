# app/routes/admin.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text
from typing import Optional
from datetime import date
from ..core.database import get_db
from ..core.logging_config import logger
from ..core.security import get_current_admin, get_password_hash
from ..models import (
    Property,
    ResidentialProperty,
    CommercialProperty,
    Agent,
    AgentListing,
    AgentShowing,
    Transaction,
    PropertyStatus,
    Contract,
    User,
    UserRole
)
import random
from fastapi import File, UploadFile
import os
from datetime import datetime
import shutil
import logging
logging.basicConfig(level=logging.INFO)

# Add at the top with other imports
UPLOAD_DIR = "app/static/property_images"

from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Only the admin can add more authenticated users (agents)
@router.post("/users", response_class=HTMLResponse)
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    agent_id: Optional[int] = Form(None),
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new user account (admin only)"""
    try:
        # Check if username exists
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=400, detail="Username already exists")

        # Get role
        role = db.query(UserRole).filter(
            UserRole.role_name == "agent" if agent_id else "admin"
        ).first()

        # Create user
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role_id=role.role_id,
            agent_id=agent_id
        )
        
        db.add(user)
        db.commit()

        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "User account created successfully",
                "type": "success"
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user account: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error creating user account: {str(e)}",
                "type": "error"
            }
        )

# Main Dashboard Route
@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Main admin dashboard view"""
    try:
        # Get properties with logging
        properties = db.query(Property).all()
        logger.info(f"Found {len(properties)} properties")

        # Get agents
        agents = db.query(Agent).all()
        logger.info(f"Found {len(agents)} agents")

        # Get statistics
        total_properties = db.query(func.count(Property.property_id)).scalar() or 0
        total_agents = db.query(func.count(Agent.agent_id)).scalar() or 0
        total_listings = db.query(func.count(AgentListing.listing_id)).scalar() or 0

        # Sales statistics
        sales_data = (
            db.query(
                func.sum(Transaction.amount).label("total_sales"),
                func.sum(Transaction.commission_amount).label("total_commissions"),
            )
            .filter(Transaction.transaction_type == "Sale")
            .first()
        )

        context = {
            "request": request,
            "current_user": current_user,
            "agents": agents,
            "properties": properties,  # Make sure we're passing properties to template
            "total_agents": total_agents,
            "total_listings": total_listings,
            "total_properties": total_properties,
            "total_sales": getattr(sales_data, "total_sales", 0) or 0,
            "total_commissions": getattr(sales_data, "total_commissions", 0) or 0,
            "today": date.today(),
        }

        logger.info("Dashboard data retrieved successfully")
        return templates.TemplateResponse("admin/dashboard.html", context)

    except Exception as e:
        logger.error("Failed to render dashboard", exc_info=True)
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "error": "Failed to load dashboard data",
                "properties": [],  # Empty list as fallback
                "agents": [],
                "total_agents": 0,
                "total_listings": 0,
                "total_properties": 0,
                "total_sales": 0,
                "total_commissions": 0,
                "today": date.today(),
            },
        )


# Property Routes
@router.get("/properties/table", response_class=HTMLResponse)
async def properties_table(request: Request, db: Session = Depends(get_db)):
    """Properties table component"""
    try:
        # Get properties with their related information
        query = (
            db.query(Property)
            .outerjoin(ResidentialProperty)
            .outerjoin(CommercialProperty)
        )

        # Calculate statistics safely
        property_stats = db.query(
            func.count(Property.property_id).label("total_properties"),
            func.sum(Property.price).label("total_value"),
            func.avg(Property.price).label("avg_price"),
        ).first()

        active_listings = (
            db.query(func.count(Property.property_id))
            .filter(Property.status.in_(["For Sale", "For Lease"]))
            .scalar()
        )

        properties = query.all()

        # Ensure all values are properly defaulted
        context = {
            "request": request,
            "properties": properties,
            "total_properties": getattr(property_stats, "total_properties", 0) or 0,
            "active_listings": active_listings or 0,
            "total_value": getattr(property_stats, "total_value", 0) or 0,
            "avg_price": getattr(property_stats, "avg_price", 0) or 0,
        }

        logger.info("Successfully fetched properties table")
        return templates.TemplateResponse("admin/properties/table.html", context)

    except Exception as e:
        logger.error("Failed to fetch properties table", exc_info=True)
        return templates.TemplateResponse(
            "admin/properties/table.html",
            {
                "request": request,
                "error": "Failed to load properties",
                "properties": [],
                "total_properties": 0,
                "active_listings": 0,
                "total_value": 0,
                "avg_price": 0,
            },
        )


@router.post("/properties", response_class=HTMLResponse)
async def create_property(
    request: Request,
    property_address: str = Form(...),
    property_type: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    year_built: int = Form(None),
    lot_size: float = Form(None),
    zoning: str = Form(None),
    property_tax: float = Form(None),
    image: UploadFile = File(None),  # Image field
    bedrooms: int = Form(None),  # Residential-specific fields
    bathrooms: float = Form(None),
    r_type: str = Form(None),
    square_feet: float = Form(None),
    garage_spaces: int = Form(None),
    has_basement: bool = Form(False),
    has_pool: bool = Form(False),
    commercial_sqft: float = Form(None),  # Commercial-specific fields
    industry: str = Form(None),
    c_type: str = Form(None),
    num_units: int = Form(None),
    parking_spaces: int = Form(None),
    zoning_type: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Creating new property: {property_address}")

        # Map status to ENUM-compatible value
        status_map = {
            "For Sale": "FOR_SALE",
            "Sold": "SOLD",
            "For Lease": "FOR_LEASE",
            "Leased": "LEASED",
        }
        status_db = status_map.get(status, "FOR_SALE")  # Default to "FOR_SALE" if invalid

        # Validate status
        if status not in status_map:
            return templates.TemplateResponse(
                "shared/toast.html",
                {"request": request, "message": "Invalid status value. Please select a valid option."},
            )

        # Assign default values for missing optional parameters
        year_built = year_built or 2000
        lot_size = lot_size or 0.0
        zoning = zoning or "Unknown"
        property_tax = property_tax or 0.0
        bedrooms = bedrooms or 0
        bathrooms = bathrooms or 0.0
        r_type = r_type or "Single Family"
        square_feet = square_feet or 0.0
        garage_spaces = garage_spaces or 0
        commercial_sqft = commercial_sqft or 0.0
        industry = industry or "General"
        c_type = c_type or "Office"
        num_units = num_units or 0
        parking_spaces = parking_spaces or 0
        zoning_type = zoning_type or "General"

        # Generate a unique tax ID
        tax_id = f"TAX{random.randint(100000, 999999)}"

        # Call the `create_property` stored procedure
        property_id = db.execute(
            text("""
                CALL create_property(
                    :tax_id, :property_address, :status, :price, :lot_size, :year_built, :zoning, :property_tax,
                    :property_type, :bedrooms, :bathrooms, :r_type, :square_feet, :garage_spaces, :has_basement,
                    :has_pool, :commercial_sqft, :industry, :c_type, :num_units, :parking_spaces, :zoning_type,
                    @property_id
                )
            """),
            {
                "tax_id": tax_id,
                "property_address": property_address,
                "status": status_db,
                "price": price,
                "lot_size": lot_size,
                "year_built": year_built,
                "zoning": zoning,
                "property_tax": property_tax,
                "property_type": property_type.upper(),
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "r_type": r_type,
                "square_feet": square_feet,
                "garage_spaces": garage_spaces,
                "has_basement": has_basement,
                "has_pool": has_pool,
                "commercial_sqft": commercial_sqft,
                "industry": industry,
                "c_type": c_type,
                "num_units": num_units,
                "parking_spaces": parking_spaces,
                "zoning_type": zoning_type,
            },
        )


        # Handle image upload if provided
        if image:
            try:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                file_name = f"{datetime.now().timestamp()}_{image.filename}"
                file_path = os.path.join(UPLOAD_DIR, file_name)

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)

                # Call `add_property_image` procedure
                db.execute(
                    text("""
                        CALL add_property_image(:property_id, :file_path, :is_primary)
                    """),
                    {
                        "property_id": property_id,
                        "file_path": f"/static/uploads/{file_name}",
                        "is_primary": True,
                    },
                )

            except Exception as img_error:
                logger.error(f"Failed to save image: {str(img_error)}", exc_info=True)

        # Commit changes
        db.commit()
        logger.info(f"Property created successfully with ID: {property_id}")

        # Render success response
        created_property = db.query(Property).filter(Property.property_id == property_id).first()
        return templates.TemplateResponse(
            "admin/properties/table_row.html",
            {"request": request, "property": created_property},
            headers={"HX-Trigger": "propertyCreated"},
        )
    except Exception as e:
        logger.error(f"Error creating property: {str(e)}", exc_info=True)
        db.rollback()
        # Render error message using toast template
        return templates.TemplateResponse(
            "components/toast.html",
            {"request": request, "message": "Failed to create property. Please try again."},
        )


# Agent Routes
@router.get("/agents/table", response_class=HTMLResponse)
async def agents_table(request: Request, db: Session = Depends(get_db)):
    """Agents table component"""
    try:
        agents = db.query(Agent).all()

        stats = {
            "total_agents": db.query(func.count(Agent.agent_id)).scalar() or 0,
            "total_listings": db.query(func.count(AgentListing.listing_id)).scalar()
            or 0,
        }

        sales_data = (
            db.query(
                func.sum(Transaction.amount).label("total_sales"),
                func.sum(Transaction.commission_amount).label("total_commissions"),
            )
            .filter(Transaction.transaction_type == "Sale")
            .first()
        )

        logger.info("Successfully fetched agents table")
        return templates.TemplateResponse(
            "admin/agents/table.html",  # Make sure this template exists
            {
                "request": request,
                "agents": agents,
                "total_agents": stats["total_agents"],
                "total_listings": stats["total_listings"],
                "total_sales": sales_data.total_sales or 0 if sales_data else 0,
                "total_commissions": (
                    sales_data.total_commissions or 0 if sales_data else 0
                ),
                "today": date.today(),
            },
        )
    except Exception as e:
        logger.error("Failed to fetch agents table", exc_info=True)
        return templates.TemplateResponse(
            "admin/agents/table.html",
            {
                "request": request,
                "error": "Failed to load agents",
                "agents": [],
                "total_agents": 0,
                "total_listings": 0,
                "total_sales": 0,
                "total_commissions": 0,
                "today": date.today(),
            },
        )


@router.post("/agents", response_class=HTMLResponse)
async def create_agent(
    request: Request,
    agent_name: str = Form(...),
    NRDS: str = Form(...),
    agent_phone: str = Form(...),
    agent_email: str = Form(...),
    SSN: str = Form(...),
    license_number: str = Form(...),
    license_expiration: str = Form(...),
    db: Session = Depends(get_db),
):
    """Create a new agent"""
    try:
        # Format and validate data
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()
        phone = (
            agent_phone.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )
        ssn = SSN.replace("-", "")

        agent = Agent(
            agent_name=agent_name,
            NRDS=NRDS,
            agent_phone=phone,
            agent_email=agent_email,
            SSN=ssn,
            license_number=license_number,
            license_expiration=expiration_date,
            broker_id=1,
        )

        db.add(agent)
        db.commit()

        logger.info(f"Agent created successfully: {agent_name}")
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Agent {agent_name} created successfully",
                "type": "success",
            },
        )
    except ValueError as e:
        db.rollback()
        logger.error("Invalid data format for agent creation", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Invalid date format for license expiration",
                "type": "error",
            },
        )
    except Exception as e:
        db.rollback()
        logger.error("Failed to create agent", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error creating agent: {str(e)}",
                "type": "error",
            },
        )


@router.get("/agents/{agent_id}/edit", response_class=HTMLResponse)
async def edit_agent_form(
    request: Request, agent_id: int, db: Session = Depends(get_db)
):
    """Get the edit form for an agent"""
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        logger.info(f"Fetching edit form for agent: {agent_id}")
        return templates.TemplateResponse(
            "admin/agents/edit_form.html", {"request": request, "agent": agent}
        )
    except Exception as e:
        logger.error(f"Error fetching agent edit form: {agent_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}", response_class=HTMLResponse)
async def update_agent(
    request: Request,
    agent_id: int,
    agent_name: str = Form(...),
    NRDS: str = Form(...),
    agent_phone: str = Form(...),
    agent_email: str = Form(...),
    license_number: str = Form(...),
    license_expiration: str = Form(...),
    db: Session = Depends(get_db),
):
    """Update an existing agent"""
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Update agent fields
        agent.agent_name = agent_name
        agent.NRDS = NRDS
        agent.agent_phone = (
            agent_phone.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )
        agent.agent_email = agent_email
        agent.license_number = license_number
        agent.license_expiration = datetime.strptime(
            license_expiration, "%Y-%m-%d"
        ).date()

        db.commit()

        logger.info(f"Agent updated successfully: {agent_id}")
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Agent updated successfully",
                "type": "success",
            },
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update agent: {agent_id}", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error updating agent: {str(e)}",
                "type": "error",
            },
        )


@router.delete("/properties/{property_id}")
async def delete_property(property_id: int, db: Session = Depends(get_db)):
    """Delete a property"""
    try:
        logger.info(f"Attempting to delete property {property_id}")

        # Begin transaction
        property = (
            db.query(Property).filter(Property.property_id == property_id).first()
        )
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

        # Delete residential/commercial details first if they exist
        residential = (
            db.query(ResidentialProperty)
            .filter(ResidentialProperty.property_id == property_id)
            .first()
        )
        if residential:
            db.delete(residential)

        commercial = (
            db.query(CommercialProperty)
            .filter(CommercialProperty.property_id == property_id)
            .first()
        )
        if commercial:
            db.delete(commercial)

        # Delete related records
        db.query(AgentListing).filter(AgentListing.property_id == property_id).delete()
        db.query(AgentShowing).filter(AgentShowing.property_id == property_id).delete()
        db.query(Contract).filter(Contract.property_id == property_id).delete()
        db.query(Transaction).filter(Transaction.property_id == property_id).delete()

        # Delete the property
        db.delete(property)
        db.commit()

        logger.info(f"Successfully deleted property {property_id}")
        # Return empty string to swap out the row
        return Response("")

    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to delete property {property_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to delete property: {str(e)}"
        )


@router.delete("/agents/{agent_id}")
async def delete_agent(request: Request, agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent"""
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        db.delete(agent)
        db.commit()

        logger.info(f"Agent deleted successfully: {agent_id}")
        return JSONResponse(
            content={"success": True, "message": "Agent deleted successfully"}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete agent: {agent_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
