#!/usr/bin/env python3
"""
Redundancy Routes
=================

API routes for redundancy operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from api.dependencies import get_redundancy_service
from api.models import RedundancyProcessResponse, RedundancyStatsResponse
from api.auth import verify_api_key_optional
from api.api_utils import validate_items_data, validate_similarity_threshold
from services import RedundancyService
from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class RedundancyProcessRequest(BaseModel):
    """Request model for processing redundancy."""
    items: List[List[List[float]]] = Field(..., description="Items como lista 3D")
    similarity_threshold: Optional[float] = Field(0.85, description="Umbral de similitud")


@router.post("/process", response_model=RedundancyProcessResponse)
async def process_redundancy(
    request: RedundancyProcessRequest,
    req: Request,
    service: RedundancyService = Depends(get_redundancy_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> RedundancyProcessResponse:
    """
    Process items removing redundant entries based on similarity.
    
    Processes a batch of 3D tensor items and removes duplicates based on
    cosine similarity threshold. Returns only unique items along with
    statistics about the reduction process.
    
    Args:
        request: Redundancy process request containing:
            - items: 3D list of floats (List[List[List[float]]]) representing tensor items
            - similarity_threshold: Optional float (0.0-1.0) for similarity matching (default: 0.85)
        req: FastAPI request object for accessing request state
        service: RedundancyService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        RedundancyProcessResponse containing:
            - unique_items: List of unique items after redundancy removal
            - stats: Dictionary with processing statistics:
                - total_items: Original number of items
                - unique_items: Number of unique items after processing
                - removed_items: Number of redundant items removed
                - reduction_rate: Percentage of items removed (0.0-1.0)
            - reduction_rate: Float representing the reduction rate
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails (invalid data format, invalid threshold)
            - 503: If redundancy service is unavailable
            - 500: If unexpected error occurs during processing
    
    Note:
        The similarity_threshold in the request is validated but currently
        uses the module's configured threshold. This parameter is reserved
        for future per-request threshold customization.
    
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/v1/redundancy/process",
        ...     json={
        ...         "items": [[[0.1, 0.2], [0.1, 0.2]], [[0.3, 0.4], [0.5, 0.6]]],
        ...         "similarity_threshold": 0.85
        ...     }
        ... )
        >>> response.json()["reduction_rate"]
        0.5
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Redundancy module not available")
        
        items = validate_items_data(request.items, name="items")
        # Note: similarity_threshold is configured at module initialization
        # The threshold in the request is validated but not used (for future enhancement)
        validate_similarity_threshold(request.similarity_threshold)
        
        unique_items, stats = service.process_bulk(items)
        
        return RedundancyProcessResponse(
            unique_items=unique_items.tolist(),
            stats=stats,
            reduction_rate=stats.get('reduction_rate', 0.0),
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in process_redundancy: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error processing redundancy: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing redundancy"
        )


@router.get("/stats", response_model=RedundancyStatsResponse)
async def get_stats(
    req: Request,
    service: RedundancyService = Depends(get_redundancy_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> RedundancyStatsResponse:
    """
    Get redundancy processing statistics.
    
    Retrieves comprehensive statistics about the redundancy removal system,
    including total items processed, unique items found, reduction rates,
    and performance metrics.
    
    Args:
        req: FastAPI request object for accessing request state
        service: RedundancyService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        RedundancyStatsResponse containing:
            - stats: Dictionary with redundancy statistics including:
                - total_processed: Total number of items processed
                - unique_items: Number of unique items found
                - removed_items: Total number of redundant items removed
                - average_reduction_rate: Average reduction rate across all batches
                - similarity_threshold: Current similarity threshold in use
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails
            - 503: If redundancy service is unavailable
            - 500: If unexpected error occurs
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/v1/redundancy/stats")
        >>> stats = response.json()["stats"]
        >>> stats["average_reduction_rate"]
        0.25
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Redundancy module not available")
        
        stats = service.get_stats()
        return RedundancyStatsResponse(
            stats=stats,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in get_stats: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error getting redundancy stats: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting redundancy stats"
        )


