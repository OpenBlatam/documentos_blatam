#!/usr/bin/env python3
"""
Sistema de Alertas para la API Multimodal.

Monitorea condiciones críticas y envía alertas.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Severidad de alerta."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alerta."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AlertRule:
    """Regla de alerta."""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message_template: str,
        cooldown_seconds: int = 300
    ):
        """
        Inicializa una regla de alerta.
        
        Args:
            name: Nombre de la regla
            condition: Función que evalúa la condición
            severity: Severidad
            message_template: Plantilla de mensaje
            cooldown_seconds: Tiempo de cooldown entre alertas
        """
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.cooldown_seconds = cooldown_seconds
        self.last_triggered: Optional[datetime] = None
    
    def check(self, context: Dict[str, Any]) -> Optional[Alert]:
        """
        Verifica la condición.
        
        Args:
            context: Contexto con métricas
        
        Returns:
            Alerta si se cumple la condición, None si no
        """
        # Verificar cooldown
        if self.last_triggered:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return None
        
        if self.condition(context):
            self.last_triggered = datetime.now()
            message = self.message_template.format(**context)
            
            return Alert(
                id=f"{self.name}_{datetime.now().timestamp()}",
                severity=self.severity,
                title=self.name,
                message=message,
                timestamp=datetime.now(),
                metadata=context
            )
        
        return None


class AlertManager:
    """Gestor de alertas."""
    
    def __init__(self):
        """Inicializa el gestor de alertas."""
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.handlers: List[Callable[[Alert], None]] = []
        
        # Registrar reglas por defecto
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Registra reglas de alerta por defecto."""
        # Alta tasa de errores
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda ctx: ctx.get("error_rate", 0) > 0.1,  # > 10%
            severity=AlertSeverity.ERROR,
            message_template="Tasa de errores alta: {error_rate:.1%}",
            cooldown_seconds=300
        ))
        
        # Cola muy grande
        self.add_rule(AlertRule(
            name="large_queue",
            condition=lambda ctx: ctx.get("queue_size", 0) > 1000,
            severity=AlertSeverity.WARNING,
            message_template="Cola grande: {queue_size} tareas pendientes",
            cooldown_seconds=600
        ))
        
        # Alta latencia
        self.add_rule(AlertRule(
            name="high_latency",
            condition=lambda ctx: ctx.get("avg_response_time", 0) > 5.0,  # > 5 segundos
            severity=AlertSeverity.WARNING,
            message_template="Latencia alta: {avg_response_time:.2f}s",
            cooldown_seconds=300
        ))
        
        # Cache hit rate bajo
        self.add_rule(AlertRule(
            name="low_cache_hit_rate",
            condition=lambda ctx: ctx.get("cache_hit_rate", 1.0) < 0.5,  # < 50%
            severity=AlertSeverity.INFO,
            message_template="Cache hit rate bajo: {cache_hit_rate:.1%}",
            cooldown_seconds=600
        ))
        
        # Sin workers activos
        self.add_rule(AlertRule(
            name="no_active_workers",
            condition=lambda ctx: ctx.get("active_workers", 0) == 0,
            severity=AlertSeverity.CRITICAL,
            message_template="No hay workers activos",
            cooldown_seconds=60
        ))
    
    def add_rule(self, rule: AlertRule):
        """
        Agrega una regla de alerta.
        
        Args:
            rule: Regla a agregar
        """
        self.rules.append(rule)
        logger.info(f"Regla de alerta agregada: {rule.name}")
    
    def register_handler(self, handler: Callable[[Alert], None]):
        """
        Registra un manejador de alertas.
        
        Args:
            handler: Función que maneja alertas
        """
        self.handlers.append(handler)
        logger.info("Handler de alertas registrado")
    
    def check_alerts(self, context: Dict[str, Any]):
        """
        Verifica todas las reglas de alerta.
        
        Args:
            context: Contexto con métricas
        """
        for rule in self.rules:
            alert = rule.check(context)
            if alert:
                self.trigger_alert(alert)
    
    def trigger_alert(self, alert: Alert):
        """
        Dispara una alerta.
        
        Args:
            alert: Alerta a disparar
        """
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Mantener solo últimos 1000 alertas
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Notificar handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error en handler de alerta: {e}")
        
        logger.warning(
            f"Alerta disparada: {alert.severity.value} - {alert.title}",
            alert_id=alert.id,
            message=alert.message
        )
    
    def resolve_alert(self, alert_id: str):
        """
        Resuelve una alerta.
        
        Args:
            alert_id: ID de la alerta
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            del self.active_alerts[alert_id]
            logger.info(f"Alerta resuelta: {alert_id}")
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Obtiene alertas activas.
        
        Returns:
            Lista de alertas activas
        """
        return list(self.active_alerts.values())
    
    def get_alert_history(
        self,
        severity: Optional[AlertSeverity] = None,
        hours: int = 24
    ) -> List[Alert]:
        """
        Obtiene historial de alertas.
        
        Args:
            severity: Filtrar por severidad
            hours: Horas a revisar
        
        Returns:
            Lista de alertas
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        alerts = [
            a for a in self.alert_history
            if a.timestamp > cutoff
        ]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de alertas.
        
        Returns:
            Estadísticas
        """
        active_by_severity = {}
        for alert in self.active_alerts.values():
            severity = alert.severity.value
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1
        
        recent_alerts = self.get_alert_history(hours=24)
        recent_by_severity = {}
        for alert in recent_alerts:
            severity = alert.severity.value
            recent_by_severity[severity] = recent_by_severity.get(severity, 0) + 1
        
        return {
            "active_alerts": len(self.active_alerts),
            "active_by_severity": active_by_severity,
            "recent_alerts_24h": len(recent_alerts),
            "recent_by_severity": recent_by_severity,
            "total_rules": len(self.rules)
        }


