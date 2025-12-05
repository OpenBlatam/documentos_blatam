#!/usr/bin/env python3
"""
Techniques Module - Advanced Techniques Implementation
======================================================

Este módulo contiene implementaciones de técnicas avanzadas basadas en papers
de investigación para mejorar el rendimiento y eficiencia de modelos.

Módulos disponibles:
- paper_2506_10987v1: Adaptive Sparse Attention
- paper_2506_10987v1_chain_of_draft: Chain of Draft for Software Engineering
- paper_2503_00735v3: Efficient Flash Attention

Características principales:
- ✅ Atención adaptativa y dispersa
- ✅ Chain of Draft con reasoning conciso
- ✅ Flash Attention eficiente
- ✅ Optimización de memoria
- ✅ Gradient checkpointing

Funciones de utilidad:
- create_technique_module(): Crea módulos de técnicas
- get_technique_metrics(): Obtiene métricas de módulos
- compare_techniques(): Compara múltiples técnicas
- validate_technique_config(): Valida configuraciones
- get_available_techniques(): Lista técnicas disponibles
- get_technique_info(): Obtiene información detallada de una técnica
- list_all_techniques(): Lista todas las técnicas con información
- get_technique_recommendations(): Obtiene recomendaciones basadas en caso de uso
- benchmark_technique(): Realiza benchmarking de rendimiento
- export_technique_report(): Exporta reportes completos en JSON
- optimize_technique_config(): Optimiza configuraciones automáticamente
- compare_technique_performance(): Compara rendimiento de múltiples técnicas
- get_technique_health_report(): Genera reportes de salud de módulos
- export_technique_state(): Exporta estado de módulos
- import_technique_state(): Importa estado de módulos
- merge_technique_configs(): Combina configuraciones
- estimate_optimal_config(): Estima configuraciones óptimas
- validate_technique_compatibility(): Valida compatibilidad entre técnicas

Ejemplos de uso:
    >>> from techniques import create_technique_module, get_technique_info
    >>> 
    >>> # Crear un módulo de atención adaptativa
    >>> module = create_technique_module(
    ...     "adaptive_sparse_attention",
    ...     hidden_dim=512,
    ...     num_heads=8,
    ...     sparsity_ratio=0.5
    ... )
    >>> 
    >>> # Obtener información de una técnica
    >>> info = get_technique_info("chain_of_draft")
    >>> print(info['description'])
    >>> 
    >>> # Obtener recomendaciones
    >>> recommendations = get_technique_recommendations("memory_efficient")
"""

from typing import TYPE_CHECKING, Optional, Dict, List, Tuple, Any
from pathlib import Path
import json
import time
import statistics

if TYPE_CHECKING:
    import torch

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Importar módulos de técnicas
try:
    from .paper_2506_10987v1 import (
        Paper2506_10987v1Config,
        AdaptiveSparseAttention,
        Paper2506_10987v1Module,
        TruthGPT_Paper2506_10987v1_Integration
    )
    PAPER_2506_10987_AVAILABLE = True
except ImportError as e:
    Paper2506_10987v1Config = None
    AdaptiveSparseAttention = None
    Paper2506_10987v1Module = None
    TruthGPT_Paper2506_10987v1_Integration = None
    PAPER_2506_10987_AVAILABLE = False
    _import_error_2506_10987 = e

try:
    from .paper_2506_10987v1_chain_of_draft import (
        ChainOfDraftConfig,
        ChainOfDraftModule,
        ChainOfDraftModuleWrapper
    )
    CHAIN_OF_DRAFT_AVAILABLE = True
except ImportError as e:
    ChainOfDraftConfig = None
    ChainOfDraftModule = None
    ChainOfDraftModuleWrapper = None
    CHAIN_OF_DRAFT_AVAILABLE = False
    _import_error_chain_of_draft = e

try:
    from .paper_2503_00735v3 import (
        Paper2503_00735v3Config,
        EfficientFlashAttention,
        Paper2503_00735v3Module,
        TruthGPT_Paper2503_00735v3_Integration
    )
    PAPER_2503_00735_AVAILABLE = True
except ImportError as e:
    Paper2503_00735v3Config = None
    EfficientFlashAttention = None
    Paper2503_00735v3Module = None
    TruthGPT_Paper2503_00735v3_Integration = None
    PAPER_2503_00735_AVAILABLE = False
    _import_error_2503_00735 = e

__all__ = [
    # Configuraciones
    'Paper2506_10987v1Config',
    'ChainOfDraftConfig',
    'Paper2503_00735v3Config',
    # Módulos de atención
    'AdaptiveSparseAttention',
    'EfficientFlashAttention',
    # Módulos principales
    'Paper2506_10987v1Module',
    'ChainOfDraftModule',
    'ChainOfDraftModuleWrapper',
    'Paper2503_00735v3Module',
    # Integraciones
    'TruthGPT_Paper2506_10987v1_Integration',
    'TruthGPT_Paper2503_00735v3_Integration',
    # Utilidades
    'create_technique_module',
    'get_technique_metrics',
    'compare_techniques',
    'validate_technique_config',
    'get_available_techniques',
    'get_technique_info',
    'list_all_techniques',
    'get_technique_recommendations',
    'benchmark_technique',
    'export_technique_report',
    'optimize_technique_config',
    'compare_technique_performance',
    'get_technique_health_report',
    'export_technique_state',
    'import_technique_state',
    'merge_technique_configs',
    'estimate_optimal_config',
    'validate_technique_compatibility',
    'get_technique_summary',
]

__version__ = '2.0.0'

_VALID_TECHNIQUES = {
    'adaptive_sparse_attention',
    'chain_of_draft',
    'efficient_flash_attention'
}

_MINIMIZE_METRICS = {'latency', 'memory'}
_MAXIMIZE_METRICS = {'sparsity', 'quality'}

