#!/usr/bin/env python3
"""
Monitoring Utilities for Paper Modules
=======================================

Utilidades para monitoreo y observabilidad de módulos en producción.
"""

import torch
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
import threading

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class Metric:
    """Métrica individual."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Resultado de un health check."""
    status: str
    message: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Colector de métricas para módulos."""
    
    def __init__(self, max_history: int = 1000, use_prometheus: bool = False):
        """
        Inicializa el colector de métricas.
        
        Args:
            max_history: Número máximo de métricas a mantener en historial
            use_prometheus: Si True, también registra métricas en Prometheus
        
        Raises:
            ValueError: Si max_history <= 0
        """
        if max_history <= 0:
            raise ValueError(f"max_history debe ser > 0, recibido: {max_history}")
        
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self.use_prometheus = use_prometheus and PROMETHEUS_AVAILABLE
        self._prometheus_counters: Dict[str, Counter] = {}
        self._prometheus_gauges: Dict[str, Gauge] = {}
        self._prometheus_histograms: Dict[str, Histogram] = {}
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Registra una métrica.
        
        Args:
            name: Nombre de la métrica
            value: Valor de la métrica
            tags: Tags opcionales
        
        Raises:
            ValueError: Si name está vacío o value no es numérico
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"name debe ser un string no vacío, recibido: {name}")
        
        if not isinstance(value, (int, float)):
            raise ValueError(f"value debe ser numérico, recibido: {type(value)}")
        
        if tags is not None and not isinstance(tags, dict):
            raise ValueError(f"tags debe ser dict o None, recibido: {type(tags)}")
        
        with self._lock:
            metric = Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {}
            )
            self.metrics.append(metric)
            
            if self.use_prometheus:
                prom_name = name.replace('.', '_').replace('-', '_')
                if prom_name not in self._prometheus_gauges:
                    self._prometheus_gauges[prom_name] = Gauge(
                        prom_name,
                        f'Métrica {name}',
                        list(tags.keys()) if tags else []
                    )
                if tags:
                    self._prometheus_gauges[prom_name].labels(**tags).set(value)
                else:
                    self._prometheus_gauges[prom_name].set(value)
    
    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Incrementa un contador.
        
        Args:
            name: Nombre del contador
            value: Valor a incrementar
            tags: Tags opcionales
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"name debe ser un string no vacío, recibido: {name}")
        
        if not isinstance(value, int):
            raise ValueError(f"value debe ser int, recibido: {type(value)}")
        
        if tags is not None and not isinstance(tags, dict):
            raise ValueError(f"tags debe ser dict o None, recibido: {type(tags)}")
        
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] = self._counters.get(key, 0) + value
            self.record(f"{name}_total", self._counters[key], tags)
            
            if self.use_prometheus:
                prom_name = name.replace('.', '_').replace('-', '_')
                if prom_name not in self._prometheus_counters:
                    self._prometheus_counters[prom_name] = Counter(
                        prom_name,
                        f'Contador {name}',
                        list(tags.keys()) if tags else []
                    )
                if tags:
                    self._prometheus_counters[prom_name].labels(**tags).inc(value)
                else:
                    self._prometheus_counters[prom_name].inc(value)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Establece un gauge.
        
        Args:
            name: Nombre del gauge
            value: Valor del gauge
            tags: Tags opcionales
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"name debe ser un string no vacío, recibido: {name}")
        
        if not isinstance(value, (int, float)):
            raise ValueError(f"value debe ser numérico, recibido: {type(value)}")
        
        if tags is not None and not isinstance(tags, dict):
            raise ValueError(f"tags debe ser dict o None, recibido: {type(tags)}")
        
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            self.record(name, value, tags)
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Crea una clave única para métricas con tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        since: Optional[float] = None
    ) -> List[Metric]:
        """
        Obtiene métricas filtradas.
        
        Args:
            name: Filtrar por nombre (opcional)
            since: Filtrar por timestamp (opcional)
        
        Returns:
            Lista de métricas
        """
        with self._lock:
            metrics = list(self.metrics)
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de métricas.
        
        Returns:
            Diccionario con resumen
        """
        with self._lock:
            return {
                'total_metrics': len(self.metrics),
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'recent_metrics': [
                    {
                        'name': m.name,
                        'value': m.value,
                        'timestamp': m.timestamp,
                        'tags': m.tags
                    }
                    for m in list(self.metrics)[-10:]
                ]
            }


