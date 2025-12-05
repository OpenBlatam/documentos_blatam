#!/usr/bin/env python3
"""
Error Handling - Manejo Mejorado de Errores
============================================

Sistema mejorado de manejo de errores para el módulo Sora.
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum
import traceback
import functools

from core.utils import setup_logger

logger = setup_logger(__name__)


class SoraError(Exception):
    """Error base para el módulo Sora."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Inicializa error.
        
        Args:
            message: Mensaje de error
            error_code: Código de error
            details: Detalles adicionales
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte error a diccionario."""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ConfigurationError(SoraError):
    """Error de configuración."""
    pass


class GenerationError(SoraError):
    """Error durante generación."""
    pass


class ValidationError(SoraError):
    """Error de validación."""
    pass


class ResourceError(SoraError):
    """Error de recursos (memoria, GPU, etc.)."""
    pass


def handle_errors(
    error_class: type = SoraError,
    default_message: str = "Error desconocido",
    log_traceback: bool = True
):
    """
    Decorador para manejo de errores.
    
    Args:
        error_class: Clase de error a lanzar
        default_message: Mensaje por defecto
        log_traceback: Si loguear traceback
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SoraError:
                raise
            except Exception as e:
                if log_traceback:
                    logger.error(
                        f"Error en {func.__name__}: {e}",
                        exc_info=True
                    )
                else:
                    logger.error(f"Error en {func.__name__}: {e}")
                
                raise error_class(
                    message=str(e) or default_message,
                    error_code=func.__name__,
                    details={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
                )
        return wrapper
    return decorator


def handle_async_errors(
    error_class: type = SoraError,
    default_message: str = "Error desconocido",
    log_traceback: bool = True
):
    """
    Decorador para manejo de errores asíncronos.
    
    Args:
        error_class: Clase de error a lanzar
        default_message: Mensaje por defecto
        log_traceback: Si loguear traceback
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SoraError:
                raise
            except Exception as e:
                if log_traceback:
                    logger.error(
                        f"Error en {func.__name__}: {e}",
                        exc_info=True
                    )
                else:
                    logger.error(f"Error en {func.__name__}: {e}")
                
                raise error_class(
                    message=str(e) or default_message,
                    error_code=func.__name__,
                    details={'function': func.__name__}
                )
        return wrapper
    return decorator


class ErrorRecovery:
    """Utilidades para recuperación de errores."""
    
    @staticmethod
    def retry_on_failure(
        max_attempts: int = 3,
        backoff_factor: float = 1.0,
        exceptions: tuple = (Exception,)
    ):
        """
        Decorador para reintentar en caso de fallo.
        
        Args:
            max_attempts: Número máximo de intentos
            backoff_factor: Factor de backoff
            exceptions: Excepciones a capturar
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            import time
                            delay = backoff_factor * (2 ** attempt)
                            logger.warning(
                                f"Intento {attempt + 1}/{max_attempts} falló, "
                                f"reintentando en {delay}s: {e}"
                            )
                            time.sleep(delay)
                        else:
                            logger.error(f"Todos los intentos fallaron: {e}")
                
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def retry_async_on_failure(
        max_attempts: int = 3,
        backoff_factor: float = 1.0,
        exceptions: tuple = (Exception,)
    ):
        """
        Decorador para reintentar en caso de fallo (async).
        
        Args:
            max_attempts: Número máximo de intentos
            backoff_factor: Factor de backoff
            exceptions: Excepciones a capturar
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            import asyncio
                            delay = backoff_factor * (2 ** attempt)
                            logger.warning(
                                f"Intento {attempt + 1}/{max_attempts} falló, "
                                f"reintentando en {delay}s: {e}"
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"Todos los intentos fallaron: {e}")
                
                raise last_exception
            return wrapper
        return decorator


