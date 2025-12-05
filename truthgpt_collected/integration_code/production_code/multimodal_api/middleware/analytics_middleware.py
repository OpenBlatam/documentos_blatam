#!/usr/bin/env python3
"""
Middleware de Analytics.

Registra automáticamente requests y métricas para analytics.
"""

from typing import Callable
from datetime import datetime
import time

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


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware para registrar analytics automáticamente."""
    
    def __init__(self, app, analytics_engine=None):
        """
        Inicializa el middleware.
        
        Args:
            app: Aplicación FastAPI
            analytics_engine: Instancia de AnalyticsEngine
        """
        super().__init__(app)
        self.analytics_engine = analytics_engine
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa el request y registra analytics.
        
        Args:
            request: Request HTTP
            call_next: Función para continuar
        
        Returns:
            Response HTTP
        """
        if not self.analytics_engine:
            return await call_next(request)
        
        start_time = time.time()
        
        # Extraer información del request
        modality = None
        generation_type = None
        user_id = None
        
        # Intentar obtener de headers o path
        if request.url.path.startswith("/api/v1/generate"):
            modality = request.headers.get("X-Modality")
            user_id = request.headers.get("X-User-ID")
        
        # Procesar request
        response = await call_next(request)
        
        # Calcular tiempo de respuesta
        response_time = time.time() - start_time
        
        # Determinar si fue exitoso
        success = 200 <= response.status_code < 400
        
        # Registrar en analytics (de forma asíncrona para no bloquear)
        try:
            if modality:
                self.analytics_engine.record_request(
                    modality=modality,
                    generation_type=generation_type or "unknown",
                    success=success,
                    response_time=response_time,
                    user_id=user_id
                )
        except Exception as e:
            logger.warning(f"Error registrando analytics: {e}")
        
        return response


