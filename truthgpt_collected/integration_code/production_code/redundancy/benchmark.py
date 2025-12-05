#!/usr/bin/env python3
"""
Benchmarking para Redundancy Module
===================================

Herramientas para medir y comparar rendimiento de diferentes configuraciones.
"""

import torch
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark."""
    method: str
    threshold: float
    batch_size: int
    processing_time: float
    reduction_rate: float
    memory_used: float
    throughput: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'method': self.method,
            'threshold': self.threshold,
            'batch_size': self.batch_size,
            'processing_time': self.processing_time,
            'reduction_rate': self.reduction_rate,
            'memory_used': self.memory_used,
            'throughput': self.throughput
        }


class RedundancyBenchmark:
    """
    Sistema de benchmarking para supresión de redundancia.
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def benchmark_method(
        self,
        items: torch.Tensor,
        method: str,
        threshold: float = 0.85,
        num_runs: int = 3
    ) -> BenchmarkResult:
        """
        Ejecuta benchmark para un método específico.
        
        Args:
            items: Items a procesar
            method: Método de similitud
            threshold: Umbral de similitud
            num_runs: Número de ejecuciones para promediar
        
        Returns:
            Resultado del benchmark
        """
        from .redundancy_utils import batch_deduplicate
        
        def _benchmark():
            times = []
            reduction_rates = []
            
            for _ in range(num_runs):
                start_time = time.time()
                unique_items, stats = batch_deduplicate(
                    items,
                    threshold=threshold,
                    method=method
                )
                processing_time = time.time() - start_time
                
                times.append(processing_time)
                reduction_rates.append(stats['reduction_rate'])
            
            avg_time = np.mean(times)
            avg_reduction = np.mean(reduction_rates)
            
            if torch.cuda.is_available():
                memory_used = torch.cuda.max_memory_allocated() / 1024**2
                torch.cuda.reset_peak_memory_stats()
            else:
                memory_used = 0.0
            
            throughput = items.size(0) / avg_time if avg_time > 0 else 0.0
            
            return BenchmarkResult(
                method=method,
                threshold=threshold,
                batch_size=items.size(0),
                processing_time=avg_time,
                reduction_rate=avg_reduction,
                memory_used=memory_used,
                throughput=throughput
            )
        
        result, error = safe_execute(
            _benchmark,
            default_value=None,
            log_errors=True
        )
        
        if error or result is None:
            logger.warning(f"Error en benchmark para método {method}: {error}")
            return BenchmarkResult(
                method=method,
                threshold=threshold,
                batch_size=items.size(0),
                processing_time=0.0,
                reduction_rate=0.0,
                memory_used=0.0,
                throughput=0.0
            )
        
        self.results.append(result)
        return result
    
    def benchmark_all_methods(
        self,
        items: torch.Tensor,
        threshold: float = 0.85,
        methods: Optional[List[str]] = None
    ) -> List[BenchmarkResult]:
        """
        Ejecuta benchmark para todos los métodos.
        
        Args:
            items: Items a procesar
            threshold: Umbral de similitud
            methods: Lista de métodos (None = todos)
        
        Returns:
            Lista de resultados
        """
        if methods is None:
            methods = ["cosine", "euclidean", "dot", "semantic"]
        
        results = []
        for method in methods:
            result = self.benchmark_method(items, method, threshold)
            results.append(result)
        
        return results
    
    def benchmark_thresholds(
        self,
        items: torch.Tensor,
        method: str = "cosine",
        thresholds: Optional[List[float]] = None
    ) -> List[BenchmarkResult]:
        """
        Ejecuta benchmark para diferentes thresholds.
        
        Args:
            items: Items a procesar
            method: Método de similitud
            thresholds: Lista de thresholds (None = rango estándar)
        
        Returns:
            Lista de resultados
        """
        if thresholds is None:
            thresholds = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        
        results = []
        for threshold in thresholds:
            result = self.benchmark_method(items, method, threshold)
            results.append(result)
        
        return results
    
    def compare_results(self) -> Dict[str, Any]:
        """
        Compara todos los resultados del benchmark.
        
        Returns:
            Diccionario con comparación
        """
        if not self.results:
            return {'error': 'No hay resultados para comparar'}
        
        comparison = {
            'total_runs': len(self.results),
            'best_throughput': None,
            'best_reduction': None,
            'fastest_method': None,
            'most_efficient': None
        }
        
        best_throughput = max(self.results, key=lambda x: x.throughput)
        best_reduction = max(self.results, key=lambda x: x.reduction_rate)
        fastest = min(self.results, key=lambda x: x.processing_time)
        
        efficiency_scores = [
            (r.reduction_rate / (r.processing_time + 1e-8), r)
            for r in self.results
        ]
        most_efficient = max(efficiency_scores, key=lambda x: x[0])[1]
        
        comparison.update({
            'best_throughput': best_throughput.to_dict(),
            'best_reduction': best_reduction.to_dict(),
            'fastest_method': fastest.to_dict(),
            'most_efficient': most_efficient.to_dict()
        })
        
        return comparison
    
    def export_results(self, output_path: str) -> bool:
        """
        Exporta resultados a JSON.
        
        Args:
            output_path: Ruta de salida
        
        Returns:
            True si exitoso
        """
        def _export():
            data = {
                'timestamp': time.time(),
                'results': [r.to_dict() for r in self.results],
                'comparison': self.compare_results()
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Resultados exportados a {output_path}")
            return True
        
        result, error = safe_execute(_export, default_value=False, log_errors=True)
        return result
    
    def reset(self):
        """Resetea todos los resultados."""
        self.results.clear()


def run_quick_benchmark(
    batch_size: int = 100,
    seq_len: int = 32,
    hidden_dim: int = 512
) -> Dict[str, Any]:
    """
    Ejecuta un benchmark rápido.
    
    Args:
        batch_size: Tamaño del batch
        seq_len: Longitud de secuencia
        hidden_dim: Dimensión oculta
    
    Returns:
        Diccionario con resultados
    """
    items = torch.randn(batch_size, seq_len, hidden_dim)
    benchmark = RedundancyBenchmark()
    
    results = benchmark.benchmark_all_methods(items, threshold=0.85)
    comparison = benchmark.compare_results()
    
    return {
        'results': [r.to_dict() for r in results],
        'comparison': comparison
    }


if __name__ == "__main__":
    print("Ejecutando benchmark rápido...")
    results = run_quick_benchmark(batch_size=50)
    print("\nResultados:")
    print(json.dumps(results['comparison'], indent=2))


