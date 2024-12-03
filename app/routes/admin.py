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


# GET Routes
@router.get("")
async def admin_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection),
):
    """Main admin dashboard view"""
    try:
        # Get all clients
        clients = execute_procedure(conn, "get_all_clients")

        # Get properties with their images
        properties = execute_procedure(conn, "get_all_properties_with_images")

        context = {
            "request": request,
            "current_user": current_user,
            "agents": [],
            "properties": properties,
            "property": {},  # Add empty property for new property form
            "total_agents": 0,
            "total_listings": 0,
            "total_properties": 0,
            "total_sales": 0,
            "total_commissions": 0,
            "today": date.today(),
            "clients": clients,
        }

        # Fetch dashboard stats
        dashboard_stats = execute_procedure(conn, "get_admin_dashboard_stats")
        if dashboard_stats:
            context.update(dashboard_stats[0])

        # Fetch agents
        context["agents"] = execute_procedure(conn, "get_all_agents")

        return templates.TemplateResponse("admin/dashboard.html", context)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load dashboard data")


@router.get("/clients")
async def list_clients(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection),
):
    """List all clients"""
    try:
        clients = execute_procedure(conn, "get_all_clients")
        return templates.TemplateResponse(
            "admin/clients/list.html",
            {"request": request, "clients": clients, "current_user": current_user},
        )
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch clients")


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

        context["properties"] = execute_procedure(conn, "get_all_properties")
        stats = execute_procedure(conn, "get_property_stats")
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

        context["agents"] = execute_procedure(conn, "get_all_agents")
        stats = execute_procedure(conn, "get_agent_stats")
        sales_data = execute_procedure(conn, "get_sales_stats")

        if stats:
            context.update(
                {
                    "total_agents": stats[0].get("total_agents", 0),
                    "total_listings": stats[0].get("total_listings", 0),
                }
            )
        if sales_data:
            context.update(
                {
                    "total_sales": sales_data[0].get("total_sales", 0),
                    "total_commissions": sales_data[0].get("total_commissions", 0),
                }
            )

        return templates.TemplateResponse("admin/agents/table.html", context)
    except Exception as e:
        logger.error(f"Failed to fetch agents table: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load agents")


