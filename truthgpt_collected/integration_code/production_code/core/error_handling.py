#!/usr/bin/env python3
"""
Error Handling Utilities for Paper Modules
==========================================

Utilidades mejoradas para manejo de errores y recuperación.
"""

import functools
import time
import asyncio
from typing import Callable, Any, Optional, Type, Tuple, Dict, Awaitable, TypeVar
from enum import Enum

from .utils import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')


class CoreError(Exception):
    """Base exception for core module errors."""
    pass


class ConfigurationError(CoreError):
    """Raised when there's a configuration error."""
    pass


class ValidationError(CoreError):
    """Raised when validation fails."""
    pass


class RetryStrategy(Enum):
    """Estrategias de reintento."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    NO_RETRY = "no_retry"


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[Callable], Callable]:
    """
    Decorador para reintentos con diferentes estrategias.
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial en segundos
        strategy: Estrategia de reintento
        exceptions: Tupla de excepciones a capturar
        on_retry: Callback opcional llamado en cada reintento
    
    Returns:
        Función decorada
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            "Máximo de intentos alcanzado",
                            function=func.__name__,
                            attempts=attempt,
                            error=str(e)
                        )
                        raise
                    
                    if strategy == RetryStrategy.NO_RETRY:
                        raise
                    
                    wait_time = _calculate_wait_time(attempt, delay, strategy)
                    
                    logger.warning(
                        "Reintentando función",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception:
                            pass
                    
                    time.sleep(wait_time)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def _calculate_wait_time(attempt: int, delay: float, strategy: RetryStrategy) -> float:
    """Calcula el tiempo de espera según la estrategia."""
    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        return delay * (2 ** (attempt - 1))
    elif strategy == RetryStrategy.LINEAR_BACKOFF:
        return delay * attempt
    elif strategy == RetryStrategy.FIXED_DELAY:
        return delay
    else:
        return 0.0


def safe_execute(
    func: Callable,
    default_value: Any = None,
    log_errors: bool = True,
    *args: Any,
    **kwargs: Any
) -> Tuple[Any, Optional[Exception]]:
    """
    Ejecuta una función de forma segura, capturando excepciones.
    
    Args:
        func: Función a ejecutar
        default_value: Valor por defecto si falla
        log_errors: Si True, registra errores
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
    
    Returns:
        Tupla (resultado, excepción)
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        if log_errors:
            logger.error(
                "Error en ejecución segura",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
        return default_value, e


class ErrorHandler:
    """Manejador de errores con políticas configurables."""
    
    def __init__(self):
        """Inicializa el manejador de errores."""
        self.handlers: Dict[Type[Exception], Callable] = {}
        self.default_handler: Optional[Callable[[Exception, Optional[dict]], Any]] = None
    
    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable
    ):
        """
        Registra un manejador para un tipo de excepción.
        
        Args:
            exception_type: Tipo de excepción
            handler: Función manejadora
        """
        self.handlers[exception_type] = handler
        logger.info("Handler registrado", exception_type=exception_type.__name__)
    
    def set_default_handler(self, handler: Callable):
        """
        Establece un manejador por defecto.
        
        Args:
            handler: Función manejadora por defecto
        """
        self.default_handler = handler
    
    def handle(self, exception: Exception, context: Optional[dict] = None) -> Any:
        """
        Maneja una excepción usando los handlers registrados.
        
        Args:
            exception: Excepción a manejar
            context: Contexto adicional
        
        Returns:
            Resultado del handler o None
        """
        exception_type = type(exception)
        
        for exc_type, handler in self.handlers.items():
            if issubclass(exception_type, exc_type):
                try:
                    return handler(exception, context)
                except Exception as e:
                    logger.error(
                        "Error en handler",
                        handler=handler.__name__,
                        error=str(e)
                    )
        
        if self.default_handler:
            try:
                return self.default_handler(exception, context)
            except Exception as e:
                logger.error(
                    "Error en handler por defecto",
                    error=str(e)
                )
        
        logger.error(
            "No handler encontrado para excepción",
            exception_type=exception_type.__name__,
            error=str(exception)
        )
        
        return None


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorador para reintentos con diferentes estrategias (versión asíncrona).
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial en segundos
        strategy: Estrategia de reintento
        exceptions: Tupla de excepciones a capturar
        on_retry: Callback opcional llamado en cada reintento
    
    Returns:
        Función decorada
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            "Máximo de intentos alcanzado (async)",
                            function=func.__name__,
                            attempts=attempt,
                            error=str(e)
                        )
                        raise
                    
                    if strategy == RetryStrategy.NO_RETRY:
                        raise
                    
                    wait_time = _calculate_wait_time(attempt, delay, strategy)
                    
                    logger.warning(
                        "Reintentando función (async)",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    
                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(attempt, e)
                            else:
                                on_retry(attempt, e)
                        except Exception:
                            pass
                    
                    await asyncio.sleep(wait_time)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def _fallback_safe_execute(
    func: Callable,
    default_value: Any = None,
    log_errors: bool = True,
    *args: Any,
    **kwargs: Any
) -> Tuple[Any, Optional[Exception]]:
    """
    Implementación de fallback para safe_execute cuando el módulo no está disponible.
    
    Args:
        func: Función a ejecutar
        default_value: Valor por defecto si falla
        log_errors: Si True, registra errores
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
    
    Returns:
        Tupla (resultado, excepción)
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        if log_errors:
            import logging
            logging.error(f"Error en {func.__name__}: {e}")
        return default_value, e
