#!/usr/bin/env python3
"""
Monitoring - Sistema de Monitoreo y Alertas
============================================

Sistema de monitoreo para el módulo Sora.
"""

import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import threading

from core.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class AlertThreshold:
    """Umbral para alertas."""
    metric_name: str
    threshold: float
    comparison: str  # "gt", "lt", "eq"
    severity: str = "warning"  # "info", "warning", "error", "critical"
    message: Optional[str] = None


@dataclass
class MetricSnapshot:
    """Snapshot de métricas."""
    timestamp: datetime
    metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SoraMonitor:
    """
    Monitor para el módulo Sora.
    
    Proporciona monitoreo de métricas, alertas y estadísticas.
    """
    
    def __init__(
        self,
        history_size: int = 1000,
        alert_callbacks: Optional[List[Callable]] = None
    ):
        """
        Inicializa el monitor.
        
        Args:
            history_size: Tamaño del historial de métricas
            alert_callbacks: Callbacks para alertas
        """
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.current_metrics: Dict[str, float] = {}
        self.alert_thresholds: List[AlertThreshold] = []
        self.alert_callbacks = alert_callbacks or []
        self.lock = threading.RLock()
        self.start_time = datetime.now()
    
    def record_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Registra una métrica.
        
        Args:
            name: Nombre de la métrica
            value: Valor de la métrica
            metadata: Metadata adicional
        """
        with self.lock:
            self.current_metrics[name] = value
            
            snapshot = MetricSnapshot(
                timestamp=datetime.now(),
                metrics={name: value},
                metadata=metadata or {}
            )
            self.metrics_history.append(snapshot)
            
            # Verificar alertas
            self._check_alerts(name, value)
    
    def record_metrics(self, metrics: Dict[str, float], metadata: Optional[Dict[str, Any]] = None):
        """
        Registra múltiples métricas.
        
        Args:
            metrics: Diccionario de métricas
            metadata: Metadata adicional
        """
        with self.lock:
            self.current_metrics.update(metrics)
            
            snapshot = MetricSnapshot(
                timestamp=datetime.now(),
                metrics=metrics.copy(),
                metadata=metadata or {}
            )
            self.metrics_history.append(snapshot)
            
            # Verificar alertas
            for name, value in metrics.items():
                self._check_alerts(name, value)
    
    def add_alert_threshold(
        self,
        metric_name: str,
        threshold: float,
        comparison: str = "gt",
        severity: str = "warning",
        message: Optional[str] = None
    ):
        """
        Agrega umbral de alerta.
        
        Args:
            metric_name: Nombre de la métrica
            threshold: Valor umbral
            comparison: Comparación ("gt", "lt", "eq")
            severity: Severidad de la alerta
            message: Mensaje personalizado
        """
        threshold_obj = AlertThreshold(
            metric_name=metric_name,
            threshold=threshold,
            comparison=comparison,
            severity=severity,
            message=message
        )
        self.alert_thresholds.append(threshold_obj)
    
    def _check_alerts(self, metric_name: str, value: float):
        """Verifica alertas para una métrica."""
        for threshold in self.alert_thresholds:
            if threshold.metric_name != metric_name:
                continue
            
            triggered = False
            if threshold.comparison == "gt" and value > threshold.threshold:
                triggered = True
            elif threshold.comparison == "lt" and value < threshold.threshold:
                triggered = True
            elif threshold.comparison == "eq" and abs(value - threshold.threshold) < 0.001:
                triggered = True
            
            if triggered:
                message = threshold.message or (
                    f"Alerta {threshold.severity}: {metric_name} = {value} "
                    f"{threshold.comparison} {threshold.threshold}"
                )
                self._trigger_alert(threshold.severity, message, {
                    'metric_name': metric_name,
                    'value': value,
                    'threshold': threshold.threshold
                })
    
    def _trigger_alert(self, severity: str, message: str, details: Dict[str, Any]):
        """Dispara una alerta."""
        alert = {
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        if severity == "error" or severity == "critical":
            logger.error(f"ALERTA: {message}", **details)
        elif severity == "warning":
            logger.warning(f"ALERTA: {message}", **details)
        else:
            logger.info(f"ALERTA: {message}", **details)
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    def get_metrics(self, last_n: Optional[int] = None) -> List[MetricSnapshot]:
        """
        Obtiene métricas del historial.
        
        Args:
            last_n: Número de snapshots a obtener (None = todos)
        
        Returns:
            Lista de snapshots
        """
        with self.lock:
            if last_n:
                return list(self.metrics_history)[-last_n:]
            return list(self.metrics_history)
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Obtiene métricas actuales."""
        with self.lock:
            return self.current_metrics.copy()
    
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """
        Obtiene estadísticas de una métrica.
        
        Args:
            metric_name: Nombre de la métrica
        
        Returns:
            Estadísticas (mean, std, min, max, count)
        """
        values = []
        for snapshot in self.metrics_history:
            if metric_name in snapshot.metrics:
                values.append(snapshot.metrics[metric_name])
        
        if not values:
            return {}
        
        import numpy as np
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'count': len(values),
            'latest': values[-1] if values else None
        }
    
    def get_uptime(self) -> timedelta:
        """Obtiene tiempo de actividad."""
        return datetime.now() - self.start_time
    
    def reset(self):
        """Resetea el monitor."""
        with self.lock:
            self.metrics_history.clear()
            self.current_metrics.clear()
            self.start_time = datetime.now()