_USE_CASE_RECOMMENDATIONS = {
    'memory_efficient': ['efficient_flash_attention', 'adaptive_sparse_attention'],
    'fast_inference': ['efficient_flash_attention', 'adaptive_sparse_attention'],
    'code_generation': ['chain_of_draft'],
    'long_sequences': ['efficient_flash_attention'],
    'sparse_attention': ['adaptive_sparse_attention'],
    'reasoning': ['chain_of_draft'],
}

_ESTIMATE_METRICS = {'balanced', 'speed', 'quality', 'memory'}

_MERGE_STRATEGIES = {'override', 'merge', 'deep_merge'}

_DEFAULT_TEST_BATCH_SIZE = 2
_DEFAULT_TEST_SEQ_LEN = 32
_DEFAULT_HIDDEN_DIM = 512

_INCOMPATIBLE_TECHNIQUE_PAIRS = {
    ('adaptive_sparse_attention', 'efficient_flash_attention'),
    ('efficient_flash_attention', 'adaptive_sparse_attention')
}

_TECHNIQUE_REGISTRY = {
    'adaptive_sparse_attention': {
        'available': PAPER_2506_10987_AVAILABLE,
        'config_cls': Paper2506_10987v1Config,
        'module_cls': Paper2506_10987v1Module
    },
    'chain_of_draft': {
        'available': CHAIN_OF_DRAFT_AVAILABLE,
        'config_cls': ChainOfDraftConfig,
        'module_cls': ChainOfDraftModule
    },
    'efficient_flash_attention': {
        'available': PAPER_2503_00735_AVAILABLE,
        'config_cls': Paper2503_00735v3Config,
        'module_cls': Paper2503_00735v3Module
    }
}

_OPTIMIZATION_ADJUSTMENTS = {
    'memory': {
        'adaptive_sparse_attention': lambda config: {
            'sparsity_ratio': min(0.7, config['sparsity_ratio'] + 0.1),
            'num_heads': max(4, config['num_heads'] - 2)
        },
        'efficient_flash_attention': lambda config: {
            'chunk_size': max(32, config['chunk_size'] - 16)
        }
    },
    'speed': {
        'adaptive_sparse_attention': lambda config: {
            'sparsity_ratio': min(0.8, config['sparsity_ratio'] + 0.2)
        },
        'efficient_flash_attention': lambda config: {
            'chunk_size': max(32, config['chunk_size'] - 32)
        }
    },
    'quality': {
        'adaptive_sparse_attention': lambda config: {
            'sparsity_ratio': max(0.3, config['sparsity_ratio'] - 0.1)
        }
    }
}


_DEFAULT_OPTIMIZATION_RANGES = {
    'adaptive_sparse_attention': {
        'sparsity_ratio': [0.3, 0.4, 0.5, 0.6, 0.7],
        'num_heads': [4, 8, 16]
    },
    'efficient_flash_attention': {
        'chunk_size': [32, 64, 128, 256]
    },
    'chain_of_draft': {
        'max_words_per_step': [3, 4, 5, 6]
    }
}

_DEFAULT_TECHNIQUE_CONFIGS = {
    'adaptive_sparse_attention': {
        'hidden_dim': _DEFAULT_HIDDEN_DIM,
        'num_heads': 8,
        'sparsity_ratio': 0.5
    },
    'chain_of_draft': {
        'hidden_dim': _DEFAULT_HIDDEN_DIM,
        'max_words_per_step': 5
    },
    'efficient_flash_attention': {
        'hidden_dim': _DEFAULT_HIDDEN_DIM,
        'num_heads': 8,
        'chunk_size': 64
    }
}


def _validate_technique_type(technique_type: Any) -> str:
    """
    Valida y normaliza un tipo de técnica.
    
    Args:
        technique_type: Tipo de técnica a validar
    
    Returns:
        Tipo de técnica normalizado (lowercase, stripped)
    
    Raises:
        ValueError: Si technique_type no es válido
    """
    if not isinstance(technique_type, str) or not technique_type.strip():
        raise ValueError(f"technique_type debe ser una cadena no vacía, recibido: {technique_type}")
    
    technique_type = technique_type.strip().lower()
    
    if technique_type not in _VALID_TECHNIQUES:
        raise ValueError(f"technique_type debe ser uno de {sorted(_VALID_TECHNIQUES)}, recibido: {technique_type}")
    
    return technique_type


