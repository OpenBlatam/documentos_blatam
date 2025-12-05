#!/usr/bin/env python3
"""
API Utilities
=============

Validation and utility functions for API routes.

This module provides comprehensive validation and utility functions for API endpoints,
including tensor validation, response formatting, pagination, and range validation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException
import torch

from core.utils import setup_logger

logger = setup_logger(__name__)

# Constants
DEFAULT_TENSOR_DTYPE = torch.float32
DEFAULT_TENSOR_DEVICE = "cpu"
MAX_TENSOR_ELEMENTS = 10_000_000


def validate_tensor_shape(
    data: List[float],
    expected_dims: int,
    min_size: int = 1,
    name: str = "tensor",
    dtype: torch.dtype = DEFAULT_TENSOR_DTYPE,
    device: str = DEFAULT_TENSOR_DEVICE,
    max_elements: Optional[int] = MAX_TENSOR_ELEMENTS
) -> torch.Tensor:
    """
    Validate and convert list to tensor with comprehensive validation.
    
    Performs comprehensive validation including:
    - Empty check
    - Dimension validation
    - Size validation
    - NaN/Inf detection
    - Maximum elements check
    
    Args:
        data: List of numeric data to convert to tensor
        expected_dims: Expected number of dimensions (e.g., 1 for vector, 2 for matrix)
        min_size: Minimum size along first dimension
        name: Name for error messages (used in HTTPException details)
        dtype: Tensor data type (default: torch.float32)
        device: Tensor device (default: "cpu")
        max_elements: Maximum number of elements allowed (default: 10,000,000)
    
    Returns:
        Validated torch.Tensor with specified dtype and device
    
    Raises:
        HTTPException: 
            - 400: If data is empty, wrong dimensions, too small, or contains NaN/Inf
            - 413: If tensor exceeds maximum elements
    
    Example:
        >>> data = [1.0, 2.0, 3.0, 4.0]
        >>> tensor = validate_tensor_shape(data, expected_dims=1, name="episode")
        >>> tensor.shape
        torch.Size([4])
    """
    try:
        tensor = torch.as_tensor(data, dtype=dtype, device=device)
        
        if tensor.numel() == 0:
            raise HTTPException(status_code=400, detail=f"{name} cannot be empty")
        
        if tensor.dim() != expected_dims:
            raise HTTPException(
                status_code=400,
                detail=f"{name} must be {expected_dims}D tensor, got {tensor.dim()}D"
            )
        
        if tensor.size(0) < min_size:
            raise HTTPException(
                status_code=400,
                detail=f"{name} must have at least {min_size} items, got {tensor.size(0)}"
            )
        
        if max_elements is not None and tensor.numel() > max_elements:
            raise HTTPException(
                status_code=413,
                detail=f"{name} exceeds maximum supported elements ({max_elements})"
            )
        
        # Check for NaN/Inf
        if torch.isnan(tensor).any() or torch.isinf(tensor).any():
            raise HTTPException(status_code=400, detail=f"{name} contains NaN or Inf values")
        
        return tensor
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid {name} data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing {name}: {str(e)}")


def tensor_to_list(tensor: torch.Tensor) -> List[float]:
    """
    Convert tensor to list representation.
    
    Safely converts a PyTorch tensor to a Python list, handling
    errors gracefully by returning an empty list on failure.
    
    Args:
        tensor: PyTorch tensor to convert (any shape)
    
    Returns:
        List representation of tensor data. Returns empty list
        if conversion fails.
    
    Example:
        >>> tensor = torch.tensor([1.0, 2.0, 3.0])
        >>> tensor_to_list(tensor)
        [1.0, 2.0, 3.0]
    """
    try:
        return tensor.detach().cpu().tolist()
    except Exception as e:
        logger.error(f"Error converting tensor to list: {e}")
        return []


def validate_episode_data(episode: List[float]) -> torch.Tensor:
    """
    Validate and convert episode data to 1D tensor.
    
    Validates that episode data is a non-empty list of floats and converts
    it to a 1-dimensional PyTorch tensor.
    
    Args:
        episode: Episode data as list of floats. Must not be empty.
    
    Returns:
        Episode as 1D torch.Tensor with shape (n,) where n is the length
        of the input episode list.
    
    Raises:
        HTTPException: 
            - 400: If episode is empty or validation fails
    
    Example:
        >>> episode = [0.1, 0.2, 0.3, 0.4, 0.5]
        >>> tensor = validate_episode_data(episode)
        >>> tensor.shape
        torch.Size([5])
    """
    if not episode:
        raise HTTPException(status_code=400, detail="Episode cannot be empty")
    return validate_tensor_shape(
        episode,
        expected_dims=1,
        name="episode"
    )


def validate_query_data(query: List[float]) -> torch.Tensor:
    """
    Validate and convert query data to 1D tensor.
    
    Validates that query data is a non-empty list of floats and converts
    it to a 1-dimensional PyTorch tensor for similarity search operations.
    
    Args:
        query: Query vector as list of floats. Must not be empty.
    
    Returns:
        Query as 1D torch.Tensor with shape (n,) where n is the length
        of the input query list.
    
    Raises:
        HTTPException: 
            - 400: If query is empty or validation fails
    
    Example:
        >>> query = [0.1, 0.2, 0.3]
        >>> tensor = validate_query_data(query)
        >>> tensor.shape
        torch.Size([3])
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return validate_tensor_shape(
        query,
        expected_dims=1,
        name="query"
    )


