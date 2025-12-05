#!/usr/bin/env python3
"""
Response Utilities
==================

Utilities for formatting and standardizing API responses.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse

from api.helpers import get_request_id
from core.utils import setup_logger

logger = setup_logger(__name__)


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    req: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        req: Optional FastAPI request object
        metadata: Optional additional metadata
    
    Returns:
        Standardized success response dictionary
    """
    response: Dict[str, Any] = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    request_id = get_request_id(req)
    if request_id:
        response["request_id"] = request_id
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_error_response(
    error: str,
    code: Optional[str] = None,
    status_code: int = 400,
    req: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        code: Optional error code
        status_code: HTTP status code
        req: Optional FastAPI request object
        details: Optional error details
    
    Returns:
        JSONResponse with error information
    """
    response: Dict[str, Any] = {
        "success": False,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    
    if code:
        response["code"] = code
    
    request_id = get_request_id(req)
    if request_id:
        response["request_id"] = request_id
    
    if details:
        response["details"] = details
    
    return JSONResponse(
        content=response,
        status_code=status_code
    )


def create_paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total: Optional[int] = None,
    req: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized paginated response.
    
    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total: Total number of items (if None, uses len(items))
        req: Optional FastAPI request object
        metadata: Optional additional metadata
    
    Returns:
        Standardized paginated response dictionary
    """
    if total is None:
        total = len(items)
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    response: Dict[str, Any] = {
        "success": True,
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        },
        "timestamp": datetime.now().isoformat()
    }
    
    request_id = get_request_id(req)
    if request_id:
        response["request_id"] = request_id
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_list_response(
    items: List[Any],
    req: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized list response.
    
    Args:
        items: List of items
        req: Optional FastAPI request object
        metadata: Optional additional metadata
    
    Returns:
        Standardized list response dictionary
    """
    response: Dict[str, Any] = {
        "success": True,
        "data": items,
        "count": len(items),
        "timestamp": datetime.now().isoformat()
    }
    
    request_id = get_request_id(req)
    if request_id:
        response["request_id"] = request_id
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_stats_response(
    stats: Dict[str, Any],
    req: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized statistics response.
    
    Args:
        stats: Statistics dictionary
        req: Optional FastAPI request object
        metadata: Optional additional metadata
    
    Returns:
        Standardized statistics response dictionary
    """
    response: Dict[str, Any] = {
        "success": True,
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }
    
    request_id = get_request_id(req)
    if request_id:
        response["request_id"] = request_id
    
    if metadata:
        response["metadata"] = metadata
    
    return response



