from fastapi import APIRouter, Request, Depends, HTTPException, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from typing import Optional
from datetime import datetime, date
from app.core.logging_config import logger
from app.core.security import get_current_admin, get_password_hash
from app.core.database import get_db_connection, execute_procedure
import mysql.connector
UPLOAD_DIR = "app/static/property_images"

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection)
):
    """Main admin dashboard view"""
    try:
        # Get all clients
        clients = execute_procedure(conn, 'get_all_clients')

        context = {
            "request": request,
            "current_user": current_user,
            "agents": [],
            "properties": [],
            "total_agents": 0,
            "total_listings": 0,
            "total_properties": 0,
            "total_sales": 0,
            "total_commissions": 0,
            "today": date.today(),
            "clients": clients  # Add clients to context
        }

        # Fetch dashboard stats
        dashboard_stats = execute_procedure(conn, 'get_admin_dashboard_stats')
        if dashboard_stats:
            context.update(dashboard_stats[0])

        # Fetch agents and properties
        context["properties"] = execute_procedure(conn, 'get_all_properties')
        context["agents"] = execute_procedure(conn, 'get_all_agents')

        return templates.TemplateResponse("admin/dashboard.html", context)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load dashboard data")

@router.get("/clients")
async def list_clients(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection)
):
    """List all clients"""
    try:
        clients = execute_procedure(conn, 'get_all_clients')
        return templates.TemplateResponse(
            "admin/clients/list.html",
            {
                "request": request,
                "clients": clients,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch clients")

@router.post("/clients")
async def create_client(
    request: Request,
    client_name: str = Form(...),
    client_phone: str = Form(...),
    client_email: str = Form(...),
    mailing_address: str = Form(...),
    SSN: str = Form(...),
    conn=Depends(get_db_connection)
):
    """Create a new client"""
    try:
        # Format phone number and SSN
        phone = client_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        ssn = SSN.replace("-", "")

        # Create client using stored procedure
        execute_procedure(
            conn,
            'create_client',
            (client_name, phone, client_email, mailing_address, ssn)
        )
        
        # Get the newly created client
        client = execute_procedure(conn, 'get_all_clients')[-1]  # Get most recently added client

        # Return the new row HTML
        return templates.TemplateResponse(
            "admin/clients/table_row.html",
            {
                "request": request,
                "client": client
            }
        )
    except Exception as e:
        logger.error(f"Failed to create client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating client: {str(e)}")

@router.get("/clients/{client_id}/edit")
async def edit_client_form(
    request: Request,
    client_id: int,
    conn=Depends(get_db_connection)
):
    """Get the edit form for a client"""
    try:
        client = execute_procedure(conn, 'get_client_details', (client_id,))
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return templates.TemplateResponse(
            "admin/clients/edit_form.html",
            {"request": request, "client": client[0]}
        )
    except Exception as e:
        logger.error(f"Error fetching client edit form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/clients/{client_id}")
async def update_client(
    request: Request,
    client_id: int,
    client_name: str = Form(...),
    client_phone: str = Form(...),
    client_email: str = Form(...),
    mailing_address: str = Form(...),
    conn=Depends(get_db_connection)
):
    """Update an existing client"""
    try:
        phone = client_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")

        execute_procedure(
            conn,
            'update_client',
            (client_id, client_name, phone, client_email, mailing_address)
        )

        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Client updated successfully",
                "type": "success"
            }
        )
    except Exception as e:
        logger.error(f"Failed to update client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating client: {str(e)}")

@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, conn=Depends(get_db_connection)):
    """Delete a client"""
    try:
        execute_procedure(conn, 'delete_client', (client_id,))
        return JSONResponse(content={"success": True, "message": "Client deleted successfully"})
    except Exception as e:
        logger.error(f"Failed to delete client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/properties/{property_id}")
