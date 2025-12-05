#!/usr/bin/env python3
"""
Load Balancer para Distribución de Carga.

Distribuye tareas entre múltiples workers o servicios.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random
import time

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Estrategias de load balancing."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"


@dataclass
class Backend:
    """Backend para load balancing."""
    id: str
    weight: int = 1
    active_connections: int = 0
    total_requests: int = 0
    total_errors: int = 0
    avg_response_time: float = 0.0
    last_response_time: float = 0.0
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LoadBalancer:
    """Load balancer para distribuir carga."""
    
    def __init__(
        self,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    ):
        """
        Inicializa el load balancer.
        
        Args:
            strategy: Estrategia de balanceo
        """
        self.strategy = strategy
        self.backends: Dict[str, Backend] = {}
        self.round_robin_index = 0
        self.last_update = time.time()
    
    def add_backend(
        self,
        backend_id: str,
        weight: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Agrega un backend.
        
        Args:
            backend_id: ID del backend
            weight: Peso para weighted strategies
            metadata: Metadatos adicionales
        """
        self.backends[backend_id] = Backend(
            id=backend_id,
            weight=weight,
            metadata=metadata or {}
        )
        logger.info(f"Backend agregado: {backend_id} (weight: {weight})")
    
    def remove_backend(self, backend_id: str):
        """
        Elimina un backend.
        
        Args:
            backend_id: ID del backend
        """
        if backend_id in self.backends:
            del self.backends[backend_id]
            logger.info(f"Backend eliminado: {backend_id}")
    
    def enable_backend(self, backend_id: str):
        """Habilita un backend."""
        if backend_id in self.backends:
            self.backends[backend_id].enabled = True
    
    def disable_backend(self, backend_id: str):
        """Deshabilita un backend."""
        if backend_id in self.backends:
            self.backends[backend_id].enabled = False
    
    def select_backend(self) -> Optional[str]:
        """
        Selecciona un backend según la estrategia.
        
        Returns:
            ID del backend seleccionado o None
        """
        # Filtrar backends habilitados
        enabled_backends = [
            bid for bid, backend in self.backends.items()
            if backend.enabled
        ]
        
        if not enabled_backends:
            logger.warning("No hay backends habilitados")
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(enabled_backends)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random(enabled_backends)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(enabled_backends)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(enabled_backends)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time(enabled_backends)
        else:
            return self._round_robin(enabled_backends)
    
    def _round_robin(self, backends: List[str]) -> str:
        """Round robin."""
        backend = backends[self.round_robin_index % len(backends)]
        self.round_robin_index += 1
        return backend
    
    def _random(self, backends: List[str]) -> str:
        """Selección aleatoria."""
        return random.choice(backends)
    
    def _least_connections(self, backends: List[str]) -> str:
        """Menor número de conexiones."""
        return min(
            backends,
            key=lambda bid: self.backends[bid].active_connections
        )
    
    def _weighted_round_robin(self, backends: List[str]) -> str:
        """Round robin ponderado."""
        # Crear lista de backends según su peso
        weighted_list = []
        for bid in backends:
            weight = self.backends[bid].weight
            weighted_list.extend([bid] * weight)
        
        backend = weighted_list[self.round_robin_index % len(weighted_list)]
        self.round_robin_index += 1
        return backend
    
    def _least_response_time(self, backends: List[str]) -> str:
        """Menor tiempo de respuesta."""
        return min(
            backends,
            key=lambda bid: self.backends[bid].avg_response_time
        )
    
    def record_request(
        self,
        backend_id: str,
        response_time: float,
        success: bool = True
    ):
        """
        Registra una request en un backend.
        
        Args:
            backend_id: ID del backend
            response_time: Tiempo de respuesta
            success: Si fue exitosa
        """
        if backend_id not in self.backends:
            return
        
        backend = self.backends[backend_id]
        backend.total_requests += 1
        backend.last_response_time = response_time
        
        # Actualizar promedio (moving average)
        if backend.avg_response_time == 0.0:
            backend.avg_response_time = response_time
        else:
            backend.avg_response_time = (
                backend.avg_response_time * 0.9 + response_time * 0.1
            )
        
        if not success:
            backend.total_errors += 1
    
    def increment_connections(self, backend_id: str):
        """Incrementa conexiones activas."""
        if backend_id in self.backends:
            self.backends[backend_id].active_connections += 1
    
    def decrement_connections(self, backend_id: str):
        """Decrementa conexiones activas."""
        if backend_id in self.backends:
            self.backends[backend_id].active_connections = max(
                0,
                self.backends[backend_id].active_connections - 1
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del load balancer.
        
        Returns:
            Estadísticas
        """
        total_requests = sum(b.total_requests for b in self.backends.values())
        total_errors = sum(b.total_errors for b in self.backends.values())
        
        return {
            "strategy": self.strategy.value,
            "total_backends": len(self.backends),
            "enabled_backends": sum(1 for b in self.backends.values() if b.enabled),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0.0,
            "backends": {
                bid: {
                    "weight": b.weight,
                    "active_connections": b.active_connections,
                    "total_requests": b.total_requests,
                    "total_errors": b.total_errors,
                    "avg_response_time": b.avg_response_time,
                    "enabled": b.enabled
                }
                for bid, b in self.backends.items()
            }
        }


