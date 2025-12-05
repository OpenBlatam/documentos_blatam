#!/usr/bin/env python3
"""
Funciones Helper para Redundancy
=================================

Funciones auxiliares y helpers para trabajar con sistemas de redundancia.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import numpy as np
from pathlib import Path
import json
import time

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


def estimate_optimal_threshold(
    sample_items: torch.Tensor,
    target_reduction_rate: float = 0.3,
    method: str = "cosine"
) -> float:
    """
    Estima un threshold óptimo basado en una muestra de items.
    
    Args:
        sample_items: Items de muestra [batch_size, seq_len, hidden_dim] o [batch_size, hidden_dim]
        target_reduction_rate: Tasa de reducción objetivo
        method: Método de similitud
    
    Returns:
        Threshold estimado
    
    Raises:
        ValueError: Si los parámetros no son válidos
        TypeError: Si sample_items no es un tensor
    """
    if sample_items is None:
        raise ValueError("sample_items no puede ser None")
    if not isinstance(sample_items, torch.Tensor):
        raise TypeError(f"sample_items debe ser torch.Tensor, recibido: {type(sample_items)}")
    if sample_items.numel() == 0:
        raise ValueError("sample_items no puede estar vacío")
    if not (0.0 <= target_reduction_rate <= 1.0):
        raise ValueError(f"target_reduction_rate debe estar en [0.0, 1.0], recibido: {target_reduction_rate}")
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    if method not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    from .redundancy_utils import optimize_threshold
    
    def _estimate():
        result = optimize_threshold(
            sample_items,
            method=method,
            target_reduction_rate=target_reduction_rate,
            threshold_range=(0.5, 0.99),
            num_samples=15
        )
        
        if 'optimal_threshold' in result:
            return result['optimal_threshold']
        return 0.85
    
    result, error = safe_execute(_estimate, default_value=0.85, log_errors=True)
    return result


def validate_redundancy_config(
    config: Any,
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """
    Valida una configuración de redundancia.
    
    Args:
        config: Configuración a validar
        strict: Si True, valida estrictamente
    
    Returns:
        Tupla (es_válida, lista_de_errores)
    """
    errors = []
    
    def _validate():
        if not hasattr(config, 'similarity_threshold'):
            errors.append("Config debe tener 'similarity_threshold'")
            return False
        
        threshold = config.similarity_threshold
        if not isinstance(threshold, (int, float)):
            errors.append(f"similarity_threshold debe ser numérico, recibido: {type(threshold)}")
        elif not (0.0 <= threshold <= 1.0):
            errors.append(f"similarity_threshold debe estar en [0.0, 1.0], recibido: {threshold}")
        
        if hasattr(config, 'redundancy_detection_method'):
            method = config.redundancy_detection_method
            valid_methods = ["cosine", "euclidean", "dot", "semantic"]
            if method not in valid_methods:
                errors.append(
                    f"redundancy_detection_method debe ser uno de {valid_methods}, "
                    f"recibido: {method}"
                )
        
        if hasattr(config, 'max_cluster_size'):
            max_size = config.max_cluster_size
            if not isinstance(max_size, int) or max_size <= 0:
                errors.append(
                    f"max_cluster_size debe ser un entero positivo, recibido: {max_size}"
                )
        
        if strict:
            if hasattr(config, 'bulk_processing_batch_size'):
                batch_size = config.bulk_processing_batch_size
                if not isinstance(batch_size, int) or batch_size <= 0:
                    errors.append(
                        f"bulk_processing_batch_size debe ser un entero positivo, "
                        f"recibido: {batch_size}"
                    )
        
        return len(errors) == 0
    
    result, error = safe_execute(_validate, default_value=False, log_errors=True)
    
    if error:
        errors.append(f"Error validando configuración: {error}")
    
    return result, errors


def get_redundancy_health_report(
    suppressor: Any
) -> Dict[str, Any]:
    """
    Genera un reporte de salud del supresor de redundancia.
    
    Args:
        suppressor: Instancia del supresor
    
    Returns:
        Diccionario con reporte de salud
    
    Raises:
        ValueError: Si suppressor es None
    """
    if suppressor is None:
        raise ValueError("suppressor no puede ser None")
    
    def _generate_report():
        report = {
            'timestamp': time.time(),
            'status': 'healthy',
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        if not hasattr(suppressor, 'get_metrics'):
            report['status'] = 'error'
            report['warnings'].append('Supresor no tiene método get_metrics')
            return report
        
        try:
            metrics = suppressor.get_metrics()
            report['metrics'] = metrics
            
            total_processed = metrics.get('total_processed', 0)
            avg_reduction_rate = metrics.get('avg_reduction_rate', 0.0)
            
            if total_processed == 0:
                report['warnings'].append('No se ha procesado ningún batch aún')
                report['status'] = 'warning'
            
            if avg_reduction_rate < 0.1:
                report['warnings'].append('Tasa de reducción muy baja (<10%)')
                report['recommendations'].append('Considerar reducir similarity_threshold')
            
            if avg_reduction_rate > 0.9:
                report['warnings'].append('Tasa de reducción muy alta (>90%)')
                report['recommendations'].append('Considerar aumentar similarity_threshold')
            
            if hasattr(suppressor, 'processing_times') and suppressor.processing_times:
                avg_time = np.mean(suppressor.processing_times)
                if avg_time > 1.0:
                    report['warnings'].append('Tiempo de procesamiento alto')
                    report['recommendations'].append('Considerar optimizar batch size')
            
            if report['warnings']:
                report['status'] = 'warning'
            
        except Exception as e:
            report['status'] = 'error'
            report['warnings'].append(f"Error obteniendo métricas: {e}")
        
        return report
    
    result, error = safe_execute(
        _generate_report,
        default_value={
            'timestamp': time.time(),
            'status': 'error',
            'warnings': ['Error generando reporte'],
            'recommendations': [],
            'metrics': {}
        },
        log_errors=True
    )
    
    return result


def merge_redundancy_suppressors(
    source_suppressor: Any,
    target_suppressor: Any,
    merge_strategy: str = "metrics"
) -> Dict[str, Any]:
    """
    Fusiona métricas de dos supresores de redundancia.
    
    Args:
        source_suppressor: Supresor fuente
        target_suppressor: Supresor destino
        merge_strategy: Estrategia ("metrics", "config", "both")
    
    Returns:
        Diccionario con resultados de la fusión
    
    Raises:
        ValueError: Si alguno de los supresores es None o merge_strategy es inválido
    """
    if source_suppressor is None:
        raise ValueError("source_suppressor no puede ser None")
    if target_suppressor is None:
        raise ValueError("target_suppressor no puede ser None")
    valid_strategies = ["metrics", "config", "both"]
    if merge_strategy not in valid_strategies:
        raise ValueError(f"merge_strategy debe ser uno de {valid_strategies}, recibido: {merge_strategy}")
    
    def _merge():
        result = {
            'merged': False,
            'strategy': merge_strategy,
            'details': {}
        }
        
        if not (hasattr(source_suppressor, 'get_metrics') and 
                hasattr(target_suppressor, 'get_metrics')):
            result['details']['error'] = 'Uno o ambos supresores no tienen get_metrics'
            return result
        
        if merge_strategy in ["metrics", "both"]:
            source_metrics = source_suppressor.get_metrics()
            target_metrics = target_suppressor.get_metrics()
            
            if hasattr(target_suppressor, 'total_processed'):
                target_suppressor.total_processed += source_metrics.get('total_processed', 0)
            
            if hasattr(target_suppressor, 'total_reduced'):
                target_suppressor.total_reduced += source_metrics.get('total_reduced', 0)
            
            if hasattr(target_suppressor, 'avg_reduction_rate'):
                total_processed = target_suppressor.total_processed
                if total_processed > 0:
                    target_suppressor.avg_reduction_rate = (
                        target_suppressor.total_reduced / total_processed
                    )
            
            result['details']['metrics_merged'] = True
        
        if merge_strategy in ["config", "both"]:
            if hasattr(source_suppressor, 'config') and hasattr(target_suppressor, 'config'):
                result['details']['config_merged'] = True
        
        result['merged'] = True
        return result
    
    result, error = safe_execute(
        _merge,
        default_value={
            'merged': False,
            'strategy': merge_strategy,
            'details': {'error': str(error) if error else 'Unknown error'}
        },
        log_errors=True
    )
    
    return result


def export_suppressor_state(
    suppressor: Any,
    output_path: str,
    include_metrics: bool = True,
    include_config: bool = True
) -> bool:
    """
    Exporta el estado completo de un supresor.
    
    Args:
        suppressor: Supresor a exportar
        output_path: Ruta de salida
        include_metrics: Si incluir métricas
        include_config: Si incluir configuración
    
    Returns:
        True si exitoso
    
    Raises:
        ValueError: Si suppressor es None o output_path está vacío
    """
    if suppressor is None:
        raise ValueError("suppressor no puede ser None")
    if not output_path or not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("output_path debe ser una cadena no vacía")
    
    def _export():
        state = {
            'timestamp': time.time(),
            'version': '1.0'
        }
        
        if include_metrics and hasattr(suppressor, 'get_metrics'):
            state['metrics'] = suppressor.get_metrics()
        
        if include_config and hasattr(suppressor, 'config'):
            config = suppressor.config
            if hasattr(config, 'model_dump'):
                state['config'] = config.model_dump()
            elif hasattr(config, '__dict__'):
                state['config'] = config.__dict__
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Estado exportado a {output_path}")
        return True
    
    result, error = safe_execute(_export, default_value=False, log_errors=True)
    return result


def import_suppressor_state(
    suppressor: Any,
    input_path: str,
    load_metrics: bool = True
) -> bool:
    """
    Importa estado de un supresor desde archivo.
    
    Args:
        suppressor: Supresor a actualizar
        input_path: Ruta del archivo
        load_metrics: Si cargar métricas
    
    Returns:
        True si exitoso
    
    Raises:
        ValueError: Si suppressor es None o input_path está vacío
    """
    if suppressor is None:
        raise ValueError("suppressor no puede ser None")
    if not input_path or not isinstance(input_path, str) or not input_path.strip():
        raise ValueError("input_path debe ser una cadena no vacía")
    
    def _import():
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
        
        with open(input_file, 'r') as f:
            state = json.load(f)
        
        if load_metrics and 'metrics' in state:
            metrics = state['metrics']
            if hasattr(suppressor, 'total_processed'):
                suppressor.total_processed = metrics.get('total_processed', 0)
            if hasattr(suppressor, 'total_reduced'):
                suppressor.total_reduced = metrics.get('total_reduced', 0)
            if hasattr(suppressor, 'avg_reduction_rate'):
                suppressor.avg_reduction_rate = metrics.get('avg_reduction_rate', 0.0)
        
        logger.info(f"Estado importado desde {input_path}")
        return True
    
    result, error = safe_execute(_import, default_value=False, log_errors=True)
    return result

