#!/usr/bin/env python3
"""
Benchmarking Utilities for Paper Modules
========================================

Utilidades para benchmarking y evaluación de rendimiento de módulos.
"""

import time
import torch
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import statistics

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark."""
    module_name: str
    batch_size: int
    seq_len: int
    hidden_dim: int
    forward_time: float
    backward_time: Optional[float] = None
    memory_used: Optional[float] = None
    throughput: Optional[float] = None
    latency: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BenchmarkRunner:
    """Runner para benchmarks de módulos."""
    
    def __init__(
        self,
        device: str = "cpu",
        warmup_runs: int = 3,
        num_runs: int = 10,
        enable_backward: bool = False
    ):
        """
        Inicializa el benchmark runner.
        
        Args:
            device: Dispositivo a usar ('cpu', 'cuda', etc.)
            warmup_runs: Número de runs de calentamiento
            num_runs: Número de runs para medir
            enable_backward: Si True, también mide backward pass
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not isinstance(device, str) or not device:
            raise ValueError(f"device debe ser un string no vacío, recibido: {device}")
        
        if warmup_runs < 0:
            raise ValueError(f"warmup_runs debe ser >= 0, recibido: {warmup_runs}")
        
        if num_runs <= 0:
            raise ValueError(f"num_runs debe ser > 0, recibido: {num_runs}")
        
        self.device = torch.device(device)
        self.warmup_runs = warmup_runs
        self.num_runs = num_runs
        self.enable_backward = enable_backward
    
    def benchmark(
        self,
        module: BasePaperModule,
        batch_size: int = 1,
        seq_len: int = 128,
        hidden_dim: Optional[int] = None
    ) -> BenchmarkResult:
        """
        Ejecuta un benchmark en un módulo.
        
        Args:
            module: Módulo a benchmarkear
            batch_size: Tamaño del batch
            seq_len: Longitud de secuencia
            hidden_dim: Dimensión hidden (usa config si None)
        
        Returns:
            BenchmarkResult con métricas
        
        Raises:
            ValueError: Si los parámetros son inválidos o module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        if batch_size <= 0:
            raise ValueError(f"batch_size debe ser > 0, recibido: {batch_size}")
        
        if seq_len <= 0:
            raise ValueError(f"seq_len debe ser > 0, recibido: {seq_len}")
        
        if hidden_dim is None:
            hidden_dim = module.config.hidden_dim
        
        if hidden_dim <= 0:
            raise ValueError(f"hidden_dim debe ser > 0, recibido: {hidden_dim}")
        
        module.to(self.device)
        module.eval()
        
        hidden_states = torch.randn(
            batch_size,
            seq_len,
            hidden_dim,
            device=self.device,
            dtype=torch.float32
        )
        
        for _ in range(self.warmup_runs):
            with torch.no_grad():
                _ = module(hidden_states)
        
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        
        forward_times = []
        backward_times = []
        
        for _ in range(self.num_runs):
            if self.device.type == 'cuda':
                torch.cuda.synchronize()
            
            start = time.perf_counter()
            
            if self.enable_backward:
                output, _ = module(hidden_states)
                loss = output.mean()
                loss.backward()
                
                if self.device.type == 'cuda':
                    torch.cuda.synchronize()
                
                backward_time = time.perf_counter() - start
                backward_times.append(backward_time)
            else:
                with torch.no_grad():
                    output, metadata = module(hidden_states)
                
                if self.device.type == 'cuda':
                    torch.cuda.synchronize()
            
            forward_time = time.perf_counter() - start
            forward_times.append(forward_time)
        
        avg_forward = statistics.mean(forward_times)
        std_forward = statistics.stdev(forward_times) if len(forward_times) > 1 else 0.0
        
        avg_backward = None
        if backward_times:
            avg_backward = statistics.mean(backward_times)
        
        memory_used = None
        if self.device.type == 'cuda':
            memory_used = torch.cuda.max_memory_allocated() / 1024**2
        
        total_tokens = batch_size * seq_len * self.num_runs
        throughput = total_tokens / sum(forward_times) if forward_times else None
        latency = avg_forward * 1000
        
        result = BenchmarkResult(
            module_name=module.__class__.__name__,
            batch_size=batch_size,
            seq_len=seq_len,
            hidden_dim=hidden_dim,
            forward_time=avg_forward,
            backward_time=avg_backward,
            memory_used=memory_used,
            throughput=throughput,
            latency=latency,
            metadata={
                'std_forward': std_forward,
                'min_forward': min(forward_times),
                'max_forward': max(forward_times),
                'device': str(self.device)
            }
        )
        
        return result
    
    def benchmark_batch(
        self,
        modules: List[BasePaperModule],
        **kwargs: Any
    ) -> List[BenchmarkResult]:
        """
        Ejecuta benchmarks en múltiples módulos.
        
        Args:
            modules: Lista de módulos
            **kwargs: Argumentos para benchmark()
        
        Returns:
            Lista de BenchmarkResult
        
        Raises:
            ValueError: Si modules está vacío o contiene None
        """
        if not modules:
            raise ValueError("modules no puede estar vacío")
        
        if any(m is None for m in modules):
            raise ValueError("modules no puede contener None")
        
        from .error_handling import safe_execute
        
        results = []
        for module in modules:
            result, error = safe_execute(
                self.benchmark,
                default_value=None,
                log_errors=True,
                module=module,
                **kwargs
            )
            if result is not None:
                results.append(result)
        return results


def compare_results(results: List[BenchmarkResult]) -> Dict[str, Any]:
    """
    Compara resultados de benchmarks.
    
    Args:
        results: Lista de resultados
    
    Returns:
        Diccionario con comparación
    
    Raises:
        ValueError: Si results está vacío o contiene None
    """
    if not results:
        raise ValueError("results no puede estar vacío")
    
    if any(r is None for r in results):
        raise ValueError("results no puede contener None")
    
    fastest = min(results, key=lambda r: r.forward_time)
    slowest = max(results, key=lambda r: r.forward_time)
    
    return {
        'fastest': {
            'module': fastest.module_name,
            'time': fastest.forward_time
        },
        'slowest': {
            'module': slowest.module_name,
            'time': slowest.forward_time
        },
        'speedup': slowest.forward_time / fastest.forward_time if fastest.forward_time > 0 else 0,
        'results': [
            {
                'module': r.module_name,
                'forward_time': r.forward_time,
                'throughput': r.throughput,
                'latency': r.latency
            }
            for r in results
        ]
    }

