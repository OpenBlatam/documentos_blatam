#!/usr/bin/env python3
"""
Redundancy Module - Sistemas de Supresión de Redundancia
========================================================

Este módulo contiene implementaciones de sistemas de supresión de redundancia
basados en papers de investigación para procesamiento masivo (bulk processing).

Módulos disponibles:
- paper_2510_00071: Sistema de supresión de redundancia para bulk processing
- redundancy_utils: Utilidades para detección y eliminación de redundancia
- redundancy_analytics: Analytics, optimización y exportación

Características principales:
- ✅ Detección de redundancia con múltiples métodos (cosine, euclidean, dot, semantic)
- ✅ Clustering jerárquico optimizado
- ✅ Procesamiento masivo eficiente
- ✅ Métricas de reducción y estadísticas
- ✅ Selección inteligente de representantes
- ✅ Batch processing optimizado
- ✅ Comparación de métodos de similitud
- ✅ Optimización automática de umbrales
- ✅ Analytics avanzados y exportación de reportes
- ✅ Factory functions para creación fácil
"""

from typing import TYPE_CHECKING, Optional, Any, Dict, List, Tuple

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

# Importar configuraciones y clases principales
try:
    from .paper_2510_00071 import (
        Paper2510_00071Config,
        Paper2510_00071_RedundancySuppressor,
        TruthGPT_Paper2510_00071_Integration
    )
    PAPER_2510_AVAILABLE = True
except ImportError:
    Paper2510_00071Config = None
    Paper2510_00071_RedundancySuppressor = None
    TruthGPT_Paper2510_00071_Integration = None
    PAPER_2510_AVAILABLE = False

# Importar utilidades
try:
    from .redundancy_utils import (
        compute_similarity_batch,
        find_duplicate_items,
        batch_deduplicate,
        calculate_reduction_stats,
        export_redundancy_report,
        compare_redundancy_methods,
        optimize_threshold
    )
    UTILS_AVAILABLE = True
except ImportError:
    compute_similarity_batch = None
    find_duplicate_items = None
    batch_deduplicate = None
    calculate_reduction_stats = None
    export_redundancy_report = None
    compare_redundancy_methods = None
    optimize_threshold = None
    UTILS_AVAILABLE = False