async def delete_property(property_id: int, conn=Depends(get_db_connection)):
    """Delete a property using stored procedure"""
    try:
        execute_procedure(conn, 'delete_property', (property_id,))
        return Response("")
    except Exception as e:
        logger.error(f"Failed to delete property {property_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete property: {str(e)}")

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, conn=Depends(get_db_connection)):
    """Delete an agent using stored procedure"""
    try:
        execute_procedure(conn, 'delete_agent', (agent_id,))
        return JSONResponse(content={"success": True, "message": "Agent deleted successfully"})
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties/table", response_class=HTMLResponse)
async def properties_table(request: Request, conn=Depends(get_db_connection)):
    """Properties table component using stored procedure"""
    try:
        context = {
            "request": request,
            "properties": [],
            "total_properties": 0,
            "active_listings": 0,
            "total_value": 0,
            "avg_price": 0,
        }

        context["properties"] = execute_procedure(conn, 'get_all_properties')
        stats = execute_procedure(conn, 'get_property_stats')
        if stats:
            context.update(stats[0])

        return templates.TemplateResponse("admin/properties/table.html", context)
    except Exception as e:
        logger.error(f"Failed to fetch properties table: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load properties")


@router.get("/agents/table", response_class=HTMLResponse)
async def agents_table(request: Request, conn=Depends(get_db_connection)):
    """Agents table component using stored procedure"""
    try:
        context = {
            "request": request,
            "agents": [],
            "total_agents": 0,
            "total_listings": 0,
            "total_sales": 0,
            "total_commissions": 0,
            "today": date.today(),
        }

        context["agents"] = execute_procedure(conn, 'get_all_agents')
        stats = execute_procedure(conn, 'get_agent_stats')
        sales_data = execute_procedure(conn, 'get_sales_stats')

        if stats:
            context.update({
                "total_agents": stats[0].get("total_agents", 0),
                "total_listings": stats[0].get("total_listings", 0),
            })
        if sales_data:
            context.update({
                "total_sales": sales_data[0].get("total_sales", 0),
                "total_commissions": sales_data[0].get("total_commissions", 0),
            })

        return templates.TemplateResponse("admin/agents/table.html", context)
    except Exception as e:
        logger.error(f"Failed to fetch agents table: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load agents")

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
    conn=Depends(get_db_connection),
):
    """Create a new agent using stored procedure."""
    try:
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        # Call the procedure
        agent_id_result = execute_procedure(
            conn,
            "create_agent",
            (agent_name, NRDS, agent_phone, agent_email, SSN, license_number, expiration_date, 1),
        )

        # Log the raw result for debugging
        logger.debug(f"Procedure result: {agent_id_result}")

        # Check for empty result or improper format
        if not agent_id_result or not isinstance(agent_id_result, list):
            raise ValueError("Procedure returned no data or unexpected format.")

        # Extract agent ID from the first row
        agent_data = agent_id_result[0]  # Assuming the procedure returns the agent record
        agent_id = agent_data["agent_id"] if isinstance(agent_data, dict) else agent_data[0]

        # Render the HTML row
        return templates.TemplateResponse(
            "admin/agents/agent_row.html",
            {"request": request, "agent": agent_data},
        )

    except mysql.connector.errors.IntegrityError as e:
        logger.error(f"Integrity error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Duplicate entry or integrity constraint violation.")
    except ValueError as e:
        logger.error(f"Value error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {e}")
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {e}")

@router.get("/agents/{agent_id}/edit", response_class=HTMLResponse)
async def edit_agent_form(request: Request, agent_id: int, conn=Depends(get_db_connection)):
    """Get the edit form for an agent using stored procedure"""
    try:
        agent = execute_procedure(conn, 'get_agent_details', (agent_id,))
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return templates.TemplateResponse("admin/agents/edit_form.html", {"request": request, "agent": agent[0]})
    except Exception as e:
        logger.error(f"Error fetching agent edit form: {str(e)}", exc_info=True)
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
    conn=Depends(get_db_connection),
):
    """Update an existing agent using stored procedure"""
    try:
        phone = agent_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        execute_procedure(
            conn,
            'update_agent',
            (agent_id, agent_name, NRDS, phone, agent_email, license_number, expiration_date)
        )

        return templates.TemplateResponse(
            "admin/components/toast.html",
            {"request": request, "message": "Agent updated successfully", "type": "success"},
        )
    except Exception as e:
        logger.error(f"Failed to update agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")


