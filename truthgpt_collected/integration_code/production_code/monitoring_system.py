#!/usr/bin/env python3
"""
Sistema de Monitoreo y Métricas
================================

Sistema unificado para monitorear todos los módulos y generar métricas.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
import json
from pathlib import Path
from enum import Enum

from core.utils import setup_logger

logger = setup_logger(__name__)

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


class MetricType(str, Enum):
    """Tipos de métricas."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Métrica individual."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Resultado de health check."""
    module: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Recolector de métricas.
    
    Almacena y gestiona métricas de todos los módulos.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Inicializa recolector.
        
        Args:
            max_history: Máximo de métricas a mantener en historial
        """
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        logger.info("MetricsCollector inicializado")
    
    def record(self, metric: Metric):
        """
        Registra una métrica.
        
        Args:
            metric: Métrica a registrar
        """
        self.metrics[metric.name].append(metric)
        
        if metric.metric_type == MetricType.COUNTER:
            self.counters[metric.name] += metric.value
        elif metric.metric_type == MetricType.GAUGE:
            self.gauges[metric.name] = metric.value
        elif metric.metric_type == MetricType.HISTOGRAM:
            self.histograms[metric.name].append(metric.value)
        elif metric.metric_type == MetricType.TIMER:
            self.timers[metric.name].append(metric.value)
        
        logger.debug(f"Métrica registrada: {metric.name}={metric.value}")
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict] = None):
        """Incrementa un contador."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            tags=tags or {}
        )
        self.record(metric)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict] = None):
        """Establece un gauge."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            tags=tags or {}
        )
        self.record(metric)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict] = None):
        """Registra un valor en histograma."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            tags=tags or {}
        )
        self.record(metric)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict] = None):
        """Registra duración de operación."""
        metric = Metric(
            name=name,
            value=duration,
            metric_type=MetricType.TIMER,
            tags=tags or {}
        )
        self.record(metric)
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """
        Obtiene resumen de una métrica.
        
        Args:
            name: Nombre de la métrica
        
        Returns:
            Diccionario con resumen
        """
        if name not in self.metrics or len(self.metrics[name]) == 0:
            return {'error': f'Métrica {name} no encontrada'}
        
        values = [m.value for m in self.metrics[name]]
        
        summary = {
            'name': name,
            'count': len(values),
            'mean': sum(values) / len(values) if values else 0.0,
            'min': min(values) if values else 0.0,
            'max': max(values) if values else 0.0,
            'sum': sum(values) if values else 0.0
        }
        
        if len(values) > 1:
            import statistics
            summary['std'] = statistics.stdev(values)
            summary['median'] = statistics.median(values)
        
        return summary
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Obtiene todas las métricas.
        
        Returns:
            Diccionario con todas las métricas
        """
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {k: len(v) for k, v in self.histograms.items()},
            'timers': {k: len(v) for k, v in self.timers.items()},
            'total_metrics': sum(len(v) for v in self.metrics.values())
        }
    
    def export_metrics(self, filepath: str) -> bool:
        """
        Exporta métricas a archivo.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si se exportó exitosamente
        """
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    name: [{
                        'value': m.value,
                        'timestamp': m.timestamp,
                        'tags': m.tags
                    } for m in metrics[-1000:]]  # Últimas 1000
                    for name, metrics in self.metrics.items()
                },
                'summary': self.get_all_metrics()
            }
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"Métricas exportadas a {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}")
            return False


class HealthMonitor:
    """
    Monitor de salud del sistema.
    
    Verifica el estado de todos los módulos.
    """
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Inicializa monitor.
        
        Args:
            metrics_collector: Recolector de métricas (opcional)
        """
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, Callable] = {}
        
        logger.info("HealthMonitor inicializado")
    
    def register_check(self, module: str, check_function: Callable):
        """
        Registra función de health check.
        
        Args:
            module: Nombre del módulo
            check_function: Función que retorna HealthCheck
        """
        self.check_functions[module] = check_function
        logger.info(f"Health check registrado para {module}")
    
    def check_module(self, module: str) -> HealthCheck:
        """
        Ejecuta health check de un módulo.
        
        Args:
            module: Nombre del módulo
        
        Returns:
            HealthCheck con resultado
        """
        if module not in self.check_functions:
            return HealthCheck(
                module=module,
                status="unhealthy",
                message=f"No hay health check registrado para {module}"
            )
        
        try:
            check = self.check_functions[module]()
            self.health_checks[module] = check
            
            # Registrar métrica
            status_value = 1.0 if check.status == "healthy" else 0.5 if check.status == "degraded" else 0.0
            self.metrics_collector.set_gauge(f"health.{module}", status_value)
            
            return check
        except Exception as e:
            logger.error(f"Error en health check de {module}: {e}")
            check = HealthCheck(
                module=module,
                status="unhealthy",
                message=f"Error: {str(e)}"
            )
            self.health_checks[module] = check
            return check
    
    def check_all(self) -> Dict[str, HealthCheck]:
        """
        Ejecuta health checks de todos los módulos.
        
        Returns:
            Diccionario con resultados
        """
        results = {}
        for module in self.check_functions.keys():
            results[module] = self.check_module(module)
        
        return results
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Obtiene salud general del sistema.
        
        Returns:
            Diccionario con salud general
        """
        checks = self.check_all()
        
        healthy = sum(1 for c in checks.values() if c.status == "healthy")
        degraded = sum(1 for c in checks.values() if c.status == "degraded")
        unhealthy = sum(1 for c in checks.values() if c.status == "unhealthy")
        total = len(checks)
        
        overall_status = "healthy"
        if unhealthy > 0:
            overall_status = "unhealthy"
        elif degraded > 0:
            overall_status = "degraded"
        
        return {
            'status': overall_status,
            'healthy': healthy,
            'degraded': degraded,
            'unhealthy': unhealthy,
            'total': total,
            'health_percentage': (healthy / total * 100) if total > 0 else 0.0,
            'checks': {k: {
                'status': v.status,
                'message': v.message
            } for k, v in checks.items()}
        }


