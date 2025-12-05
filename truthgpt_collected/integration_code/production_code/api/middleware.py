#!/usr/bin/env python3
"""
API Middleware
=============

Custom middleware for the API.
"""

import uuid
import time
import json
from typing import Callable, Tuple, Dict, Any, TYPE_CHECKING
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import FastAPI

from core.utils import setup_logger

logger = setup_logger(__name__)

# Optional monitoring system import
try:
    from monitoring_system import get_system_monitor
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request state and response headers.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response with X-Request-ID header
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response with timing information.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response with X-Process-Time header
        
        Raises:
            Re-raises any exception from the request handler
        """
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', None)
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            request_id=request_id
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
                request_id=request_id
            )
            
            # Add process time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=f"{process_time:.3f}s",
                request_id=request_id,
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle unhandled exceptions and return JSON error responses.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response (normal or error JSONResponse)
        
        Note:
            Catches all exceptions and returns a 500 error response.
            Logs the exception with full traceback.
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, 'request_id', None)
            logger.error(
                "Unhandled exception",
                path=request.url.path,
                error=str(e),
                request_id=request_id,
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(e) if logger.level <= 10 else "An error occurred",
                    "request_id": request_id
                }
            )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for metrics collection."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with metrics collection.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response after recording metrics
        
        Note:
            If monitoring is unavailable, continues without metrics.
            If metrics collection fails, continues without metrics.
        """
        if not MONITORING_AVAILABLE:
            return await call_next(request)
        
        try:
            monitor = get_system_monitor()
            
            # Increment counters
            monitor.metrics_collector.increment("api.requests.total")
            monitor.metrics_collector.increment(f"api.requests.{request.method}")
            
            # Process request
            response = await call_next(request)
            
            # Record status code
            monitor.metrics_collector.increment(f"api.responses.{response.status_code}")
            
            return response
        except Exception:
            # If monitoring fails, continue without metrics
            return await call_next(request)


class CachingMiddleware(BaseHTTPMiddleware):
    """Middleware for response caching."""
    
    def __init__(self, app: "FastAPI", cache_ttl: int = 60) -> None:
        """
        Initialize caching middleware.
        
        Args:
            app: FastAPI application
            cache_ttl: Cache time-to-live in seconds
        
        Note:
            Only caches GET requests with 200 status codes.
            Cache key format: "{method}:{path}"
        """
        super().__init__(app)
        self.cache: Dict[str, Tuple[Dict[str, Any], float]] = {}  # path -> (response_data, timestamp)
        self.cache_ttl = cache_ttl
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with caching.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Cached response if available and valid, otherwise fresh response
        
        Note:
            Only caches GET requests. Cache is checked before processing.
            Successful responses (200) are cached for future requests.
        """
        import json
        
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check cache
        cache_key = f"{request.method}:{request.url.path}"
        if cache_key in self.cache:
            response_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return JSONResponse(content=response_data)
        
        # Process request
        response = await call_next(request)
        
        # Save to cache if successful
        if response.status_code == 200:
            try:
                # Only cache JSON responses
                if hasattr(response, 'body'):
                    body = json.loads(response.body.decode())
                    self.cache[cache_key] = (body, time.time())
            except Exception:
                pass
        
        return response
