#!/usr/bin/env python3
"""
Performance Utilities for Paper Modules
=======================================

Utilidades para optimización de rendimiento y análisis.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
import time
import functools

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


class PerformanceMonitor:
    """Monitor de rendimiento para módulos."""
    
    def __init__(self):
        """Inicializa el monitor."""
        self.metrics: Dict[str, List[float]] = {}
        self.active = False
    
    def start(self):
        """Inicia el monitoreo."""
        self.active = True
        self.metrics.clear()
        logger.debug("Performance monitoring iniciado")
    
    def stop(self):
        """Detiene el monitoreo."""
        self.active = False
        logger.debug("Performance monitoring detenido")
    
    @contextmanager
    def measure(self, name: str):
        """
        Context manager para medir tiempo.
        
        Args:
            name: Nombre de la operación
        """
        if not self.active:
            yield
            return
        
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(elapsed)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de métricas.
        
        Returns:
            Diccionario con resumen
        """
        if not self.metrics:
            return {'total_operations': 0}
        
        summary = {
            'total_operations': sum(len(times) for times in self.metrics.values()),
            'operations': {}
        }
        
        for name, times in self.metrics.items():
            summary['operations'][name] = {
                'count': len(times),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        return summary


def optimize_for_inference(module: BasePaperModule):
    """
    Optimiza un módulo para inferencia.
    
    Args:
        module: Módulo a optimizar
    """
    module.eval()
    
    for param in module.parameters():
        param.requires_grad = False
    
    if hasattr(torch.jit, 'optimize_for_inference'):
        def _optimize_jit():
            return torch.jit.optimize_for_inference(module)
        
        result, error = safe_execute(_optimize_jit, default_value=module, log_errors=False)
        if result != module:
            logger.info("Módulo optimizado con torch.jit")
            module = result
        elif error:
            logger.warning("No se pudo optimizar con torch.jit", error=str(error))
    
    logger.info("Módulo optimizado para inferencia")


def fuse_modules(module: BasePaperModule, patterns: Optional[List[tuple]] = None):
    """
    Fusiona módulos para mejor rendimiento.
    
    Args:
        module: Módulo
        patterns: Patrones de fusión (opcional)
    """
    if patterns is None:
        patterns = [
            (nn.Linear, nn.ReLU),
            (nn.Conv1d, nn.BatchNorm1d),
            (nn.Linear, nn.GELU),
        ]
    
    def _fuse_modules():
        for pattern in patterns:
            torch.quantization.fuse_modules(module, [pattern], inplace=True)
    
    result, error = safe_execute(_fuse_modules, default_value=None, log_errors=False)
    if result is not None:
        logger.info("Módulos fusionados", patterns=len(patterns))
    elif error:
        logger.warning("No se pudieron fusionar módulos", error=str(error))


def compile_module(module: BasePaperModule, mode: str = 'default'):
    """
    Compila un módulo para mejor rendimiento (PyTorch 2.0+).
    
    Args:
        module: Módulo a compilar
        mode: Modo de compilación ('default', 'reduce-overhead', 'max-autotune')
    
    Returns:
        Módulo compilado
    """
    def _compile_module():
        if hasattr(torch, 'compile'):
            return torch.compile(module, mode=mode)
        else:
            logger.warning("torch.compile no disponible (requiere PyTorch 2.0+)")
            return module
    
    result, error = safe_execute(_compile_module, default_value=module, log_errors=False)
    if result != module:
        logger.info("Módulo compilado", mode=mode)
    elif error:
        logger.warning("Error compilando módulo", error=str(error))
    return result


def profile_memory(
    module: BasePaperModule,
    hidden_states: torch.Tensor,
    device: str = 'cuda'
) -> Dict[str, Any]:
    """
    Perfila el uso de memoria de un módulo.
    
    Args:
        module: Módulo
        hidden_states: Input
        device: Dispositivo
    
    Returns:
        Diccionario con información de memoria
    """
    if device != 'cuda' or not torch.cuda.is_available():
        return {'available': False, 'message': 'CUDA no disponible'}
    
    module.to(device)
    hidden_states = hidden_states.to(device)
    
    def _profile_memory():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()
        
        initial_memory = torch.cuda.memory_allocated() / 1024**2
        
        with torch.no_grad():
            output, _ = module(hidden_states)
        
        peak_memory = torch.cuda.max_memory_allocated() / 1024**2
        current_memory = torch.cuda.memory_allocated() / 1024**2
        
        return {
            'available': True,
            'initial_mb': initial_memory,
            'peak_mb': peak_memory,
            'current_mb': current_memory,
            'used_mb': peak_memory - initial_memory,
            'reserved_mb': torch.cuda.memory_reserved() / 1024**2
        }
    
    result, error = safe_execute(_profile_memory, default_value={'available': False, 'message': 'Error profiling memory'}, log_errors=True)
    if error:
        logger.error("Error perfilando memoria", error=str(error))
    return result

