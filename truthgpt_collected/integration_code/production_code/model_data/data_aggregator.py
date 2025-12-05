#!/usr/bin/env python3
"""
Data Aggregator
===============

Agrega y analiza datos de múltiples modelos y fuentes de información.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import statistics
from collections import defaultdict
import time

from .data_collector import ModelData
from .info_connector import InfoConnector
from core.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class AggregatedData:
    """Datos agregados de múltiples modelos."""
    total_models: int
    categories: Dict[str, int] = field(default_factory=dict)
    total_parameters: Dict[str, Any] = field(default_factory=dict)
    benchmark_stats: Dict[str, Any] = field(default_factory=dict)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    best_models: List[Dict[str, Any]] = field(default_factory=list)
    aggregated_at: float = field(default_factory=time.time)


class DataAggregator:
    """
    Agregador de datos de modelos.
    
    Agrega y analiza datos de:
    - Múltiples modelos
    - Diferentes categorías
    - Benchmarks
    - Métricas
    """
    
    def __init__(self, info_connector: Optional[InfoConnector] = None):
        """
        Inicializa el agregador.
        
        Args:
            info_connector: Conector a información (opcional)
        """
        self.info_connector = info_connector
    
    def aggregate(
        self,
        model_data_list: List[ModelData],
        include_benchmarks: bool = True,
        include_metrics: bool = True
    ) -> AggregatedData:
        """
        Agrega datos de múltiples modelos.
        
        Args:
            model_data_list: Lista de ModelData
            include_benchmarks: Si True, incluye estadísticas de benchmarks
            include_metrics: Si True, incluye estadísticas de métricas
        
        Returns:
            AggregatedData con datos agregados
        """
        if not model_data_list:
            return AggregatedData(total_models=0)
        
        logger.info("Agregando datos", total_models=len(model_data_list))
        
        # Categorías
        categories = self._aggregate_categories(model_data_list)
        
        # Parámetros
        total_parameters = self._aggregate_parameters(model_data_list)
        
        # Benchmarks
        benchmark_stats = {}
        if include_benchmarks:
            benchmark_stats = self._aggregate_benchmarks(model_data_list)
        
        # Métricas
        metrics_summary = {}
        if include_metrics:
            metrics_summary = self._aggregate_metrics(model_data_list)
        
        # Mejores modelos
        best_models = self._identify_best_models(model_data_list)
        
        return AggregatedData(
            total_models=len(model_data_list),
            categories=categories,
            total_parameters=total_parameters,
            benchmark_stats=benchmark_stats,
            metrics_summary=metrics_summary,
            best_models=best_models
        )
    
    def _aggregate_categories(self, model_data_list: List[ModelData]) -> Dict[str, int]:
        """Agrega modelos por categoría."""
        categories = defaultdict(int)
        
        for data in model_data_list:
            category = data.category or 'unknown'
            categories[category] += 1
        
        return dict(categories)
    
    def _aggregate_parameters(self, model_data_list: List[ModelData]) -> Dict[str, Any]:
        """Agrega estadísticas de parámetros."""
        total_params = [
            data.parameters['total_parameters']
            for data in model_data_list
            if 'total_parameters' in data.parameters
        ]
        trainable_params = [
            data.parameters['trainable_parameters']
            for data in model_data_list
            if 'trainable_parameters' in data.parameters
        ]
        num_layers = [
            data.parameters['num_layers']
            for data in model_data_list
            if 'num_layers' in data.parameters
        ]
        
        stats = {}
        
        if total_params:
            stats['total_parameters'] = {
                'sum': sum(total_params),
                'mean': statistics.mean(total_params),
                'median': statistics.median(total_params),
                'min': min(total_params),
                'max': max(total_params),
                'stdev': statistics.stdev(total_params) if len(total_params) > 1 else 0
            }
        
        if trainable_params:
            stats['trainable_parameters'] = {
                'sum': sum(trainable_params),
                'mean': statistics.mean(trainable_params),
                'median': statistics.median(trainable_params),
                'min': min(trainable_params),
                'max': max(trainable_params),
                'stdev': statistics.stdev(trainable_params) if len(trainable_params) > 1 else 0
            }
        
        if num_layers:
            stats['num_layers'] = {
                'mean': statistics.mean(num_layers),
                'median': statistics.median(num_layers),
                'min': min(num_layers),
                'max': max(num_layers)
            }
        
        return stats
    
    def _aggregate_benchmarks(self, model_data_list: List[ModelData]) -> Dict[str, Any]:
        """
        Agrega estadísticas de benchmarks.
        
        Args:
            model_data_list: Lista de ModelData
        
        Returns:
            Diccionario con estadísticas agregadas de benchmarks
        """
        all_forward_times = [
            benchmark['forward_time']
            for data in model_data_list
            if data.benchmarks
            for benchmark in data.benchmarks
            if 'forward_time' in benchmark and benchmark['forward_time'] is not None
        ]
        all_throughputs = [
            benchmark['throughput']
            for data in model_data_list
            if data.benchmarks
            for benchmark in data.benchmarks
            if 'throughput' in benchmark and benchmark.get('throughput')
        ]
        all_latencies = [
            benchmark['latency']
            for data in model_data_list
            if data.benchmarks
            for benchmark in data.benchmarks
            if 'latency' in benchmark and benchmark.get('latency')
        ]
        all_memory = [
            benchmark['memory_used']
            for data in model_data_list
            if data.benchmarks
            for benchmark in data.benchmarks
            if 'memory_used' in benchmark and benchmark.get('memory_used')
        ]
        
        stats = {}
        
        if all_forward_times:
            stats['forward_time'] = {
                'mean': statistics.mean(all_forward_times),
                'median': statistics.median(all_forward_times),
                'min': min(all_forward_times),
                'max': max(all_forward_times),
                'stdev': statistics.stdev(all_forward_times) if len(all_forward_times) > 1 else 0
            }
        
        if all_throughputs:
            stats['throughput'] = {
                'mean': statistics.mean(all_throughputs),
                'median': statistics.median(all_throughputs),
                'min': min(all_throughputs),
                'max': max(all_throughputs),
                'stdev': statistics.stdev(all_throughputs) if len(all_throughputs) > 1 else 0
            }
        
        if all_latencies:
            stats['latency'] = {
                'mean': statistics.mean(all_latencies),
                'median': statistics.median(all_latencies),
                'min': min(all_latencies),
                'max': max(all_latencies),
                'stdev': statistics.stdev(all_latencies) if len(all_latencies) > 1 else 0
            }
        
        if all_memory:
            stats['memory'] = {
                'mean': statistics.mean(all_memory),
                'median': statistics.median(all_memory),
                'min': min(all_memory),
                'max': max(all_memory),
                'stdev': statistics.stdev(all_memory) if len(all_memory) > 1 else 0
            }
        
        return stats
    
    def _aggregate_metrics(self, model_data_list: List[ModelData]) -> Dict[str, Any]:
        """Agrega estadísticas de métricas."""
        forward_counts = [
            data.metrics['forward_count']
            for data in model_data_list
            if 'forward_count' in data.metrics
        ]
        
        stats = {}
        
        if forward_counts:
            stats['forward_count'] = {
                'sum': sum(forward_counts),
                'mean': statistics.mean(forward_counts),
                'median': statistics.median(forward_counts),
                'min': min(forward_counts),
                'max': max(forward_counts)
            }
        
        return stats
    
    def _identify_best_models(
        self,
        model_data_list: List[ModelData],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identifica los mejores modelos según diferentes métricas.
        
        Args:
            model_data_list: Lista de ModelData
            top_k: Número de mejores modelos a retornar
        
        Returns:
            Lista de mejores modelos ordenados por score
        """
        if not model_data_list:
            return []
        
        def _calculate_score(data: ModelData) -> float:
            score = 0.0
            
            # Score basado en forward_count
            forward_count = data.metrics.get('forward_count', 0)
            score += forward_count * 0.3
            
            # Score basado en número de parámetros (menos es mejor para eficiencia)
            total_params = data.parameters.get('total_parameters', 0)
            if total_params > 0:
                # Normalizar: menos parámetros = mejor score
                score += (1.0 / (1.0 + total_params / 1e6)) * 0.2
            
            # Score basado en benchmarks (throughput)
            if data.benchmarks:
                throughputs = [
                    b.get('throughput', 0) or 0
                    for b in data.benchmarks
                    if b.get('throughput')
                ]
                if throughputs:
                    avg_throughput = statistics.mean(throughputs)
                    if avg_throughput > 0:
                        score += avg_throughput * 0.5
            
            return score
        
        scored_models = [
            {
                'model_name': data.model_name,
                'paper_id': data.paper_id,
                'category': data.category,
                'score': _calculate_score(data),
                'forward_count': data.metrics.get('forward_count', 0),
                'total_parameters': data.parameters.get('total_parameters', 0)
            }
            for data in model_data_list
        ]
        
        # Ordenar por score (descendente)
        scored_models.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_models[:max(1, top_k)]
    
    def compare_models(
        self,
        model_data_list: List[ModelData],
        metric: str = 'total_parameters'
    ) -> Dict[str, Any]:
        """
        Compara modelos según una métrica.
        
        Args:
            model_data_list: Lista de ModelData
            metric: Métrica para comparar
        
        Returns:
            Diccionario con comparación
        
        Raises:
            ValueError: Si la métrica no es válida o no hay datos
        """
        if not model_data_list:
            return {}
        
        values = []
        model_names = []
        
        for data in model_data_list:
            if metric == 'total_parameters':
                value = data.parameters.get('total_parameters', 0)
            elif metric == 'forward_count':
                value = data.metrics.get('forward_count', 0)
            elif metric == 'throughput':
                if data.benchmarks:
                    throughputs = [
                        b.get('throughput', 0) or 0
                        for b in data.benchmarks
                        if b.get('throughput')
                    ]
                    value = statistics.mean(throughputs) if throughputs else 0
                else:
                    value = 0
            else:
                logger.warning(f"Métrica desconocida: {metric}")
                value = 0
            
            values.append(value)
            model_names.append(data.model_name)
        
        if not values or all(v == 0 for v in values):
            return {
                'metric': metric,
                'values': dict(zip(model_names, values)),
                'error': 'No hay datos válidos para comparar'
            }
        
        return {
            'metric': metric,
            'values': dict(zip(model_names, values)),
            'best': model_names[values.index(max(values))],
            'worst': model_names[values.index(min(values))],
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'range': max(values) - min(values)
        }
    
    def get_category_analysis(
        self,
        model_data_list: List[ModelData]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analiza modelos por categoría.
        
        Args:
            model_data_list: Lista de ModelData
        
        Returns:
            Diccionario con análisis por categoría
        """
        category_data = defaultdict(list)
        
        for data in model_data_list:
            category = data.category or 'unknown'
            category_data[category].append(data)
        
        analysis = {}
        
        for category, data_list in category_data.items():
            aggregated = self.aggregate(data_list, include_benchmarks=True, include_metrics=True)
            
            analysis[category] = {
                'count': len(data_list),
                'total_parameters': aggregated.total_parameters,
                'benchmark_stats': aggregated.benchmark_stats,
                'best_models': aggregated.best_models[:3]  # Top 3 por categoría
            }
        
        return analysis


