from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    Query,
    Form,
    File,
    UploadFile,
)
from typing import Optional, List
import json
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.routing import websocket_session
from ..core.logging_config import logger
from ..core.database import get_db_connection, execute_procedure
from ..core.image_utils import save_property_image, delete_property_images, validate_image
from ..core.security import get_current_admin
from datetime import date
import os

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


@router.get("/clients/form", response_class=HTMLResponse)
async def client_form(
    request: Request,
    form_type: str = Query("add"),
    client_id: Optional[int] = None,
    conn=Depends(get_db_connection),
):
    """Unified route for client forms"""
    try:
        context = {"request": request}

        if form_type == "edit" and client_id:
            client_details = execute_procedure(conn, "get_client_details", (client_id,))
            if not client_details:
                raise HTTPException(status_code=404, detail="Client not found")

            context["client"] = client_details[0]
            logger.debug(f"Client data for editing: {client_details[0]}")

        return templates.TemplateResponse("admin/clients/client_form.html", context)
    except Exception as e:
        logger.error(f"Error loading client form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties/form", response_class=HTMLResponse)
async def property_form(
    request: Request,
    form_type: str = Query("add"),  # 'add' or 'edit'
    property_id: Optional[int] = None,
    conn=Depends(get_db_connection),
):
    """Unified route for property forms"""
    try:
        context = {"request": request}

        # If it's an edit form, get the property details
        if form_type == "edit" and property_id:
            property_details = execute_procedure(
                conn, "get_property_details_with_images", (property_id,)
            )
            if not property_details:
                raise HTTPException(status_code=404, detail="Property not found")
            property_data = property_details[0]
            # Return updated image list
            images = execute_procedure(conn, "get_property_images", (property_id,))
            context = {"request": request,
                       "property": property_data,
                       "images": images}
        return templates.TemplateResponse(
            "admin/properties/property_form.html", context
        )
    except Exception as e:
        logger.error(f"Error loading property form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/form", response_class=HTMLResponse)
