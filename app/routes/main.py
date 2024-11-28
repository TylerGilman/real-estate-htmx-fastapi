# app/routes/main.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Optional
from ..core.logging_config import logger
from app.core.database import get_db_connection
from mysql.connector import Error

router = APIRouter(tags=["main"])
templates = Jinja2Templates(directory="app/templates")


async def call_procedure(conn, procedure_name: str, params: tuple = ()):
    """Helper function to call stored procedures"""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(procedure_name, params)

        results = None
        for result in cursor.stored_results():
            results = result.fetchall()

        return results
    except Error as e:
        logger.error(f"Database error in {procedure_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()


async def is_db_empty(conn) -> bool:
    """Check if the database is empty using stored procedure"""
    try:
        result = await call_procedure(conn, "get_property_count")
        return result[0]["count"] == 0 if result else True
    except Error as e:
        logger.error(f"Error checking if database is empty: {str(e)}")
        return True


@router.get("/")
async def index(request: Request, conn=Depends(get_db_connection)):
    """Homepage route"""
    try:
        # Get all properties with their details
        properties = await call_procedure(conn, "get_all_properties_with_details")

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "properties": properties,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching properties: {str(e)}")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "properties": [],
                "error": "Failed to load properties",
            },
        )


@router.get("/about")
async def about(request: Request):
    """About page route"""
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/contact")
async def contact(request: Request):
    """Contact page route"""
    return templates.TemplateResponse("contact.html", {"request": request})


@router.get("/search")
async def search(
    request: Request,
    query: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    conn=Depends(get_db_connection),
):
    """Search properties route"""
    try:
        # Search properties using stored procedure
        properties = await call_procedure(
            conn,
            "search_properties_with_filters",
            (query, property_type, min_price, max_price),
        )

        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/listings.html", {"request": request, "properties": properties}
            )

        return templates.TemplateResponse(
            "search.html", {"request": request, "properties": properties}
        )

    except Exception as e:
        logger.error(f"Error searching properties: {str(e)}")
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "properties": [],
                "error": "Failed to search properties",
            },
        )
