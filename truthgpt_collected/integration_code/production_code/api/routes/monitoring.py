#!/usr/bin/env python3
"""
Monitoring Routes
=================

API routes for monitoring operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from api.dependencies import get_monitoring_service
from api.models import MonitorStatusResponse, MonitorHealthResponse, MonitorMetricsResponse
from api.auth import verify_api_key_optional
from services import MonitoringService
from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/status", response_model=MonitorStatusResponse)
async def get_status(
    req: Request,
    service: MonitoringService = Depends(get_monitoring_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> MonitorStatusResponse:
    """
    Get comprehensive system status information.
    
    Retrieves the current status of all system components including services,
    modules, and infrastructure. This endpoint provides a high-level overview
    of system health and availability.
    
    Args:
        req: FastAPI request object for accessing request state
        service: MonitoringService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        MonitorStatusResponse containing:
            - status: Dictionary with system status including:
                - services: Status of all services (memory, pipeline, redundancy, etc.)
                - modules: Status of all modules
                - infrastructure: Infrastructure status (CPU, memory, disk)
                - overall_status: Overall system status (healthy, degraded, down)
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails
            - 503: If monitoring service is unavailable
            - 500: If unexpected error occurs
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/v1/monitor/status")
        >>> status = response.json()["status"]
        >>> status["overall_status"]
        "healthy"
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Monitor not initialized")
        
        status = service.get_status()
        return MonitorStatusResponse(
            status=status,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in get_status: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error getting system status: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting system status"
        )


@router.get("/health", response_model=MonitorHealthResponse)
async def get_health(
    req: Request,
    service: MonitoringService = Depends(get_monitoring_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> MonitorHealthResponse:
    """
    Get detailed health check information for all system components.
    
    Performs health checks on all system components and returns detailed
    information about each component's health status, including any issues
    or warnings detected.
    
    Args:
        req: FastAPI request object for accessing request state
        service: MonitoringService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        MonitorHealthResponse containing:
            - health: Dictionary with health check results including:
                - components: Health status of individual components
                - checks: List of health checks performed
                - issues: List of any issues detected
                - warnings: List of any warnings
                - overall_health: Overall health status (healthy, degraded, unhealthy)
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails
            - 503: If monitoring service is unavailable
            - 500: If unexpected error occurs
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/v1/monitor/health")
        >>> health = response.json()["health"]
        >>> health["overall_health"]
        "healthy"
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Monitor not initialized")
        
        health = service.get_health()
        return MonitorHealthResponse(
            health=health,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in get_health: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error getting health: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting health"
        )


@router.get("/metrics", response_model=MonitorMetricsResponse)
async def get_metrics(
    req: Request,
    service: MonitoringService = Depends(get_monitoring_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
):
    """
    Get system metrics and performance data.
    
    Retrieves comprehensive metrics about system performance including:
    - Request counts and rates
    - Response times
    - Resource utilization (CPU, memory, disk)
    - Error rates
    - Service-specific metrics
    
    Args:
        req: FastAPI request object for accessing request state
        service: MonitoringService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        MonitorMetricsResponse containing:
            - metrics: Dictionary with metrics including:
                - requests: Request statistics (total, per second, etc.)
                - response_times: Response time statistics (avg, p50, p95, p99)
                - resources: Resource utilization metrics
                - errors: Error statistics
                - services: Service-specific metrics
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails
            - 503: If monitoring service is unavailable
            - 500: If unexpected error occurs
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/v1/monitor/metrics")
        >>> metrics = response.json()["metrics"]
        >>> metrics["requests"]["total"]
        1500
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Monitor not initialized")
        
        metrics = service.get_metrics()
        return MonitorMetricsResponse(
            metrics=metrics,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in get_metrics: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error getting metrics: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting metrics"
        )


