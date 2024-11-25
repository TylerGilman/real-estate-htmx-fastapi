# app/routes/admin.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any
from datetime import date, datetime
from ..core.database import get_db
from ..core.logging_config import logger
from ..models import (
    Property, ResidentialProperty, CommercialProperty,
    Agent, AgentListing, AgentShowing, Transaction
)

from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Main Dashboard Route
@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Main admin dashboard view"""
    try:
        agents = db.query(Agent).all()
        
        # Agent statistics with safe defaults
        total_agents = db.query(func.count(Agent.agent_id)).scalar() or 0
        total_listings = db.query(func.count(AgentListing.listing_id)).scalar() or 0
        
        # Sales statistics with safe handling of None values
        sales_data = db.query(
            func.sum(Transaction.amount).label('total_sales'),
            func.sum(Transaction.commission_amount).label('total_commissions')
        ).filter(Transaction.transaction_type == 'Sale').first()

        context = {
            "request": request,
            "agents": agents,
            "total_agents": total_agents,
            "total_listings": total_listings,
            "total_sales": getattr(sales_data, 'total_sales', 0) or 0,
            "total_commissions": getattr(sales_data, 'total_commissions', 0) or 0,
            "today": date.today()
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
                "agents": [],
                "total_agents": 0,
                "total_listings": 0,
                "total_sales": 0,
                "total_commissions": 0,
                "today": date.today()
            }
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
            func.count(Property.property_id).label('total_properties'),
            func.sum(Property.price).label('total_value'),
            func.avg(Property.price).label('avg_price')
        ).first()
        
        active_listings = db.query(func.count(Property.property_id))\
            .filter(Property.status.in_(['For Sale', 'For Lease']))\
            .scalar()

        properties = query.all()

        # Ensure all values are properly defaulted
        context = {
            "request": request,
            "properties": properties,
            "total_properties": getattr(property_stats, 'total_properties', 0) or 0,
            "active_listings": active_listings or 0,
            "total_value": getattr(property_stats, 'total_value', 0) or 0,
            "avg_price": getattr(property_stats, 'avg_price', 0) or 0
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
                "avg_price": 0
            }
        )

@router.post("/properties", response_class=HTMLResponse)
async def create_property(
    request: Request,
    title: str = Form(...),
    property_type: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    square_feet: int = Form(...),
    year_built: int = Form(...),
    street_address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Create and add the property
        property = Property(
            title=title,
            property_type=property_type,
            price=price,
            status=status,
            square_feet=square_feet,
            year_built=year_built,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
        )
        db.add(property)
        db.commit()

        # Render the new property row
        property_row = templates.TemplateResponse(
            "admin/properties/table_row.html",
            {"request": request, "property": property},
        )

        # Render the toast
        toast = templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Property created successfully",
                "type": "success",
            },
        )

        # Combine the row and toast for HTMX response
        response_content = f"{property_row.body.decode()} {toast.body.decode()}"
        return HTMLResponse(response_content)
    except Exception as e:
        db.rollback()
        logger.error("Failed to create property", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error creating property: {str(e)}",
                "type": "error",
            },
        )

@router.delete("/properties/{property_id}")
async def delete_property(property_id: int, db: Session = Depends(get_db)):
    """Delete a property"""
    try:
        property = db.query(Property).filter(Property.property_id == property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
            
        db.delete(property)
        db.commit()
        
        logger.info(f"Property deleted successfully: {property_id}")
        return JSONResponse(content={"success": True, "message": "Property deleted successfully"})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete property: {property_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Agent Routes
@router.get("/agents/table", response_class=HTMLResponse)
async def agents_table(request: Request, db: Session = Depends(get_db)):
    """Agents table component"""
    try:
        agents = db.query(Agent).all()
        
        stats = {
            "total_agents": db.query(func.count(Agent.agent_id)).scalar() or 0,
            "total_listings": db.query(func.count(AgentListing.listing_id)).scalar() or 0,
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
                "total_commissions": sales_data.total_commissions or 0 if sales_data else 0,
                "today": date.today()
            }
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
                "today": date.today()
            }
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
    db: Session = Depends(get_db)
):
    """Create a new agent"""
    try:
        # Format and validate data
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()
        phone = agent_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        ssn = SSN.replace("-", "")

        agent = Agent(
            agent_name=agent_name,
            NRDS=NRDS,
            agent_phone=phone,
            agent_email=agent_email,
            SSN=ssn,
            license_number=license_number,
            license_expiration=expiration_date,
            broker_id=1
        )

        db.add(agent)
        db.commit()

        logger.info(f"Agent created successfully: {agent_name}")
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Agent {agent_name} created successfully",
                "type": "success"
            }
        )
    except ValueError as e:
        db.rollback()
        logger.error("Invalid data format for agent creation", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Invalid date format for license expiration",
                "type": "error"
            }
        )
    except Exception as e:
        db.rollback()
        logger.error("Failed to create agent", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error creating agent: {str(e)}",
                "type": "error"
            }
        )

@router.get("/agents/{agent_id}/edit", response_class=HTMLResponse)
async def edit_agent_form(request: Request, agent_id: int, db: Session = Depends(get_db)):
    """Get the edit form for an agent"""
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        logger.info(f"Fetching edit form for agent: {agent_id}")
        return templates.TemplateResponse(
            "admin/agents/edit_form.html",
            {
                "request": request,
                "agent": agent
            }
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
    db: Session = Depends(get_db)
):
    """Update an existing agent"""
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Update agent fields
        agent.agent_name = agent_name
        agent.NRDS = NRDS
        agent.agent_phone = agent_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        agent.agent_email = agent_email
        agent.license_number = license_number
        agent.license_expiration = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        db.commit()
        
        logger.info(f"Agent updated successfully: {agent_id}")
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Agent updated successfully",
                "type": "success"
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update agent: {agent_id}", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error updating agent: {str(e)}",
                "type": "error"
            }
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
        return JSONResponse(content={"success": True, "message": "Agent deleted successfully"})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete agent: {agent_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
