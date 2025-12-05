#!/usr/bin/env python3
"""
Logging Utilities for Redundancy Module
========================================

Utilidades de logging estructurado para el módulo de redundancia.
"""

from typing import Dict, Any, Optional
import time
from functools import wraps
from contextlib import contextmanager

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class RedundancyLogger:
    """
    Logger estructurado para operaciones de redundancia.
    """
    
    def __init__(self, module_name: str = "redundancy"):
        """
        Args:
            module_name: Nombre del módulo para logging
        """
        self.module_name = module_name
        self.logger = setup_logger(f"{module_name}.logger")
        self.operation_count = 0
        self.start_time = time.time()
    
    def log_operation(
        self,
        operation: str,
        level: str = "info",
        **kwargs
    ):
        """
        Registra una operación con contexto estructurado.
        
        Args:
            operation: Nombre de la operación
            level: Nivel de log (debug, info, warning, error)
            **kwargs: Contexto adicional
        """
        context = {
            'module': self.module_name,
            'operation': operation,
            'operation_count': self.operation_count,
            'uptime': time.time() - self.start_time,
            **kwargs
        }
        
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{operation}]", extra=context)
        self.operation_count += 1
    
    def log_processing_start(
        self,
        batch_size: int,
        method: str,
        threshold: float,
        **kwargs
    ):
        """Registra inicio de procesamiento."""
        self.log_operation(
            "processing_start",
            level="info",
            batch_size=batch_size,
            method=method,
            threshold=threshold,
            **kwargs
        )
    
    def log_processing_end(
        self,
        batch_size: int,
        reduced_size: int,
        processing_time: float,
        reduction_rate: float,
        **kwargs
    ):
        """Registra fin de procesamiento."""
        self.log_operation(
            "processing_end",
            level="info",
            batch_size=batch_size,
            reduced_size=reduced_size,
            processing_time=processing_time,
            reduction_rate=reduction_rate,
            throughput=batch_size / processing_time if processing_time > 0 else 0.0,
            **kwargs
        )
    
    def log_cache_hit(self, cache_key: str, saved_time: float):
        """Registra un cache hit."""
        self.log_operation(
            "cache_hit",
            level="debug",
            cache_key=cache_key[:16] if cache_key else None,
            saved_time=saved_time
        )
    
    def log_cache_miss(self, cache_key: str):
        """Registra un cache miss."""
        self.log_operation(
            "cache_miss",
            level="debug",
            cache_key=cache_key[:16] if cache_key else None
        )
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        **kwargs
    ):
        """Registra un error."""
        self.log_operation(
            operation,
            level="error",
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "",
        **kwargs
    ):
        """Registra una métrica de rendimiento."""
        self.log_operation(
            "performance_metric",
            level="debug",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )


def log_function_call(func):
    """
    Decorador para logging automático de llamadas a funciones.
    
    Args:
        func: Función a decorar
    
    Returns:
        Función decorada
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_logger = RedundancyLogger(func.__module__)
        func_name = func.__name__
        
        start_time = time.time()
        func_logger.log_operation(
            f"{func_name}_start",
            level="debug",
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            func_logger.log_operation(
                f"{func_name}_end",
                level="debug",
                duration=duration,
                success=True
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            func_logger.log_error(
                f"{func_name}_error",
                e,
                duration=duration
            )
            raise
    
    return wrapper


@contextmanager
def log_operation_context(operation_name: str, **context):
    """
    Context manager para logging de operaciones.
    
    Args:
        operation_name: Nombre de la operación
        **context: Contexto adicional
    
    Yields:
        RedundancyLogger para uso dentro del contexto
    """
    op_logger = RedundancyLogger()
    start_time = time.time()
    
    op_logger.log_operation(
        f"{operation_name}_start",
        level="info",
        **context
    )
    
    try:
        yield op_logger
        duration = time.time() - start_time
        op_logger.log_operation(
            f"{operation_name}_end",
            level="info",
            duration=duration,
            success=True
        )
    except Exception as e:
        duration = time.time() - start_time
        op_logger.log_error(
            f"{operation_name}_error",
            e,
            duration=duration
        )
        raise


def create_redundancy_logger(module_name: str = "redundancy") -> RedundancyLogger:
    """
    Crea un logger de redundancia.
    
    Args:
        module_name: Nombre del módulo
    
    Returns:
        RedundancyLogger instance
    """
    return RedundancyLogger(module_name)


