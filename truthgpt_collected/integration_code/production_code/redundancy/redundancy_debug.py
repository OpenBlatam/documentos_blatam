#!/usr/bin/env python3
"""
Utilidades de Depuración para Redundancy
========================================

Herramientas para debugging y análisis detallado del módulo de redundancia.
"""

from typing import Dict, Any, Optional, List, Callable
import time
from dataclasses import dataclass, field
from collections import defaultdict
import traceback

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class DebugInfo:
    """Información de depuración."""
    timestamp: float
    operation: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    execution_time: Optional[float] = None


class RedundancyDebugger:
    """
    Depurador para el módulo de redundancia.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: Si el debugger está habilitado
        """
        self.enabled = enabled
        self.debug_log: List[DebugInfo] = []
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.errors: List[Dict[str, Any]] = []
        self.max_log_size = 1000
    
    def log_operation(
        self,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        capture_stack: bool = False
    ):
        """
        Registra una operación para debugging.
        
        Args:
            operation: Nombre de la operación
            details: Detalles adicionales
            capture_stack: Si capturar stack trace
        """
        if not self.enabled:
            return
        
        debug_info = DebugInfo(
            timestamp=time.time(),
            operation=operation,
            details=details or {},
            stack_trace=traceback.format_stack() if capture_stack else None
        )
        
        if len(self.debug_log) >= self.max_log_size:
            self.debug_log.pop(0)
        
        self.debug_log.append(debug_info)
        self.operation_counts[operation] += 1
    
    def time_operation(
        self,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecuta una función y mide su tiempo.
        
        Args:
            operation: Nombre de la operación
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
        
        Returns:
            Resultado de la función
        """
        if not self.enabled:
            return func(*args, **kwargs)
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            self.operation_times[operation].append(execution_time)
            self.log_operation(
                operation,
                details={
                    'execution_time': execution_time,
                    'success': True
                }
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_error(operation, e, execution_time)
            raise
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        execution_time: Optional[float] = None
    ):
        """
        Registra un error.
        
        Args:
            operation: Nombre de la operación
            error: Excepción
            execution_time: Tiempo de ejecución antes del error
        """
        if not self.enabled:
            return
        
        error_info = {
            'timestamp': time.time(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'execution_time': execution_time
        }
        
        self.errors.append(error_info)
        self.log_operation(
            f"{operation}_error",
            details=error_info,
            capture_stack=True
        )
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de operaciones.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'total_operations': len(self.debug_log),
            'operation_counts': dict(self.operation_counts),
            'total_errors': len(self.errors)
        }
        
        operation_avg_times = {}
        for op, times in self.operation_times.items():
            if times:
                operation_avg_times[op] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times)
                }
        
        stats['operation_times'] = operation_avg_times
        return stats
    
    def get_recent_operations(self, count: int = 10) -> List[DebugInfo]:
        """
        Obtiene operaciones recientes.
        
        Args:
            count: Número de operaciones a obtener
        
        Returns:
            Lista de operaciones recientes
        """
        return self.debug_log[-count:] if self.debug_log else []
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Obtiene todos los errores registrados."""
        return self.errors.copy()
    
    def clear_log(self):
        """Limpia el log de debugging."""
        self.debug_log.clear()
        self.operation_counts.clear()
        self.operation_times.clear()
        self.errors.clear()
        logger.info("Debug log limpiado")
    
    def export_debug_report(self, output_path: str) -> bool:
        """
        Exporta un reporte de debugging.
        
        Args:
            output_path: Ruta del archivo de salida
        
        Returns:
            True si exitoso
        """
        def _export():
            import json
            from pathlib import Path
            
            report = {
                'timestamp': time.time(),
                'stats': self.get_operation_stats(),
                'recent_operations': [
                    {
                        'timestamp': op.timestamp,
                        'operation': op.operation,
                        'details': op.details,
                        'execution_time': op.execution_time
                    }
                    for op in self.get_recent_operations(50)
                ],
                'errors': self.get_errors()
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Reporte de debugging exportado a {output_path}")
            return True
        
        result, error = safe_execute(_export, default_value=False, log_errors=True)
        return result


def create_redundancy_debugger(enabled: bool = True) -> RedundancyDebugger:
    """
    Crea un depurador de redundancia.
    
    Args:
        enabled: Si habilitar el debugger
    
    Returns:
        RedundancyDebugger instance
    """
    return RedundancyDebugger(enabled)


