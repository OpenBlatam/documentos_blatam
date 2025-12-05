#!/usr/bin/env python3
"""
Optimization Utilities for Paper Modules
========================================

Utilidades para optimización y tuning de módulos.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
import time

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class OptimizationResult:
    """Resultado de una optimización."""
    parameter_name: str
    original_value: Any
    optimized_value: Any
    improvement: float
    metadata: Dict[str, Any]


class ModuleOptimizer:
    """Optimizador de módulos."""
    
    def __init__(self, device: str = "cpu"):
        """
        Inicializa el optimizador.
        
        Args:
            device: Dispositivo a usar
        
        Raises:
            ValueError: Si device no es válido
        """
        if not isinstance(device, str) or not device:
            raise ValueError(f"device debe ser un string no vacío, recibido: {device}")
        
        self.device = torch.device(device)
    
    def optimize_batch_size(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor,
        max_batch_size: int = 32,
        target_memory_mb: Optional[float] = None
    ) -> OptimizationResult:
        """
        Optimiza el tamaño de batch para un módulo.
        
        Args:
            module: Módulo a optimizar
            hidden_states: Tensor de entrada de referencia
            max_batch_size: Tamaño máximo de batch a probar
            target_memory_mb: Memoria objetivo en MB (opcional)
        
        Returns:
            OptimizationResult con batch size óptimo
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        if not isinstance(hidden_states, torch.Tensor):
            raise ValueError(f"hidden_states debe ser torch.Tensor, recibido: {type(hidden_states)}")
        
        if max_batch_size <= 0:
            raise ValueError(f"max_batch_size debe ser > 0, recibido: {max_batch_size}")
        
        if target_memory_mb is not None and target_memory_mb <= 0:
            raise ValueError(f"target_memory_mb debe ser > 0, recibido: {target_memory_mb}")
        
        module.to(self.device)
        module.eval()
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        optimal_batch_size = batch_size
        best_throughput = 0.0
        
        if self.device.type == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        
        for test_batch_size in [1, 2, 4, 8, 16, 32, max_batch_size]:
            if test_batch_size > max_batch_size:
                continue
            
            try:
                test_input = torch.randn(
                    test_batch_size,
                    seq_len,
                    hidden_dim,
                    device=self.device
                )
                
                if self.device.type == 'cuda':
                    torch.cuda.reset_peak_memory_stats()
                
                start = time.perf_counter()
                with torch.no_grad():
                    output, _ = module(test_input)
                
                if self.device.type == 'cuda':
                    torch.cuda.synchronize()
                
                elapsed = time.perf_counter() - start
                throughput = (test_batch_size * seq_len) / elapsed
                
                memory_used = None
                if self.device.type == 'cuda':
                    memory_used = torch.cuda.max_memory_allocated() / 1024**2
                
                if throughput > best_throughput:
                    if target_memory_mb is None or (memory_used and memory_used <= target_memory_mb):
                        best_throughput = throughput
                        optimal_batch_size = test_batch_size
                
            except RuntimeError as e:
                if "out of memory" in str(e):
                    logger.debug(
                        "OOM con batch size",
                        batch_size=test_batch_size
                    )
                    break
                raise
        
        improvement = (best_throughput / (batch_size * seq_len / 0.1)) - 1.0 if best_throughput > 0 else 0.0
        
        return OptimizationResult(
            parameter_name='batch_size',
            original_value=batch_size,
            optimized_value=optimal_batch_size,
            improvement=improvement,
            metadata={
                'best_throughput': best_throughput,
                'device': str(self.device)
            }
        )
    
    def optimize_precision(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor,
        dtypes: Optional[List[torch.dtype]] = None
    ) -> OptimizationResult:
        """
        Optimiza la precisión (dtype) del módulo.
        
        Args:
            module: Módulo a optimizar
            hidden_states: Tensor de entrada
            dtypes: Lista de dtypes a probar (default: [float32, float16, bfloat16])
        
        Returns:
            OptimizationResult con dtype óptimo
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        if not isinstance(hidden_states, torch.Tensor):
            raise ValueError(f"hidden_states debe ser torch.Tensor, recibido: {type(hidden_states)}")
        
        if dtypes is None:
            dtypes = [torch.float32, torch.float16]
            if hasattr(torch, 'bfloat16'):
                dtypes.append(torch.bfloat16)
        
        module.to(self.device)
        original_dtype = next(module.parameters()).dtype
        
        best_dtype = original_dtype
        best_time = float('inf')
        
        for dtype in dtypes:
            try:
                module.set_dtype(dtype)
                test_input = hidden_states.to(dtype)
                
                start = time.perf_counter()
                with torch.no_grad():
                    output, _ = module(test_input)
                
                if self.device.type == 'cuda':
                    torch.cuda.synchronize()
                
                elapsed = time.perf_counter() - start
                
                if elapsed < best_time:
                    best_time = elapsed
                    best_dtype = dtype
                
            except Exception as e:
                logger.warning(
                    "Error probando dtype",
                    dtype=str(dtype),
                    error=str(e)
                )
                continue
        
        module.set_dtype(original_dtype)
        
        original_time = best_time if best_time < float('inf') else 1.0
        improvement = ((original_time - best_time) / original_time) * 100 if original_time > 0 else 0.0
        
        return OptimizationResult(
            parameter_name='dtype',
            original_value=str(original_dtype),
            optimized_value=str(best_dtype),
            improvement=improvement,
            metadata={
                'best_time': best_time,
                'original_time': best_time
            }
        )


def auto_optimize_module(
    module: BasePaperModule,
    hidden_states: torch.Tensor,
    device: str = "cpu"
) -> Dict[str, OptimizationResult]:
    """
    Optimiza automáticamente un módulo.
    
    Args:
        module: Módulo a optimizar
        hidden_states: Tensor de entrada
        device: Dispositivo
    
    Returns:
        Diccionario con resultados de optimización
    
    Raises:
        ValueError: Si los parámetros son inválidos
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if not isinstance(hidden_states, torch.Tensor):
        raise ValueError(f"hidden_states debe ser torch.Tensor, recibido: {type(hidden_states)}")
    
    if not isinstance(device, str) or not device:
        raise ValueError(f"device debe ser un string no vacío, recibido: {device}")
    
    optimizer = ModuleOptimizer(device=device)
    
    results = {}
    
    batch_result, _ = safe_execute(
        optimizer.optimize_batch_size,
        default_value=None,
        module=module,
        hidden_states=hidden_states
    )
    if batch_result:
        results['batch_size'] = batch_result
    
    precision_result, _ = safe_execute(
        optimizer.optimize_precision,
        default_value=None,
        module=module,
        hidden_states=hidden_states
    )
    if precision_result:
        results['precision'] = precision_result
    
    return results


