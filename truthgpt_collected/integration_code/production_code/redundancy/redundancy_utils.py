#!/usr/bin/env python3
"""
Utilidades para Sistemas de Supresión de Redundancia
=====================================================

Funciones de utilidad para trabajar con sistemas de supresión de redundancia.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import torch.nn.functional as F
import numpy as np
from pathlib import Path
import json
import time
from collections import defaultdict

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


def compute_similarity_batch(
    embeddings: torch.Tensor,
    method: str = "cosine"
) -> torch.Tensor:
    """
    Calcula matriz de similitud para un batch de embeddings.
    
    Args:
        embeddings: [batch_size, hidden_dim]
        method: Método de similitud ("cosine", "euclidean", "dot", "semantic")
    
    Returns:
        similarity_matrix: [batch_size, batch_size]
    
    Raises:
        ValueError: Si los parámetros no son válidos
    """
    if embeddings is None:
        raise ValueError("embeddings no puede ser None")
    if not isinstance(embeddings, torch.Tensor):
        raise TypeError(f"embeddings debe ser torch.Tensor, recibido: {type(embeddings)}")
    if embeddings.numel() == 0:
        raise ValueError("embeddings no puede estar vacío")
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    if method not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    
    def _compute():
        if embeddings.dim() != 2:
            raise ValueError(f"Expected 2D embeddings [batch, hidden_dim], got {embeddings.dim()}D")
        
        if method == "cosine":
            embeddings_norm = F.normalize(embeddings, p=2, dim=-1)
            similarity_matrix = torch.matmul(embeddings_norm, embeddings_norm.transpose(-2, -1))
        elif method == "euclidean":
            distances = torch.cdist(embeddings, embeddings, p=2)
            max_dist = distances.max()
            similarity_matrix = 1.0 - (distances / (max_dist + 1e-8))
        elif method == "dot":
            similarity_matrix = torch.matmul(embeddings, embeddings.transpose(-2, -1))
        elif method == "semantic":
            similarity_matrix = torch.matmul(embeddings, embeddings.transpose(-2, -1))
            similarity_matrix = F.softmax(similarity_matrix, dim=-1)
        else:
            raise ValueError(f"Método no soportado: {method}")
        
        return similarity_matrix
    
    result, error = safe_execute(
        _compute,
        default_value=None,
        log_errors=True
    )
    
    if error or result is None:
        batch_size = embeddings.size(0) if embeddings.dim() >= 1 else 1
        return torch.eye(batch_size, device=embeddings.device, dtype=embeddings.dtype)
    
    return result


def find_duplicate_items(
    items: torch.Tensor,
    threshold: float = 0.85,
    method: str = "cosine"
) -> List[Tuple[int, int, float]]:
    """
    Encuentra items duplicados en un batch.
    
    Args:
        items: [batch_size, seq_len, hidden_dim] o [batch_size, hidden_dim]
        threshold: Umbral de similitud
        method: Método de similitud
    
    Returns:
        Lista de tuplas (idx1, idx2, similarity) de items duplicados
    
    Raises:
        ValueError: Si los parámetros no son válidos
        TypeError: Si items no es un tensor
    """
    if items is None:
        raise ValueError("items no puede ser None")
    if items is None:
        raise ValueError("items no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if items.numel() == 0:
        raise ValueError("items no puede estar vacío")
    if items.dim() not in [2, 3]:
        raise ValueError(f"items debe ser 2D o 3D, recibido: {items.dim()}D")
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold debe estar en [0.0, 1.0], recibido: {threshold}")
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    if method not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    
    if items.dim() == 3:
        embeddings = items[:, -1, :]
    else:
        embeddings = items
    
    similarity_matrix = compute_similarity_batch(embeddings, method)
    
    duplicates = []
    batch_size = similarity_matrix.size(0)
    
    for i in range(batch_size):
        for j in range(i + 1, batch_size):
            similarity = similarity_matrix[i, j].item()
            if similarity >= threshold:
                duplicates.append((i, j, similarity))
    
    return duplicates


def batch_deduplicate(
    items: torch.Tensor,
    threshold: float = 0.85,
    method: str = "cosine",
    keep_strategy: str = "first"
) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """
    Elimina duplicados de un batch.
    
    Args:
        items: [batch_size, seq_len, hidden_dim] o [batch_size, hidden_dim]
        threshold: Umbral de similitud
        method: Método de similitud
        keep_strategy: Estrategia para mantener items ("first", "last", "center")
    
    Returns:
        unique_items: Items únicos
        stats: Estadísticas de deduplicación
    
    Raises:
        ValueError: Si los parámetros no son válidos
    """
    if items is None:
        raise ValueError("items no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if items.numel() == 0:
        raise ValueError("items no puede estar vacío")
    if items.dim() not in [2, 3]:
        raise ValueError(f"items debe ser 2D o 3D, recibido: {items.dim()}D")
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold debe estar en [0.0, 1.0], recibido: {threshold}")
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    if method not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    valid_strategies = ["first", "last", "center"]
    if keep_strategy not in valid_strategies:
        raise ValueError(f"keep_strategy debe ser uno de {valid_strategies}, recibido: {keep_strategy}")
    
    original_size = items.size(0)
    
    if original_size <= 1:
        return items, {
            'original_size': original_size,
            'unique_size': original_size,
            'removed': 0,
            'reduction_rate': 0.0
        }
    
    if items.dim() == 3:
        embeddings = items[:, -1, :]
    else:
        embeddings = items
    
    similarity_matrix = compute_similarity_batch(embeddings, method)
    
    unique_indices = []
    visited = set()
    removed_indices = []
    
    for i in range(original_size):
        if i in visited:
            continue
        
        unique_indices.append(i)
        visited.add(i)
        
        for j in range(i + 1, original_size):
            if j not in visited and similarity_matrix[i, j].item() >= threshold:
                visited.add(j)
                removed_indices.append(j)
    
    unique_items = items[unique_indices]
    
    stats = {
        'original_size': original_size,
        'unique_size': len(unique_indices),
        'removed': len(removed_indices),
        'reduction_rate': len(removed_indices) / original_size if original_size > 0 else 0.0,
        'removed_indices': removed_indices
    }
    
    return unique_items, stats


def calculate_reduction_stats(
    original_size: int,
    reduced_size: int,
    processing_time: float = 0.0
) -> Dict[str, Any]:
    """
    Calcula estadísticas de reducción.
    
    Args:
        original_size: Tamaño original
        reduced_size: Tamaño después de reducción
        processing_time: Tiempo de procesamiento en segundos
    
    Returns:
        Diccionario con estadísticas
    
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
    compression_ratio = original_size / reduced_size if reduced_size > 0 else 1.0
    
    items_per_second = original_size / processing_time if processing_time > 0 else 0.0
    
    return {
        'original_size': original_size,
        'reduced_size': reduced_size,
        'reduction': reduction,
        'reduction_rate': reduction_rate,
        'compression_ratio': compression_ratio,
        'processing_time': processing_time,
        'items_per_second': items_per_second,
        'efficiency': reduction_rate * 100
    }


