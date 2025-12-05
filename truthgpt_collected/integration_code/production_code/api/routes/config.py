#!/usr/bin/env python3
"""
Config Routes
=============

API routes for configuration operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Optional, Any

from api.dependencies import get_config_service
from api.models import ConfigResponse, ConfigUpdateResponse
from api.auth import verify_api_key_optional
from services import ConfigService
from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("", response_model=ConfigResponse)
async def get_config(
    req: Request,
    module: Optional[str] = None,
    service: ConfigService = Depends(get_config_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, True))  # Auth required for config
) -> ConfigResponse:
    """
    Get configuration for a module or all modules.
    
    Retrieves configuration data from the centralized config manager.
    If a module name is provided, returns only that module's configuration.
    If no module is specified, returns all module configurations.
    
    **Authentication Required**: This endpoint requires API key authentication.
    
    Args:
        req: FastAPI request object for accessing request state
        module: Optional module name to get specific module config (e.g., "memory", "pipeline")
        service: ConfigService instance injected via dependency injection
        _auth: API key for authentication (required)
    
    Returns:
        ConfigResponse containing:
            - config: Dictionary with configuration data (module-specific or all modules)
            - module: Module name if specified, None otherwise
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 401: If authentication fails (API key missing or invalid)
            - 400: If validation fails (invalid module name)
            - 503: If config service is unavailable
            - 500: If unexpected error occurs
    
    Example:
        >>> import requests
        >>> headers = {"X-API-Key": "your-api-key"}
        >>> response = requests.get(
        ...     "http://localhost:8000/api/v1/config?module=memory",
        ...     headers=headers
        ... )
        >>> config = response.json()["config"]
        >>> config["max_episodes"]
        10000
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Config manager not initialized")
        
        config = service.get_config(module)
        return ConfigResponse(
            config=config,
            module=module,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in get_config: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error getting config: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting config"
        )


@router.put("/{module}", response_model=ConfigUpdateResponse)
async def update_config(
    module: str,
    config: Dict[str, Any],
    req: Request,
    service: ConfigService = Depends(get_config_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, True))  # Auth required for config
):
    """
    Update configuration for a specific module.
    
    Updates the configuration for the specified module with the provided
    configuration dictionary. The configuration is validated and merged
    with existing configuration.
    
    **Authentication Required**: This endpoint requires API key authentication.
    
    Args:
        module: Module name to update (e.g., "memory", "pipeline", "redundancy")
        config: Dictionary with configuration key-value pairs to update
        req: FastAPI request object for accessing request state
        service: ConfigService instance injected via dependency injection
        _auth: API key for authentication (required)
    
    Returns:
        ConfigUpdateResponse containing:
            - message: Success message indicating the update
            - module: Module name that was updated
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 401: If authentication fails (API key missing or invalid)
            - 400: If validation fails (invalid module name, invalid config values)
            - 503: If config service is unavailable
            - 500: If unexpected error occurs during update
    
    Example:
        >>> import requests
        >>> headers = {"X-API-Key": "your-api-key"}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/v1/config/memory",
        ...     json={"max_episodes": 20000, "similarity_threshold": 0.9},
        ...     headers=headers
        ... )
        >>> response.json()["message"]
        "Config updated for memory"
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Config manager not initialized")
        
        service.update_config(module, config)
        return ConfigUpdateResponse(
            message=f"Config updated for {module}",
            module=module,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in update_config: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error updating config: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating config"
        )


