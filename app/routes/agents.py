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

router = APIRouter(tags=["agents"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def agent_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    print("agent")
    """Agent's personal dashboard"""
    try:
        agent = current_user["agent"]
        
        # Get agent's listings
        listings = (
            db.query(Property)
            .join(AgentListing)
            .filter(AgentListing.agent_id == agent.agent_id)
            .all()
        )
        
        # Get statistics
        active_listings = len([l for l in listings if l.status in 
                             [PropertyStatus.FOR_SALE, PropertyStatus.FOR_LEASE]])
        
        total_sales = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.agent_id == agent.agent_id)
            .scalar() or 0
        )
        
        total_commissions = (
            db.query(func.sum(Transaction.commission_amount))
            .filter(Transaction.agent_id == agent.agent_id)
            .scalar() or 0
        )
        
        # Get upcoming showings
        upcoming_showings = (
            db.query(AgentShowing)
            .filter(
                AgentShowing.agent_id == agent.agent_id,
                AgentShowing.showing_date >= date.today()
            )
            .order_by(AgentShowing.showing_date)
            .limit(5)
            .all()
        )

        context = {
            "request": request,
            "agent": agent,
            "listings": listings,
            "active_listings": active_listings,
            "total_sales": total_sales,
            "total_commissions": total_commissions,
            "upcoming_showings": upcoming_showings
        }
        
        logger.info(f"Agent dashboard loaded for agent {agent.agent_id}")
        return templates.TemplateResponse("agents/dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Error loading agent dashboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading dashboard")

@router.get("/listings", response_class=HTMLResponse)
async def agent_listings(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """View agent's listings"""
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
                "listings": listings
            }
        )
    except Exception as e:
        logger.error(f"Error fetching agent listings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching listings")

@router.get("/showings", response_class=HTMLResponse)
async def agent_showings(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """View and manage showings"""
    try:
        agent = current_user["agent"]
        showings = (
            db.query(AgentShowing)
            .filter(AgentShowing.agent_id == agent.agent_id)
            .order_by(AgentShowing.showing_date.desc())
            .all()
        )
        
        return templates.TemplateResponse(
            "agents/showings.html",
            {
                "request": request,
                "agent": agent,
                "showings": showings
            }
        )
    except Exception as e:
        logger.error(f"Error fetching agent showings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching showings")

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
        showing_datetime = datetime.strptime(showing_date, "%Y-%m-%d").date()
        
        showing = AgentShowing(
            property_id=property_id,
            agent_id=agent.agent_id,
            client_id=client_id,
            showing_date=showing_datetime,
            notes=notes
        )
        
        db.add(showing)
        db.commit()
        
        return templates.TemplateResponse(
            "agents/components/showing_card.html",
            {
                "request": request,
                "showing": showing
            }
        )
    except Exception as e:
        logger.error(f"Error creating showing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating showing")

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