def _validate_string_param(value: Any, param_name: str) -> str:
    """
    Valida que un parámetro sea una cadena no vacía.
    
    Args:
        value: Valor a validar
        param_name: Nombre del parámetro para mensajes de error
    
    Returns:
        Cadena validada y normalizada (stripped)
    
    Raises:
        ValueError: Si el valor no es válido
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{param_name} debe ser una cadena no vacía, recibido: {value}")
    return value.strip()


def _validate_positive_int(value: Any, param_name: str) -> int:
    """
    Valida que un parámetro sea un entero positivo.
    
    Args:
        value: Valor a validar
        param_name: Nombre del parámetro para mensajes de error
    
    Returns:
        Entero positivo validado
    
    Raises:
        ValueError: Si el valor no es válido
    """
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{param_name} debe ser un entero positivo, recibido: {value}")
    return value


def _validate_technique_types_list(technique_types: Any, param_name: str = "technique_types") -> List[str]:
    """
    Valida que un parámetro sea una lista no vacía de técnicas válidas.
    
    Args:
        technique_types: Lista de técnicas a validar
        param_name: Nombre del parámetro para mensajes de error
    
    Returns:
        Lista de técnicas validadas y normalizadas
    
    Raises:
        ValueError: Si la lista no es válida
    """
    if not isinstance(technique_types, list) or not technique_types:
        raise ValueError(f"{param_name} debe ser una lista no vacía, recibido: {technique_types}")
    
    if not all(isinstance(t, str) and t.strip() for t in technique_types):
        raise ValueError(f"Todos los elementos de {param_name} deben ser cadenas no vacías")
    
    return [t.strip().lower() for t in technique_types]


def _create_test_input(
    hidden_dim: int = _DEFAULT_HIDDEN_DIM,
    batch_size: int = _DEFAULT_TEST_BATCH_SIZE,
    seq_len: int = _DEFAULT_TEST_SEQ_LEN
) -> Any:
    """
    Crea un tensor de prueba para testing.
    
    Args:
        hidden_dim: Dimensión oculta
        batch_size: Tamaño del batch
        seq_len: Longitud de secuencia
    
    Returns:
        Tensor de prueba
    """
    if not TORCH_AVAILABLE:
        raise ImportError("torch no está disponible")
    return torch.randn(batch_size, seq_len, hidden_dim)



def create_technique_module(
    technique_type: str = "adaptive_sparse_attention",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear módulos de técnicas.
    
    Args:
        technique_type: Tipo de técnica:
            - "adaptive_sparse_attention": Atención adaptativa dispersa (paper 2506.10987v1)
            - "chain_of_draft": Chain of Draft (paper 2506.10987v1)
            - "efficient_flash_attention": Flash Attention eficiente (paper 2503.00735v3)
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Instancia del módulo de técnica o None si hay error
    
    Raises:
        ValueError: Si technique_type no es válido
    
    Examples:
        >>> module = create_technique_module(
        ...     "adaptive_sparse_attention",
        ...     hidden_dim=512,
        ...     num_heads=8,
        ...     sparsity_ratio=0.5
        ... )
        >>> module = create_technique_module(
        ...     "chain_of_draft",
        ...     hidden_dim=512,
        ...     max_words_per_step=5
        ... )
    """
    technique_type = _validate_technique_type(technique_type)
    
    registry_entry = _TECHNIQUE_REGISTRY.get(technique_type)
    
    if not registry_entry:
        available = get_available_techniques()
        logger.error(
            f"Técnica no disponible: {technique_type} (available_techniques={available})"
        )
        return None
    
    if not registry_entry['available']:
        logger.error(f"Técnica no disponible: {technique_type}")
        return None
    
    config_cls = registry_entry['config_cls']
    module_cls = registry_entry['module_cls']
    
    if config_cls is None or module_cls is None:
        logger.error(f"Clases no disponibles para la técnica: {technique_type}")
        return None
    
    try:
        config = config_cls(**config_kwargs)
        return module_cls(config)
    except Exception as e:
        logger.error(
            f"Error creando módulo de técnica (technique_type={technique_type}): {e}",
            exc_info=True
        )
        return None


def get_technique_metrics(module: Any) -> Optional[Dict[str, Any]]:
    """
    Obtiene métricas de un módulo de técnica.
    
    Args:
        module: Instancia del módulo de técnica
    
    Returns:
        Diccionario con métricas o None si no están disponibles
    
    Raises:
        ValueError: Si module es None
    
    Examples:
        >>> module = create_technique_module("adaptive_sparse_attention")
        >>> metrics = get_technique_metrics(module)
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    try:
        if hasattr(module, 'get_metrics'):
            return module.get_metrics()
        return None
    except Exception as e:
        logger.warning(f"Error obteniendo métricas (module_type={type(module).__name__}): {e}")
        return None


def compare_techniques(
    technique_types: List[str],
    test_input: Optional[Any] = None,
    **config_kwargs
) -> Dict[str, Any]:
    """
    Compara múltiples técnicas con el mismo input.
    
    Args:
        technique_types: Lista de tipos de técnicas a comparar
        test_input: Tensor de prueba (opcional, se genera si no se proporciona)
        **config_kwargs: Argumentos de configuración comunes
    
    Returns:
        Diccionario con resultados de la comparación
    
    Examples:
        >>> results = compare_techniques(
        ...     ["adaptive_sparse_attention", "efficient_flash_attention"],
        ...     hidden_dim=512,
        ...     num_heads=8
        ... )
    """
    if not TORCH_AVAILABLE:
        raise ImportError("torch no está disponible")
    
    technique_types = _validate_technique_types_list(technique_types)
    
    results = {}
    
    if test_input is None:
        hidden_dim = config_kwargs.get('hidden_dim', _DEFAULT_HIDDEN_DIM)
        test_input = _create_test_input(hidden_dim)
    
    for technique_type in technique_types:
        try:
            module = create_technique_module(technique_type, **config_kwargs)
            if module is None:
                results[technique_type] = {'error': 'Module creation failed'}
                continue
            
            with torch.no_grad():
                output = module(test_input)
                metrics = get_technique_metrics(module)
                
                results[technique_type] = {
                    'output_shape': list(output.shape),
                    'metrics': metrics,
                    'num_parameters': sum(p.numel() for p in module.parameters()),
                }
        except Exception as e:
            logger.error(f"Error comparando técnica {technique_type}: {e}", exc_info=True)
            results[technique_type] = {'error': str(e)}
    
    return results


def validate_technique_config(
    technique_type: str,
    **config_kwargs
) -> Tuple[bool, Optional[str]]:
    """
    Valida una configuración de técnica sin crear el módulo.
    
    Args:
        technique_type: Tipo de técnica
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Tuple (is_valid, error_message)
    
    Raises:
        ValueError: Si technique_type no es válido
    
    Examples:
        >>> is_valid, error = validate_technique_config(
        ...     "adaptive_sparse_attention",
        ...     hidden_dim=512,
        ...     num_heads=8,
        ...     sparsity_ratio=0.5
        ... )
    """
    try:
        technique_type = _validate_technique_type(technique_type)
    except ValueError as e:
        return False, str(e)
    
    registry_entry = _TECHNIQUE_REGISTRY.get(technique_type)
    if not registry_entry:
        return False, f"Técnica no disponible: {technique_type}"
    
    if not registry_entry['available']:
        return False, f"Técnica no disponible: {technique_type}"
    
    config_class = registry_entry['config_cls']
    
    if config_class is None:
        return False, f"Config no disponible para técnica: {technique_type}"
    
    try:
        config = config_class(**config_kwargs)
        if hasattr(config, 'validate'):
            config.validate()
        return True, None
    except Exception as e:
        return False, str(e)


def get_available_techniques() -> Dict[str, bool]:
    """
    Obtiene el estado de disponibilidad de todas las técnicas.
    
    Returns:
        Diccionario con el estado de cada técnica
    
    Examples:
        >>> available = get_available_techniques()
        >>> print(available)
    """
    return {
        'adaptive_sparse_attention': PAPER_2506_10987_AVAILABLE,
        'chain_of_draft': CHAIN_OF_DRAFT_AVAILABLE,
        'efficient_flash_attention': PAPER_2503_00735_AVAILABLE,
    }


def get_technique_info(technique_type: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene información detallada sobre una técnica específica.
    
    Args:
        technique_type: Tipo de técnica
    
    Returns:
        Diccionario con información de la técnica o None si no está disponible
    
    Raises:
        ValueError: Si technique_type no es válido
    
    Examples:
        >>> info = get_technique_info("adaptive_sparse_attention")
        >>> print(info['description'])
    """
    technique_type = _validate_technique_type(technique_type)
    
    info_map = {
        'adaptive_sparse_attention': {
            'name': 'Adaptive Sparse Attention',
            'paper': '2506.10987v1',
            'description': 'Atención adaptativa y dispersa con pruning dinámico',
            'features': [
                'Atención adaptativa con threshold aprendible',
                'Control de sparsity ratio',
                'Métricas de entropía de atención',
                'Gradient checkpointing opcional'
            ],
            'available': PAPER_2506_10987_AVAILABLE,
            'config_class': 'Paper2506_10987v1Config',
            'module_class': 'Paper2506_10987v1Module'
        },
        'chain_of_draft': {
            'name': 'Chain of Draft',
            'paper': '2506.10987v1',
            'description': 'Chain of Draft para software engineering con reasoning conciso',
            'features': [
                'Reasoning extremadamente conciso (≤5 palabras por paso)',
                'Múltiples variantes (baseline, structured, hierarchical, iterative, code-specific)',
                'Reducción de ~45% en tokens vs CoT',
                'Mantiene >90% de calidad de código'
            ],
            'available': CHAIN_OF_DRAFT_AVAILABLE,
            'config_class': 'ChainOfDraftConfig',
            'module_class': 'ChainOfDraftModule'
        },
        'efficient_flash_attention': {
            'name': 'Efficient Flash Attention',
            'paper': '2503.00735v3',
            'description': 'Flash Attention eficiente con chunked processing',
            'features': [
                'Chunked attention para reducir complejidad O(n²) a O(n²/C)',
                'Optimización de memoria O(n)',
                'Procesamiento incremental',
                'Soporte para secuencias muy largas'
            ],
            'available': PAPER_2503_00735_AVAILABLE,
            'config_class': 'Paper2503_00735v3Config',
            'module_class': 'Paper2503_00735v3Module'
        }
    }
    
    return info_map.get(technique_type)


