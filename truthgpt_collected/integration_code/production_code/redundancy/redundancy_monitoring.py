#!/usr/bin/env python3
"""
Monitoreo y Observabilidad para Redundancy
==========================================

Integración con el sistema de monitoreo para métricas y observabilidad.
"""

from typing import Dict, List, Optional, Any
import time
from dataclasses import dataclass

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)

try:
    from core.monitoring import MetricsCollector, HealthCheck
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    MetricsCollector = None
    HealthCheck = None


@dataclass
class RedundancyMetrics:
    """Métricas de redundancia."""
    total_processed: int = 0
    total_reduced: int = 0
    avg_reduction_rate: float = 0.0
    avg_processing_time: float = 0.0
    cache_hit_rate: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0


class RedundancyMonitor:
    """
    Monitor de redundancia con integración al sistema de monitoreo.
    """
    
    def __init__(
        self,
        suppressor: Any,
        metrics_collector: Optional[Any] = None
    ):
        """
        Args:
            suppressor: Supresor de redundancia a monitorear
            metrics_collector: Colector de métricas (opcional)
        
        Raises:
            ValueError: Si suppressor es None
        """
        if suppressor is None:
            raise ValueError("suppressor no puede ser None")
        
        self.suppressor = suppressor
        self.metrics_collector = metrics_collector
        
        if metrics_collector is None and MONITORING_AVAILABLE:
            self.metrics_collector = MetricsCollector()
        
        self.start_time = time.time()
        self.processed_count = 0
        self.error_count = 0
    
    def record_processing(
        self,
        original_size: int,
        reduced_size: int,
        processing_time: float,
        success: bool = True
    ):
        """
        Registra un procesamiento.
        
        Args:
            original_size: Tamaño original
            reduced_size: Tamaño reducido
            processing_time: Tiempo de procesamiento
            success: Si fue exitoso
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if original_size < 0:
            raise ValueError(f"original_size debe ser >= 0, recibido: {original_size}")
        if reduced_size < 0:
            raise ValueError(f"reduced_size debe ser >= 0, recibido: {reduced_size}")
        if reduced_size > original_size:
            raise ValueError(f"reduced_size ({reduced_size}) no puede ser mayor que original_size ({original_size})")
        if processing_time < 0:
            raise ValueError(f"processing_time debe ser >= 0, recibido: {processing_time}")
        if not self.metrics_collector:
            return
        
        reduction_rate = (original_size - reduced_size) / original_size if original_size > 0 else 0.0
        throughput = original_size / processing_time if processing_time > 0 else 0.0
        
        def _record():
            self.metrics_collector.record(
                'redundancy.reduction_rate',
                reduction_rate,
                tags={'method': getattr(self.suppressor, 'detection_method', 'unknown')}
            )
            
            self.metrics_collector.record(
                'redundancy.processing_time',
                processing_time,
                tags={'method': getattr(self.suppressor, 'detection_method', 'unknown')}
            )
            
            self.metrics_collector.record(
                'redundancy.throughput',
                throughput,
                tags={'method': getattr(self.suppressor, 'detection_method', 'unknown')}
            )
            
            self.metrics_collector.increment(
                'redundancy.items_processed',
                original_size
            )
            
            self.metrics_collector.increment(
                'redundancy.items_reduced',
                original_size - reduced_size
            )
            
            if success:
                self.metrics_collector.increment('redundancy.success')
            else:
                self.metrics_collector.increment('redundancy.errors')
            
            self.processed_count += 1
            if not success:
                self.error_count += 1
        
        safe_execute(_record, default_value=None, log_errors=False)
    
    def record_cache_stats(
        self,
        hits: int,
        misses: int
    ):
        """
        Registra estadísticas de caché.
        
        Args:
            hits: Número de cache hits
            misses: Número de cache misses
        """
        if not self.metrics_collector:
            return
        
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0
        
        def _record():
            self.metrics_collector.set_gauge('redundancy.cache.hits', hits)
            self.metrics_collector.set_gauge('redundancy.cache.misses', misses)
            self.metrics_collector.set_gauge('redundancy.cache.hit_rate', hit_rate)
        
        safe_execute(_record, default_value=None, log_errors=False)
    
    def get_health_check(self) -> Optional[Any]:
        """
        Obtiene un health check del supresor.
        
        Returns:
            HealthCheck o None
        """
        if not MONITORING_AVAILABLE:
            return None
        
        def _check():
            uptime = time.time() - self.start_time
            error_rate = self.error_count / self.processed_count if self.processed_count > 0 else 0.0
            
            status = 'healthy'
            message = 'Redundancy suppressor is operating normally'
            details = {
                'uptime_seconds': uptime,
                'processed_count': self.processed_count,
                'error_count': self.error_count,
                'error_rate': error_rate
            }
            
            if error_rate > 0.1:
                status = 'degraded'
                message = f'High error rate: {error_rate:.2%}'
            elif error_rate > 0.05:
                status = 'warning'
                message = f'Moderate error rate: {error_rate:.2%}'
            
            if hasattr(self.suppressor, 'get_metrics'):
                metrics = self.suppressor.get_metrics()
                details['suppressor_metrics'] = metrics
            
            return HealthCheck(
                status=status,
                message=message,
                timestamp=time.time(),
                details=details
            )
        
        result, error = safe_execute(_check, default_value=None, log_errors=False)
        return result
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de métricas.
        
        Returns:
            Diccionario con resumen de métricas
        """
        def _get_summary():
            uptime = time.time() - self.start_time
            error_rate = self.error_count / self.processed_count if self.processed_count > 0 else 0.0
            
            summary = {
                'uptime_seconds': uptime,
                'processed_count': self.processed_count,
                'error_count': self.error_count,
                'error_rate': error_rate,
                'avg_throughput': self.processed_count / uptime if uptime > 0 else 0.0
            }
            
            if self.metrics_collector and hasattr(self.metrics_collector, 'get_summary'):
                collector_summary = self.metrics_collector.get_summary()
                summary['collector_metrics'] = collector_summary
            
            if hasattr(self.suppressor, 'get_metrics'):
                suppressor_metrics = self.suppressor.get_metrics()
                summary['suppressor_metrics'] = suppressor_metrics
            
            return summary
        
        result, error = safe_execute(_get_summary, default_value={}, log_errors=False)
        return result


def create_redundancy_monitor(
    suppressor: Any,
    enable_monitoring: bool = True
) -> Optional[RedundancyMonitor]:
    """
    Crea un monitor de redundancia.
    
    Args:
        suppressor: Supresor de redundancia
        enable_monitoring: Si habilitar monitoreo
    
    Returns:
        RedundancyMonitor o None
    """
    if not enable_monitoring or not MONITORING_AVAILABLE:
        return None
    
    return RedundancyMonitor(suppressor)

