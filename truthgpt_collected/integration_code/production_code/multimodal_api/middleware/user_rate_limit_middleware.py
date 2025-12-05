#!/usr/bin/env python3
"""
Middleware de Rate Limiting por Usuario.

Aplica rate limiting por usuario/API key.
"""

from typing import Callable, Optional
from fastapi import HTTPException, status

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class UserRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting por usuario."""
    
    def __init__(self, app, user_rate_limiter=None, auth_manager=None):
        """
        Inicializa el middleware.
        
        Args:
            app: Aplicación FastAPI
            user_rate_limiter: Instancia de UserRateLimiter
            auth_manager: Instancia de AuthManager
        """
        super().__init__(app)
        self.user_rate_limiter = user_rate_limiter
        self.auth_manager = auth_manager
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa el request y aplica rate limiting por usuario.
        
        Args:
            request: Request HTTP
            call_next: Función para continuar
        
        Returns:
            Response HTTP
        """
        if not self.user_rate_limiter:
            return await call_next(request)
        
        # Obtener user_id del request
        user_id = None
        
        # Intentar obtener de headers
        user_id = request.headers.get("X-User-ID")
        
        # Si no está en headers, intentar obtener de autenticación
        if not user_id and self.auth_manager:
            try:
                # Intentar obtener de token o API key
                auth_header = request.headers.get("Authorization")
                if auth_header:
                    # Aquí se podría extraer user_id del token
                    # Por ahora, usar el header directamente
                    pass
            except Exception:
                pass
        
        # Si no hay user_id, usar IP como fallback
        if not user_id:
            user_id = request.client.host if request.client else "unknown"
        
        # Verificar rate limit
        allowed, info = self.user_rate_limiter.check_rate_limit(user_id)
        
        if not allowed:
            # Agregar headers informativos
            response = Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = info["reset_at"]
            return response
        
        # Continuar con el request
        response = await call_next(request)
        
        # Agregar headers informativos
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = info["reset_at"]
        
        return response


