# app/routes/admin.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, date
from ..core.logging_config import logger
from ..core.security import get_current_admin, get_password_hash
from ..core.database import get_db_connection, execute_procedure
import os
import shutil
from mysql.connector import Error

UPLOAD_DIR = "app/static/property_images"

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def call_procedure(conn, procedure_name: str, params: tuple) -> Dict[str, Any]:
    """Helper function to call stored procedures"""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(procedure_name, params)
        
        # Get results if any
        results = None
        for result in cursor.stored_results():
            results = result.fetchall()
            
        conn.commit()
        return results
    except Error as e:
        conn.rollback()
        logger.error(f"Database error in {procedure_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """Main admin dashboard view"""
    try:
        # Initialize default context
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
        }
        
        # Get dashboard stats and update context safely
        dashboard_stats = await call_procedure(conn, 'get_admin_dashboard_stats', ())
        if dashboard_stats and len(dashboard_stats) > 0:
            context.update(dashboard_stats[0])
        
        # Get properties and agents
        properties = await call_procedure(conn, 'get_all_properties', ())
        agents = await call_procedure(conn, 'get_all_agents', ())
        
        # Update context with results if they exist
        if properties:
            context["properties"] = properties
        if agents:
            context["agents"] = agents

        return templates.TemplateResponse("admin/dashboard.html", context)

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "error": "Failed to load dashboard data",
                "properties": [],
                "agents": [],
                "total_agents": 0,
                "total_listings": 0,
                "total_properties": 0,
                "total_sales": 0,
                "total_commissions": 0,
                "today": date.today(),
            },
        )

@router.get("/properties/table", response_class=HTMLResponse)
async def properties_table(
    request: Request, 
    conn = Depends(get_db_connection)
):
    """Properties table component using stored procedure"""
    try:
        # Initialize default context
        context = {
            "request": request,
            "properties": [],
            "total_properties": 0,
            "active_listings": 0,
            "total_value": 0,
            "avg_price": 0,
        }

        # Get properties and stats
        properties = await call_procedure(conn, 'get_all_properties', ())
        stats = await call_procedure(conn, 'get_property_stats', ())

        # Update context safely
        if properties:
            context["properties"] = properties
        
        if stats and len(stats) > 0:
            context.update(stats[0])

        return templates.TemplateResponse("admin/properties/table.html", context)
    except Exception as e:
        logger.error(f"Failed to fetch properties table: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin/properties/table.html",
            {
                "request": request,
                "error": "Failed to load properties",
                "properties": [],
                "total_properties": 0,
                "active_listings": 0,
                "total_value": 0,
                "avg_price": 0,
            },
        )

@router.get("/agents/table", response_class=HTMLResponse)
async def agents_table(
    request: Request, 
    conn = Depends(get_db_connection)
):
    """Agents table component using stored procedure"""
    try:
        # Initialize default context
        context = {
            "request": request,
            "agents": [],
            "total_agents": 0,
            "total_listings": 0,
            "total_sales": 0,
            "total_commissions": 0,
            "today": date.today(),
        }

        # Get all required data
        agents = await call_procedure(conn, 'get_all_agents', ())
        stats = await call_procedure(conn, 'get_agent_stats', ())
        sales_data = await call_procedure(conn, 'get_sales_stats', ())

        # Update context safely
        if agents:
            context["agents"] = agents
            
        if stats and len(stats) > 0:
            context.update({
                "total_agents": stats[0].get("total_agents", 0),
                "total_listings": stats[0].get("total_listings", 0),
            })
            
        if sales_data and len(sales_data) > 0:
            context.update({
                "total_sales": sales_data[0].get("total_sales", 0),
                "total_commissions": sales_data[0].get("total_commissions", 0),
            })

        return templates.TemplateResponse("admin/agents/table.html", context)
    except Exception as e:
        logger.error(f"Failed to fetch agents table: {str(e)}", exc_info=True)
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
                "today": date.today(),
            },
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
    conn = Depends(get_db_connection),
):
    """Create a new agent using stored procedure"""
    try:
        phone = agent_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        ssn = SSN.replace("-", "")
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        result = await call_procedure(
            conn,
            'create_agent',
            (
                agent_name, NRDS, phone, agent_email, ssn,
                license_number, expiration_date, 1  # broker_id=1
            )
        )

        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Agent {agent_name} created successfully",
                "type": "success",
            },
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error creating agent: {str(e)}",
                "type": "error",
            },
        )

@router.get("/agents/{agent_id}/edit", response_class=HTMLResponse)
async def edit_agent_form(
    request: Request, 
    agent_id: int, 
    conn = Depends(get_db_connection)
):
    """Get the edit form for an agent"""
    try:
        agent = await call_procedure(conn, 'get_agent_details', (agent_id,))
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return templates.TemplateResponse(
            "admin/agents/edit_form.html", 
            {"request": request, "agent": agent[0]}
        )
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
    conn = Depends(get_db_connection),
):
    """Update an existing agent using stored procedure"""
    try:
        phone = agent_phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        expiration_date = datetime.strptime(license_expiration, "%Y-%m-%d").date()

        await call_procedure(
            conn,
            'update_agent',
            (
                agent_id, agent_name, NRDS, phone, agent_email,
                license_number, expiration_date
            )
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
        return templates.TemplateResponse(
            "admin/components/toast.html",
            {
                "request": request,
                "message": f"Error updating agent: {str(e)}",
                "type": "error",
            },
        )

@router.delete("/properties/{property_id}")
async def delete_property(
    property_id: int, 
    conn = Depends(get_db_connection)
):
    """Delete a property using stored procedure"""
    try:
        await call_procedure(conn, 'delete_property', (property_id,))
        return Response("")
    except Exception as e:
        logger.error(f"Failed to delete property {property_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete property: {str(e)}")

@router.delete("/agents/{agent_id}")
async def delete_agent(
    request: Request, 
    agent_id: int, 
    conn = Depends(get_db_connection)
):
    """Delete an agent using stored procedure"""
    try:
        await call_procedure(conn, 'delete_agent', (agent_id,))
        return JSONResponse(content={"success": True, "message": "Agent deleted successfully"})
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
