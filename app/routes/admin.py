# app/routes/admin.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text  # Add text import here
from typing import Optional
from datetime import date
from ..core.database import get_db
from ..core.logging_config import logger
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
)
import random
from fastapi import File, UploadFile
import os
from datetime import datetime
import shutil

# Add at the top with other imports
UPLOAD_DIR = "app/static/property_images"

from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Main Dashboard Route
@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
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
    year_built: int = Form(...),
    lot_size: float = Form(None),
    zoning: str = Form(None),
    property_tax: float = Form(None),
    # Add image field
    image: UploadFile = File(None),
    # Residential specific fields
    bedrooms: int = Form(None),
    bathrooms: float = Form(None),
    r_type: str = Form(None),
    square_feet: float = Form(None),
    garage_spaces: int = Form(None),
    has_basement: bool = Form(False),
    has_pool: bool = Form(False),
    # Commercial specific fields
    commercial_sqft: float = Form(None),  # Changed from sqft to commercial_sqft
    industry: str = Form(None),
    c_type: str = Form(None),
    num_units: int = Form(None),
    parking_spaces: int = Form(None),
    zoning_type: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Creating new property: {property_address}")

        # Generate a unique tax_id
        tax_id = f"TAX{random.randint(100000, 999999)}"

        # Create base property first
        property = Property(
            tax_id=tax_id,
            property_address=property_address,
            status=PropertyStatus(status),
            price=price,
            lot_size=lot_size if lot_size else None,
            year_built=year_built,
            zoning=zoning if zoning else None,
            property_tax=property_tax if property_tax else None,
        )

        db.add(property)
        db.flush()  # Get the property_id

        # Handle image upload if provided
        if image:
            try:
                # Create directory structure: property_images/year/month/property_id/
                date_path = datetime.now().strftime("%Y/%m")
                property_path = f"{property.property_id}"
                full_path = os.path.join(UPLOAD_DIR, date_path, property_path)
                os.makedirs(full_path, exist_ok=True)

                # Generate unique filename
                file_name = f"{datetime.now().timestamp()}_{image.filename}"
                file_path = os.path.join(full_path, file_name)

                # Save the file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)

                # Store the relative path in the database
                property.image_url = f"/static/property_images/{date_path}/{property_path}/{file_name}"
                logger.info(f"Saved property image: {property.image_url}")

            except Exception as img_error:
                logger.error(f"Failed to save image: {str(img_error)}", exc_info=True)
                # Continue with property creation even if image upload fails
                property.image_url = None

        # Rest of your existing property creation code...
        if property_type.upper() == "RESIDENTIAL":
            logger.info("Adding residential details")
            residential = ResidentialProperty(
                property_id=property.property_id,
                bedrooms=bedrooms if bedrooms else None,
                bathrooms=bathrooms if bathrooms else None,
                r_type=r_type if r_type else None,
                square_feet=square_feet if square_feet else None,
                garage_spaces=garage_spaces if garage_spaces else None,
                has_basement=True if has_basement == "true" else False,
                has_pool=True if has_pool == "true" else False,
            )
            db.add(residential)

        elif property_type.upper() == "COMMERCIAL":
            logger.info("Adding commercial details")
            commercial = CommercialProperty(
                property_id=property.property_id,
                sqft=commercial_sqft if commercial_sqft else None,  # Updated to use commercial_sqft
                industry=industry if industry else None,
                c_type=c_type if c_type else None,
                num_units=num_units if num_units else None,
                parking_spaces=parking_spaces if parking_spaces else None,
                zoning_type=zoning_type if zoning_type else None,
            )
            db.add(commercial)
            logger.info("Commercial details added")

        db.commit()
        logger.info(f"Property committed to database with ID: {property.property_id}")

        created_property = db.query(Property).filter(Property.tax_id == tax_id).first()
        
        return templates.TemplateResponse(
            "admin/properties/table_row.html",
            {"request": request, "property": created_property},
            headers={"HX-Trigger": "propertyCreated"},
        )

    except Exception as e:
        logger.error(f"Failed to create property", exc_info=True)
        raise


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
