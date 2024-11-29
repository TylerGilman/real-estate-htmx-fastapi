from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Optional
from app.core.database import get_db_connection, execute_procedure
from app.core.security import get_current_agent
from app.core.logging_config import logger

router = APIRouter(tags=["properties"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def properties_list(
    request: Request, page: int = 1, limit: int = 12, conn=Depends(get_db_connection)
):
    """List all properties with pagination using stored procedure"""
    try:
        offset = (page - 1) * limit
        properties = execute_procedure(
            conn, "get_paginated_properties", (offset, limit)
        )
        total_count = execute_procedure(conn, "get_total_property_count")

        total = total_count[0]["count"] if total_count else 0
        total_pages = (total + limit - 1) // limit

        return templates.TemplateResponse(
            "properties/list.html",
            {
                "request": request,
                "properties": properties,
                "page": page,
                "total_pages": total_pages,
                "total": total,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching properties list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching properties")


@router.get("/{tax_id}")
async def property_detail(
    request: Request, tax_id: str, conn=Depends(get_db_connection)
):
    """Get property details using stored procedure"""
    try:
        property = execute_procedure(conn, "get_property_by_tax_id", (tax_id,))

        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

        return templates.TemplateResponse(
            "properties/detail.html", {"request": request, "property": property[0]}
        )
    except Exception as e:
        logger.error(f"Error fetching property {tax_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching property")


@router.post("/search")
async def search_properties(request: Request, conn=Depends(get_db_connection)):
    """Search properties using stored procedure"""
    try:
        form = await request.form()
        search_query = form.get("search-text", "").lower()

        properties = execute_procedure(conn, "search_properties", (search_query,))

        return templates.TemplateResponse(
            "partials/listings.html", {"request": request, "properties": properties}
        )
    except Exception as e:
        logger.error(f"Error searching properties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error searching properties")


@router.post("/randomize")
async def randomize_properties(request: Request, conn=Depends(get_db_connection)):
    """Randomize property listing order using stored procedure"""
    try:
        properties = execute_procedure(conn, "get_all_properties")

        # Shuffle the list of properties
        properties_list = list(properties)
        random.shuffle(properties_list)

        return templates.TemplateResponse(
            "partials/listings.html",
            {"request": request, "properties": properties_list},
        )
    except Exception as e:
        logger.error(f"Error randomizing properties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error randomizing properties")


@router.get("/agent-listings", response_class=HTMLResponse)
async def agent_listings(
    request: Request,
    current_user: dict = Depends(get_current_agent),
    conn=Depends(get_db_connection),
):
    """Get listings for the current agent using stored procedure"""
    try:
        agent_id = current_user["agent"]["agent_id"]
        properties = execute_procedure(conn, "get_agent_properties", (agent_id,))

        return templates.TemplateResponse(
            "properties/agent_listings.html",
            {"request": request, "properties": properties},
        )
    except Exception as e:
        logger.error(f"Error fetching agent listings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching agent listings")
