from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from datetime import date, datetime
from ..core.database import get_db_connection, execute_procedure
from ..core.logging_config import logger
from ..core.security import get_current_agent

router = APIRouter(tags=["agents"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def agent_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """Agent's personal dashboard using stored procedures"""
    try:
        agent = current_user["agent"]

        # Fetch data using stored procedures
        listings = execute_procedure(conn, "get_agent_listings", (agent["agent_id"],))
        active_listings = execute_procedure(
            conn, "get_active_listings_count", (agent["agent_id"],)
        )
        total_sales = execute_procedure(conn, "get_total_sales", (agent["agent_id"],))
        upcoming_showings = execute_procedure(
            conn, "get_upcoming_showings", (agent["agent_id"],)
        )

        context = {
            "request": request,
            "agent": agent,
            "listings": listings,
            "active_listings": active_listings[0]["count"] if active_listings else 0,
            "total_sales": total_sales[0]["total"] if total_sales else 0,
            "upcoming_showings": upcoming_showings,
        }

        return templates.TemplateResponse("agents/dashboard.html", context)
    except Exception as e:
        logger.error(f"Error loading agent dashboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading dashboard")


@router.get("/listings/{property_id}/edit", response_class=HTMLResponse)
async def edit_property_form(
    request: Request,
    property_id: int,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """Get the form for editing a property using stored procedure"""
    try:
        agent = current_user["agent"]

        # Ensure the agent is the listing agent for this property
        listing = execute_procedure(
            conn, "get_agent_property", (agent["agent_id"], property_id)
        )
        if not listing:
            raise HTTPException(
                status_code=403, detail="Not authorized to edit this property."
            )

        return templates.TemplateResponse(
            "agents/edit_property.html",
            {"request": request, "property": listing[0]},
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
    conn=Depends(get_db_connection),
):
    """Update an existing property listing using stored procedure"""
    try:
        agent = current_user["agent"]

        # Update property details
        execute_procedure(
            conn,
            "update_property",
            (property_id, agent["agent_id"], address, price, status),
        )

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
    conn=Depends(get_db_connection),
):
    """Schedule a new showing using stored procedure"""
    try:
        agent = current_user["agent"]
        showing_datetime = datetime.strptime(showing_date, "%Y-%m-%d %H:%M")

        execute_procedure(
            conn,
            "create_showing",
            (property_id, agent["agent_id"], client_id, showing_datetime, notes),
        )

        return templates.TemplateResponse(
            "components/toast.html",
            {
                "request": request,
                "message": "Showing scheduled successfully",
                "type": "success",
            },
        )
    except Exception as e:
        logger.error(f"Error creating showing: {str(e)}")
        return templates.TemplateResponse(
            "components/toast.html",
            {
                "request": request,
                "message": "Failed to schedule showing",
                "type": "error",
            },
        )


@router.delete("/showings/{showing_id}")
async def cancel_showing(
    showing_id: int,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """Cancel a showing using stored procedure"""
    try:
        execute_procedure(
            conn, "cancel_showing", (showing_id, current_user["agent"]["agent_id"])
        )
        return {"message": "Showing cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling showing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel showing")


@router.get("/listings", response_class=HTMLResponse)
async def agent_listings(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """View all properties the agent is listing using stored procedure"""
    try:
        agent = current_user["agent"]
        listings = execute_procedure(conn, "get_agent_listings", (agent["agent_id"],))

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
    conn=Depends(get_db_connection),
):
    """View agent's transactions using stored procedure"""
    try:
        agent = current_user["agent"]
        transactions = execute_procedure(
            conn, "get_agent_transactions", (agent["agent_id"],)
        )

        return templates.TemplateResponse(
            "agents/transactions.html",
            {"request": request, "agent": agent, "transactions": transactions},
        )
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching transactions")
