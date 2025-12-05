#!/usr/bin/env python3
"""
Sistema de Alertas para Redundancy
===================================

Sistema de alertas y notificaciones para el módulo de redundancia.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class AlertLevel(Enum):
    """Niveles de alerta."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alerta individual."""
    level: AlertLevel
    message: str
    timestamp: float
    source: str
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None


class AlertRule:
    """
    Regla de alerta configurable.
    """
    
    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        level: AlertLevel,
        message_template: str
    ):
        """
        Args:
            name: Nombre de la regla
            condition: Función que evalúa si se debe alertar
            level: Nivel de alerta
            message_template: Plantilla del mensaje
        """
        self.name = name
        self.condition = condition
        self.level = level
        self.message_template = message_template
        self.trigger_count = 0
        self.last_triggered = None
    
    def check(self, context: Dict[str, Any]) -> Optional[Alert]:
        """
        Verifica si la regla debe disparar una alerta.
        
        Args:
            context: Contexto para evaluación
        
        Returns:
            Alert si se debe alertar, None en caso contrario
        """
        try:
            if self.condition(context):
                self.trigger_count += 1
                self.last_triggered = time.time()
                
                message = self.message_template.format(**context)
                
                return Alert(
                    level=self.level,
                    message=message,
                    timestamp=time.time(),
                    source=self.name,
                    details=context
                )
        except Exception as e:
            logger.warning(f"Error evaluando regla {self.name}: {e}")
        
        return None


class RedundancyAlertSystem:
    """
    Sistema de alertas para redundancia.
    """
    
    def __init__(self):
        """Inicializa el sistema de alertas."""
        self.rules: List[AlertRule] = []
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        self.max_alerts = 1000
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configura reglas de alerta por defecto."""
        def high_error_rate(context):
            error_rate = context.get('error_rate', 0.0)
            return error_rate > 0.1
        
        def low_reduction_rate(context):
            reduction_rate = context.get('reduction_rate', 1.0)
            return reduction_rate < 0.05
        
        def high_processing_time(context):
            processing_time = context.get('processing_time', 0.0)
            return processing_time > 5.0
        
        def cache_miss_rate_high(context):
            cache_hit_rate = context.get('cache_hit_rate', 1.0)
            return cache_hit_rate < 0.3
        
        self.add_rule(
            AlertRule(
                name="high_error_rate",
                condition=high_error_rate,
                level=AlertLevel.ERROR,
                message_template="Tasa de error alta: {error_rate:.2%}"
            )
        )
        
        self.add_rule(
            AlertRule(
                name="low_reduction_rate",
                condition=low_reduction_rate,
                level=AlertLevel.WARNING,
                message_template="Tasa de reducción baja: {reduction_rate:.2%}"
            )
        )
        
        self.add_rule(
            AlertRule(
                name="high_processing_time",
                condition=high_processing_time,
                level=AlertLevel.WARNING,
                message_template="Tiempo de procesamiento alto: {processing_time:.2f}s"
            )
        )
        
        self.add_rule(
            AlertRule(
                name="cache_miss_rate_high",
                condition=cache_miss_rate_high,
                level=AlertLevel.INFO,
                message_template="Tasa de cache miss alta: {cache_hit_rate:.2%}"
            )
        )
    
    def add_rule(self, rule: AlertRule):
        """
        Agrega una regla de alerta.
        
        Args:
            rule: Regla a agregar
        """
        self.rules.append(rule)
        logger.info(f"Regla de alerta agregada: {rule.name}")
    
    def check_alerts(self, context: Dict[str, Any]) -> List[Alert]:
        """
        Verifica todas las reglas y genera alertas si es necesario.
        
        Args:
            context: Contexto para evaluación
        
        Returns:
            Lista de alertas generadas
        """
        new_alerts = []
        
        for rule in self.rules:
            alert = rule.check(context)
            if alert:
                new_alerts.append(alert)
                self._handle_alert(alert)
        
        return new_alerts
    
    def _handle_alert(self, alert: Alert):
        """
        Maneja una alerta.
        
        Args:
            alert: Alerta a manejar
        """
        if len(self.alerts) >= self.max_alerts:
            self.alerts.pop(0)
        
        self.alerts.append(alert)
        
        handlers = self.alert_handlers.get(alert.level, [])
        for handler in handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error en handler de alerta: {e}")
        
        logger.log(
            getattr(logger, alert.level.value, logger.info),
            f"[{alert.level.value.upper()}] {alert.message}",
            extra={'alert_source': alert.source, 'alert_details': alert.details}
        )
    
    def register_handler(
        self,
        level: AlertLevel,
        handler: Callable[[Alert], None]
    ):
        """
        Registra un handler para un nivel de alerta.
        
        Args:
            level: Nivel de alerta
            handler: Función handler
        """
        self.alert_handlers[level].append(handler)
        logger.info(f"Handler registrado para nivel {level.value}")
    
    def get_active_alerts(
        self,
        level: Optional[AlertLevel] = None
    ) -> List[Alert]:
        """
        Obtiene alertas activas (no resueltas).
        
        Args:
            level: Filtrar por nivel (opcional)
        
        Returns:
            Lista de alertas activas
        """
        alerts = [a for a in self.alerts if not a.resolved]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def resolve_alert(self, alert_index: int) -> bool:
        """
        Marca una alerta como resuelta.
        
        Args:
            alert_index: Índice de la alerta
        
        Returns:
            True si exitoso
        """
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].resolved = True
            self.alerts[alert_index].resolved_at = time.time()
            logger.info(f"Alerta {alert_index} marcada como resuelta")
            return True
        return False
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de alertas.
        
        Returns:
            Diccionario con resumen
        """
        summary = {
            'total_alerts': len(self.alerts),
            'active_alerts': len(self.get_active_alerts()),
            'resolved_alerts': len([a for a in self.alerts if a.resolved]),
            'by_level': {}
        }
        
        for level in AlertLevel:
            alerts_by_level = [a for a in self.alerts if a.level == level]
            summary['by_level'][level.value] = {
                'total': len(alerts_by_level),
                'active': len([a for a in alerts_by_level if not a.resolved])
            }
        
        return summary


def create_redundancy_alert_system() -> RedundancyAlertSystem:
    """
    Crea un sistema de alertas de redundancia.
    
    Returns:
        RedundancyAlertSystem instance
    """
    return RedundancyAlertSystem()


