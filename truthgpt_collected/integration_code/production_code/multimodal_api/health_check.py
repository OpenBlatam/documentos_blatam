#!/usr/bin/env python3
"""
Sistema de Health Checks Avanzado.

Monitorea la salud de todos los componentes del sistema.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
import time

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Estados de salud."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Salud de un componente."""
    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    last_check: Optional[datetime] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.last_check is None:
            self.last_check = datetime.now()


class HealthChecker:
    """Verificador de salud del sistema."""
    
    def __init__(self):
        """Inicializa el verificador de salud."""
        self.components: Dict[str, ComponentHealth] = {}
        self.check_interval = 30  # segundos
        self.last_full_check: Optional[datetime] = None
    
    def register_component(
        self,
        name: str,
        check_func: callable,
        critical: bool = True
    ):
        """
        Registra un componente para verificación.
        
        Args:
            name: Nombre del componente
            check_func: Función que verifica el componente
            critical: Si es crítico para el sistema
        """
        self.components[name] = {
            "check_func": check_func,
            "critical": critical,
            "health": ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN
            )
        }
        logger.info(f"Componente registrado para health check: {name}")
    
    async def check_component(self, name: str) -> ComponentHealth:
        """
        Verifica la salud de un componente.
        
        Args:
            name: Nombre del componente
        
        Returns:
            Estado de salud del componente
        """
        if name not in self.components:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Componente {name} no registrado"
            )
        
        component = self.components[name]
        start_time = time.time()
        
        try:
            # Ejecutar check
            if asyncio.iscoroutinefunction(component["check_func"]):
                result = await component["check_func"]()
            else:
                result = component["check_func"]()
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Interpretar resultado
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Check failed"
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                message = result.get("message", "")
                details = result.get("details", {})
            else:
                status = HealthStatus.HEALTHY
                message = "OK"
                details = {}
            
            health = ComponentHealth(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time,
                last_check=datetime.now(),
                details=result.get("details", {}) if isinstance(result, dict) else {}
            )
            
            component["health"] = health
            return health
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            health = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Error en check: {str(e)}",
                response_time_ms=response_time,
                last_check=datetime.now()
            )
            component["health"] = health
            return health
    
    async def check_all(self) -> Dict[str, ComponentHealth]:
        """
        Verifica todos los componentes.
        
        Returns:
            Estado de salud de todos los componentes
        """
        results = {}
        
        # Verificar todos los componentes en paralelo
        tasks = [
            self.check_component(name)
            for name in self.components.keys()
        ]
        
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, health in zip(self.components.keys(), health_results):
            if isinstance(health, Exception):
                results[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Exception: {str(health)}"
                )
            else:
                results[name] = health
        
        self.last_full_check = datetime.now()
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """
        Obtiene el estado general del sistema.
        
        Returns:
            Estado general
        """
        if not self.components:
            return HealthStatus.UNKNOWN
        
        critical_components = [
            name for name, comp in self.components.items()
            if comp["critical"]
        ]
        
        # Si algún componente crítico está unhealthy, el sistema está unhealthy
        for name in critical_components:
            health = self.components[name]["health"]
            if health.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        
        # Si algún componente crítico está degraded, el sistema está degraded
        for name in critical_components:
            health = self.components[name]["health"]
            if health.status == HealthStatus.DEGRADED:
                return HealthStatus.DEGRADED
        
        # Si todos están healthy, el sistema está healthy
        all_healthy = all(
            self.components[name]["health"].status == HealthStatus.HEALTHY
            for name in critical_components
        )
        
        return HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado de salud.
        
        Returns:
            Resumen
        """
        overall = self.get_overall_status()
        components_status = {
            name: {
                "status": comp["health"].status.value,
                "message": comp["health"].message,
                "response_time_ms": comp["health"].response_time_ms,
                "last_check": comp["health"].last_check.isoformat() if comp["health"].last_check else None,
                "critical": comp["critical"]
            }
            for name, comp in self.components.items()
        }
        
        return {
            "overall_status": overall.value,
            "last_check": self.last_full_check.isoformat() if self.last_full_check else None,
            "components": components_status,
            "total_components": len(self.components),
            "healthy_components": sum(
                1 for comp in self.components.values()
                if comp["health"].status == HealthStatus.HEALTHY
            ),
            "unhealthy_components": sum(
                1 for comp in self.components.values()
                if comp["health"].status == HealthStatus.UNHEALTHY
            )
        }


