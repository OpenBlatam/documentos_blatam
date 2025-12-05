#!/usr/bin/env python3
"""
Optimizaciones de Rendimiento para la API Multimodal.

Técnicas avanzadas de optimización de rendimiento.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import time
import asyncio
from functools import lru_cache, wraps

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """Configuración de rendimiento."""
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_connection_pooling: bool = True
    max_connections: int = 100
    enable_compression: bool = True
    enable_async_processing: bool = True
    batch_size: int = 100


class PerformanceOptimizer:
    """Optimizador de rendimiento."""
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        """
        Inicializa el optimizador.
        
        Args:
            config: Configuración de rendimiento
        """
        self.config = config or PerformanceConfig()
        self.metrics: Dict[str, List[float]] = {}
    
    def measure_time(self, operation_name: str):
        """
        Decorador para medir tiempo de operación.
        
        Args:
            operation_name: Nombre de la operación
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start
                    self._record_metric(operation_name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start
                    self._record_metric(f"{operation_name}_error", duration)
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start
                    self._record_metric(operation_name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start
                    self._record_metric(f"{operation_name}_error", duration)
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def _record_metric(self, name: str, value: float):
        """
        Registra una métrica.
        
        Args:
            name: Nombre de la métrica
            value: Valor
        """
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
        
        # Mantener solo últimos 1000 valores
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de rendimiento.
        
        Returns:
            Estadísticas
        """
        stats = {}
        
        for name, values in self.metrics.items():
            if values:
                stats[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": sorted(values)[len(values) // 2] if values else 0,
                    "p95": sorted(values)[int(len(values) * 0.95)] if values else 0,
                    "p99": sorted(values)[int(len(values) * 0.99)] if values else 0
                }
        
        return stats
    
    @lru_cache(maxsize=1000)
    def cached_computation(self, key: str, computation_func):
        """
        Cachea una computación.
        
        Args:
            key: Clave de cache
            computation_func: Función de computación
        
        Returns:
            Resultado
        """
        return computation_func()
    
    def batch_process(self, items: List[Any], batch_size: int, processor):
        """
        Procesa items en batches.
        
        Args:
            items: Items a procesar
            batch_size: Tamaño de batch
            processor: Función procesadora
        
        Returns:
            Resultados
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)
        return results
    
    async def async_batch_process(
        self,
        items: List[Any],
        batch_size: int,
        processor
    ):
        """
        Procesa items en batches de forma asíncrona.
        
        Args:
            items: Items a procesar
            batch_size: Tamaño de batch
            processor: Función procesadora asíncrona
        
        Returns:
            Resultados
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(*[processor(item) for item in batch])
            results.extend(batch_results)
        return results


