#!/usr/bin/env python3
"""
API Helpers
===========

Helper functions and utilities for API routes to reduce duplication
and improve code organization.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import Request, HTTPException
from datetime import datetime

from core.utils import setup_logger

logger = setup_logger(__name__)


def get_request_id(req: Optional[Request]) -> Optional[str]:
    """
    Extract request ID from request state.
    
    Args:
        req: FastAPI request object
    
    Returns:
        Request ID if available, None otherwise
    """
    if req is None:
        return None
    return getattr(req.state, 'request_id', None)


def format_error_message(operation: str, error: Exception) -> str:
    """
    Format error message consistently.
    
    Args:
        operation: Name of the operation that failed
        error: Exception that occurred
    
    Returns:
        Formatted error message
    """
    return f"Error {operation}: {str(error)}"


def validate_file_size(file_path: Path, max_size_mb: int = 100) -> None:
    """
    Validate file size.
    
    Args:
        file_path: Path to file to validate
        max_size_mb: Maximum file size in MB
    
    Raises:
        HTTPException: If file exceeds maximum size
    """
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size_mb:.2f}MB exceeds maximum {max_size_mb}MB"
        )


def generate_filename(base_name: Optional[str] = None, extension: str = "") -> str:
    """
    Generate a unique filename with timestamp.
    
    Args:
        base_name: Optional base name for the file
        extension: File extension (with or without dot)
    
    Returns:
        Generated filename
    """
    if base_name:
        base = base_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"file_{timestamp}"
    
    if extension and not extension.startswith('.'):
        extension = f".{extension}"
    
    return f"{base}{extension}"


def normalize_format(format_str: str, format_map: Optional[Dict[str, str]] = None) -> str:
    """
    Normalize format string (e.g., "word" -> "docx").
    
    Args:
        format_str: Format string to normalize
        format_map: Optional mapping dictionary (default: {"word": "docx", "excel": "xlsx"})
    
    Returns:
        Normalized format string
    """
    if format_map is None:
        format_map = {"word": "docx", "excel": "xlsx"}
    
    format_lower = format_str.lower()
    return format_map.get(format_lower, format_lower)


def validate_format(
    format_str: str,
    valid_formats: List[str],
    format_map: Optional[Dict[str, str]] = None
) -> str:
    """
    Validate and normalize format string.
    
    Args:
        format_str: Format string to validate
        valid_formats: List of valid formats
        format_map: Optional format mapping dictionary
    
    Returns:
        Normalized format string
    
    Raises:
        HTTPException: If format is invalid
    """
    normalized = normalize_format(format_str, format_map)
    
    if normalized not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format_str}. Valid formats: {', '.join(valid_formats)}"
        )
    
    return normalized


def get_media_type(format_str: str) -> str:
    """
    Get MIME type for a file format.
    
    Args:
        format_str: File format (e.g., "pdf", "docx", "xlsx")
    
    Returns:
        MIME type string
    """
    media_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'zip': 'application/zip',
        'json': 'application/json',
        'txt': 'text/plain',
        'html': 'text/html',
        'md': 'text/markdown'
    }
    
    return media_types.get(format_str.lower(), 'application/octet-stream')


def detect_file_type(file_path: Path) -> str:
    """
    Detect file type from extension or content.
    
    Args:
        file_path: Path to file
    
    Returns:
        Detected file type (e.g., "json", "html", "txt")
    """
    suffix = file_path.suffix.lower()
    
    # Map extensions to types
    extension_map = {
        '.json': 'json',
        '.html': 'html',
        '.htm': 'html',
        '.md': 'md',
        '.markdown': 'md',
        '.txt': 'txt',
        '.text': 'txt'
    }
    
    if suffix in extension_map:
        return extension_map[suffix]
    
    # Try to detect from content
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')[:100]
        if content.strip().startswith('<'):
            return 'html'
        elif content.strip().startswith('#'):
            return 'md'
        elif content.strip().startswith('{') or content.strip().startswith('['):
            return 'json'
    except Exception:
        pass
    
    return 'txt'


def log_operation(
    operation: str,
    req: Optional[Request] = None,
    level: str = "info",
    **kwargs: Any
) -> None:
    """
    Log operation with request context.
    
    Args:
        operation: Name of the operation
        req: Optional FastAPI request object
        level: Log level ("info", "warning", "error", "debug")
        **kwargs: Additional context to log
    """
    request_id = get_request_id(req)
    context = {"operation": operation, "request_id": request_id, **kwargs}
    
    log_func = getattr(logger, level, logger.info)
    log_func(f"Operation: {operation}", **context)