def list_all_techniques() -> List[Dict[str, Any]]:
    """
    Lista todas las técnicas disponibles con su información.
    
    Returns:
        Lista de diccionarios con información de cada técnica
    
    Examples:
        >>> techniques = list_all_techniques()
        >>> for tech in techniques:
        ...     print(f"{tech['name']}: {tech['description']}")
    """
    available = get_available_techniques()
    results = []
    
    for tech_type in available.keys():
        try:
            info = get_technique_info(tech_type)
            if info:
                results.append(info)
        except Exception as e:
            logger.warning(f"Error obteniendo información de técnica {tech_type}: {e}")
            continue
    
    return results


def get_technique_recommendations(
    use_case: str,
    constraints: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Obtiene recomendaciones de técnicas basadas en el caso de uso.
    
    Args:
        use_case: Caso de uso ('memory_efficient', 'fast_inference', 'code_generation', etc.)
        constraints: Restricciones opcionales (hidden_dim, num_heads, etc.)
    
    Returns:
        Lista de técnicas recomendadas ordenadas por relevancia
    
    Raises:
        ValueError: Si use_case no es válido o constraints no es un diccionario
    
    Examples:
        >>> recommendations = get_technique_recommendations('memory_efficient')
        >>> recommendations = get_technique_recommendations('code_generation')
    """
    use_case = _validate_string_param(use_case, "use_case").lower()
    
    if constraints is not None and not isinstance(constraints, dict):
        raise ValueError(f"constraints debe ser un diccionario o None, recibido: {type(constraints)}")
    
    recommended = _USE_CASE_RECOMMENDATIONS.get(use_case, [])
    
    if not recommended:
        logger.warning(f"use_case desconocido: {use_case}, usando todas las técnicas disponibles")
    
    available = get_available_techniques()
    filtered = [tech for tech in recommended if available.get(tech, False)]
    
    return filtered if filtered else list(available.keys())


def benchmark_technique(
    technique_type: str,
    test_inputs: Optional[List[Any]] = None,
    num_runs: int = 10,
    **config_kwargs
) -> Dict[str, Any]:
    """
    Realiza benchmarking de una técnica específica.
    
    Args:
        technique_type: Tipo de técnica a evaluar
        test_inputs: Lista de inputs de prueba (opcional)
        num_runs: Número de ejecuciones para promediar
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Diccionario con resultados del benchmarking
    
    Examples:
        >>> results = benchmark_technique(
        ...     "adaptive_sparse_attention",
        ...     num_runs=5,
        ...     hidden_dim=512,
        ...     num_heads=8
        ... )
    """
    if not TORCH_AVAILABLE:
        raise ImportError("torch no está disponible")
    
    technique_type = _validate_technique_type(technique_type)
    num_runs = _validate_positive_int(num_runs, "num_runs")
    
    if not get_available_techniques().get(technique_type, False):
        raise ValueError(f'Técnica no disponible: {technique_type}')
    
    try:
        module = create_technique_module(technique_type, **config_kwargs)
        if module is None:
            return {'error': 'Failed to create module'}
        
        if test_inputs is None:
            hidden_dim = config_kwargs.get('hidden_dim', _DEFAULT_HIDDEN_DIM)
            test_inputs = [_create_test_input(hidden_dim) for _ in range(3)]
        
        module.eval()
        latencies = []
        memory_usage = []
        
        with torch.no_grad():
            for _ in range(num_runs):
                for test_input in test_inputs:
                    if torch.cuda.is_available():
                        torch.cuda.synchronize()
                        torch.cuda.reset_peak_memory_stats()
                    
                    start_time = time.perf_counter()
                    output = module(test_input)
                    
                    if torch.cuda.is_available():
                        torch.cuda.synchronize()
                        peak_memory = torch.cuda.max_memory_allocated() / 1024**2
                        memory_usage.append(peak_memory)
                    
                    end_time = time.perf_counter()
                    latencies.append((end_time - start_time) * 1000)
        
        metrics = get_technique_metrics(module)
        num_params = sum(p.numel() for p in module.parameters())
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        try:
            std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        except (ImportError, AttributeError):
            variance = sum((x - avg_latency) ** 2 for x in latencies) / len(latencies) if latencies else 0.0
            std_latency = variance ** 0.5
        
        return {
            'technique': technique_type,
            'avg_latency_ms': avg_latency,
            'min_latency_ms': min(latencies) if latencies else 0.0,
            'max_latency_ms': max(latencies) if latencies else 0.0,
            'std_latency_ms': std_latency,
            'avg_memory_mb': sum(memory_usage) / len(memory_usage) if memory_usage else None,
            'num_parameters': num_params,
            'metrics': metrics,
            'num_runs': num_runs
        }
    except Exception as e:
        logger.error(
            f"Error en benchmarking (technique_type={technique_type}): {e}",
            exc_info=True
        )
        return {'error': str(e)}


def export_technique_report(
    technique_type: str,
    output_path: Optional[str] = None,
    **config_kwargs
) -> str:
    """
    Exporta un reporte completo de una técnica.
    
    Args:
        technique_type: Tipo de técnica
        output_path: Ruta de salida (opcional, genera automáticamente si no se proporciona)
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Ruta del archivo generado
    
    Examples:
        >>> report_path = export_technique_report(
        ...     "adaptive_sparse_attention",
        ...     hidden_dim=512,
        ...     num_heads=8
        ... )
    """
    from datetime import datetime
    
    info = get_technique_info(technique_type)
    if not info:
        raise ValueError(f"Técnica no encontrada: {technique_type}")
    
    is_valid, error = validate_technique_config(technique_type, **config_kwargs)
    if not is_valid:
        raise ValueError(f"Configuración inválida: {error}")
    
    try:
        benchmark_results = benchmark_technique(technique_type, num_runs=3, **config_kwargs)
        
        report = {
            'technique_info': info,
            'config': config_kwargs,
            'validation': {'is_valid': is_valid, 'error': error},
            'benchmark': benchmark_results,
            'generated_at': datetime.now().isoformat(),
            'version': __version__
        }
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f'technique_report_{technique_type}_{timestamp}.json'
        else:
            report_path = output_path
        
        report_path_obj = Path(report_path)
        report_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path_obj, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(
            f"Reporte exportado (technique_type={technique_type}, output_path={report_path_obj})"
        )
        
        return str(report_path_obj)
    except Exception as e:
        logger.error(
            f"Error exportando reporte (technique_type={technique_type}): {e}",
            exc_info=True
        )
        raise RuntimeError(f"Error exportando reporte: {e}") from e


def optimize_technique_config(
    technique_type: str,
    target_metric: str = 'latency',
    test_input: Optional[Any] = None,
    param_ranges: Optional[Dict[str, List[Any]]] = None
) -> Dict[str, Any]:
    """
    Optimiza la configuración de una técnica basándose en métricas objetivo.
    
    Args:
        technique_type: Tipo de técnica
        target_metric: Métrica objetivo ('latency', 'memory', 'sparsity', 'quality')
        test_input: Input de prueba (opcional)
        param_ranges: Rangos de parámetros a probar (opcional)
    
    Returns:
        Diccionario con configuración optimizada y resultados
    
    Examples:
        >>> optimal = optimize_technique_config(
        ...     "adaptive_sparse_attention",
        ...     target_metric="latency",
        ...     param_ranges={'sparsity_ratio': [0.3, 0.5, 0.7]}
        ... )
    """
    if not TORCH_AVAILABLE:
        raise ImportError("torch no está disponible")
    
    technique_type = _validate_technique_type(technique_type)
    
    if not get_available_techniques().get(technique_type, False):
        raise ValueError(f'Técnica no disponible: {technique_type}')
    
    if test_input is None:
        hidden_dim = config_kwargs.get('hidden_dim', _DEFAULT_HIDDEN_DIM)
        test_input = _create_test_input(hidden_dim)
    
    ranges = param_ranges or _DEFAULT_OPTIMIZATION_RANGES.get(technique_type, {})
    
    if not ranges:
        raise ValueError(f"No hay rangos de parámetros definidos para {technique_type}")
    
    best_config = None
    best_score = float('inf') if target_metric in _MINIMIZE_METRICS else float('-inf')
    results = []
    
    try:
        for param_name, param_values in ranges.items():
            for param_value in param_values:
                config = {param_name: param_value}
                
                try:
                    module = create_technique_module(technique_type, **config)
                    if module is None:
                        continue
                    
                    module.eval()
                    with torch.no_grad():
                        start = time.perf_counter()
                        output = module(test_input)
                        latency = (time.perf_counter() - start) * 1000
                    
                    metrics = get_technique_metrics(module)
                    
                    if target_metric == 'latency':
                        score = latency
                    elif target_metric == 'memory':
                        score = sum(p.numel() for p in module.parameters())
                    elif target_metric == 'sparsity':
                        score = -metrics.get('sparsity', 0) if metrics else float('inf')
                    else:
                        score = latency
                    
                    result = {
                        'config': config,
                        'score': score,
                        'latency_ms': latency,
                        'metrics': metrics
                    }
                    
                    results.append(result)
                    
                    is_minimizing = target_metric in _MINIMIZE_METRICS
                    is_better = (is_minimizing and score < best_score) or (not is_minimizing and score > best_score)
                    
                    if is_better:
                        best_score = score
                        best_config = config
                
                except Exception as e:
                    logger.warning(
                        f"Error probando configuración (technique_type={technique_type}, config={config}): {e}"
                    )
                    continue
        
        return {
            'technique_type': technique_type,
            'target_metric': target_metric,
            'best_config': best_config,
            'best_score': best_score,
            'all_results': results
        }
    except Exception as e:
        logger.error(
            f"Error optimizando configuración (technique_type={technique_type}): {e}",
            exc_info=True
        )
        return {'error': str(e)}


def compare_technique_performance(
    technique_types: List[str],
    test_input: Optional[Any] = None,
    **common_config
) -> Dict[str, Any]:
    """
    Compara el rendimiento de múltiples técnicas con la misma configuración.
    
    Args:
        technique_types: Lista de técnicas a comparar
        test_input: Input de prueba (opcional)
        **common_config: Configuración común para todas las técnicas
    
    Returns:
        Diccionario con comparación de rendimiento
    
    Examples:
        >>> comparison = compare_technique_performance(
        ...     ["adaptive_sparse_attention", "efficient_flash_attention"],
        ...     hidden_dim=512,
        ...     num_heads=8
        ... )
    """
    if not TORCH_AVAILABLE:
        raise ImportError("torch no está disponible")
    
    technique_types = _validate_technique_types_list(technique_types)
    
    if test_input is None:
        hidden_dim = common_config.get('hidden_dim', _DEFAULT_HIDDEN_DIM)
        test_input = _create_test_input(hidden_dim)
    
    results = {}
    
    for tech_type in technique_types:
        if not get_available_techniques().get(tech_type, False):
            results[tech_type] = {'error': 'Not available'}
            continue
        
        try:
            result = benchmark_technique(tech_type, [test_input], num_runs=5, **common_config)
            results[tech_type] = result
        except Exception as e:
            logger.error(
                f"Error comparando técnica (technique_type={tech_type}): {e}",
                exc_info=True
            )
            results[tech_type] = {'error': str(e)}
    
    if len(results) > 1:
        latencies = {
            k: v.get('avg_latency_ms', float('inf'))
            for k, v in results.items()
            if 'error' not in v
        }
        if latencies:
            fastest = min(latencies, key=latencies.get)
            results['_summary'] = {
                'fastest': fastest,
                'latency_ranking': sorted(latencies.items(), key=lambda x: x[1])
            }
    
    return results


def get_technique_health_report(
    module: Any
) -> Dict[str, Any]:
    """
    Genera un reporte de salud para un módulo de técnica.
    
    Args:
        module: Instancia del módulo de técnica
    
    Returns:
        Diccionario con información de salud del módulo
    
    Examples:
        >>> module = create_technique_module("adaptive_sparse_attention")
        >>> health = get_technique_health_report(module)
        >>> print(health['status'])
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    try:
        checks = {
            'has_forward': hasattr(module, 'forward'),
            'has_get_metrics': hasattr(module, 'get_metrics'),
            'has_parameters': hasattr(module, 'parameters'),
            'is_training': getattr(module, 'training', False),
        }
        
        if hasattr(module, 'parameters'):
            try:
                param_count = sum(p.numel() for p in module.parameters())
                checks['parameter_count'] = param_count
                checks['has_parameters'] = param_count > 0
            except Exception:
                checks['parameter_count'] = 0
                checks['has_parameters'] = False
        
        all_passed = all(checks.values() if isinstance(v, bool) else True for v in checks.values())
        
        return {
            'status': 'healthy' if all_passed else 'degraded',
            'checks': checks,
            'timestamp': time.time(),
            'module_type': type(module).__name__
        }
    except Exception as e:
        logger.warning(f"Error en health check (module_type={type(module).__name__}): {e}")
        return {
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'timestamp': time.time(),
            'module_type': type(module).__name__
        }


def export_technique_state(
    module: Any,
    output_path: Optional[str] = None
) -> str:
    """
    Exporta el estado de un módulo de técnica.
    
    Args:
        module: Instancia del módulo de técnica
        output_path: Ruta de salida (opcional)
    
    Returns:
        Ruta del archivo generado
    
    Examples:
        >>> module = create_technique_module("adaptive_sparse_attention")
        >>> state_path = export_technique_state(module)
    """
    
    if module is None:
        raise ValueError("module no puede ser None")
    
    try:
        state = {
            'module_type': type(module).__name__,
            'module_state_dict': None,
            'config': None,
            'metrics': None,
            'timestamp': time.time()
        }
        
        if hasattr(module, 'state_dict'):
            state['module_state_dict'] = {
                k: v.cpu().tolist() if hasattr(v, 'cpu') else str(v)
                for k, v in module.state_dict().items()
            }
        
        if hasattr(module, 'config'):
            config = module.config
            if hasattr(config, 'dict'):
                state['config'] = config.dict()
            elif hasattr(config, '__dict__'):
                state['config'] = {k: str(v) for k, v in config.__dict__.items()}
        
        if hasattr(module, 'get_metrics'):
            state['metrics'] = get_technique_metrics(module)
        
        if output_path is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            state_path = f'technique_state_{type(module).__name__}_{timestamp}.json'
        else:
            state_path = output_path
        
        state_path_obj = Path(state_path)
        state_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_path_obj, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logger.info(
            f"Estado exportado (module_type={type(module).__name__}, output_path={state_path_obj})"
        )
        
        return str(state_path_obj)
    except Exception as e:
        logger.error(
            f"Error exportando estado (module_type={type(module).__name__}): {e}",
            exc_info=True
        )
        raise RuntimeError(f"Error exportando estado: {e}") from e


def import_technique_state(
    state_path: str,
    technique_type: str,
    **config_kwargs
) -> Optional[Any]:
    """
    Importa el estado de un módulo de técnica.
    
    Args:
        state_path: Ruta del archivo de estado
        technique_type: Tipo de técnica
        **config_kwargs: Argumentos de configuración adicionales
    
    Returns:
        Instancia del módulo con estado restaurado o None si hay error
    
    Examples:
        >>> module = import_technique_state(
        ...     "technique_state.json",
        ...     "adaptive_sparse_attention"
        ... )
    """
    state_path = _validate_string_param(state_path, "state_path")
    technique_type = _validate_technique_type(technique_type)
    
    try:
        state_path_obj = Path(state_path)
        if not state_path_obj.exists():
            raise FileNotFoundError(f"Estado no encontrado: {state_path}")
        
        with open(state_path_obj, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        module = create_technique_module(technique_type, **config_kwargs)
        if module is None:
            raise ValueError(f"No se pudo crear módulo: {technique_type}")
        
        if 'module_state_dict' in state and state['module_state_dict']:
            if hasattr(module, 'load_state_dict'):
                if not TORCH_AVAILABLE:
                    raise ImportError("torch no está disponible para cargar el estado del módulo")
                state_dict = {
                    k: torch.tensor(v) if isinstance(v, list) else v
                    for k, v in state['module_state_dict'].items()
                }
                module.load_state_dict(state_dict, strict=False)
        
        logger.info(
            f"Estado importado (module_type={type(module).__name__}, state_path={state_path_obj})"
        )
        
        return module
    except Exception as e:
        logger.error(
            f"Error importando estado (state_path={state_path}): {e}",
            exc_info=True
        )
        return None


def merge_technique_configs(
    *configs: Dict[str, Any],
    strategy: str = 'override'
) -> Dict[str, Any]:
    """
    Combina múltiples configuraciones de técnicas.
    
    Args:
        *configs: Configuraciones a combinar
        strategy: Estrategia de combinación ('override', 'merge', 'deep_merge')
    
    Returns:
        Configuración combinada
    
    Examples:
        >>> config1 = {'hidden_dim': 512, 'num_heads': 8}
        >>> config2 = {'sparsity_ratio': 0.5}
        >>> merged = merge_technique_configs(config1, config2)
    """
    if not configs:
        return {}
    
    if strategy not in _MERGE_STRATEGIES:
        raise ValueError(f"strategy debe ser uno de {sorted(_MERGE_STRATEGIES)}, recibido: {strategy}")
    
    for config in configs:
        if not isinstance(config, dict):
            raise ValueError(f"Todas las configuraciones deben ser diccionarios, recibido: {type(config)}")
    
    try:
        if strategy == 'override':
            merged = {}
            for config in configs:
                merged.update(config)
            return merged
        
        elif strategy == 'merge':
            merged = {}
            for config in configs:
                for k, v in config.items():
                    if k not in merged:
                        merged[k] = v
            return merged
        
        elif strategy == 'deep_merge':
            def deep_merge(base, update):
                for k, v in update.items():
                    if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                        base[k] = deep_merge(base[k], v)
                    else:
                        base[k] = v
                return base
            
            merged = configs[0].copy()
            for config in configs[1:]:
                merged = deep_merge(merged, config)
            return merged
    except Exception as e:
        logger.warning(f"Error combinando configuraciones (strategy={strategy}): {e}")
        return configs[0] if configs and isinstance(configs[0], dict) else {}


def estimate_optimal_config(
    technique_type: str,
    constraints: Optional[Dict[str, Any]] = None,
    target_metric: str = 'balanced'
) -> Dict[str, Any]:
    """
    Estima una configuración óptima basada en restricciones.
    
    Args:
        technique_type: Tipo de técnica
        constraints: Restricciones (memory_limit, latency_target, etc.)
        target_metric: Métrica objetivo ('balanced', 'speed', 'quality', 'memory')
    
    Returns:
        Configuración estimada
    
    Examples:
        >>> config = estimate_optimal_config(
        ...     "adaptive_sparse_attention",
        ...     constraints={'memory_limit_mb': 1000},
        ...     target_metric='memory'
        ... )
    """
    technique_type = _validate_technique_type(technique_type)
    
    if constraints is None:
        constraints = {}
    elif not isinstance(constraints, dict):
        raise ValueError(f"constraints debe ser un diccionario, recibido: {type(constraints)}")
    
    if target_metric not in _ESTIMATE_METRICS:
        raise ValueError(f"target_metric debe ser uno de {sorted(_ESTIMATE_METRICS)}, recibido: {target_metric}")
    
    try:
        config = _DEFAULT_TECHNIQUE_CONFIGS.get(technique_type, {}).copy()
        
        if not config:
            raise ValueError(f"Técnica desconocida: {technique_type}")
        
        if target_metric in _OPTIMIZATION_ADJUSTMENTS:
            metric_adjustments = _OPTIMIZATION_ADJUSTMENTS[target_metric]
            if technique_type in metric_adjustments:
                adjustments = metric_adjustments[technique_type](config)
                config.update(adjustments)
        
        if 'memory_limit_mb' in constraints:
            memory_limit = _validate_numeric_constraint(constraints['memory_limit_mb'], 'memory_limit_mb')
            if memory_limit < 500:
                config['hidden_dim'] = min(256, config.get('hidden_dim', 512))
                if 'num_heads' in config:
                    config['num_heads'] = max(4, config['num_heads'] - 2)
        
        if 'latency_target_ms' in constraints:
            latency_target = _validate_numeric_constraint(constraints['latency_target_ms'], 'latency_target_ms')
            if latency_target < 10:
                if technique_type == 'adaptive_sparse_attention':
                    config['sparsity_ratio'] = min(0.8, config['sparsity_ratio'] + 0.3)
        
        return config
    except Exception as e:
        logger.warning(f"Error estimando configuración (technique_type={technique_type}): {e}")
        return {}


def validate_technique_compatibility(
    technique_type: str,
    other_technique_type: Optional[str] = None,
    **config_kwargs
) -> Tuple[bool, Optional[str]]:
    """
    Valida la compatibilidad de una técnica con otra o con configuraciones.
    
    Args:
        technique_type: Tipo de técnica principal
        other_technique_type: Tipo de otra técnica (opcional)
        **config_kwargs: Configuración a validar
    
    Returns:
        Tupla (es_compatible, mensaje)
    
    Examples:
        >>> compatible, msg = validate_technique_compatibility(
        ...     "adaptive_sparse_attention",
        ...     "efficient_flash_attention"
        ... )
    """
    try:
        technique_type = _validate_technique_type(technique_type)
        
        if not get_available_techniques().get(technique_type, False):
            return False, f"Técnica no disponible: {technique_type}"
        
        if other_technique_type:
            if not isinstance(other_technique_type, str) or not other_technique_type.strip():
                return False, f"other_technique_type debe ser una cadena no vacía, recibido: {other_technique_type}"
            
            other_technique_type = other_technique_type.strip().lower()
            
            if not get_available_techniques().get(other_technique_type, False):
                return False, f"Técnica no disponible: {other_technique_type}"
            
            if (technique_type, other_technique_type) in _INCOMPATIBLE_TECHNIQUE_PAIRS:
                return False, f"Técnicas incompatibles: {technique_type} y {other_technique_type}"
        
        is_valid, error = validate_technique_config(technique_type, **config_kwargs)
        if not is_valid:
            return False, f"Configuración inválida: {error}"
        
        return True, None
    except Exception as e:
        return False, f"Error validando compatibilidad: {str(e)}"


def _validate_technique_type(technique_type: str) -> Tuple[bool, Optional[str]]:
    """
    Valida que un tipo de técnica sea válido.
    
    Args:
        technique_type: Tipo de técnica a validar
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not isinstance(technique_type, str):
        return False, "technique_type debe ser una cadena"
    
    technique_type = technique_type.strip().lower()
    
    if not technique_type:
        return False, "technique_type no puede estar vacío"
    
    available = get_available_techniques()
    if technique_type not in available:
        return False, f"Técnica desconocida: {technique_type}"
    
    if not available.get(technique_type, False):
        return False, f"Técnica no disponible: {technique_type}"
    
    return True, None


def _validate_config_params(config_kwargs: Dict[str, Any], technique_type: str) -> Tuple[bool, Optional[str]]:
    """
    Valida parámetros de configuración comunes.
    
    Args:
        config_kwargs: Parámetros de configuración
        technique_type: Tipo de técnica
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if 'hidden_dim' in config_kwargs:
        hidden_dim = config_kwargs['hidden_dim']
        if not isinstance(hidden_dim, int) or hidden_dim < 1:
            return False, "hidden_dim debe ser un entero positivo"
        if hidden_dim % 2 != 0:
            logger.warning(f"hidden_dim={hidden_dim} no es par, puede causar problemas")
    
    if 'num_heads' in config_kwargs:
        num_heads = config_kwargs['num_heads']
        if not isinstance(num_heads, int) or num_heads < 1:
            return False, "num_heads debe ser un entero positivo"
    
    if 'sparsity_ratio' in config_kwargs:
        sparsity_ratio = config_kwargs['sparsity_ratio']
        if not isinstance(sparsity_ratio, (int, float)):
            return False, "sparsity_ratio debe ser un número"
        if not (0.0 <= sparsity_ratio <= 1.0):
            return False, "sparsity_ratio debe estar en [0.0, 1.0]"
    
    if 'chunk_size' in config_kwargs:
        chunk_size = config_kwargs['chunk_size']
        if not isinstance(chunk_size, int) or chunk_size < 1:
            return False, "chunk_size debe ser un entero positivo"
    
    if 'max_words_per_step' in config_kwargs:
        max_words = config_kwargs['max_words_per_step']
        if not isinstance(max_words, int) or max_words < 1:
            return False, "max_words_per_step debe ser un entero positivo"
    
    return True, None


def get_technique_summary(
    technique_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene un resumen del estado del módulo de técnicas.
    
    Args:
        technique_type: Tipo de técnica específica (opcional)
    
    Returns:
        Diccionario con resumen del módulo
    
    Raises:
        ValueError: Si technique_type se proporciona pero no es válido
    
    Examples:
        >>> summary = get_technique_summary()
        >>> summary = get_technique_summary("adaptive_sparse_attention")
    """
    try:
        available = get_available_techniques()
        total_available = sum(1 for v in available.values() if v)
        total_techniques = len(available)
        
        summary = {
            'total_techniques': total_techniques,
            'available_count': total_available,
            'unavailable_count': total_techniques - total_available,
            'availability_rate': total_available / total_techniques if total_techniques > 0 else 0.0,
            'techniques': available,
            'version': __version__
        }
        
        if technique_type is not None:
            try:
                technique_type = _validate_technique_type(technique_type)
                is_valid, error = True, None
            except ValueError as e:
                is_valid, error = False, str(e)
            
            if is_valid:
                info = get_technique_info(technique_type)
                summary['technique_info'] = info
            else:
                summary['error'] = error
        
        return summary
    except Exception as e:
        logger.warning(f"Error generando resumen: {e}")
        return {
            'error': f'Failed to generate summary: {str(e)}',
            'version': __version__
        }
