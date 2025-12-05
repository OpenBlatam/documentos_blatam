#!/usr/bin/env python3
"""
Validation Helpers
==================

Additional validation helper functions for API routes.
"""

from typing import Any, Optional, List, Dict, Union
from fastapi import HTTPException
from pathlib import Path

from core.utils import setup_logger

logger = setup_logger(__name__)


def validate_not_empty(
    value: Any,
    name: str = "value",
    allow_whitespace: bool = False
) -> Any:
    """
    Validate that a value is not empty.
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        allow_whitespace: If True, allows whitespace-only strings
    
    Returns:
        Validated value
    
    Raises:
        HTTPException: If value is empty
    """
    if value is None:
        raise HTTPException(status_code=400, detail=f"{name} cannot be None")
    
    if isinstance(value, str):
        if not value.strip() if not allow_whitespace else not value:
            raise HTTPException(status_code=400, detail=f"{name} cannot be empty")
    
    if isinstance(value, (list, dict, tuple)):
        if len(value) == 0:
            raise HTTPException(status_code=400, detail=f"{name} cannot be empty")
    
    return value


def validate_string_length(
    value: str,
    min_length: int = 1,
    max_length: Optional[int] = None,
    name: str = "string"
) -> str:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum length
        max_length: Maximum length (None for no limit)
        name: Name of the parameter for error messages
    
    Returns:
        Validated string
    
    Raises:
        HTTPException: If length is invalid
    """
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"{name} must be a string")
    
    length = len(value)
    
    if length < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be at least {min_length} characters, got {length}"
        )
    
    if max_length is not None and length > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be at most {max_length} characters, got {length}"
        )
    
    return value


def validate_list_length(
    value: List[Any],
    min_length: int = 1,
    max_length: Optional[int] = None,
    name: str = "list"
) -> List[Any]:
    """
    Validate list length.
    
    Args:
        value: List to validate
        min_length: Minimum length
        max_length: Maximum length (None for no limit)
        name: Name of the parameter for error messages
    
    Returns:
        Validated list
    
    Raises:
        HTTPException: If length is invalid
    """
    if not isinstance(value, list):
        raise HTTPException(status_code=400, detail=f"{name} must be a list")
    
    length = len(value)
    
    if length < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{name} must have at least {min_length} items, got {length}"
        )
    
    if max_length is not None and length > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{name} must have at most {max_length} items, got {length}"
        )
    
    return value


def validate_file_exists(file_path: Union[str, Path]) -> Path:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to file
    
    Returns:
        Path object if file exists
    
    Raises:
        HTTPException: If file does not exist
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {path}"
        )
    
    if not path.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a file: {path}"
        )
    
    return path


def validate_dict_keys(
    data: Dict[str, Any],
    required_keys: List[str],
    name: str = "dictionary"
) -> Dict[str, Any]:
    """
    Validate that a dictionary contains required keys.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required keys
        name: Name of the parameter for error messages
    
    Returns:
        Validated dictionary
    
    Raises:
        HTTPException: If required keys are missing
    """
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail=f"{name} must be a dictionary")
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail=f"{name} missing required keys: {', '.join(missing_keys)}"
        )
    
    return data


def validate_one_of(
    value: Any,
    allowed_values: List[Any],
    name: str = "value"
) -> Any:
    """
    Validate that a value is one of the allowed values.
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        name: Name of the parameter for error messages
    
    Returns:
        Validated value
    
    Raises:
        HTTPException: If value is not in allowed values
    """
    if value not in allowed_values:
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be one of {allowed_values}, got {value}"
        )
    
    return value



