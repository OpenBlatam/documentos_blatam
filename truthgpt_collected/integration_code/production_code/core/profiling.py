#!/usr/bin/env python3
"""
Profiling Utilities for Paper Modules
=====================================

Utilidades para profiling y análisis de rendimiento detallado.
"""

import torch
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import functools

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class ProfileResult:
    """Resultado de un profiling."""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    cumulative_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Profiler:
    """Profiler para funciones y módulos."""
    
    def __init__(self):
        """Inicializa el profiler."""
        self.results: Dict[str, ProfileResult] = {}
        self._call_times: Dict[str, List[float]] = {}
        self._active: bool = False
    
    def start(self):
        """Inicia el profiling."""
        self._active = True
        self.results.clear()
        self._call_times.clear()
        logger.info("Profiling iniciado")
    
    def stop(self):
        """Detiene el profiling y calcula resultados."""
        self._active = False
        self._calculate_results()
        logger.info("Profiling detenido", total_functions=len(self.results))
    
    def profile(self, func: Callable) -> Callable:
        """
        Decorador para profiling de funciones.
        
        Args:
            func: Función a perfilar
        
        Returns:
            Función decorada
        
        Raises:
            ValueError: Si func es None o no es callable
        """
        if func is None:
            raise ValueError("func no puede ser None")
        
        if not callable(func):
            raise ValueError(f"func debe ser callable, recibido: {type(func)}")
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self._active:
                return func(*args, **kwargs)
            
            start = time.perf_counter()
            result, error = safe_execute(
                func,
                default_value=None,
                log_errors=False,
                *args,
                **kwargs
            )
            elapsed = time.perf_counter() - start
            
            func_name = f"{func.__module__}.{func.__name__}"
            if func_name not in self._call_times:
                self._call_times[func_name] = []
            self._call_times[func_name].append(elapsed)
            
            if error:
                logger.error(
                    "Error en función perfilada",
                    function=func.__name__,
                    error=str(error),
                    time=elapsed
                )
                raise error
            
            return result
        
        return wrapper
    
    @contextmanager
    def profile_context(self, name: str):
        """
        Context manager para profiling de bloques de código.
        
        Args:
            name: Nombre del bloque a perfilar
        
        Raises:
            ValueError: Si name está vacío o es None
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"name debe ser un string no vacío, recibido: {name}")
        
        if not self._active:
            yield
            return
        
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            if name not in self._call_times:
                self._call_times[name] = []
            self._call_times[name].append(elapsed)
    
    def _calculate_results(self):
        """Calcula resultados finales del profiling."""
        for func_name, times in self._call_times.items():
            if not times:
                continue
            
            total = sum(times)
            avg = total / len(times)
            
            self.results[func_name] = ProfileResult(
                function_name=func_name,
                call_count=len(times),
                total_time=total,
                avg_time=avg,
                min_time=min(times),
                max_time=max(times),
                cumulative_time=total
            )
    
    def get_results(self, sort_by: str = 'total_time') -> List[ProfileResult]:
        """
        Obtiene resultados ordenados.
        
        Args:
            sort_by: Campo por el que ordenar ('total_time', 'avg_time', 'call_count')
        
        Returns:
            Lista de resultados ordenados
        
        Raises:
            ValueError: Si sort_by no es un campo válido
        """
        if not self.results:
            return []
        
        valid_fields = ['total_time', 'avg_time', 'call_count', 'min_time', 'max_time', 'cumulative_time', 'function_name']
        if sort_by not in valid_fields:
            raise ValueError(
                f"sort_by debe ser uno de {valid_fields}, recibido: {sort_by}"
            )
        
        reverse = sort_by in ('total_time', 'avg_time', 'max_time', 'cumulative_time')
        return sorted(
            self.results.values(),
            key=lambda x: getattr(x, sort_by),
            reverse=reverse
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del profiling.
        
        Returns:
            Diccionario con resumen
        """
        if not self.results:
            return {'total_functions': 0, 'total_time': 0.0}
        
        total_time = sum(r.total_time for r in self.results.values())
        total_calls = sum(r.call_count for r in self.results.values())
        
        return {
            'total_functions': len(self.results),
            'total_calls': total_calls,
            'total_time': total_time,
            'avg_time_per_call': total_time / total_calls if total_calls > 0 else 0.0,
            'top_functions': [
                {
                    'name': r.function_name,
                    'total_time': r.total_time,
                    'avg_time': r.avg_time,
                    'calls': r.call_count
                }
                for r in self.get_results('total_time')[:10]
            ]
        }


def profile_module(
    module: BasePaperModule,
    hidden_states: torch.Tensor,
    num_runs: int = 10
) -> Dict[str, Any]:
    """
    Perfila un módulo completo.
    
    Args:
        module: Módulo a perfilar
        hidden_states: Input para el módulo
        num_runs: Número de ejecuciones
    
    Returns:
        Diccionario con resultados del profiling
    
    Raises:
        ValueError: Si los parámetros son inválidos
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if not isinstance(hidden_states, torch.Tensor):
        raise ValueError(f"hidden_states debe ser torch.Tensor, recibido: {type(hidden_states)}")
    
    if num_runs <= 0:
        raise ValueError(f"num_runs debe ser > 0, recibido: {num_runs}")
    
    profiler = Profiler()
    profiler.start()
    
    module.eval()
    with torch.no_grad():
        for _ in range(num_runs):
            with profiler.profile_context('forward'):
                output, metadata = module(hidden_states)
    
    profiler.stop()
    
    return {
        'module_name': module.__class__.__name__,
        'summary': profiler.get_summary(),
        'detailed_results': [
            {
                'function': r.function_name,
                'calls': r.call_count,
                'total_time': r.total_time,
                'avg_time': r.avg_time,
                'min_time': r.min_time,
                'max_time': r.max_time
            }
            for r in profiler.get_results()
        ]
    }

