#!/usr/bin/env python3
"""
Tests para Rate Limiter.
"""

import pytest
import time
from multimodal_api.middleware.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy
)


def test_rate_limiter_sliding_window():
    """Test de rate limiter con sliding window."""
    config = RateLimitConfig(
        max_requests=5,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
    limiter = RateLimiter(config)
    
    identifier = "test_user"
    
    # Primeras 5 requests deberían pasar
    for i in range(5):
        result = limiter.check_rate_limit(identifier)
        assert result.allowed, f"Request {i+1} debería estar permitido"
    
    # La 6ta debería ser bloqueada
    result = limiter.check_rate_limit(identifier)
    assert not result.allowed, "Request 6 debería estar bloqueado"
    assert result.limit_exceeded


def test_rate_limiter_priority():
    """Test de rate limiter con prioridad."""
    config = RateLimitConfig(
        max_requests=10,
        window_seconds=60
    )
    limiter = RateLimiter(config)
    
    identifier = "test_user"
    
    # Prioridad alta (1) debería tener más límite
    result_high = limiter.check_rate_limit(identifier, priority=1)
    result_low = limiter.check_rate_limit(identifier, priority=10)
    
    # Ambos deberían pasar, pero high priority tiene más remaining
    assert result_high.allowed
    assert result_low.allowed


