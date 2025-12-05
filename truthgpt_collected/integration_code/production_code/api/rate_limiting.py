#!/usr/bin/env python3
"""
Rate Limiting
=============

Rate limiting with sliding window for expensive endpoints.
"""

import time
from collections import deque
from typing import Optional, Dict, Deque, Tuple, Callable, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.utils import setup_logger

logger = setup_logger(__name__)

security = HTTPBearer(auto_error=False)


class SlidingWindowRateLimiter:
    """Rate limiter using sliding window algorithm."""
    
    def __init__(self, default_limit: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default requests per window
            window_seconds: Time window in seconds
        """
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._windows: Dict[str, Deque[float]] = {}
        logger.info(f"Rate limiter initialized: {default_limit} requests per {window_seconds}s")
    
    def _clean_old_requests(self, window: Deque[float], now: float) -> None:
        """Remove requests outside the time window."""
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()
    
    def check_rate_limit(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (IP, API key, etc.)
            limit: Request limit (uses default if None)
            window_seconds: Time window (uses default if None)
        
        Returns:
            Tuple of (allowed, remaining, reset_after_seconds)
            - allowed: True if request is allowed, False if rate limit exceeded
            - remaining: Number of requests remaining in the window
            - reset_after_seconds: Seconds until the window resets
        
        Note:
            Uses sliding window algorithm. Old requests outside the window
            are automatically cleaned up.
        """
        limit = limit or self.default_limit
        window_seconds = window_seconds or self.window_seconds
        now = time.time()
        
        # Get or create window for identifier
        if identifier not in self._windows:
            self._windows[identifier] = deque()
        
        window = self._windows[identifier]
        
        # Clean old requests
        self._clean_old_requests(window, now)
        
        # Check limit
        if len(window) >= limit:
            # Calculate reset time (oldest request + window)
            oldest_request = window[0]
            reset_after = int(self.window_seconds - (now - oldest_request))
            return False, 0, max(1, reset_after)
        
        # Add current request
        window.append(now)
        
        # Calculate remaining
        remaining = limit - len(window)
        
        # Calculate reset time
        if window:
            oldest_request = window[0]
            reset_after = int(self.window_seconds - (now - oldest_request))
        else:
            reset_after = self.window_seconds
        
        return True, remaining, max(1, reset_after)
    
    def get_remaining(self, identifier: str, limit: Optional[int] = None) -> int:
        """
        Get remaining requests for identifier.
        
        Args:
            identifier: Unique identifier (IP, API key, etc.)
            limit: Request limit (uses default if None)
        
        Returns:
            Number of requests remaining in the current window
        """
        allowed, remaining, _ = self.check_rate_limit(identifier, limit)
        return remaining


# Global rate limiter instances
_rate_limiters: Dict[str, SlidingWindowRateLimiter] = {}


def get_rate_limiter(
    endpoint: str,
    limit: int = 100,
    window_seconds: int = 60
) -> SlidingWindowRateLimiter:
    """
    Get or create rate limiter for endpoint.
    
    Args:
        endpoint: Endpoint identifier (path or name)
        limit: Default requests per window
        window_seconds: Default time window in seconds
    
    Returns:
        SlidingWindowRateLimiter instance for the endpoint
    
    Note:
        Rate limiters are cached per endpoint. Same endpoint returns
        the same limiter instance.
    """
    if endpoint not in _rate_limiters:
        _rate_limiters[endpoint] = SlidingWindowRateLimiter(limit, window_seconds)
    return _rate_limiters[endpoint]


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier from request (IP or API key).
    
    Args:
        request: FastAPI request object
    
    Returns:
        Client identifier string in format "api_key:{hash}" or "ip:{ip_address}"
    
    Note:
        Prioritizes API key from Authorization header if available.
        Falls back to client IP address. Uses first 16 chars of API key for privacy.
    """
    # Try to get API key from header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        api_key = auth_header.replace("Bearer ", "")
        if api_key:
            return f"api_key:{api_key[:16]}"  # Use first 16 chars for privacy
    
    # Fallback to IP
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


def rate_limit_dependency(
    limit: int = 100,
    window_seconds: int = 60,
    endpoint_name: Optional[str] = None
) -> Callable[[Request], Any]:
    """
    Create a FastAPI dependency for rate limiting.
    
    Args:
        limit: Requests per window
        window_seconds: Time window in seconds
        endpoint_name: Endpoint name for logging (uses path if None)
    
    Returns:
        FastAPI dependency function that checks rate limits
    
    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    
    Note:
        Rate limit information is added to request.state:
        - rate_limit_remaining: Number of requests remaining
        - rate_limit_reset_after: Seconds until reset
    """
    async def check_rate_limit(request: Request) -> None:
        """Check rate limit for request."""
        identifier = get_client_identifier(request)
        endpoint = endpoint_name or request.url.path
        
        limiter = get_rate_limiter(endpoint, limit, window_seconds)
        allowed, remaining, reset_after = limiter.check_rate_limit(identifier, limit, window_seconds)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {identifier} on {endpoint}",
                extra={
                    "identifier": identifier,
                    "endpoint": endpoint,
                    "limit": limit,
                    "window_seconds": window_seconds
                }
            )
            
            # Build recommendations
            recommendations = [
                f"Limit: {limit} requests per {window_seconds} seconds",
                f"Retry after {reset_after} seconds",
                "Consider using API key for higher limits"
            ]
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "window_seconds": window_seconds,
                    "remaining": remaining,
                    "reset_after_seconds": reset_after,
                    "recommendations": recommendations
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset-After": str(reset_after),
                    "Retry-After": str(reset_after)
                }
            )
        
        # Add rate limit info to request state
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset_after = reset_after
    
    return check_rate_limit

