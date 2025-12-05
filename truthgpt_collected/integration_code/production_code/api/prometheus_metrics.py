#!/usr/bin/env python3
"""
Prometheus Metrics
==================

Prometheus metrics collection and exposure.
"""

import time
from typing import Callable, TYPE_CHECKING, Any, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

if TYPE_CHECKING:
    from fastapi import FastAPI

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    def generate_latest():
        return b"# Prometheus client not available\n"
    
    CONTENT_TYPE_LATEST = "text/plain"

from core.utils import setup_logger

logger = setup_logger(__name__)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for Prometheus metrics collection."""
    
    def __init__(self, app: "FastAPI", app_name: str = "api") -> None:
        """
        Initialize metrics middleware.
        
        Args:
            app: FastAPI application instance
            app_name: Application name for metrics (used in metric names)
        
        Note:
            Creates Prometheus metrics:
            - Counter: {app_name}_requests_total
            - Histogram: {app_name}_request_duration_seconds
            - Gauge: {app_name}_active_requests
            If prometheus_client is not available, metrics are disabled.
        """
        super().__init__(app)
        self.app_name = app_name
        
        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client not available, metrics disabled")
            return
        
        # Request counters
        self.request_count = Counter(
            f"{app_name}_requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"]
        )
        
        # Request duration histogram
        self.request_duration = Histogram(
            f"{app_name}_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        # Active requests gauge
        self.active_requests = Gauge(
            f"{app_name}_active_requests",
            "Number of active requests",
            ["method", "endpoint"]
        )
        
        logger.info("Prometheus metrics middleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with Prometheus metrics collection.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response after recording metrics
        
        Raises:
            Re-raises any exception from the request handler
        
        Note:
            Records the following metrics:
            - Request count by method, endpoint, and status code
            - Request duration histogram by method and endpoint
            - Active requests gauge by method and endpoint
            If prometheus_client is not available, continues without metrics.
        """
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)
        
        # Get endpoint (normalize path)
        endpoint = self._normalize_path(request.url.path)
        method = request.method
        
        # Increment active requests
        self.active_requests.labels(method=method, endpoint=endpoint).inc()
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Get status code
            status_code = response.status_code
            status_class = f"{status_code // 100}xx"
            
            # Record metrics
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status_class
            ).inc()
            
            duration = time.time() - start_time
            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
        
        except Exception as e:
            # Record error
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status="5xx"
            ).inc()
            
            duration = time.time() - start_time
            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
        
        finally:
            # Decrement active requests
            self.active_requests.labels(method=method, endpoint=endpoint).dec()
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for metrics (remove IDs, etc.).
        
        Args:
            path: Request path
        
        Returns:
            Normalized path
        """
        # Remove common ID patterns
        import re
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        return path


def metrics_endpoint(request: Request) -> Response:
    """
    Endpoint to expose Prometheus metrics.
    
    Args:
        request: FastAPI request
    
    Returns:
        Response with metrics
    """
    if not PROMETHEUS_AVAILABLE:
        return StarletteResponse(
            content="# Prometheus client not available\n",
            media_type=CONTENT_TYPE_LATEST
        )
    
    metrics = generate_latest(REGISTRY)
    return StarletteResponse(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )

