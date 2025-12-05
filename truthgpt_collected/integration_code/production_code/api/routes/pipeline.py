#!/usr/bin/env python3
"""
Pipeline Routes
===============

API routes for pipeline operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from api.dependencies import get_pipeline_service
from api.models import PipelineProcessResponse, PipelineStatsResponse
from api.rate_limiting import rate_limit_dependency
from api.auth import verify_api_key_optional
from api.api_utils import validate_items_data
from services import PipelineService
from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class PipelineProcessRequest(BaseModel):
    """Request model for processing pipeline."""
    data: List[List[List[float]]] = Field(..., description="Datos como lista 3D")
    use_memory: Optional[bool] = Field(True, description="Usar memoria")
    use_redundancy: Optional[bool] = Field(True, description="Usar redundancia")


@router.post("/process", response_model=PipelineProcessResponse)
async def process_pipeline(
    request: PipelineProcessRequest,
    req: Request,
    service: PipelineService = Depends(get_pipeline_service),
    _rate_limit: None = Depends(rate_limit_dependency(limit=30, window_seconds=60, endpoint_name="/pipeline/process")),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> PipelineProcessResponse:
    """
    Process data through the integrated pipeline system.
    
    Processes 3D tensor data through the pipeline with optional memory integration
    and redundancy removal. The pipeline applies transformations, stores episodes
    in memory (if enabled), and removes redundant items (if enabled).
    
    Args:
        request: Pipeline process request containing:
            - data: 3D list of floats (List[List[List[float]]]) representing tensor data
            - use_memory: Optional boolean to enable memory integration (default: True)
            - use_redundancy: Optional boolean to enable redundancy removal (default: True)
        req: FastAPI request object for accessing request state
        service: PipelineService instance injected via dependency injection
        _rate_limit: Rate limiting dependency (30 requests per 60 seconds)
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        PipelineProcessResponse containing:
            - output: Processed output as list of lists
            - metadata: Dictionary with processing metadata
            - output_shape: Shape of the output tensor
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails (invalid data format, empty data)
            - 429: If rate limit exceeded (30 requests per 60 seconds)
            - 503: If pipeline service is unavailable
            - 500: If unexpected error occurs during processing
    
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/v1/pipeline/process",
        ...     json={
        ...         "data": [[[0.1, 0.2], [0.3, 0.4]], [[0.5, 0.6], [0.7, 0.8]]],
        ...         "use_memory": True,
        ...         "use_redundancy": True
        ...     }
        ... )
        >>> response.json()["output_shape"]
        [2, 2, 2]
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
        data = validate_items_data(request.data, name="data")
        
        output, metadata = service.process(
            data,
            use_memory=request.use_memory,
            use_redundancy=request.use_redundancy
        )
        
        return PipelineProcessResponse(
            output=output.tolist(),
            metadata=metadata,
            output_shape=list(output.shape),
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in process_pipeline: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error processing pipeline: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing pipeline"
        )


@router.get("/stats", response_model=PipelineStatsResponse)
async def get_stats(
    req: Request,
    service: PipelineService = Depends(get_pipeline_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> PipelineStatsResponse:
    """
    Get pipeline processing statistics.
    
    Retrieves comprehensive statistics about the pipeline's processing history,
    including total items processed, memory usage, redundancy removal stats,
    and performance metrics.
    
    Args:
        req: FastAPI request object for accessing request state
        service: PipelineService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        PipelineStatsResponse containing:
            - stats: Dictionary with pipeline statistics including:
                - total_processed: Total number of items processed
                - memory_episodes: Number of episodes stored in memory
                - redundancy_removed: Number of redundant items removed
                - average_processing_time: Average time per processing operation
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails
            - 503: If pipeline service is unavailable
            - 500: If unexpected error occurs
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/v1/pipeline/stats")
        >>> stats = response.json()["stats"]
        >>> stats["total_processed"]
        150
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
        stats = service.get_stats()
        return PipelineStatsResponse(
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
            f"Unexpected error getting pipeline stats: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting pipeline stats"
        )