@router.delete("/properties/{property_id}")
async def delete_property(property_id: int, conn=Depends(get_db_connection)):
    """Delete a property using stored procedure"""
    try:
        execute_procedure(conn, 'delete_property', (property_id,))
        return Response("")
    except Exception as e:
        logger.error(f"Failed to delete property {property_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete property: {str(e)}")


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, conn=Depends(get_db_connection)):
    """Delete an agent using stored procedure"""
    try:
        execute_procedure(conn, 'delete_agent', (agent_id,))
        return JSONResponse(content={"success": True, "message": "Agent deleted successfully"})
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/property", response_class=HTMLResponse)
async def admin_add_property(
    request: Request,
    property_name: str,
    tax_id: str,
    property_address: str,
    status: str,
    price: float,
    lot_size: Optional[float] = None,
    year_built: Optional[int] = None,
    zoning: Optional[str] = None,
    property_tax: Optional[float] = None,
    agent_id: Optional[int] = None,
    asking_price: Optional[float] = None,
    listing_date: Optional[str] = None,
    expiration_date: Optional[str] = None,
    db=Depends(get_db_connection)
):
    """
    Admin adds a property and optionally creates an agent listing.

    Renders an HTML row for HTMX swapping on success.
    """
    import logging

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)  # Ensure debug logging is enabled

    try:
        logger.debug("Starting admin_add_property...")
        logger.debug("Received parameters: %s", {
            "property_name": property_name,
            "tax_id": tax_id,
            "property_address": property_address,
            "status": status,
            "price": price,
            "lot_size": lot_size,
            "year_built": year_built,
            "zoning": zoning,
            "property_tax": property_tax,
            "agent_id": agent_id,
            "asking_price": asking_price,
            "listing_date": listing_date,
            "expiration_date": expiration_date,
        })

        # Step 1: Create the property
        logger.debug("Calling stored procedure 'create_property'...")
        property_id_result = execute_procedure(
            db,
            "create_property",
            [
                property_name,
                tax_id,
                property_address,
                status,
                price,
                lot_size,
                year_built,
                zoning,
                property_tax
            ]
        )
        logger.debug("Result from 'create_property': %s", property_id_result)

        if not property_id_result or len(property_id_result) == 0:
            logger.error("Failed to create property: No result returned")
            raise ValueError("Failed to create property")

        property_id = property_id_result[0][0]
        logger.debug("Created property with ID: %s", property_id)

        # Step 2: Optionally create the agent listing
        if agent_id:
            logger.debug("Calling stored procedure 'create_agent_listing'...")
            listing_result = execute_procedure(
                db,
                "create_agent_listing",
                [
                    property_id,
                    agent_id,
                    asking_price,
                    listing_date,
                    expiration_date
                ]
            )
            logger.debug("Result from 'create_agent_listing': %s", listing_result)

            if not listing_result:
                logger.error("Failed to create agent listing: No result returned")
                raise ValueError("Failed to create agent listing")

        # Step 3: Fetch the created property for rendering
        logger.debug("Fetching property details using 'get_property_details'...")
        property_data = execute_procedure(db, "get_property_details", [property_id])
        logger.debug("Result from 'get_property_details': %s", property_data)

        if not property_data or len(property_data) == 0:
            logger.error("Failed to retrieve property details: No data returned")
            raise ValueError("Failed to retrieve property details")

        logger.debug("Rendering property row template...")
        return templates.TemplateResponse(
            "partials/property_row.html",
            {
                "request": request,
                "property": property_data[0]
            }
        )

    except Exception as e:
        logger.exception("Error in admin_add_property: %s", str(e))
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )
