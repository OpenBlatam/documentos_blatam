#!/usr/bin/env python3
"""
Validation utilities for paper configurations.

Provides common validation functions to reduce code duplication.
"""

from typing import Any, Callable, Optional, Union
from functools import wraps


def validate_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    name: str = "value"
) -> float:
    """
    Validates that a value is within a specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the value for error messages
    
    Returns:
        The validated value
    
    Raises:
        ValueError: If value is outside the range
    """
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{name} debe estar en [{min_val}, {max_val}], recibido: {value}"
        )
    return value


def validate_positive(value: Union[int, float], name: str = "value") -> float:
    """
    Validates that a value is positive.
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
    
    Returns:
        The validated value
    
    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{name} debe ser > 0, recibido: {value}")
    return value


def validate_non_negative(value: Union[int, float], name: str = "value") -> float:
    """
    Validates that a value is non-negative.
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
    
    Returns:
        The validated value
    
    Raises:
        ValueError: If value is negative
    """
    if value < 0:
        raise ValueError(f"{name} debe ser >= 0, recibido: {value}")
    return value


def validate_integer(value: Any, name: str = "value") -> int:
    """
    Validates that a value is an integer.
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
    
    Returns:
        The validated integer value
    
    Raises:
        ValueError: If value is not an integer
    """
    if not isinstance(value, int):
        raise ValueError(f"{name} debe ser un entero, recibido: {type(value).__name__}")
    return value


def validate_boolean(value: Any, name: str = "value") -> bool:
    """
    Validates that a value is a boolean.
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
    
    Returns:
        The validated boolean value
    
    Raises:
        ValueError: If value is not a boolean
    """
    if not isinstance(value, bool):
        raise ValueError(f"{name} debe ser un booleano, recibido: {type(value).__name__}")
    return value


