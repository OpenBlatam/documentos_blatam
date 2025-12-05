"""
Middleware para la API de Generación Multimodal.

Incluye:
- Rate limiting inteligente
- Caching optimizado
- Monitoring y métricas
"""

from .rate_limiter import RateLimiter, RateLimitConfig, RateLimitStrategy
from .cache import CacheManager, CacheConfig
from .monitoring import MonitoringMiddleware

# Middlewares adicionales
try:
    from .analytics_middleware import AnalyticsMiddleware
    from .alert_middleware import AlertMiddleware
    from .user_rate_limit_middleware import UserRateLimitMiddleware
except ImportError:
    AnalyticsMiddleware = None
    AlertMiddleware = None
    UserRateLimitMiddleware = None

__all__ = [
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitStrategy",
    "CacheManager",
    "CacheConfig",
    "MonitoringMiddleware",
    "AnalyticsMiddleware",
    "AlertMiddleware",
    "UserRateLimitMiddleware",
]

