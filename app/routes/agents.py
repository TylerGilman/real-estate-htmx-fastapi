# app/routes/agents.py
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..core.logging_config import logger
from ..core.security import get_current_agent
from ..models import (
    Agent,
    Property,
    AgentListing,
    AgentShowing,
    Transaction,
    PropertyStatus
)
from typing import Optional
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload

router = APIRouter(tags=["agents"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def agent_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Agent's personal dashboard"""
    try:
        agent = current_user["agent"]
        print("Agent - " + str(agent.agent_name))  # Debug print
        
        # Get agent's listings - check the SQL query being generated
        listings_query = (
            db.query(Property)
            .join(AgentListing)
            .filter(AgentListing.agent_id == agent.agent_id)
        )
        logger.info(f"Listings query: {str(listings_query)}")  # Log the query
        listings = listings_query.all()
        logger.info(f"Found {len(listings)} listings for agent")
        
        # Add debug prints
        for listing in listings:
            logger.info(f"Listing: {listing.property_address}")

        active_listings = len([l for l in listings if l.status in 
                             [PropertyStatus.FOR_SALE, PropertyStatus.FOR_LEASE]])
        logger.info(f"Active listings: {active_listings}")

        # Get statistics
        total_sales = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.agent_id == agent.agent_id)
            .scalar() or 0
        )
        
        upcoming_showings = (
            db.query(AgentShowing)
            .filter(
                AgentShowing.agent_id == agent.agent_id,
                AgentShowing.showing_date >= date.today()
            )
            .order_by(AgentShowing.showing_date)
            .all()
        )

        context = {
            "request": request,
            "agent": agent,
            "listings": listings,
            "active_listings": active_listings,
            "total_sales": total_sales,
            "upcoming_showings": upcoming_showings
        }
        
        return templates.TemplateResponse("agents/dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Error loading agent dashboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading dashboard")



@router.get("/listings/{property_id}/edit", response_class=HTMLResponse)
async def edit_property_form(
    request: Request, property_id: int, current_user: dict = Depends(get_current_agent), db: Session = Depends(get_db)
):
    """Get the form for editing a property."""
    try:
        agent = current_user["agent"]
        # Ensure the agent is the listing agent for this property
        listing = (
            db.query(Property)
            .join(AgentListing)
            .filter(AgentListing.agent_id == agent.agent_id, Property.property_id == property_id)
            .first()
        )

        if not listing:
            raise HTTPException(status_code=403, detail="Not authorized to edit this property.")

        return templates.TemplateResponse(
            "agents/edit_property.html",
            {"request": request, "property": listing},
        )
    except Exception as e:
        logger.error(f"Error fetching edit form for property {property_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching edit form")


@router.post("/listings/{property_id}/edit", response_class=HTMLResponse)
async def update_property(
    request: Request,
    property_id: int,
    address: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Update an existing property listing."""
    try:
        agent = current_user["agent"]

        # Ensure the agent is the listing agent for this property
        listing = (
            db.query(Property)
            .join(AgentListing)
            .filter(AgentListing.agent_id == agent.agent_id, Property.property_id == property_id)
            .first()
        )

        if not listing:
            raise HTTPException(status_code=403, detail="Not authorized to edit this property.")

        # Update property details
        listing.address = address
        listing.price = price
        listing.status = status
        db.commit()

        return RedirectResponse(url="/agent/listings", status_code=303)
    except Exception as e:
        logger.error(f"Failed to update property {property_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating property")

@router.post("/showings", response_class=HTMLResponse)
async def create_showing(
    request: Request,
    property_id: int = Form(...),
    showing_date: str = Form(...),
    client_id: int = Form(...),
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Schedule a new showing"""
    try:
        agent = current_user["agent"]
        showing_datetime = datetime.strptime(showing_date, "%Y-%m-%d %H:%M")
        
        showing = AgentShowing(
            property_id=property_id,
            agent_id=agent.agent_id,
            client_id=client_id,
            showing_date=showing_datetime,
            notes=notes,
            agent_role=AgentRole.SELLER_AGENT
        )
        
        db.add(showing)
        db.commit()
        
        return templates.TemplateResponse(
            "components/toast.html",
            {"request": request, "message": "Showing scheduled successfully", "type": "success"}
        )

    except Exception as e:
        logger.error(f"Error creating showing: {str(e)}")
        return templates.TemplateResponse(
            "components/toast.html",
            {"request": request, "message": "Failed to schedule showing", "type": "error"}
        )

@router.delete("/showings/{showing_id}")
async def cancel_showing(
    showing_id: int,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Cancel a showing"""
    try:
        showing = db.query(AgentShowing).filter(
            AgentShowing.showing_id == showing_id,
            AgentShowing.agent_id == current_user["agent"].agent_id
        ).first()
        
        if not showing:
            raise HTTPException(status_code=404, detail="Showing not found")
            
        db.delete(showing)
        db.commit()
        
        return {"message": "Showing cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling showing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel showing")

@router.get("/listings", response_class=HTMLResponse)
async def agent_listings(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """View all properties the agent is listing."""
    try:
        agent = current_user["agent"]
        listings = (
            db.query(Property)
            .join(AgentListing)
            .filter(AgentListing.agent_id == agent.agent_id)
            .all()
        )

        return templates.TemplateResponse(
            "agents/listings.html",
            {
                "request": request,
                "agent": agent,
                "listings": listings,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching agent listings: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching listings")

@router.get("/transactions", response_class=HTMLResponse)
async def agent_transactions(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """View agent's transactions"""
    try:
        agent = current_user["agent"]
        transactions = (
            db.query(Transaction)
            .filter(Transaction.agent_id == agent.agent_id)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )
        
        return templates.TemplateResponse(
            "agents/transactions.html",
            {
                "request": request,
                "agent": agent,
                "transactions": transactions
            }
        )
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching transactions")
