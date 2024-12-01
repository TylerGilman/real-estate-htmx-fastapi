from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Optional
from ..core.logging_config import logger
from app.core.database import get_db_connection, execute_procedure

router = APIRouter(tags=["main"])
templates = Jinja2Templates(directory="app/templates")


async def is_db_empty(conn) -> bool:
    """Check if the database is empty using stored procedure"""
    try:
        result = execute_procedure(conn, "get_property_count")
        return result[0]["count"] == 0 if result else True
    except Exception as e:
        logger.error(f"Error checking if database is empty: {str(e)}")
        return True


@router.get("/")
async def index(request: Request, conn=Depends(get_db_connection)):
    """Homepage route"""
    try:
        # First get debug info
        logger.debug("Running debug query...")
        debug_info = execute_procedure(conn, "debug_tables_data")
        logger.debug(f"Debug info: {debug_info}")

        # Fetch all properties with their agent listings and details
        logger.debug("Fetching listings...")
        listings = execute_procedure(conn, "get_all_agent_listings_with_details")
        logger.debug(f"Found {len(listings) if listings else 0} listings")

        if not listings:
            logger.warning("No listings found in the database")

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "listings": listings,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching listings: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "listings": [],
                "error": "Failed to load listings",
            },
        )


@router.get("/search")
async def search(
    request: Request,
    query: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    agent_name: Optional[str] = None,
    conn=Depends(get_db_connection),
):
    """Search listings route with extended filters"""
    try:
        # Search listings using stored procedure with extended parameters
        listings = execute_procedure(
            conn,
            "search_agent_listings_with_filters",
            (query, property_type, min_price, max_price, agent_name),
        )

        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/listings.html", {"request": request, "listings": listings}
            )

        return templates.TemplateResponse(
            "search.html", {"request": request, "listings": listings}
        )

    except Exception as e:
        logger.error(f"Error searching listings: {str(e)}")
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "listings": [],
                "error": "Failed to search listings",
            },
        )


@router.get("/properties/{property_id}")
async def property_detail(
    request: Request, property_id: int, conn=Depends(get_db_connection)
):
    """Get detailed property information"""
    try:
        # Get property details with agent info and residential/commercial details
        property_details = execute_procedure(
            conn, "get_property_details", (property_id,)
        )

        if not property_details:
            raise HTTPException(status_code=404, detail="Property not found")

        logger.debug(f"Found property details: {property_details[0]}")

        return templates.TemplateResponse(
            "properties/detail.html",
            {"request": request, "property": property_details[0]},
        )
    except Exception as e:
        logger.error(f"Error fetching property details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Keep other routes as is
@router.get("/about")
async def about(request: Request):
    """About page route"""
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/contact")
async def contact(request: Request):
    """Contact page route"""
    return templates.TemplateResponse("contact.html", {"request": request})