@router.get("/agents/{agent_id}/edit", response_class=HTMLResponse)
async def edit_agent_form(
    request: Request, agent_id: int, conn=Depends(get_db_connection)
):
    """Get the edit form for an agent using stored procedure"""
    try:
        agent = execute_procedure(conn, "get_agent_details", (agent_id,))
        if not agent:
            raise HTTPException(status_code=403, detail="Agent not found")

        return templates.TemplateResponse(
            "admin/agents/edit_form.html", {"request": request, "agent": agent[-1]}
        )
    except Exception as e:
        logger.error(f"Error fetching agent edit form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=499, detail=str(e))


@router.get("/clients/{client_id}/edit")
async def edit_client_form(
    request: Request, client_id: int, conn=Depends(get_db_connection)
):
    """Get the edit form for a client"""
    try:
        client = execute_procedure(conn, "get_client_details", (client_id,))
        if not client:
            raise HTTPException(status_code=403, detail="Client not found")

        return templates.TemplateResponse(
            "admin/clients/edit_form.html", {"request": request, "client": client[-1]}
        )
    except Exception as e:
        logger.error(f"Error fetching client edit form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=499, detail=str(e))


@router.get("/properties/{property_id}/edit")
async def edit_property_form(
    request: Request,
    property_id: int,
    conn=Depends(get_db_connection)
):
    """Get the edit form for a property"""
    try:
        # Get property with images and details
        property_details = execute_procedure(conn, 'get_property_details_with_images', (property_id,))
        if not property_details:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get agents and clients for form dropdowns
        agents = execute_procedure(conn, 'get_all_agents')
        clients = execute_procedure(conn, 'get_all_clients')
        
        # Render the edit template
        return templates.TemplateResponse(
            "admin/properties/edit.html",  # Use edit.html instead of form.html
            {
                "request": request,
                "property": property_details[0],
                "agents": agents,
                "clients": clients
            }
        )
    except Exception as e:
        logger.error(f"Error fetching property edit form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# POST routes
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
            (
                agent_name,
                NRDS,
                agent_phone,
                agent_email,
                SSN,
                license_number,
                expiration_date,
                1,
            ),
        )

        # Log the raw result for debugging
        logger.debug(f"Procedure result: {agent_id_result}")

        # Check for empty result or improper format
        if not agent_id_result or not isinstance(agent_id_result, list):
            raise ValueError("Procedure returned no data or unexpected format.")

        # Extract agent ID from the first row
        agent_data = agent_id_result[
            0
        ]  # Assuming the procedure returns the agent record
        agent_id = (
            agent_data["agent_id"] if isinstance(agent_data, dict) else agent_data[0]
        )

        # Render the HTML row
        return templates.TemplateResponse(
            "admin/agents/agent_row.html",
            {"request": request, "agent": agent_data},
        )

    except mysql.connector.errors.IntegrityError as e:
        logger.error(f"Integrity error: {e}", exc_info=True)
        raise HTTPException(
            status_code=400, detail="Duplicate entry or integrity constraint violation."
        )
    except ValueError as e:
        logger.error(f"Value error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {e}")
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating agent: {e}")


@router.post("/clients")
async def create_client(
    request: Request,
    client_name: str = Form(...),
    client_phone: str = Form(...),
    client_email: str = Form(...),
    mailing_address: str = Form(...),
    SSN: str = Form(...),
    conn=Depends(get_db_connection),
):
    """Create a new client"""
    try:
        # Format phone number and SSN
        phone = (
            client_phone.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )
        ssn = SSN.replace("-", "")

        # Create client using stored procedure
        execute_procedure(
            conn,
            "create_client",
            (client_name, phone, client_email, mailing_address, ssn),
        )

        # Get the newly created client
        client = execute_procedure(conn, "get_all_clients")[
            -1
        ]  # Get most recently added client

        # Return the new row HTML
        return templates.TemplateResponse(
            "admin/clients/table_row.html", {"request": request, "client": client}
        )
    except Exception as e:
        logger.error(f"Failed to create client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating client: {str(e)}")


@router.post("/property", response_class=HTMLResponse)
async def admin_add_property(
    request: Request,
    tax_id: str = Form(...),
    property_address: str = Form(...),
    status: str = Form(...),
    price: float = Form(...),
    property_type: str = Form(...),
    lot_size: Optional[float] = Form(None),
    year_built: Optional[int] = Form(None),
    zoning: Optional[str] = Form(None),
    property_tax: Optional[float] = Form(None),
    # Residential specific fields
    bedrooms: Optional[int] = Form(None),
    bathrooms: Optional[float] = Form(None),
    r_type: Optional[str] = Form(None),
    square_feet: Optional[float] = Form(None),
    garage_spaces: Optional[int] = Form(None),
    has_basement: Optional[bool] = Form(False),
    has_pool: Optional[bool] = Form(False),
    # Commercial specific fields
    sqft: Optional[float] = Form(None),
    industry: Optional[str] = Form(None),
    c_type: Optional[str] = Form(None),
    num_units: Optional[int] = Form(None),
    parking_spaces: Optional[int] = Form(None),
    zoning_type: Optional[str] = Form(None),
    conn=Depends(get_db_connection),
):
    """Create a new property with either residential or commercial details"""
    try:
        logger.debug("Starting property creation...")
        logger.debug(f"Property Type: {property_type}")
        logger.debug(
            f"Form Data - Address: {property_address}, Price: {price}, Status: {status}"
        )

        # Execute stored procedure to create property
        property_result = execute_procedure(
            conn,
            "create_property",
            (
                tax_id,
                property_address,
                status,
                price,
                lot_size or 0.0,
                year_built or 0,
                zoning or "",
                property_tax or 0.0,
                property_type,
                # Residential parameters
                bedrooms or 0,
                bathrooms or 0.0,
                r_type or "",
                square_feet or 0.0,
                garage_spaces or 0,
                has_basement or False,
                has_pool or False,
                # Commercial parameters
                sqft or 0.0,
                industry or "",
                c_type or "",
                num_units or 0,
                parking_spaces or 0,
                zoning_type or "",
            ),
        )

        if not property_result:
            logger.error("No result returned from create_property procedure")
            raise HTTPException(status_code=500, detail="Failed to create property")

        # Get the created property details for the response
        property_id = property_result[0]["property_id"]
        property_details = execute_procedure(
            conn, "get_property_details", (property_id,)
        )

        if not property_details:
            logger.error(f"Could not fetch details for created property {property_id}")
            raise HTTPException(
                status_code=500, detail="Failed to fetch property details"
            )

        logger.info(f"Successfully created property with ID: {property_id}")

        # Return the property row template with the new property data
        return templates.TemplateResponse(
            "admin/properties/table_row.html",
            {"request": request, "property": property_details[0]},
        )

    except Exception as e:
        logger.error(f"Error creating property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# PUT Routes

@router.put("/properties/{property_id}", response_class=HTMLResponse)
async def update_property(
    request: Request,
    property_id: int,
    # Agent Listing fields
    agent_id: int = Form(...),
    client_id: int = Form(...),
    # Base Property fields
    tax_id: str = Form(...),
    property_address: str = Form(...),
    status: str = Form(...),
    price: float = Form(...),
    property_type: str = Form(...),
    lot_size: float = Form(0.0),
    year_built: int = Form(None),
    zoning: str = Form(None),
    property_tax: float = Form(0.0),
    # Residential fields
    bedrooms: int = Form(0),
    bathrooms: float = Form(0.0),
    r_type: str = Form(None),
    square_feet: float = Form(0.0),
    garage_spaces: int = Form(0),
    has_basement: bool = Form(False),
    has_pool: bool = Form(False),
    # Commercial fields
    sqft: float = Form(0.0),
    industry: str = Form(None),
    c_type: str = Form(None),
    num_units: int = Form(0),
    parking_spaces: int = Form(0),
    zoning_type: str = Form(None),
    conn=Depends(get_db_connection)
):
    try:
        logger.debug(f"Updating property {property_id}")
        
        # First update base property
        execute_procedure(
            conn,
            "update_property",
            (
                property_id, 
                tax_id,
                property_address,
                status,
                price,
                lot_size,
                year_built,
                zoning,
                property_tax,
                bedrooms,
                bathrooms,
                r_type,
                square_feet,
                garage_spaces,
                has_basement,
                has_pool,
                sqft,
                industry,
                c_type,
                num_units,
                parking_spaces,
                zoning_type
            )
        )

        # Update agent listing with asking price
        execute_procedure(
            conn,
            "update_agent_listing",
            (
                property_id,
                agent_id,
                client_id,
                'SellerAgent',
                price  # Use the same price as asking price
            )
        )

        # Update type-specific details
        if property_type == "RESIDENTIAL":
            execute_procedure(
                conn,
                "update_residential_property",
                (
                    property_id,
                    bedrooms,
                    bathrooms,
                    r_type,
                    square_feet,
                    garage_spaces,
                    has_basement,
                    has_pool
                )
            )
        elif property_type == "COMMERCIAL":
            execute_procedure(
                conn,
                "update_commercial_property",
                (
                    property_id,
                    sqft,
                    industry,
                    c_type,
                    num_units,
                    parking_spaces,
                    zoning_type
                )
            )

        # Get updated property for response
        updated_property = execute_procedure(
            conn,
            "get_property_details_with_images",
            (property_id,)
        )

        if not updated_property:
            raise HTTPException(status_code=404, detail="Property not found after update")

        return templates.TemplateResponse(
            "admin/properties/table_row.html",
            {
                "request": request,
                "property": updated_property[0]
            }
        )

    except Exception as e:
        logger.error(f"Error updating property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/clients/{client_id}")
async def update_client(
    request: Request,
    client_id: int,
    client_name: str = Form(...),
    client_phone: str = Form(...),
    client_email: str = Form(...),
    mailing_address: str = Form(...),
    conn=Depends(get_db_connection),
):
    """Update an existing client"""
    try:
        phone = (
            client_phone.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )

        execute_procedure(
            conn,
            "update_client",
            (client_id, client_name, phone, client_email, mailing_address),
        )

        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Client updated successfully",
                "type": "success",
            },
        )
    except Exception as e:
        logger.error(f"Failed to update client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating client: {str(e)}")


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
        phone = (
            agent_phone.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        execute_procedure(
            conn,
            "update_agent",
            (
                agent_id,
                agent_name,
                NRDS,
                phone,
                agent_email,
                license_number,
                expiration_date,
            ),
        )

        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": "Agent updated successfully",
                "type": "success",
            },
        )
    except Exception as e:
        logger.error(f"Failed to update agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")


# DELETE Routes


@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, conn=Depends(get_db_connection)):
    """Delete a client"""
    try:
        execute_procedure(conn, "delete_client", (client_id,))
        return JSONResponse(
            content={"success": True, "message": "Client deleted successfully"}
        )
    except Exception as e:
        logger.error(f"Failed to delete client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/properties/{property_id}")
async def delete_property(property_id: int, conn=Depends(get_db_connection)):
    """Delete a property using stored procedure"""
    try:
        execute_procedure(conn, "delete_property", (property_id,))
        return Response("")
    except Exception as e:
        logger.error(
            f"Failed to delete property {property_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to delete property: {str(e)}"
        )


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, conn=Depends(get_db_connection)):
    """Delete an agent using stored procedure"""
    try:
        execute_procedure(conn, "delete_agent", (agent_id,))
        return JSONResponse(
            content={"success": True, "message": "Agent deleted successfully"}
        )
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
