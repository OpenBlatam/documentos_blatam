#!/usr/bin/env python3
"""
Health Routes
=============

API routes for health checks and root endpoint.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
from pathlib import Path

router = APIRouter()


@router.get("/")
async def root() -> dict:
    """
    Root endpoint providing API information.
    
    Returns basic information about the API including name, version, status,
    and available endpoints. This is the entry point for API discovery.
    
    Returns:
        Dictionary containing:
            - name: API name
            - version: API version
            - status: Current API status
            - endpoints: Dictionary mapping endpoint names to paths
            - documentation: Link to API documentation
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/")
        >>> response.json()["version"]
        "2.0.0"
    """
    return {
        "name": "Production Code API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "memory": "/api/v1/memory",
            "redundancy": "/api/v1/redundancy",
            "pipeline": "/api/v1/pipeline",
            "chat": "/api/v1/chat",
            "config": "/api/v1/config",
            "monitor": "/api/v1/monitor",
            "documents": "/api/v1/documents",
            "health": "/health"
        }
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with health status and timestamp
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/dashboard")
async def dashboard() -> FileResponse | JSONResponse:
    """
    Serve dashboard HTML.
    
    Returns:
        FileResponse with dashboard HTML if found, otherwise JSONResponse with 404 error
    
    Note:
        Looks for dashboard.html in the project root directory
    """
    dashboard_path = Path(__file__).parent.parent.parent / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    else:
        return JSONResponse({"error": "Dashboard not found"}, status_code=404)