# Importar analytics
try:
    from .redundancy_analytics import (
        RedundancyAnalytics,
        RedundancyOptimizer,
        RedundancyExporter
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    RedundancyAnalytics = None
    RedundancyOptimizer = None
    RedundancyExporter = None
    ANALYTICS_AVAILABLE = False

__all__ = [
    # Configuraciones
    'Paper2510_00071Config',
    # Supresores de redundancia
    'Paper2510_00071_RedundancySuppressor',
    # Integraciones
    'TruthGPT_Paper2510_00071_Integration',
    # Analytics y optimización
    'RedundancyAnalytics',
    'RedundancyOptimizer',
    'RedundancyExporter',
    # Utilidades
    'create_redundancy_suppressor',
    'get_available_modules',
    'recommend_similarity_method',
    'estimate_optimal_threshold',
    'validate_redundancy_config',
    # Helpers
    'get_redundancy_health_report',
    'merge_redundancy_suppressors',
    'export_suppressor_state',
    'import_suppressor_state',
    'compute_similarity_batch',
    'find_duplicate_items',
    'batch_deduplicate',
    'calculate_reduction_stats',
    'export_redundancy_report',
    'compare_redundancy_methods',
    'optimize_threshold',
]

__version__ = '2.0.0'


def create_redundancy_suppressor(
    paper_type: str = "2510_00071",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear supresores de redundancia.
    
    Args:
        paper_type: Tipo de paper ("2510_00071")
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Instancia del supresor de redundancia o None si hay error
    
    Raises:
        ValueError: Si paper_type no es válido
    
    Examples:
        >>> suppressor = create_redundancy_suppressor(
        ...     "2510_00071",
        ...     similarity_threshold=0.85,
        ...     redundancy_detection_method="cosine"
        ... )
    """
    if not isinstance(paper_type, str) or not paper_type.strip():
        raise ValueError(f"paper_type debe ser una cadena no vacía, recibido: {paper_type}")
    
    paper_type = paper_type.lower()
    valid_types = ["2510_00071"]
    
    if paper_type not in valid_types:
        raise ValueError(f"paper_type debe ser uno de {valid_types}, recibido: {paper_type}")
    
    try:
        if paper_type == "2510_00071" and PAPER_2510_AVAILABLE:
            config = Paper2510_00071Config(**config_kwargs)
            return Paper2510_00071_RedundancySuppressor(config)
        else:
            logger.error(f"Paper type no disponible: {paper_type} (available: {PAPER_2510_AVAILABLE})")
            return None
    except Exception as e:
        logger.error(f"Error creando supresor de redundancia (paper_type={paper_type}): {e}", exc_info=True)
        return None


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene la lista de módulos y utilidades disponibles.
    
    Returns:
        Diccionario con módulos y su disponibilidad
    
    Examples:
        >>> available = get_available_modules()
        >>> print(available)
        {'paper_2510_00071': True, 'utils': True, 'analytics': True}
    """
    return {
        'paper_2510_00071': PAPER_2510_AVAILABLE,
        'utils': UTILS_AVAILABLE,
        'analytics': ANALYTICS_AVAILABLE,
        'helpers': HELPERS_AVAILABLE if 'HELPERS_AVAILABLE' in globals() else False,
        'benchmark': BENCHMARK_AVAILABLE if 'BENCHMARK_AVAILABLE' in globals() else False,
        'cache': CACHE_AVAILABLE if 'CACHE_AVAILABLE' in globals() else False,
        'integration': INTEGRATION_AVAILABLE if 'INTEGRATION_AVAILABLE' in globals() else False,
        'visualization': VISUALIZATION_AVAILABLE if 'VISUALIZATION_AVAILABLE' in globals() else False,
        'gpu': GPU_AVAILABLE if 'GPU_AVAILABLE' in globals() else False,
        'monitoring': MONITORING_AVAILABLE if 'MONITORING_AVAILABLE' in globals() else False,
        'logging': LOGGING_AVAILABLE if 'LOGGING_AVAILABLE' in globals() else False,
        'config': CONFIG_AVAILABLE if 'CONFIG_AVAILABLE' in globals() else False,
        'debug': DEBUG_AVAILABLE if 'DEBUG_AVAILABLE' in globals() else False,
        'alerts': ALERTS_AVAILABLE if 'ALERTS_AVAILABLE' in globals() else False,
        'test_utils': TEST_UTILS_AVAILABLE if 'TEST_UTILS_AVAILABLE' in globals() else False,
    }


def recommend_similarity_method(
    use_case: str = "general",
    data_type: str = "embeddings",
    performance_priority: str = "balanced"
) -> str:
    """
    Recomienda el mejor método de similitud según el caso de uso.
    
    Args:
        use_case: Caso de uso. Opciones:
            - "general": Uso general (recomendado: cosine)
            - "semantic": Búsqueda semántica (recomendado: semantic)
            - "exact_match": Coincidencia exacta (recomendado: dot)
            - "distance_based": Basado en distancias (recomendado: euclidean)
        data_type: Tipo de datos ("embeddings", "vectors", "text")
        performance_priority: Prioridad de rendimiento ("speed", "accuracy", "balanced")
    
    Returns:
        Nombre del método recomendado
    
    Raises:
        ValueError: Si los parámetros no son válidos
    
    Examples:
        >>> method = recommend_similarity_method("general")
        >>> method = recommend_similarity_method("semantic", performance_priority="accuracy")
        >>> method = recommend_similarity_method("exact_match", data_type="vectors")
    """
    valid_use_cases = ["general", "semantic", "exact_match", "distance_based"]
    if use_case not in valid_use_cases:
        raise ValueError(f"use_case debe ser uno de {valid_use_cases}, recibido: {use_case}")
    
    valid_priorities = ["speed", "accuracy", "balanced"]
    if performance_priority not in valid_priorities:
        raise ValueError(f"performance_priority debe ser uno de {valid_priorities}, recibido: {performance_priority}")
    
    if use_case == "semantic":
        return "semantic"
    
    elif use_case == "exact_match":
        if performance_priority == "speed":
            return "dot"
        return "cosine"
    
    elif use_case == "distance_based":
        return "euclidean"
    
    elif use_case == "general":
        if performance_priority == "speed":
            return "dot"
        elif performance_priority == "accuracy":
            return "semantic"
        else:
            return "cosine"
    
    return "cosine"


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
    
    Raises:
        ValueError: Si config es None
    """
    if config is None:
        raise ValueError("config no puede ser None")
    
    errors = []
    
    if hasattr(config, 'similarity_threshold'):
        threshold = getattr(config, 'similarity_threshold', 0.85)
        if not (0.0 <= threshold <= 1.0):
            errors.append(f"similarity_threshold debe estar en [0.0, 1.0], recibido: {threshold}")
    
    if hasattr(config, 'redundancy_detection_method'):
        method = getattr(config, 'redundancy_detection_method', 'cosine')
        valid_methods = ["cosine", "euclidean", "dot", "semantic"]
        if method not in valid_methods:
            errors.append(f"redundancy_detection_method debe ser uno de {valid_methods}, recibido: {method}")
    
    if strict and errors:
        return False, errors
    
    try:
        from .redundancy_helpers import validate_redundancy_config as _validate
        return _validate(config, strict)
    except ImportError:
        if errors:
            return False, errors
        return True, []


try:
    from .redundancy_helpers import (
        get_redundancy_health_report,
        merge_redundancy_suppressors,
        export_suppressor_state,
        import_suppressor_state
    )
    HELPERS_AVAILABLE = True
    __all__.extend([
        'get_redundancy_health_report',
        'merge_redundancy_suppressors',
        'export_suppressor_state',
        'import_suppressor_state'
    ])
except ImportError:
    HELPERS_AVAILABLE = False
    get_redundancy_health_report = None
    merge_redundancy_suppressors = None
    export_suppressor_state = None
    import_suppressor_state = None

# Importar benchmarking
try:
    from .benchmark import (
        RedundancyBenchmark,
        BenchmarkResult,
        run_quick_benchmark
    )
    BENCHMARK_AVAILABLE = True
    __all__.extend([
        'RedundancyBenchmark',
        'BenchmarkResult',
        'run_quick_benchmark'
    ])
except ImportError:
    BENCHMARK_AVAILABLE = False
    RedundancyBenchmark = None
    BenchmarkResult = None
    run_quick_benchmark = None

# Importar caché avanzado
try:
    from .redundancy_cache import (
        LRUSimilarityCache,
        CacheEntry,
        OptimizedRedundancyProcessor
    )
    CACHE_AVAILABLE = True
    __all__.extend([
        'LRUSimilarityCache',
        'CacheEntry',
        'OptimizedRedundancyProcessor'
    ])
except ImportError:
    CACHE_AVAILABLE = False
    LRUSimilarityCache = None
    CacheEntry = None
    OptimizedRedundancyProcessor = None

# Importar integración
try:
    from .redundancy_integration import (
        RedundancyMemoryIntegration,
        RedundancyPipelineIntegration,
        RedundancyStreamingProcessor,
        RedundancyWithBestTechniques,
        create_integrated_redundancy_system,
        create_redundancy_with_best_techniques
    )
    INTEGRATION_AVAILABLE = True
    __all__.extend([
        'RedundancyMemoryIntegration',
        'RedundancyPipelineIntegration',
        'RedundancyStreamingProcessor',
        'RedundancyWithBestTechniques',
        'create_integrated_redundancy_system',
        'create_redundancy_with_best_techniques'
    ])
except ImportError:
    INTEGRATION_AVAILABLE = False
    RedundancyMemoryIntegration = None
    RedundancyPipelineIntegration = None
    RedundancyStreamingProcessor = None
    RedundancyWithBestTechniques = None
    create_integrated_redundancy_system = None
    create_redundancy_with_best_techniques = None

# Importar visualización
try:
    from .redundancy_visualization import (
        RedundancyVisualizer
    )
    VISUALIZATION_AVAILABLE = True
    __all__.extend([
        'RedundancyVisualizer'
    ])
except ImportError:
    VISUALIZATION_AVAILABLE = False
    RedundancyVisualizer = None

# Importar optimizaciones GPU
try:
    from .redundancy_gpu import (
        GPUOptimizedRedundancyProcessor,
        GPUOptimizedRedundancyWithBestTechniques,
        ParallelRedundancyProcessor,
        optimize_for_device,
        get_gpu_memory_stats,
        benchmark_redundancy_processing,
        optimize_chunk_size
    )
    GPU_AVAILABLE = True
    __all__.extend([
        'GPUOptimizedRedundancyProcessor',
        'GPUOptimizedRedundancyWithBestTechniques',
        'ParallelRedundancyProcessor',
        'optimize_for_device',
        'get_gpu_memory_stats',
        'benchmark_redundancy_processing',
        'optimize_chunk_size'
    ])
except ImportError:
    GPU_AVAILABLE = False
    GPUOptimizedRedundancyProcessor = None
    GPUOptimizedRedundancyWithBestTechniques = None
    ParallelRedundancyProcessor = None
    optimize_for_device = None
    get_gpu_memory_stats = None
    benchmark_redundancy_processing = None
    optimize_chunk_size = None

# Importar monitoreo
try:
    from .redundancy_monitoring import (
        RedundancyMonitor,
        RedundancyMetrics,
        create_redundancy_monitor
    )
    MONITORING_AVAILABLE = True
    __all__.extend([
        'RedundancyMonitor',
        'RedundancyMetrics',
        'create_redundancy_monitor'
    ])
except ImportError:
    MONITORING_AVAILABLE = False
    RedundancyMonitor = None
    RedundancyMetrics = None
    create_redundancy_monitor = None

# Importar logging
try:
    from .redundancy_logging import (
        RedundancyLogger,
        log_function_call,
        log_operation_context,
        create_redundancy_logger
    )
    LOGGING_AVAILABLE = True
    __all__.extend([
        'RedundancyLogger',
        'log_function_call',
        'log_operation_context',
        'create_redundancy_logger'
    ])
except ImportError:
    LOGGING_AVAILABLE = False
    RedundancyLogger = None
    log_function_call = None
    log_operation_context = None
    create_redundancy_logger = None

# Importar configuración avanzada
try:
    from .redundancy_config import (
        PerformanceProfile,
        RedundancyConfigProfile,
        RedundancyConfigManager,
        create_config_from_profile,
        get_recommended_profile
    )
    CONFIG_AVAILABLE = True
    __all__.extend([
        'PerformanceProfile',
        'RedundancyConfigProfile',
        'RedundancyConfigManager',
        'create_config_from_profile',
        'get_recommended_profile'
    ])
except ImportError:
    CONFIG_AVAILABLE = False
    PerformanceProfile = None
    RedundancyConfigProfile = None
    RedundancyConfigManager = None
    create_config_from_profile = None
    get_recommended_profile = None

# Importar debugging
try:
    from .redundancy_debug import (
        RedundancyDebugger,
        DebugInfo,
        create_redundancy_debugger
    )
    DEBUG_AVAILABLE = True
    __all__.extend([
        'RedundancyDebugger',
        'DebugInfo',
        'create_redundancy_debugger'
    ])
except ImportError:
    DEBUG_AVAILABLE = False
    RedundancyDebugger = None
    DebugInfo = None
    create_redundancy_debugger = None

# Importar alertas
try:
    from .redundancy_alerts import (
        AlertLevel,
        Alert,
        AlertRule,
        RedundancyAlertSystem,
        create_redundancy_alert_system
    )
    ALERTS_AVAILABLE = True
    __all__.extend([
        'AlertLevel',
        'Alert',
        'AlertRule',
        'RedundancyAlertSystem',
        'create_redundancy_alert_system'
    ])
except ImportError:
    ALERTS_AVAILABLE = False
    AlertLevel = None
    Alert = None
    AlertRule = None
    RedundancyAlertSystem = None
    create_redundancy_alert_system = None

# Importar utilidades de testing
try:
    from .redundancy_test_utils import (
        RedundancyTestUtils,
        TestData,
        create_test_suppressor,
        run_quick_test
    )
    TEST_UTILS_AVAILABLE = True
    __all__.extend([
        'RedundancyTestUtils',
        'TestData',
        'create_test_suppressor',
        'run_quick_test'
    ])
except ImportError:
    TEST_UTILS_AVAILABLE = False
    RedundancyTestUtils = None
    TestData = None
    create_test_suppressor = None
    run_quick_test = None

# Importar sistema de plugins
try:
    from .redundancy_plugins import (
        PluginType,
        PluginMetadata,
        BasePlugin,
        SimilarityMethodPlugin,
        ClusteringAlgorithmPlugin,
        SelectionStrategyPlugin,
        PreprocessorPlugin,
        PostprocessorPlugin,
        PluginRegistry,
        get_plugin_registry,
        register_plugin,
        get_plugin,
        list_plugins,
        JaccardSimilarityPlugin
    )
    PLUGINS_AVAILABLE = True
    __all__.extend([
        'PluginType',
        'PluginMetadata',
        'BasePlugin',
        'SimilarityMethodPlugin',
        'ClusteringAlgorithmPlugin',
        'SelectionStrategyPlugin',
        'PreprocessorPlugin',
        'PostprocessorPlugin',
        'PluginRegistry',
        'get_plugin_registry',
        'register_plugin',
        'get_plugin',
        'list_plugins',
        'JaccardSimilarityPlugin'
    ])
except ImportError:
    PLUGINS_AVAILABLE = False
    PluginType = None
    PluginMetadata = None
    BasePlugin = None
    SimilarityMethodPlugin = None
    ClusteringAlgorithmPlugin = None
    SelectionStrategyPlugin = None
    PreprocessorPlugin = None
    PostprocessorPlugin = None
    PluginRegistry = None
    get_plugin_registry = None
    register_plugin = None
    get_plugin = None
    list_plugins = None
    JaccardSimilarityPlugin = None

# Importar sistema de serialización
try:
    from .redundancy_serialization import (
        RedundancySerializer,
        SerializationMetadata,
        create_serializer
    )
    SERIALIZATION_AVAILABLE = True
    __all__.extend([
        'RedundancySerializer',
        'SerializationMetadata',
        'create_serializer'
    ])
except ImportError:
    SERIALIZATION_AVAILABLE = False
    RedundancySerializer = None
    SerializationMetadata = None
    create_serializer = None


def estimate_optimal_threshold(
    sample_embeddings: Any,
    target_reduction_rate: float = 0.3,
    method: str = "cosine",
    tolerance: float = 0.05
) -> float:
    """
    Estima el umbral óptimo para lograr una tasa de reducción objetivo.
    
    Args:
        sample_embeddings: Tensor de embeddings de muestra [batch, hidden_dim]
        target_reduction_rate: Tasa de reducción objetivo (0.0 - 1.0)
        method: Método de similitud a usar
        tolerance: Tolerancia para la tasa de reducción objetivo
    
    Returns:
        Umbral estimado óptimo
    
    Raises:
        ValueError: Si los parámetros no son válidos
    
    Examples:
        >>> import torch
        >>> embeddings = torch.randn(100, 512)
        >>> threshold = estimate_optimal_threshold(embeddings, target_reduction_rate=0.3)
        >>> print(f"Umbral óptimo: {threshold:.3f}")
    """
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch no disponible, usando umbral por defecto")
        return 0.85
    
    if not UTILS_AVAILABLE:
        logger.warning("Utils no disponibles, usando umbral por defecto")
        return 0.85
    
    if not (0.0 <= target_reduction_rate <= 1.0):
        raise ValueError(f"target_reduction_rate debe estar en [0.0, 1.0], recibido: {target_reduction_rate}")
    if not (0.0 < tolerance <= 1.0):
        raise ValueError(f"tolerance debe estar en (0.0, 1.0], recibido: {tolerance}")
    valid_methods = ["cosine", "euclidean", "dot", "semantic"]
    if method not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    
    try:
        if not isinstance(sample_embeddings, torch.Tensor):
            raise ValueError(f"sample_embeddings debe ser torch.Tensor, recibido: {type(sample_embeddings)}")
        
        if sample_embeddings.dim() not in [2, 3]:
            raise ValueError(f"sample_embeddings debe ser 2D o 3D, recibido: {sample_embeddings.dim()}D")
        
        if sample_embeddings.size(0) < 10:
            logger.warning("Muestra muy pequeña, usando umbral por defecto")
            return 0.85
        
        if optimize_threshold is not None:
            try:
                result = optimize_threshold(
                    sample_embeddings,
                    target_reduction_rate=target_reduction_rate,
                    method=method
                )
                if isinstance(result, dict) and 'optimal_threshold' in result:
                    return result['optimal_threshold']
            except TypeError:
                pass
        
        thresholds = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        best_threshold = 0.85
        best_diff = float('inf')
        
        for threshold in thresholds:
            try:
                _, stats = batch_deduplicate(sample_embeddings, threshold=threshold, method=method)
                reduction_rate = stats.get('reduction_rate', 0.0)
                diff = abs(reduction_rate - target_reduction_rate)
                
                if diff < best_diff:
                    best_diff = diff
                    best_threshold = threshold
                
                if diff <= tolerance:
                    return threshold
            except Exception:
                continue
        
        return best_threshold
    
    except Exception as e:
        logger.warning(f"Error estimando umbral óptimo: {e}, usando umbral por defecto")
        return 0.85



