#!/usr/bin/env python3
"""
Middleware de Alertas.

Verifica condiciones y dispara alertas automáticamente.
"""

from typing import Callable, Optional
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


class AlertMiddleware(BaseHTTPMiddleware):
    """Middleware para verificar alertas automáticamente."""
    
    def __init__(
        self,
        app,
        alert_manager=None,
        metrics_collector=None,
        task_queue=None,
        cache_manager=None
    ):
        """
        Inicializa el middleware.
        
        Args:
            app: Aplicación FastAPI
            alert_manager: Instancia de AlertManager
            metrics_collector: Instancia de MetricsCollector
            task_queue: Instancia de TaskQueue
            cache_manager: Instancia de CacheManager
        """
        super().__init__(app)
        self.alert_manager = alert_manager
        self.metrics_collector = metrics_collector
        self.task_queue = task_queue
        self.cache_manager = cache_manager
        self.last_check = datetime.now()
        self.check_interval = 60  # Verificar cada 60 segundos
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa el request y verifica alertas.
        
        Args:
            request: Request HTTP
            call_next: Función para continuar
        
        Returns:
            Response HTTP
        """
        response = await call_next(request)
        
        # Verificar alertas periódicamente
        if self.alert_manager and (datetime.now() - self.last_check).total_seconds() >= self.check_interval:
            try:
                self._check_alerts()
                self.last_check = datetime.now()
            except Exception as e:
                logger.warning(f"Error verificando alertas: {e}")
        
        return response
    
    def _check_alerts(self):
        """Verifica todas las alertas."""
        if not self.alert_manager:
            return
        
        context = {}
        
        # Obtener métricas
        if self.metrics_collector:
            try:
                stats = self.metrics_collector.get_stats()
                context["error_rate"] = stats.get("error_rate", 0)
                context["avg_response_time"] = stats.get("avg_response_time", 0)
            except Exception:
                pass
        
        # Obtener estadísticas de cola
        if self.task_queue:
            try:
                queue_stats = self.task_queue.get_queue_stats()
                context["queue_size"] = queue_stats.get("queue_size", 0)
                context["active_workers"] = queue_stats.get("active_workers", 0)
            except Exception:
                pass
        
        # Obtener estadísticas de cache
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_stats()
                context["cache_hit_rate"] = cache_stats.get("hit_rate", 1.0)
            except Exception:
                pass
        
        # Verificar alertas
        self.alert_manager.check_alerts(context)