def export_redundancy_report(
    stats: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exporta reporte de redundancia a archivo JSON.
    
    Args:
        stats: Estadísticas de redundancia
        output_path: Ruta de salida (opcional)
    
    Returns:
        Diccionario con el reporte
    
    Raises:
        ValueError: Si los parámetros no son válidos
    """
    if not isinstance(stats, dict):
        raise ValueError(f"stats debe ser un diccionario, recibido: {type(stats)}")
    if output_path is not None and (not isinstance(output_path, str) or not output_path):
        raise ValueError(f"output_path debe ser una cadena no vacía, recibido: {output_path}")
    
    def _create_report():
        return {
            'timestamp': time.time(),
            'stats': stats,
            'summary': {
                'total_processed': stats.get('total_processed', 0),
                'total_reduced': stats.get('total_reduced', 0),
                'avg_reduction_rate': stats.get('avg_reduction_rate', 0.0),
                'efficiency': stats.get('efficiency', 0.0)
            }
        }
    
    report, error = safe_execute(
        _create_report,
        default_value={'timestamp': time.time(), 'stats': stats, 'summary': {}},
        log_errors=True
    )
    
    if output_path:
        def _export():
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Reporte exportado a {output_path}")
        
        _, export_error = safe_execute(_export, default_value=None, log_errors=True)
        if export_error:
            logger.warning(f"No se pudo exportar reporte a {output_path}: {export_error}")
    
    return report


def compare_redundancy_methods(
    items: torch.Tensor,
    threshold: float = 0.85,
    methods: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Compara diferentes métodos de detección de redundancia.
    
    Args:
        items: [batch_size, seq_len, hidden_dim] o [batch_size, hidden_dim]
        threshold: Umbral de similitud
        methods: Lista de métodos a comparar (None = todos)
    
    Returns:
        Diccionario con resultados por método
    
    Raises:
        ValueError: Si los parámetros no son válidos
    """
    if items is None:
        raise ValueError("items no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if items.numel() == 0:
        raise ValueError("items no puede estar vacío")
    if items.dim() not in [2, 3]:
        raise ValueError(f"items debe ser 2D o 3D, recibido: {items.dim()}D")
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold debe estar en [0.0, 1.0], recibido: {threshold}")
    
    if methods is None:
        methods = ["cosine", "euclidean", "dot", "semantic"]
    elif not isinstance(methods, list) or len(methods) == 0:
        raise ValueError("methods debe ser una lista no vacía")
    
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    for method in methods:
        if method not in valid_methods:
            raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    
    results = {}
    
    for method in methods:
        def _compare_method():
            start_time = time.time()
            unique_items, stats = batch_deduplicate(items, threshold, method)
            processing_time = time.time() - start_time
            
            return {
                'stats': stats,
                'processing_time': processing_time,
                'unique_size': unique_items.size(0),
                'reduction_rate': stats['reduction_rate']
            }
        
        result, error = safe_execute(_compare_method, default_value={'error': 'Method comparison failed'}, log_errors=False)
        if error:
            logger.warning(f"Error comparando método {method}: {error}")
            results[method] = {'error': str(error)}
        else:
            results[method] = result
    
    return results


def optimize_threshold(
    items: torch.Tensor,
    method: str = "cosine",
    target_reduction_rate: float = 0.3,
    threshold_range: Tuple[float, float] = (0.5, 0.99),
    num_samples: int = 20
) -> Dict[str, Any]:
    """
    Optimiza el threshold para alcanzar una tasa de reducción objetivo.
    
    Args:
        items: [batch_size, seq_len, hidden_dim] o [batch_size, hidden_dim]
        method: Método de similitud
        target_reduction_rate: Tasa de reducción objetivo
        threshold_range: Rango de thresholds a probar
        num_samples: Número de thresholds a probar
    
    Returns:
        Diccionario con threshold óptimo y resultados
    
    Raises:
        ValueError: Si los parámetros no son válidos
    """
    if items is None:
        raise ValueError("items no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if items.numel() == 0:
        raise ValueError("items no puede estar vacío")
    if items.dim() not in [2, 3]:
        raise ValueError(f"items debe ser 2D o 3D, recibido: {items.dim()}D")
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    if method not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    if not (0.0 <= target_reduction_rate <= 1.0):
        raise ValueError(f"target_reduction_rate debe estar en [0.0, 1.0], recibido: {target_reduction_rate}")
    if not isinstance(threshold_range, tuple) or len(threshold_range) != 2:
        raise ValueError(f"threshold_range debe ser una tupla de 2 elementos, recibido: {threshold_range}")
    if not (0.0 <= threshold_range[0] < threshold_range[1] <= 1.0):
        raise ValueError(f"threshold_range debe ser [min, max] con 0.0 <= min < max <= 1.0, recibido: {threshold_range}")
    if not isinstance(num_samples, int) or num_samples <= 0:
        raise ValueError(f"num_samples debe ser un entero > 0, recibido: {num_samples}")
    
    thresholds = np.linspace(threshold_range[0], threshold_range[1], num_samples)
    results = []
    
    for threshold in thresholds:
        def _test_threshold():
            unique_items, stats = batch_deduplicate(items, threshold, method)
            reduction_rate = stats['reduction_rate']
            
            return {
                'threshold': float(threshold),
                'reduction_rate': reduction_rate,
                'unique_size': unique_items.size(0),
                'error': abs(reduction_rate - target_reduction_rate)
            }
        
        result, error = safe_execute(_test_threshold, default_value=None, log_errors=False)
        if error:
            logger.warning(f"Error probando threshold {threshold}: {error}")
            continue
        
        if result:
            results.append(result)
    
    if not results:
        return {'error': 'No se pudieron calcular resultados'}
    
    best_result = min(results, key=lambda x: x['error'])
    
    return {
        'optimal_threshold': best_result['threshold'],
        'achieved_reduction_rate': best_result['reduction_rate'],
        'target_reduction_rate': target_reduction_rate,
        'error': best_result['error'],
        'all_results': results
    }

