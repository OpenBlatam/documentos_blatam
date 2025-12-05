#!/usr/bin/env python3
"""
Circuit Breaker Pattern para la API Multimodal.

Protege el sistema de fallos en cascada implementando el patrón Circuit Breaker.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"      # Normal, permitiendo requests
    OPEN = "open"          # Fallando, bloqueando requests
    HALF_OPEN = "half_open"  # Probando si el servicio se recuperó


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker."""
    failure_threshold: int = 5  # Fallos antes de abrir
    success_threshold: int = 2  # Éxitos para cerrar desde half-open
    timeout_seconds: int = 60  # Tiempo antes de intentar half-open
    expected_exception: tuple = (Exception,)  # Excepciones que cuentan como fallos


class CircuitBreaker:
    """Circuit breaker para proteger servicios."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Inicializa el circuit breaker.
        
        Args:
            name: Nombre del circuit breaker
            config: Configuración
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función a través del circuit breaker.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        
        Returns:
            Resultado de la función
        
        Raises:
            Exception: Si el circuit está abierto o la función falla
        """
        # Verificar estado
        if self.state == CircuitState.OPEN:
            # Verificar si debemos intentar half-open
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = datetime.now()
                logger.info(f"Circuit breaker {self.name} movido a HALF_OPEN")
            else:
                raise Exception(
                    f"Circuit breaker {self.name} está OPEN. "
                    f"Espera {self.config.timeout_seconds}s antes de reintentar."
                )
        
        # Ejecutar función
        try:
            result = func(*args, **kwargs)
            
            # Éxito
            self._on_success()
            return result
        
        except self.config.expected_exception as e:
            # Falla
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función asíncrona a través del circuit breaker.
        
        Args:
            func: Función asíncrona a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        
        Returns:
            Resultado de la función
        
        Raises:
            Exception: Si el circuit está abierto o la función falla
        """
        # Verificar estado
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = datetime.now()
                logger.info(f"Circuit breaker {self.name} movido a HALF_OPEN")
            else:
                raise Exception(
                    f"Circuit breaker {self.name} está OPEN. "
                    f"Espera {self.config.timeout_seconds}s antes de reintentar."
                )
        
        # Ejecutar función
        try:
            result = await func(*args, **kwargs)
            
            # Éxito
            self._on_success()
            return result
        
        except self.config.expected_exception as e:
            # Falla
            self._on_failure()
            raise
    
    def _on_success(self):
        """Maneja un éxito."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = datetime.now()
                logger.info(f"Circuit breaker {self.name} cerrado (recuperado)")
        else:
            # En estado CLOSED, resetear contador de fallos
            self.failure_count = 0
    
    def _on_failure(self):
        """Maneja un fallo."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Si falla en half-open, volver a abrir
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            logger.warning(f"Circuit breaker {self.name} abierto (falló en half-open)")
        elif self.failure_count >= self.config.failure_threshold:
            # Abrir circuit si excede threshold
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            logger.warning(
                f"Circuit breaker {self.name} abierto "
                f"({self.failure_count} fallos >= {self.config.failure_threshold})"
            )
    
    def _should_attempt_reset(self) -> bool:
        """
        Determina si debemos intentar resetear el circuit.
        
        Returns:
            True si debemos intentar
        """
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    def reset(self):
        """Resetea manualmente el circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
        logger.info(f"Circuit breaker {self.name} reseteado manualmente")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del circuit breaker.
        
        Returns:
            Estado
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (
                self.last_failure_time.isoformat()
                if self.last_failure_time else None
            ),
            "last_state_change": self.last_state_change.isoformat()
        }


class CircuitBreakerManager:
    """Gestor de múltiples circuit breakers."""
    
    def __init__(self):
        """Inicializa el gestor."""
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Obtiene o crea un circuit breaker.
        
        Args:
            name: Nombre del breaker
            config: Configuración (opcional)
        
        Returns:
            Circuit breaker
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, config)
            logger.info(f"Circuit breaker creado: {name}")
        
        return self.breakers[name]
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene el estado de todos los circuit breakers.
        
        Returns:
            Estados de todos los breakers
        """
        return {
            name: breaker.get_state()
            for name, breaker in self.breakers.items()
        }


