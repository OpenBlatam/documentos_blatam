#!/usr/bin/env python3
"""
Analytics y Optimización para Sistemas de Redundancia
======================================================

Módulo para análisis, optimización y exportación de datos de redundancia.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import numpy as np
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict
from collections import defaultdict

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class RedundancyMetrics:
    """Métricas de redundancia."""
    total_processed: int = 0
    total_reduced: int = 0
    avg_reduction_rate: float = 0.0
    efficiency: float = 0.0
    processing_times: List[float] = None
    reduction_rates: List[float] = None
    
    def __post_init__(self):
        if self.processing_times is None:
            self.processing_times = []
        if self.reduction_rates is None:
            self.reduction_rates = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'total_processed': self.total_processed,
            'total_reduced': self.total_reduced,
            'avg_reduction_rate': self.avg_reduction_rate,
            'efficiency': self.efficiency,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0.0,
            'min_processing_time': np.min(self.processing_times) if self.processing_times else 0.0,
            'max_processing_time': np.max(self.processing_times) if self.processing_times else 0.0,
            'num_batches': len(self.processing_times)
        }


class RedundancyAnalytics:
    """
    Sistema de analytics para supresión de redundancia.
    """
    
    def __init__(self):
        self.metrics = RedundancyMetrics()
        self.batch_history: List[Dict[str, Any]] = []
        self.method_comparisons: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def record_batch(
        self,
        original_size: int,
        reduced_size: int,
        processing_time: float,
        method: str = "unknown"
    ):
        """
        Registra métricas de un batch procesado.
        
        Args:
            original_size: Tamaño original
            reduced_size: Tamaño reducido
            processing_time: Tiempo de procesamiento
            method: Método usado
        
        Raises:
            ValueError: Si los parámetros no son válidos
        """
        if original_size < 0:
            raise ValueError(f"original_size debe ser >= 0, recibido: {original_size}")
        if reduced_size < 0:
            raise ValueError(f"reduced_size debe ser >= 0, recibido: {reduced_size}")
        if reduced_size > original_size:
            raise ValueError(f"reduced_size ({reduced_size}) no puede ser mayor que original_size ({original_size})")
        if processing_time < 0:
            raise ValueError(f"processing_time debe ser >= 0, recibido: {processing_time}")
        
        reduction = original_size - reduced_size
        reduction_rate = reduction / original_size if original_size > 0 else 0.0
        
        self.metrics.total_processed += original_size
        self.metrics.total_reduced += reduction
        self.metrics.processing_times.append(processing_time)
        self.metrics.reduction_rates.append(reduction_rate)
        
        if self.metrics.total_processed > 0:
            self.metrics.avg_reduction_rate = (
                self.metrics.total_reduced / self.metrics.total_processed
            )
            self.metrics.efficiency = self.metrics.avg_reduction_rate * 100
        
        batch_record = {
            'timestamp': time.time(),
            'original_size': original_size,
            'reduced_size': reduced_size,
            'reduction': reduction,
            'reduction_rate': reduction_rate,
            'processing_time': processing_time,
            'method': method
        }
        
        self.batch_history.append(batch_record)
        self.method_comparisons[method].append(batch_record)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas."""
        return {
            'metrics': self.metrics.to_dict(),
            'total_batches': len(self.batch_history),
            'methods_used': list(self.method_comparisons.keys())
        }
    
    def compare_methods(self) -> Dict[str, Dict[str, Any]]:
        """
        Compara rendimiento de diferentes métodos.
        
        Returns:
            Diccionario con estadísticas por método
        """
        comparison = {}
        
        for method, records in self.method_comparisons.items():
            if not records:
                continue
            
            reduction_rates = [r['reduction_rate'] for r in records]
            processing_times = [r['processing_time'] for r in records]
            
            comparison[method] = {
                'num_batches': len(records),
                'avg_reduction_rate': np.mean(reduction_rates),
                'avg_processing_time': np.mean(processing_times),
                'min_processing_time': np.min(processing_times),
                'max_processing_time': np.max(processing_times),
                'total_processed': sum(r['original_size'] for r in records),
                'total_reduced': sum(r['reduction'] for r in records)
            }
        
        return comparison
    
    def export_report(self, output_path: str) -> Dict[str, Any]:
        """
        Exporta reporte completo a JSON.
        
        Args:
            output_path: Ruta de salida
        
        Returns:
            Diccionario con el reporte
        """
        def _create_report():
            return {
                'timestamp': time.time(),
                'summary': self.get_summary(),
                'method_comparison': self.compare_methods(),
                'batch_history': self.batch_history[-100:]
            }
        
        report, error = safe_execute(
            _create_report,
            default_value={'timestamp': time.time(), 'summary': {}, 'method_comparison': {}, 'batch_history': []},
            log_errors=True
        )
        
        def _export():
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Reporte exportado a {output_path}")
        
        _, export_error = safe_execute(_export, default_value=None, log_errors=True)
        if export_error:
            logger.warning(f"No se pudo exportar reporte a {output_path}: {export_error}")
        
        return report
    
    def reset(self):
        """Resetea todas las métricas."""
        self.metrics = RedundancyMetrics()
        self.batch_history.clear()
        self.method_comparisons.clear()


