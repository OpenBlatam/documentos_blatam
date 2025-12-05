#!/usr/bin/env python3
"""
Paper Comparison Module
========================

Módulo para comparar y analizar los dos papers implementados.
"""

import torch
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .paper_2506_10848v2 import (
    Paper2506_10848v2Config,
    Paper2506_10848v2_BestTechniques
)
from .paper_2510_04871v1 import (
    Paper2510_04871v1Config,
    Paper2510_04871v1_BestTechniques
)
from core.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class ComparisonResult:
    """Resultado de comparación entre papers."""
    paper_2506: Dict[str, Any] = field(default_factory=dict)
    paper_2510: Dict[str, Any] = field(default_factory=dict)
    differences: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class PaperComparator:
    """Comparador de papers."""
    
    def __init__(
        self,
        config_2506: Optional[Paper2506_10848v2Config] = None,
        config_2510: Optional[Paper2510_04871v1Config] = None
    ):
        """Inicializa el comparador."""
        self.config_2506 = config_2506 or Paper2506_10848v2Config()
        self.config_2510 = config_2510 or Paper2510_04871v1Config()
        
        self.model_2506 = Paper2506_10848v2_BestTechniques(self.config_2506)
        self.model_2510 = Paper2510_04871v1_BestTechniques(self.config_2510)
    
    def compare_architectures(self) -> Dict[str, Any]:
        """Compara las arquitecturas de ambos papers."""
        info_2506 = self.model_2506.get_model_info()
        info_2510 = self.model_2510.get_model_info()
        
        return {
            'paper_2506': {
                'total_parameters': info_2506['total_parameters'],
                'total_size_mb': info_2506['total_size_mb'],
                'hidden_dim': info_2506['hidden_dim'],
                'num_heads': info_2506['num_heads'],
                'features': [
                    'Adaptive Layer Normalization',
                    'Gated Attention',
                    'Gradient Checkpointing'
                ]
            },
            'paper_2510': {
                'total_parameters': info_2510['total_parameters'],
                'total_size_mb': info_2510['total_size_mb'],
                'hidden_dim': info_2510['hidden_dim'],
                'num_heads': info_2510['num_heads'],
                'features': [
                    'Ensemble Attention',
                    'Weighted Combination',
                    'Residual Connections'
                ]
            },
            'differences': {
                'parameter_diff': abs(info_2506['total_parameters'] - info_2510['total_parameters']),
                'size_diff_mb': abs(info_2506['total_size_mb'] - info_2510['total_size_mb']),
                'larger_model': 'paper_2506' if info_2506['total_parameters'] > info_2510['total_parameters'] else 'paper_2510'
            }
        }
    
    def compare_performance(
        self,
        batch_size: int = 4,
        seq_len: int = 128,
        num_runs: int = 10,
        device: Optional[torch.device] = None
    ) -> Dict[str, Any]:
        """Compara el rendimiento de ambos papers."""
        bench_2506 = self.model_2506.benchmark(
            batch_size=batch_size,
            seq_len=seq_len,
            num_runs=num_runs,
            device=device
        )
        
        bench_2510 = self.model_2510.benchmark(
            batch_size=batch_size,
            seq_len=seq_len,
            num_runs=num_runs,
            device=device
        )
        
        faster = 'paper_2506' if bench_2506['avg_time'] < bench_2510['avg_time'] else 'paper_2510'
        speedup = max(bench_2506['avg_time'], bench_2510['avg_time']) / min(bench_2506['avg_time'], bench_2510['avg_time'])
        
        return {
            'paper_2506': bench_2506,
            'paper_2510': bench_2510,
            'faster_model': faster,
            'speedup': speedup,
            'throughput_diff': abs(bench_2506['throughput'] - bench_2510['throughput'])
        }
    
    def compare_memory_usage(
        self,
        batch_size: int = 4,
        seq_len: int = 128,
        dtype: torch.dtype = torch.float32
    ) -> Dict[str, Any]:
        """Compara el uso de memoria de ambos papers."""
        mem_2506 = self.model_2506.estimate_memory_usage(
            batch_size=batch_size,
            seq_len=seq_len,
            dtype=dtype
        )
        
        mem_2510 = self.model_2510.estimate_memory_usage(
            batch_size=batch_size,
            seq_len=seq_len,
            dtype=dtype
        )
        
        more_efficient = 'paper_2506' if mem_2506['total_estimated_mb'] < mem_2510['total_estimated_mb'] else 'paper_2510'
        memory_savings = abs(mem_2506['total_estimated_mb'] - mem_2510['total_estimated_mb'])
        
        return {
            'paper_2506': mem_2506,
            'paper_2510': mem_2510,
            'more_efficient': more_efficient,
            'memory_savings_mb': memory_savings,
            'memory_savings_percent': (memory_savings / max(mem_2506['total_estimated_mb'], mem_2510['total_estimated_mb'])) * 100
        }
    
    def full_comparison(
        self,
        batch_size: int = 4,
        seq_len: int = 128,
        num_runs: int = 10,
        device: Optional[torch.device] = None
    ) -> ComparisonResult:
        """Realiza una comparación completa."""
        architecture = self.compare_architectures()
        performance = self.compare_performance(
            batch_size=batch_size,
            seq_len=seq_len,
            num_runs=num_runs,
            device=device
        )
        memory = self.compare_memory_usage(
            batch_size=batch_size,
            seq_len=seq_len
        )
        
        recommendations = []
        
        if performance['faster_model'] == 'paper_2506':
            recommendations.append("Paper 2506.10848v2 es más rápido para inferencia")
        else:
            recommendations.append("Paper 2510.04871v1 es más rápido para inferencia")
        
        if memory['more_efficient'] == 'paper_2506':
            recommendations.append("Paper 2506.10848v2 usa menos memoria")
        else:
            recommendations.append("Paper 2510.04871v1 usa menos memoria")
        
        if architecture['differences']['larger_model'] == 'paper_2506':
            recommendations.append("Paper 2506.10848v2 tiene más parámetros")
        else:
            recommendations.append("Paper 2510.04871v1 tiene más parámetros")
        
        return ComparisonResult(
            paper_2506={
                'architecture': architecture['paper_2506'],
                'performance': performance['paper_2506'],
                'memory': memory['paper_2506']
            },
            paper_2510={
                'architecture': architecture['paper_2510'],
                'performance': performance['paper_2510'],
                'memory': memory['paper_2510']
            },
            differences={
                'architecture': architecture['differences'],
                'performance': {
                    'faster': performance['faster_model'],
                    'speedup': performance['speedup']
                },
                'memory': {
                    'more_efficient': memory['more_efficient'],
                    'savings_mb': memory['memory_savings_mb']
                }
            },
            recommendations=recommendations
        )
    
    def print_comparison_report(self, comparison: ComparisonResult):
        """Imprime un reporte de comparación."""
        print("=" * 80)
        print("COMPARACIÓN DE PAPERS")
        print("=" * 80)
        print()
        
        print("📊 ARQUITECTURA")
        print("-" * 80)
        print(f"Paper 2506.10848v2:")
        print(f"  Parámetros: {comparison.paper_2506['architecture']['total_parameters']:,}")
        print(f"  Tamaño: {comparison.paper_2506['architecture']['total_size_mb']:.2f} MB")
        print(f"  Features: {', '.join(comparison.paper_2506['architecture']['features'])}")
        print()
        print(f"Paper 2510.04871v1:")
        print(f"  Parámetros: {comparison.paper_2510['architecture']['total_parameters']:,}")
        print(f"  Tamaño: {comparison.paper_2510['architecture']['total_size_mb']:.2f} MB")
        print(f"  Features: {', '.join(comparison.paper_2510['architecture']['features'])}")
        print()
        
        print("⚡ RENDIMIENTO")
        print("-" * 80)
        print(f"Paper 2506.10848v2:")
        print(f"  Tiempo promedio: {comparison.paper_2506['performance']['avg_time']:.4f}s")
        print(f"  Throughput: {comparison.paper_2506['performance']['throughput']:.2f} tokens/s")
        print()
        print(f"Paper 2510.04871v1:")
        print(f"  Tiempo promedio: {comparison.paper_2510['performance']['avg_time']:.4f}s")
        print(f"  Throughput: {comparison.paper_2510['performance']['throughput']:.2f} tokens/s")
        print()
        print(f"Modelo más rápido: {comparison.differences['performance']['faster']}")
        print(f"Speedup: {comparison.differences['performance']['speedup']:.2f}x")
        print()
        
        print("💾 MEMORIA")
        print("-" * 80)
        print(f"Paper 2506.10848v2:")
        print(f"  Memoria estimada: {comparison.paper_2506['memory']['total_estimated_mb']:.2f} MB")
        print()
        print(f"Paper 2510.04871v1:")
        print(f"  Memoria estimada: {comparison.paper_2510['memory']['total_estimated_mb']:.2f} MB")
        print()
        print(f"Modelo más eficiente: {comparison.differences['memory']['more_efficient']}")
        print(f"Ahorro de memoria: {comparison.differences['memory']['savings_mb']:.2f} MB")
        print()
        
        print("💡 RECOMENDACIONES")
        print("-" * 80)
        for i, rec in enumerate(comparison.recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        print("=" * 80)


if __name__ == "__main__":
    comparator = PaperComparator()
    comparison = comparator.full_comparison()
    comparator.print_comparison_report(comparison)