async def agent_form(
    request: Request,
    form_type: str = Query("add"),
    agent_id: Optional[int] = None,
    conn=Depends(get_db_connection),
):
    """Unified route for agent forms"""
    try:
        context = {"request": request}

        if form_type == "edit" and agent_id:
            agent_details = execute_procedure(conn, "get_agent_details", (agent_id,))
            if not agent_details:
                raise HTTPException(status_code=404, detail="Agent not found")

            context["agent"] = agent_details[0]
            logger.debug(f"Agent data for editing: {agent_details[0]}")

        return templates.TemplateResponse("admin/agents/agent_form.html", context)
    except Exception as e:
        logger.error(f"Error loading agent form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# POST routes
@router.post("/properties/{property_id}/images")
async def upload_property_image(
    request: Request,
    property_id: int,
    file: UploadFile = File(...),
    conn=Depends(get_db_connection),
):
    """Upload a new property image."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    try:
        # Save the uploaded file
        web_location = f"/static/uploads/properties/{property_id}/{file.filename}"
        file_location = "./app" + web_location
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Add the file path to the database
        execute_procedure(conn, "add_property_image", (property_id, web_location, False))
        
        # Return updated image list
        updated_images = execute_procedure(conn, "get_property_images", (property_id,))
        context = {"request": request,
                   "images": updated_images}
        return templates.TemplateResponse(
            "admin/properties/image_list.html",
            context,
        )
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")


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
            "admin/clients/client_row.html", {"request": request, "client": client}
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
            "admin/properties/property_row.html",
            {"request": request, "property": property_details[0]},
        )

    except Exception as e:
        logger.error(f"Error creating property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# PUT Routes
@router.put("/properties/images/{image_id}/primary")
async def set_primary_image(
    image_id: int,
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection),
):
    """Set an image as the primary image"""
    try:
        result = execute_procedure(conn, "set_primary_image", (image_id,))
        if not result:
            raise HTTPException(status_code=404, detail="Image not found")

        # Get property ID to fetch all images
        property_id = result[0]["property_id"]
        property_images = execute_procedure(conn, "get_property_images", (property_id,))

        return templates.TemplateResponse(
            "admin/properties/image_gallery.html",
            {"request": {}, "property_id": property_id, "images": property_images},
        )

    except Exception as e:
        logger.error(f"Error setting primary image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error setting primary image")


@router.put("/clients/{client_id}", response_class=HTMLResponse)
async def update_client(
    request: Request,
    client_id: int,
    client_name: str = Form(...),
    client_phone: str = Form(...),
    client_email: str = Form(...),
    mailing_address: str = Form(...),
    client_types: List[str] = Form([]),
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection),
):
    """Update an existing client"""
    try:
        # Format phone number
        phone = (
            client_phone.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )

        # Update client using stored procedure
        execute_procedure(
            conn,
            "update_client",
            (client_id, client_name, phone, client_email, mailing_address),
        )

        # Update client types
        execute_procedure(
            conn, "update_client_types", (client_id, ",".join(client_types))
        )

        # Get updated client for response
        updated_client = execute_procedure(conn, "get_client_details", (client_id,))
        if not updated_client:
            raise HTTPException(status_code=404, detail="Client not found after update")

        return templates.TemplateResponse(
            "admin/clients/client_row.html",
            {"request": request, "client": updated_client[0]},
        )
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    conn=Depends(get_db_connection),
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
                zoning_type,
            ),
        )

        # Update agent listing with asking price
        exclusive = 1
        execute_procedure(
            conn,
            "update_agent_listing",
            (
                property_id,
                agent_id,
                client_id,
                "SellerAgent",  # Ensure this value is valid
                price,
                exclusive,  # Explicitly set the value for `exclusive`
            ),
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
                    has_pool,
                ),
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
                    zoning_type,
                ),
            )

        # Get updated property for response
        updated_property = execute_procedure(
            conn, "get_property_details_with_images", (property_id,)
        )

        if not updated_property:
            raise HTTPException(
                status_code=404, detail="Property not found after update"
            )

        return templates.TemplateResponse(
            "admin/properties/property_row.html",
            {"request": request, "property": updated_property[0]},
        )

    except Exception as e:
        logger.error(f"Error updating property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}", response_class=HTMLResponse)
async def update_agent(
    request: Request,
    agent_id: int,
    agent_name: str = Form(...),
    agent_phone: str = Form(...),
    agent_email: str = Form(...),
    license_number: str = Form(...),
    license_expiration: str = Form(...),
    conn=Depends(get_db_connection),
):
    """Update an agent's details."""
    try:
        # Convert license expiration to a proper date
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        # Execute the procedure with all 8 parameters
        execute_procedure(
            conn,
            "update_agent",
            (
                agent_id,
                agent_name,
                agent_phone,
                agent_email,
                license_number,
                expiration_date,
                1,
            ),
        )

        # Fetch the updated agent for rendering
        updated_agent = execute_procedure(conn, "get_agent_details", (agent_id,))
        if not updated_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Render the updated row
        return templates.TemplateResponse(
            "admin/agents/agent_row.html",
            {"request": request, "agent": updated_agent[0]},
        )

    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# DELETE Routes


@router.delete("/properties/images/{image_id}")
async def delete_image(
    image_id: int,
    current_user: dict = Depends(get_current_admin),
    conn=Depends(get_db_connection),
):
    """Delete a property image"""
    try:
        # Get image info before deleting
        image_info = execute_procedure(conn, "get_image_info", (image_id,))
        if not image_info:
            raise HTTPException(status_code=404, detail="Image not found")

        property_id = image_info[0]["property_id"]
        file_path = image_info[0]["file_path"]

        # Delete physical file
        delete_property_images([file_path])

        # Delete from database
        execute_procedure(conn, "delete_property_image", (image_id,))

        # Return updated gallery
        property_images = execute_procedure(conn, "get_property_images", (property_id,))

        return templates.TemplateResponse(
            "admin/properties/image_gallery.html",
            {"request": {}, "property_id": property_id, "images": property_images},
        )

    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting image")


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