class RedundancyOptimizer:
    """
    Optimizador de parámetros para supresión de redundancia.
    """
    
    def __init__(self, suppressor):
        """
        Args:
            suppressor: Instancia de supresor de redundancia
        """
        self.suppressor = suppressor
    
    def optimize_threshold(
        self,
        sample_items: torch.Tensor,
        target_reduction_rate: float = 0.3,
        threshold_range: Tuple[float, float] = (0.5, 0.99),
        num_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Optimiza el threshold del supresor.
        
        Args:
            sample_items: Items de muestra para optimización
            target_reduction_rate: Tasa de reducción objetivo
            threshold_range: Rango de thresholds
            num_samples: Número de muestras
        
        Returns:
            Diccionario con threshold óptimo
        
        Raises:
            ValueError: Si los parámetros no son válidos
        """
        if not isinstance(sample_items, torch.Tensor):
            raise ValueError(f"sample_items debe ser torch.Tensor, recibido: {type(sample_items)}")
        if not (0.0 <= target_reduction_rate <= 1.0):
            raise ValueError(f"target_reduction_rate debe estar en [0.0, 1.0], recibido: {target_reduction_rate}")
        if not (0.0 <= threshold_range[0] < threshold_range[1] <= 1.0):
            raise ValueError(f"threshold_range debe ser [min, max] con 0.0 <= min < max <= 1.0, recibido: {threshold_range}")
        if num_samples <= 0:
            raise ValueError(f"num_samples debe ser > 0, recibido: {num_samples}")
        
        from .redundancy_utils import optimize_threshold
        
        result = optimize_threshold(
            sample_items,
            method=self.suppressor.detection_method,
            target_reduction_rate=target_reduction_rate,
            threshold_range=threshold_range,
            num_samples=num_samples
        )
        
        if 'optimal_threshold' in result:
            old_threshold = self.suppressor.similarity_threshold
            self.suppressor.similarity_threshold = result['optimal_threshold']
            logger.info(
                f"Threshold optimizado: {old_threshold:.3f} -> {result['optimal_threshold']:.3f}"
            )
        
        return result
    
    def find_optimal_method(
        self,
        sample_items: torch.Tensor,
        threshold: float = 0.85,
        methods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Encuentra el método óptimo para un conjunto de items.
        
        Args:
            sample_items: Items de muestra
            threshold: Threshold a usar
            methods: Métodos a probar
        
        Returns:
            Diccionario con método óptimo y resultados
        
        Raises:
            ValueError: Si los parámetros no son válidos
        """
        if not isinstance(sample_items, torch.Tensor):
            raise ValueError(f"sample_items debe ser torch.Tensor, recibido: {type(sample_items)}")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold debe estar en [0.0, 1.0], recibido: {threshold}")
        
        from .redundancy_utils import compare_redundancy_methods
        
        if methods is None:
            methods = ["cosine", "euclidean", "dot", "semantic"]
        
        results = compare_redundancy_methods(sample_items, threshold, methods)
        
        best_method = None
        best_reduction = -1
        best_time = float('inf')
        
        for method, result in results.items():
            if 'error' in result:
                continue
            
            reduction_rate = result['reduction_rate']
            processing_time = result['processing_time']
            
            score = reduction_rate / (processing_time + 1e-8)
            
            if score > best_reduction:
                best_method = method
                best_reduction = score
                best_time = processing_time
        
        if best_method:
            old_method = self.suppressor.detection_method
            self.suppressor.detection_method = best_method
            logger.info(f"Método optimizado: {old_method} -> {best_method}")
        
        return {
            'optimal_method': best_method,
            'all_results': results,
            'best_reduction_rate': best_reduction,
            'best_processing_time': best_time
        }


class RedundancyExporter:
    """
    Exportador de datos de redundancia.
    """
    
    @staticmethod
    def export_to_json(
        data: Dict[str, Any],
        output_path: str,
        pretty: bool = True
    ) -> bool:
        """
        Exporta datos a JSON.
        
        Args:
            data: Datos a exportar
            output_path: Ruta de salida
            pretty: Si formatear el JSON
        
        Returns:
            True si exitoso
        
        Raises:
            ValueError: Si los parámetros no son válidos
        """
        if not isinstance(data, dict):
            raise ValueError(f"data debe ser un diccionario, recibido: {type(data)}")
        if not output_path or not isinstance(output_path, str):
            raise ValueError(f"output_path debe ser una cadena no vacía, recibido: {output_path}")
        
        def _export():
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                if pretty:
                    json.dump(data, f, indent=2, default=str)
                else:
                    json.dump(data, f, default=str)
            logger.info(f"Datos exportados a {output_path}")
            return True
        
        result, error = safe_execute(_export, default_value=False, log_errors=True)
        return result
    
    @staticmethod
    def export_clusters(
        clusters: List[List[int]],
        items: torch.Tensor,
        output_path: str
    ) -> bool:
        """
        Exporta información de clusters.
        
        Args:
            clusters: Lista de clusters
            items: Items originales
            output_path: Ruta de salida
        
        Returns:
            True si exitoso
        
        Raises:
            ValueError: Si los parámetros no son válidos
        """
        if not isinstance(clusters, list):
            raise ValueError(f"clusters debe ser una lista, recibido: {type(clusters)}")
        if not isinstance(items, torch.Tensor):
            raise ValueError(f"items debe ser torch.Tensor, recibido: {type(items)}")
        if not output_path or not isinstance(output_path, str):
            raise ValueError(f"output_path debe ser una cadena no vacía, recibido: {output_path}")
        
        def _create_cluster_data():
            return {
                'num_clusters': len(clusters),
                'total_items': items.size(0),
                'clusters': [
                    {
                        'cluster_id': i,
                        'size': len(cluster),
                        'indices': cluster,
                        'representative_index': cluster[0] if cluster else None
                    }
                    for i, cluster in enumerate(clusters)
                ],
                'cluster_sizes': [len(c) for c in clusters],
                'avg_cluster_size': np.mean([len(c) for c in clusters]) if clusters else 0.0
            }
        
        cluster_data, error = safe_execute(
            _create_cluster_data,
            default_value=None,
            log_errors=True
        )
        
        if error or cluster_data is None:
            return False
        
        return RedundancyExporter.export_to_json(cluster_data, output_path)

