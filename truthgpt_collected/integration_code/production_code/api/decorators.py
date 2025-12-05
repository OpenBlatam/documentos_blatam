#!/usr/bin/env python3
"""
API Decorators
==============

Reusable decorators for API routes to reduce code duplication and ensure
consistent error handling, logging, and validation patterns.
"""

from functools import wraps
from typing import Callable, Any, Optional, TypeVar, ParamSpec
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from core.utils import setup_logger

logger = setup_logger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def handle_route_errors(
    operation_name: str,
    service_check: Optional[Callable[[Any], bool]] = None,
    service_name: Optional[str] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for consistent error handling in API routes.
    
    Provides standardized error handling with:
    - Service availability checking
    - Structured logging
    - Consistent error responses
    - Request ID tracking
    
    Args:
        operation_name: Name of the operation for logging (e.g., "store_episode")
        service_check: Optional callable to check service availability (takes service, returns bool)
        service_name: Optional name of the service for error messages
    
    Returns:
        Decorated function with error handling
    
    Example:
        >>> @router.post("/store")
        ... @handle_route_errors("store_episode", lambda s: s.is_available(), "memory")
        ... async def store_episode(request: Request, service: MemoryService):
        ...     return service.store(request.data)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Extract request and service from kwargs/args
            req: Optional[Request] = None
            service: Optional[Any] = None
            
            # Find Request object
            for arg in args:
                if isinstance(arg, Request):
                    req = arg
                    break
            if not req:
                req = kwargs.get('req') or kwargs.get('request')
            
            # Find service object
            for arg in args:
                if hasattr(arg, 'is_available'):
                    service = arg
                    break
            if not service:
                for key, value in kwargs.items():
                    if hasattr(value, 'is_available'):
                        service = value
                        break
            
            # Check service availability if check function provided
            if service_check and service:
                try:
                    if not service_check(service):
                        service_msg = f" {service_name or 'service'}" if service_name else ""
                        raise HTTPException(
                            status_code=503,
                            detail=f"{service_name or 'Service'}{service_msg} not available"
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(
                        f"Error checking service availability in {operation_name}: {e}",
                        exc_info=True
                    )
                    raise HTTPException(
                        status_code=503,
                        detail=f"Service availability check failed"
                    )
            
            # Execute function with error handling
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except ValueError as e:
                # Validation errors - return 400 with clear message
                logger.warning(
                    f"Validation error in {operation_name}: {e}",
                    request_id=getattr(req.state, 'request_id', None) if req else None
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation error: {str(e)}"
                )
            except Exception as e:
                # Unexpected errors - log and return 500
                request_id = getattr(req.state, 'request_id', None) if req else None
                logger.error(
                    f"Unexpected error in {operation_name}: {e}",
                    exc_info=True,
                    request_id=request_id
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error during {operation_name.replace('_', ' ')}"
                )
        
        return wrapper
    return decorator


def validate_request(
    *validators: Callable[[Any], tuple[bool, Optional[str]]]
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for request validation.
    
    Applies multiple validators to the request object before executing the route.
    Each validator should return (is_valid, error_message).
    
    Args:
        *validators: Validation functions that take request and return (bool, Optional[str])
    
    Returns:
        Decorated function with validation
    
    Example:
        >>> def validate_message(request: ChatRequest) -> tuple[bool, Optional[str]]:
        ...     if not request.message.strip():
        ...         return False, "Message cannot be empty"
        ...     return True, None
        ...
        >>> @router.post("/chat")
        ... @validate_request(validate_message)
        ... async def chat(request: ChatRequest):
        ...     ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Find request object
            request_obj = None
            for arg in args:
                if hasattr(arg, '__dict__') or hasattr(arg, '__fields__'):
                    request_obj = arg
                    break
            if not request_obj:
                request_obj = kwargs.get('request') or kwargs.get('req')
            
            # Run validators
            if request_obj:
                for validator in validators:
                    is_valid, error_msg = validator(request_obj)
                    if not is_valid:
                        raise HTTPException(
                            status_code=400,
                            detail=error_msg or "Validation failed"
                        )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_request(
    log_request_body: bool = False,
    log_response: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for request/response logging.
    
    Logs request and optionally response data for debugging and monitoring.
    
    Args:
        log_request_body: Whether to log request body (default: False)
        log_response: Whether to log response data (default: False)
    
    Returns:
        Decorated function with logging
    
    Example:
        >>> @router.post("/process")
        ... @log_request(log_request_body=True, log_response=False)
        ... async def process(request: Request):
        ...     ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Find request object
            req: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    req = arg
                    break
            if not req:
                req = kwargs.get('req') or kwargs.get('request')
            
            request_id = getattr(req.state, 'request_id', None) if req else None
            
            # Log request
            if req:
                logger.info(
                    f"Request: {req.method} {req.url.path}",
                    request_id=request_id,
                    client_ip=req.client.host if req.client else None
                )
                
                if log_request_body:
                    try:
                        body = await req.body()
                        logger.debug(
                            f"Request body: {body.decode('utf-8')[:500]}",
                            request_id=request_id
                        )
                    except Exception:
                        pass
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Log response
            if log_response and result:
                try:
                    response_data = str(result)[:500] if hasattr(result, '__dict__') else str(result)
                    logger.debug(
                        f"Response: {response_data}",
                        request_id=request_id
                    )
                except Exception:
                    pass
            
            return result
        
        return wrapper
    return decorator



