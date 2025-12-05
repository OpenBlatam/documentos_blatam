#!/usr/bin/env python3
"""
Tracing Middleware
==================

Middleware for request tracing with request_id generation and logging.
"""

import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.utils import setup_logger

logger = setup_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing with request_id."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with tracing and request ID generation.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response with X-Request-ID header and tracing information
        
        Raises:
            Re-raises any exception from the request handler
        
        Note:
            - Generates unique request ID for each request
            - Adds request_id to request.state and response headers
            - Logs request start and completion with timing
            - Adds request_id and duration to JSON response bodies if possible
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "query_params": dict(request.query_params) if request.query_params else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add request_id to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Add request_id to response body if JSON
            if isinstance(response, JSONResponse):
                try:
                    body = response.body
                    if body:
                        import json
                        data = json.loads(body.decode())
                        if isinstance(data, dict):
                            data["request_id"] = request_id
                            data["metadata"] = data.get("metadata", {})
                            data["metadata"]["duration"] = duration
                            response.body = json.dumps(data).encode()
                except Exception:
                    # If we can't modify the body, just log
                    pass
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration": duration
                },
                exc_info=True
            )
            raise

