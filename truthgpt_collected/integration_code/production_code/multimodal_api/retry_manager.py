#!/usr/bin/env python3
"""
Sistema de Reintentos para Tareas Fallidas.

Maneja reintentos automáticos de tareas que fallan.
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


class RetryStrategy(str, Enum):
    """Estrategias de reintento."""
    FIXED = "fixed"  # Intervalo fijo
    EXPONENTIAL = "exponential"  # Backoff exponencial
    LINEAR = "linear"  # Backoff lineal


@dataclass
class RetryConfig:
    """Configuración de reintentos."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # segundos
    max_delay: float = 60.0  # segundos
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retryable_errors: tuple = (Exception,)  # Errores que se pueden reintentar


class RetryManager:
    """Gestor de reintentos."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Inicializa el gestor de reintentos.
        
        Args:
            config: Configuración de reintentos
        """
        self.config = config or RetryConfig()
        self.retry_history: Dict[str, list] = {}
    
    async def execute_with_retry(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecuta una función con reintentos.
        
        Args:
            task_id: ID de la tarea
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        
        Returns:
            Resultado de la función
        
        Raises:
            Exception: Si todos los reintentos fallan
        """
        attempt = 0
        last_error = None
        
        if task_id not in self.retry_history:
            self.retry_history[task_id] = []
        
        while attempt < self.config.max_attempts:
            try:
                result = await func(*args, **kwargs)
                
                # Éxito
                self.retry_history[task_id].append({
                    "attempt": attempt + 1,
                    "success": True,
                    "timestamp": datetime.now()
                })
                
                return result
            
            except Exception as e:
                last_error = e
                attempt += 1
                
                # Verificar si el error es reintentable
                if not isinstance(e, self.config.retryable_errors):
                    logger.warning(f"Error no reintentable para tarea {task_id}: {e}")
                    raise
                
                # Registrar intento fallido
                self.retry_history[task_id].append({
                    "attempt": attempt,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now()
                })
                
                # Si no quedan más intentos, lanzar error
                if attempt >= self.config.max_attempts:
                    logger.error(
                        f"Tarea {task_id} falló después de {attempt} intentos: {e}"
                    )
                    raise
                
                # Calcular delay
                delay = self._calculate_delay(attempt)
                
                logger.info(
                    f"Reintentando tarea {task_id} (intento {attempt}/{self.config.max_attempts}) "
                    f"después de {delay}s"
                )
                
                await asyncio.sleep(delay)
        
        # No debería llegar aquí, pero por si acaso
        raise last_error
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calcula el delay para el siguiente intento.
        
        Args:
            attempt: Número de intento (1-indexed)
        
        Returns:
            Delay en segundos
        """
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.initial_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (2 ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * attempt
        else:
            delay = self.config.initial_delay
        
        # Limitar al máximo
        return min(delay, self.config.max_delay)
    
    def get_retry_history(self, task_id: str) -> list:
        """
        Obtiene el historial de reintentos de una tarea.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Historial de reintentos
        """
        return self.retry_history.get(task_id, [])
    
    def clear_history(self, task_id: Optional[str] = None):
        """
        Limpia el historial de reintentos.
        
        Args:
            task_id: ID de tarea específica (opcional)
        """
        if task_id:
            self.retry_history.pop(task_id, None)
        else:
            self.retry_history.clear()