class HealthMonitor:
    """Monitor de salud para módulos."""
    
    def __init__(self):
        """Inicializa el monitor de salud."""
        self.checks: Dict[str, Callable] = {}
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Registra un health check.
        
        Args:
            name: Nombre del check
            check_func: Función que retorna HealthCheck
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"name debe ser un string no vacío, recibido: {name}")
        
        if not callable(check_func):
            raise ValueError(f"check_func debe ser callable, recibido: {type(check_func)}")
        
        self.checks[name] = check_func
        logger.info("Health check registrado", check_name=name)
    
    def run_checks(self, module: BasePaperModule) -> Dict[str, HealthCheck]:
        """
        Ejecuta todos los health checks.
        
        Args:
            module: Módulo a verificar
        
        Returns:
            Diccionario con resultados de checks
        
        Raises:
            ValueError: Si module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        results = {}
        for name, check_func in self.checks.items():
            result, error = safe_execute(
                check_func,
                default_value=HealthCheck(
                    status='error',
                    message='Unknown error',
                    timestamp=time.time()
                ),
                log_errors=True,
                module=module
            )
            
            if error:
                result = HealthCheck(
                    status='error',
                    message=f"Error ejecutando check: {str(error)}",
                    timestamp=time.time()
                )
            
            results[name] = result
        return results
    
    def get_overall_health(self, module: BasePaperModule) -> HealthCheck:
        """
        Obtiene el estado de salud general.
        
        Args:
            module: Módulo a verificar
        
        Returns:
            HealthCheck con estado general
        
        Raises:
            ValueError: Si module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        checks = self.run_checks(module)
        
        statuses = [check.status for check in checks.values()]
        
        if 'error' in statuses:
            overall_status = 'error'
        elif 'degraded' in statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return HealthCheck(
            status=overall_status,
            message=f"Overall health: {overall_status}",
            timestamp=time.time(),
            details={'checks': {name: check.status for name, check in checks.items()}}
        )


def create_default_health_checks() -> HealthMonitor:
    """
    Crea health checks por defecto.
    
    Returns:
        HealthMonitor con checks predefinidos
    """
    monitor = HealthMonitor()
    
    def check_model_loaded(module: BasePaperModule) -> HealthCheck:
        """Verifica que el modelo esté cargado correctamente."""
        try:
            info = module.get_model_info()
            has_params = info['total_parameters'] > 0
            return HealthCheck(
                status='healthy' if has_params else 'degraded',
                message='Model loaded' if has_params else 'Model has no parameters',
                timestamp=time.time(),
                details={'parameters': info['total_parameters']}
            )
        except Exception as e:
            return HealthCheck(
                status='error',
                message=f"Error checking model: {str(e)}",
                timestamp=time.time()
            )
    
    def check_device_consistency(module: BasePaperModule) -> HealthCheck:
        """Verifica consistencia de device."""
        try:
            info = module.get_model_info()
            device = info.get('device', 'unknown')
            return HealthCheck(
                status='healthy',
                message=f'Device: {device}',
                timestamp=time.time(),
                details={'device': device}
            )
        except Exception as e:
            return HealthCheck(
                status='error',
                message=f"Error checking device: {str(e)}",
                timestamp=time.time()
            )
    
    monitor.register_check('model_loaded', check_model_loaded)
    monitor.register_check('device_consistency', check_device_consistency)
    
    return monitor

