#!/usr/bin/env python3
"""
Middleware para API
==================

⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.

Please use `api.middleware` instead:
    from api.middleware import LoggingMiddleware, MetricsMiddleware, ErrorHandlingMiddleware, CachingMiddleware

This file is kept for backward compatibility only.
All functionality has been migrated to `api/middleware.py`.
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "api_middleware (root) is deprecated. Use 'api.middleware' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from api.middleware for backward compatibility
try:
    from api.middleware import (
        RequestIDMiddleware,
        LoggingMiddleware,
        MetricsMiddleware,
        ErrorHandlingMiddleware,
        CachingMiddleware,
    )
except ImportError as e:
    # If api.middleware is not available, raise a clear error
    raise ImportError(
        "api.middleware is not available. "
        "Please ensure the api package is properly installed. "
        f"Original error: {e}"
    ) from e

__all__ = [
    "RequestIDMiddleware",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "ErrorHandlingMiddleware",
    "CachingMiddleware",
]


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request con logging."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None
        )
        
        # Procesar request
        try:
            response = await call_next(request)
            
            # Calcular duración
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code}",
                status_code=response.status_code,
                duration=duration
            )
            
            # Registrar métrica
            try:
                monitor = get_system_monitor()
                monitor.metrics_collector.record_timer(
                    f"api.request.{request.url.path}",
                    duration,
                    tags={'method': request.method, 'status': response.status_code}
                )
            except Exception:
                pass
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error en request: {request.method} {request.url.path}",
                error=str(e),
                duration=duration
            )
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para métricas."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request con métricas."""
        monitor = get_system_monitor()
        
        # Incrementar contador
        monitor.metrics_collector.increment("api.requests.total")
        monitor.metrics_collector.increment(f"api.requests.{request.method}")
        
        # Procesar request
        response = await call_next(request)
        
        # Registrar status code
        monitor.metrics_collector.increment(f"api.responses.{response.status_code}")
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para manejo de errores."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request con manejo de errores."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error no manejado: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": str(e),
                    "path": request.url.path
                }
            )


class CachingMiddleware(BaseHTTPMiddleware):
    """Middleware para caché de respuestas."""
    
    def __init__(self, app, cache_ttl: int = 60):
        """
        Inicializa middleware.
        
        Args:
            app: Aplicación FastAPI
            cache_ttl: Tiempo de vida del caché en segundos
        """
        super().__init__(app)
        self.cache: Dict[str, tuple] = {}  # path -> (response, timestamp)
        self.cache_ttl = cache_ttl
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request con caché."""
        # Solo cachear GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Verificar caché
        cache_key = f"{request.method}:{request.url.path}"
        if cache_key in self.cache:
            response_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return JSONResponse(content=response_data)
        
        # Procesar request
        response = await call_next(request)
        
        # Guardar en caché si es exitoso
        if response.status_code == 200:
            try:
                # Solo cachear respuestas JSON
                if hasattr(response, 'body'):
                    body = json.loads(response.body.decode())
                    self.cache[cache_key] = (body, time.time())
            except Exception:
                pass
        
        return response


