#!/usr/bin/env python3
"""
Middleware de Monitoring para la API Multimodal.

Rastrea métricas, performance y salud del sistema.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import time
import threading

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from ...metrics import metrics_collector
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class MonitoringMiddleware:
    """Middleware para monitoreo de la API."""
    
    def __init__(self):
        """Inicializa el middleware de monitoring."""
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times: list = []
        self.active_tasks = 0
        self.queue_size = 0
        self.modality_stats: Dict[str, int] = defaultdict(int)
        self.status_stats: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
    
    def record_request(
        self,
        modality: str,
        duration: float,
        status: str = "success",
        error: Optional[str] = None
    ):
        """
        Registra una request.
        
        Args:
            modality: Modalidad de la request
            duration: Duración en segundos
            status: Estado (success, error)
            error: Mensaje de error (opcional)
        """
        with self.lock:
            self.request_count += 1
            self.modality_stats[modality] += 1
            
            if status == "error":
                self.error_count += 1
                self.status_stats["error"] += 1
            else:
                self.status_stats["success"] += 1
            
            self.response_times.append(duration)
            
            # Mantener solo los últimos 1000 tiempos
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            # Registrar en métricas globales
            if METRICS_AVAILABLE:
                metrics_collector.record_counter(
                    "api.requests.total",
                    tags={"modality": modality, "status": status}
                )
                metrics_collector.record_timing(
                    "api.request.duration",
                    duration,
                    tags={"modality": modality, "status": status}
                )
                if status == "error":
                    metrics_collector.record_counter(
                        "api.errors",
                        tags={"modality": modality, "error": error or "unknown"}
                    )
    
    def update_active_tasks(self, count: int):
        """
        Actualiza el número de tareas activas.
        
        Args:
            count: Número de tareas activas
        """
        with self.lock:
            self.active_tasks = count
    
    def update_queue_size(self, size: int):
        """
        Actualiza el tamaño de la cola.
        
        Args:
            size: Tamaño de la cola
        """
        with self.lock:
            self.queue_size = size
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de monitoring.
        
        Returns:
            Estadísticas
        """
        with self.lock:
            uptime = time.time() - self.start_time
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0.0
            )
            
            error_rate = (
                (self.error_count / self.request_count * 100)
                if self.request_count > 0 else 0.0
            )
            
            return {
                "uptime_seconds": round(uptime, 2),
                "total_requests": self.request_count,
                "error_count": self.error_count,
                "error_rate": round(error_rate, 2),
                "average_response_time": round(avg_response_time, 3),
                "active_tasks": self.active_tasks,
                "queue_size": self.queue_size,
                "modality_stats": dict(self.modality_stats),
                "status_stats": dict(self.status_stats)
            }
    
    def reset(self):
        """Resetea las estadísticas."""
        with self.lock:
            self.request_count = 0
            self.error_count = 0
            self.response_times.clear()
            self.modality_stats.clear()
            self.status_stats.clear()
            self.start_time = time.time()