def validate_float_range(value: float, min_val: float, max_val: float, name: str) -> float:
    """
    Validate float range.
    
    Args:
        value: Value to validate
        min_val: Minimum value
        max_val: Maximum value
        name: Parameter name for error messages
    
    Returns:
        Validated value
    
    Raises:
        HTTPException: If value is out of range
    """
    if not (min_val <= value <= max_val):
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be between {min_val} and {max_val}, got {value}"
        )
    return value


def validate_int_range(value: int, min_val: int, max_val: int, name: str) -> int:
    """
    Validate integer range.
    
    Args:
        value: Value to validate
        min_val: Minimum value
        max_val: Maximum value
        name: Parameter name for error messages
    
    Returns:
        Validated value
    
    Raises:
        HTTPException: If value is out of range
    """
    if not (min_val <= value <= max_val):
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be between {min_val} and {max_val}, got {value}"
        )
    return value


def validate_k_value(k: Optional[int], default: int = 10) -> int:
    """
    Validate k value for retrieval.
    
    Args:
        k: Optional k value
        default: Default value if k is None
    
    Returns:
        Validated k value
    
    Raises:
        HTTPException: If validation fails
    """
    if k is None:
        return default
    return validate_int_range(k, 1, 1000, "k")


def validate_priority(priority: Optional[float], default: float = 1.0) -> float:
    """
    Validate priority value.
    
    Args:
        priority: Optional priority value
        default: Default value if priority is None
    
    Returns:
        Validated priority value
    
    Raises:
        HTTPException: If validation fails
    """
    if priority is None:
        return default
    return validate_float_range(priority, 0.0, 10.0, "priority")


def validate_items_data(
    items: List[List[List[float]]],
    name: str = "items"
) -> torch.Tensor:
    """
    Validate and convert items data to tensor (3D: batch, seq, features).
    
    Args:
        items: Items as 3D list
        name: Name of the parameter for error messages
    
    Returns:
        Items as torch.Tensor
    
    Raises:
        HTTPException: If validation fails
    """
    return validate_tensor_shape(
        items,
        expected_dims=3,
        name=name,
        min_size=1
    )


def validate_similarity_threshold(
    threshold: Optional[float],
    default: float = 0.85
) -> float:
    """
    Validate similarity threshold for redundancy detection.
    
    Args:
        threshold: Optional similarity threshold
        default: Default value if threshold is None
    
    Returns:
        Validated threshold
    
    Raises:
        HTTPException: If validation fails
    """
    if threshold is None:
        return default
    return validate_float_range(threshold, 0.0, 1.0, "similarity_threshold")


def format_response(
    data: Any,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format API response with common fields.
    
    Args:
        data: Main response data
        metadata: Optional metadata dictionary
        request_id: Optional request ID
    
    Returns:
        Formatted response dictionary
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if metadata:
        response["metadata"] = metadata
    
    if request_id:
        response["request_id"] = request_id
    
    return response


def paginate_results(
    results: List[Any],
    page: int = 1,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    Paginate results.
    
    Args:
        results: List of results
        page: Page number (1-indexed)
        page_size: Page size
    
    Returns:
        Dictionary with paginated results
    """
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": results[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }

