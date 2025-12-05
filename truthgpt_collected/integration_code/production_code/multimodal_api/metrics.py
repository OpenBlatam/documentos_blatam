#!/usr/bin/env python3
"""
Sistema de Métricas Avanzado para la API Multimodal.

Recopila y expone métricas detalladas del sistema.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Punto de métrica."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Recolector de métricas."""
    
    def __init__(self, retention_hours: int = 24):
        """
        Inicializa el recolector de métricas.
        
        Args:
            retention_hours: Horas de retención de métricas
        """
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.start_time = time.time()
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """
        Registra un contador.
        
        Args:
            name: Nombre de la métrica
            value: Valor a incrementar
            tags: Tags adicionales
        """
        key = self._build_key(name, tags)
        self.counters[key] += value
        
        self.metrics[key].append(MetricPoint(
            timestamp=datetime.now(),
            value=self.counters[key],
            tags=tags or {}
        ))
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Registra un gauge.
        
        Args:
            name: Nombre de la métrica
            value: Valor actual
            tags: Tags adicionales
        """
        key = self._build_key(name, tags)
        self.gauges[key] = value
        
        self.metrics[key].append(MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        ))
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Registra un valor en un histograma.
        
        Args:
            name: Nombre de la métrica
            value: Valor a registrar
            tags: Tags adicionales
        """
        key = self._build_key(name, tags)
        self.histograms[key].append(value)
        
        # Mantener solo los últimos 1000 valores
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """
        Registra una duración.
        
        Args:
            name: Nombre de la métrica
            duration: Duración en segundos
            tags: Tags adicionales
        """
        self.record_histogram(f"{name}.duration", duration, tags)
    
    def _build_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """
        Construye una clave única para la métrica.
        
        Args:
            name: Nombre de la métrica
            tags: Tags
        
        Returns:
            Clave única
        """
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """
        Obtiene métricas filtradas.
        
        Args:
            name: Nombre de métrica (opcional)
            start_time: Tiempo de inicio (opcional)
            end_time: Tiempo de fin (opcional)
        
        Returns:
            Lista de puntos de métrica
        """
        if name:
            metrics = self.metrics.get(name, deque())
        else:
            # Todas las métricas
            metrics = []
            for metric_deque in self.metrics.values():
                metrics.extend(metric_deque)
            metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # Filtrar por tiempo
        if start_time or end_time:
            filtered = []
            for point in metrics:
                if start_time and point.timestamp < start_time:
                    continue
                if end_time and point.timestamp > end_time:
                    continue
                filtered.append(point)
            return filtered
        
        return list(metrics)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de todas las métricas.
        
        Returns:
            Resumen de métricas
        """
        uptime = time.time() - self.start_time
        
        # Calcular estadísticas de histogramas
        histogram_stats = {}
        for name, values in self.histograms.items():
            if values:
                histogram_stats[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }
        
        return {
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": histogram_stats,
            "total_metric_points": sum(len(m) for m in self.metrics.values())
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """
        Calcula un percentil.
        
        Args:
            values: Valores
            percentile: Percentil (0-100)
        
        Returns:
            Valor del percentil
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def clear_old_metrics(self, hours: Optional[int] = None):
        """
        Limpia métricas antiguas.
        
        Args:
            hours: Horas de antigüedad (opcional)
        """
        cutoff = datetime.now() - timedelta(hours=hours or self.retention_hours)
        
        for name, metric_deque in self.metrics.items():
            # Remover puntos antiguos
            while metric_deque and metric_deque[0].timestamp < cutoff:
                metric_deque.popleft()


# Instancia global
metrics_collector = MetricsCollector()


