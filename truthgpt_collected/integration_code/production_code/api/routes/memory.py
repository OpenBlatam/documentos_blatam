#!/usr/bin/env python3
"""
Memory Routes
=============

API routes for memory operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from api.dependencies import get_memory_service
from api.models import (
    MemoryStoreResponse,
    MemoryRetrieveResponse,
    MemoryStatsResponse
)
from api.auth import verify_api_key_optional
from api.api_utils import (
    validate_episode_data,
    validate_k_value,
    validate_priority,
    validate_query_data,
    format_response,
)
from services import MemoryService
from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class MemoryStoreRequest(BaseModel):
    """Request model for storing memory episode."""
    episode: List[float] = Field(..., description="Episodio como lista")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")
    tags: Optional[List[str]] = Field(None, description="Tags")
    priority: Optional[float] = Field(1.0, description="Prioridad")


class MemoryRetrieveRequest(BaseModel):
    """Request model for retrieving memory episodes."""
    query: List[float] = Field(..., description="Query como lista")
    k: Optional[int] = Field(10, description="Número de episodios a recuperar")


@router.post("/store", response_model=MemoryStoreResponse)
async def store_episode(
    request: MemoryStoreRequest,
    req: Request,
    service: MemoryService = Depends(get_memory_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> MemoryStoreResponse:
    """
    Store episode in memory system.
    
    Validates and stores an episode in the memory system with optional metadata,
    tags, and priority. The episode is converted to a tensor and stored for
    future retrieval via similarity search.
    
    Args:
        request: Memory store request containing:
            - episode: List of floats representing the episode vector
            - metadata: Optional dictionary with additional information
            - tags: Optional list of tags for categorization
            - priority: Optional priority value (0.0-10.0, default: 1.0)
        req: FastAPI request object for accessing request state
        service: MemoryService instance injected via dependency injection
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        MemoryStoreResponse containing:
            - success: Boolean indicating if storage was successful
            - episode_count: Total number of episodes in memory
            - message: Status message
    
    Raises:
        HTTPException: 
            - 400: If validation fails (empty episode, invalid data)
            - 503: If memory service is unavailable
    
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/v1/memory/store",
        ...     json={
        ...         "episode": [0.1, 0.2, 0.3, 0.4],
        ...         "metadata": {"source": "example"},
        ...         "priority": 1.0
        ...     }
        ... )
        >>> response.json()["success"]
        True
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Memory module not available")
        
        episode = validate_episode_data(request.episode)
        priority = validate_priority(request.priority)
        
        success = service.store_episode(
            episode,
            metadata=request.metadata,
            tags=request.tags,
            priority=priority
        )
        
        episodes_count = service.get_episode_count()
        
        return MemoryStoreResponse(
            success=success,
            episodes_count=episodes_count,
            stored=success,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is (already properly formatted)
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in store_episode: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error storing episode: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while storing episode"
        )


@router.post("/retrieve", response_model=MemoryRetrieveResponse)
async def retrieve_episodes(
    request: MemoryRetrieveRequest,
    req: Request,
    service: MemoryService = Depends(get_memory_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> MemoryRetrieveResponse:
    """
    Retrieve episodes from memory.
    
    Args:
        request: Memory retrieve request with query data
        req: FastAPI request object
        service: Memory service instance
        _auth: Optional API key for authentication
    
    Returns:
        MemoryRetrieveResponse with retrieved episodes and metadata
    
    Raises:
        HTTPException: If memory module is unavailable or validation fails
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Memory module not available")
        
        query = validate_query_data(request.query)
        k_value = validate_k_value(request.k)
        
        retrieved, weights = service.retrieve_episodes(query, k=k_value)
        
        return MemoryRetrieveResponse(
            retrieved=retrieved.tolist(),
            weights=weights.tolist(),
            count=retrieved.shape[0],
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in retrieve_episodes: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error retrieving episodes: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving episodes"
        )


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_stats(
    req: Request,
    service: MemoryService = Depends(get_memory_service),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> MemoryStatsResponse:
    """
    Get memory statistics.
    
    Args:
        req: FastAPI request object
        service: Memory service instance
        _auth: Optional API key for authentication
    
    Returns:
        MemoryStatsResponse with memory statistics
    
    Raises:
        HTTPException: If memory module is unavailable or an error occurs
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Memory module not available")
        
        stats = service.get_stats()
        return MemoryStatsResponse(
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
            f"Unexpected error getting stats: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting stats"
        )


