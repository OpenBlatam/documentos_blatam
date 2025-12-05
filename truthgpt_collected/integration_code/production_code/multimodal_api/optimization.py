#!/usr/bin/env python3
"""
Sistema de Optimización para la API Multimodal.

Optimizaciones automáticas de rendimiento y recursos.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import time
import threading

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuración de optimizaciones."""
    auto_scale_workers: bool = True
    min_workers: int = 2
    max_workers: int = 16
    scale_up_threshold: float = 0.8  # 80% de utilización
    scale_down_threshold: float = 0.3  # 30% de utilización
    check_interval: int = 60  # segundos
    enable_cache_warming: bool = True
    enable_batch_optimization: bool = True


class PerformanceOptimizer:
    """Optimizador de rendimiento."""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        Inicializa el optimizador.
        
        Args:
            config: Configuración de optimización
        """
        self.config = config or OptimizationConfig()
        self.metrics_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []
        self.running = False
        self.optimizer_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Inicia el optimizador en background."""
        if self.running:
            return
        
        self.running = True
        self.optimizer_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True
        )
        self.optimizer_thread.start()
        logger.info("Performance optimizer iniciado")
    
    def stop(self):
        """Detiene el optimizador."""
        self.running = False
        if self.optimizer_thread:
            self.optimizer_thread.join(timeout=5.0)
        logger.info("Performance optimizer detenido")
    
    def _optimization_loop(self):
        """Loop principal de optimización."""
        while self.running:
            try:
                # Aquí se ejecutarían optimizaciones automáticas
                # Por ahora es un placeholder
                time.sleep(self.config.check_interval)
            except Exception as e:
                logger.error(f"Error en optimization loop: {e}")
                time.sleep(self.config.check_interval)
    
    def record_metrics(
        self,
        queue_size: int,
        active_tasks: int,
        avg_response_time: float,
        error_rate: float
    ):
        """
        Registra métricas para análisis.
        
        Args:
            queue_size: Tamaño de cola
            active_tasks: Tareas activas
            avg_response_time: Tiempo promedio de respuesta
            error_rate: Tasa de errores
        """
        metric = {
            "timestamp": datetime.now(),
            "queue_size": queue_size,
            "active_tasks": active_tasks,
            "avg_response_time": avg_response_time,
            "error_rate": error_rate
        }
        
        self.metrics_history.append(metric)
        
        # Mantener solo últimos 1000 puntos
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """
        Sugiere optimizaciones basadas en métricas.
        
        Returns:
            Lista de sugerencias
        """
        if not self.metrics_history:
            return []
        
        suggestions = []
        recent_metrics = self.metrics_history[-10:]  # Últimos 10 puntos
        
        avg_queue_size = sum(m["queue_size"] for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m["avg_response_time"] for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m["error_rate"] for m in recent_metrics) / len(recent_metrics)
        
        # Sugerencia: Aumentar workers si cola es grande
        if avg_queue_size > 50:
            suggestions.append({
                "type": "scale_up",
                "priority": "high",
                "message": f"Cola grande ({avg_queue_size:.0f} tareas). Considera aumentar workers.",
                "action": "increase_workers"
            })
        
        # Sugerencia: Reducir workers si cola es pequeña
        if avg_queue_size < 5 and len(recent_metrics) > 5:
            suggestions.append({
                "type": "scale_down",
                "priority": "low",
                "message": f"Cola pequeña ({avg_queue_size:.0f} tareas). Considera reducir workers.",
                "action": "decrease_workers"
            })
        
        # Sugerencia: Optimizar si respuesta es lenta
        if avg_response_time > 5.0:
            suggestions.append({
                "type": "performance",
                "priority": "medium",
                "message": f"Tiempo de respuesta alto ({avg_response_time:.2f}s). Revisa optimizaciones.",
                "action": "review_performance"
            })
        
        # Sugerencia: Revisar errores
        if avg_error_rate > 0.05:  # 5%
            suggestions.append({
                "type": "reliability",
                "priority": "high",
                "message": f"Tasa de errores alta ({avg_error_rate*100:.1f}%). Revisa logs.",
                "action": "review_errors"
            })
        
        return suggestions
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de optimizaciones.
        
        Returns:
            Historial
        """
        return self.optimization_history