class SystemMonitor:
    """
    Monitor completo del sistema.
    
    Combina métricas y health checks.
    """
    
    def __init__(self):
        """Inicializa monitor del sistema."""
        self.metrics_collector = MetricsCollector()
        self.health_monitor = HealthMonitor(self.metrics_collector)
        
        # Registrar health checks por defecto
        self._register_default_checks()
        
        logger.info("SystemMonitor inicializado")
    
    def _register_default_checks(self):
        """Registra health checks por defecto."""
        def check_memory():
            try:
                from memory import create_memory_system
                memory = create_memory_system("2506_15841v2", memory_dim=512)
                stats = memory.get_episodic_stats()
                
                utilization = stats.get('memory_utilization', 0.0)
                if utilization > 0.95:
                    status = "degraded"
                    message = f"Memoria casi llena: {utilization:.2%}"
                elif utilization > 0.8:
                    status = "degraded"
                    message = f"Memoria bastante llena: {utilization:.2%}"
                else:
                    status = "healthy"
                    message = f"Memoria OK: {utilization:.2%}"
                
                return HealthCheck(
                    module="memory",
                    status=status,
                    message=message,
                    metrics=stats
                )
            except Exception as e:
                return HealthCheck(
                    module="memory",
                    status="unhealthy",
                    message=f"Error: {str(e)}"
                )
        
        def check_redundancy():
            try:
                from redundancy import create_redundancy_suppressor
                redundancy = create_redundancy_suppressor("2510_00071")
                metrics = redundancy.get_metrics()
                
                efficiency = metrics.get('efficiency', 0.0)
                if efficiency > 0.5:
                    status = "healthy"
                    message = f"Redundancia eficiente: {efficiency:.2%}"
                elif efficiency > 0.2:
                    status = "degraded"
                    message = f"Redundancia moderada: {efficiency:.2%}"
                else:
                    status = "degraded"
                    message = f"Redundancia baja: {efficiency:.2%}"
                
                return HealthCheck(
                    module="redundancy",
                    status=status,
                    message=message,
                    metrics=metrics
                )
            except Exception as e:
                return HealthCheck(
                    module="redundancy",
                    status="unhealthy",
                    message=f"Error: {str(e)}"
                )
        
        self.health_monitor.register_check("memory", check_memory)
        self.health_monitor.register_check("redundancy", check_redundancy)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtiene estado completo del sistema.
        
        Returns:
            Diccionario con estado completo
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'health': self.health_monitor.get_overall_health(),
            'metrics': self.metrics_collector.get_all_metrics()
        }
    
    def export_report(self, filepath: str) -> bool:
        """
        Exporta reporte completo.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si se exportó exitosamente
        """
        try:
            report = self.get_system_status()
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Reporte exportado a {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exportando reporte: {e}")
            return False
    
    def visualize_metrics(self, save_path: Optional[str] = None):
        """
        Visualiza métricas.
        
        Args:
            save_path: Ruta para guardar visualización
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualización no disponible")
            return
        
        try:
            metrics = self.metrics_collector.get_all_metrics()
            
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # Counters
            if metrics['counters']:
                names = list(metrics['counters'].keys())[:10]
                values = [metrics['counters'][n] for n in names]
                axes[0, 0].bar(names, values)
                axes[0, 0].set_title('Counters')
                axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Gauges
            if metrics['gauges']:
                names = list(metrics['gauges'].keys())[:10]
                values = [metrics['gauges'][n] for n in names]
                axes[0, 1].barh(names, values)
                axes[0, 1].set_title('Gauges')
            
            # Health status
            health = self.health_monitor.get_overall_health()
            status_counts = {
                'healthy': health['healthy'],
                'degraded': health['degraded'],
                'unhealthy': health['unhealthy']
            }
            axes[1, 0].pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
            axes[1, 0].set_title('Health Status')
            
            # Metrics timeline (si hay timers)
            if metrics['timers']:
                timer_names = list(metrics['timers'].keys())[:5]
                axes[1, 1].text(0.5, 0.5, f"Timers: {len(timer_names)}", 
                              ha='center', va='center', fontsize=12)
                axes[1, 1].set_title('Timers')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Visualización guardada en {save_path}")
            else:
                plt.show()
            
            plt.close()
        except Exception as e:
            logger.error(f"Error visualizando métricas: {e}")


# Instancia global
_global_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """
    Obtiene instancia global del monitor.
    
    Returns:
        Instancia de SystemMonitor
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = SystemMonitor()
    
    return _global_monitor


