#!/usr/bin/env python3
"""
Model Data Collection System
============================

Sistema para recopilar datos de modelos y conectarse a las mejores
fuentes de información disponibles (registry, papers, benchmarks, etc.).

Características principales:
- ✅ Recolección de datos de modelos
- ✅ Conexión a fuentes de información
- ✅ Agregación y análisis
- ✅ Exportación a diferentes formatos
- ✅ Integración con experimentos
- ✅ Persistencia de datos
- ✅ Procesamiento paralelo
- ✅ Factory functions para creación fácil
"""

from typing import TYPE_CHECKING, Optional, Any, Dict
from pathlib import Path

if TYPE_CHECKING:
    from .model_data_manager import ModelDataManager
    from .data_collector import ModelDataCollector, ModelData
    from .info_connector import InfoConnector
    from .data_aggregator import DataAggregator, AggregatedData
    from .data_exporter import DataExporter
    from .experiment_integration import ExperimentIntegration
    from .data_persistence import DataPersistence
    from .parallel_processor import ParallelProcessor

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

try:
    from .model_data_manager import ModelDataManager
    MODEL_DATA_MANAGER_AVAILABLE = True
except ImportError:
    ModelDataManager = None
    MODEL_DATA_MANAGER_AVAILABLE = False

try:
    from .data_collector import ModelDataCollector, ModelData
    DATA_COLLECTOR_AVAILABLE = True
except ImportError:
    ModelDataCollector = None
    ModelData = None
    DATA_COLLECTOR_AVAILABLE = False

try:
    from .info_connector import InfoConnector
    INFO_CONNECTOR_AVAILABLE = True
except ImportError:
    InfoConnector = None
    INFO_CONNECTOR_AVAILABLE = False

try:
    from .data_aggregator import DataAggregator, AggregatedData
    DATA_AGGREGATOR_AVAILABLE = True
except ImportError:
    DataAggregator = None
    AggregatedData = None
    DATA_AGGREGATOR_AVAILABLE = False

try:
    from .data_exporter import DataExporter
    DATA_EXPORTER_AVAILABLE = True
except ImportError:
    DataExporter = None
    DATA_EXPORTER_AVAILABLE = False

try:
    from .experiment_integration import ExperimentIntegration
    EXPERIMENT_INTEGRATION_AVAILABLE = True
except ImportError:
    ExperimentIntegration = None
    EXPERIMENT_INTEGRATION_AVAILABLE = False

try:
    from .data_persistence import DataPersistence
    DATA_PERSISTENCE_AVAILABLE = True
except ImportError:
    DataPersistence = None
    DATA_PERSISTENCE_AVAILABLE = False

try:
    from .parallel_processor import ParallelProcessor
    PARALLEL_PROCESSOR_AVAILABLE = True
except ImportError:
    ParallelProcessor = None
    PARALLEL_PROCESSOR_AVAILABLE = False

try:
    from .dependencies import check_optional_dependencies
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    check_optional_dependencies = None
    DEPENDENCIES_AVAILABLE = False

__all__ = [
    # Clases principales
    'ModelDataManager',
    'ModelDataCollector',
    'ModelData',
    'InfoConnector',
    'DataAggregator',
    'AggregatedData',
    'DataExporter',
    'ExperimentIntegration',
    'DataPersistence',
    'ParallelProcessor',
    # Utilidades
    'create_model_data_manager',
    'create_data_collector',
    'get_available_modules',
    # Dependencias
    'check_optional_dependencies',
]

__version__ = '2.0.0'


def create_model_data_manager(
    base_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    include_benchmarks: bool = True,
    enable_persistence: bool = True,
    enable_experiment_tracking: bool = False,
    enable_parallel: bool = True,
    max_workers: Optional[int] = None,
    **kwargs
) -> Optional[Any]:
    """
    Factory function para crear un ModelDataManager.
    
    Args:
        base_dir: Directorio base para operaciones
        output_dir: Directorio de salida para exportaciones
        include_benchmarks: Incluir datos de benchmarks
        enable_persistence: Habilitar persistencia de datos
        enable_experiment_tracking: Habilitar tracking de experimentos
        enable_parallel: Habilitar procesamiento paralelo
        max_workers: Número máximo de workers para procesamiento paralelo
        **kwargs: Argumentos adicionales
    
    Returns:
        Instancia de ModelDataManager o None si hay error
    
    Raises:
        ValueError: Si max_workers, base_dir o output_dir no son válidos
    
    Examples:
        >>> manager = create_model_data_manager(
        ...     base_dir=Path("./data"),
        ...     enable_persistence=True
        ... )
    """
    from core.error_handling import ValidationError
    from .constants import MIN_WORKERS, MAX_WORKERS_LIMIT
    
    if max_workers is not None:
        if not isinstance(max_workers, int) or max_workers < MIN_WORKERS:
            raise ValidationError(f"max_workers debe ser >= {MIN_WORKERS}, recibido: {max_workers}")
        if max_workers > MAX_WORKERS_LIMIT:
            raise ValidationError(f"max_workers debe ser <= {MAX_WORKERS_LIMIT}, recibido: {max_workers}")
    
    if base_dir is not None and not isinstance(base_dir, Path):
        raise ValidationError(f"base_dir debe ser un Path, recibido: {type(base_dir)}")
    
    if output_dir is not None and not isinstance(output_dir, Path):
        raise ValidationError(f"output_dir debe ser un Path, recibido: {type(output_dir)}")
    
    if not MODEL_DATA_MANAGER_AVAILABLE:
        logger.error("ModelDataManager no disponible")
        return None
    
    try:
        return ModelDataManager(
            base_dir=base_dir,
            output_dir=output_dir,
            include_benchmarks=include_benchmarks,
            enable_persistence=enable_persistence,
            enable_experiment_tracking=enable_experiment_tracking,
            enable_parallel=enable_parallel,
            max_workers=max_workers,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error creando ModelDataManager: {e}", exc_info=True)
        return None


def create_data_collector(
    registry: Optional[Any] = None,
    **kwargs
) -> Optional[Any]:
    """
    Factory function para crear un ModelDataCollector.
    
    Args:
        registry: Registry opcional para papers
        **kwargs: Argumentos adicionales
    
    Returns:
        Instancia de ModelDataCollector o None si hay error
    
    Examples:
        >>> collector = create_data_collector()
    """
    if not DATA_COLLECTOR_AVAILABLE:
        logger.error("ModelDataCollector no disponible")
        return None
    
    try:
        return ModelDataCollector(registry=registry, **kwargs)
    except Exception as e:
        logger.error(f"Error creando ModelDataCollector: {e}", exc_info=True)
        return None


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene la lista de módulos disponibles.
    
    Returns:
        Diccionario con módulos y su disponibilidad
    
    Examples:
        >>> available = get_available_modules()
        >>> print(available)
    """
    return {
        'model_data_manager': MODEL_DATA_MANAGER_AVAILABLE,
        'data_collector': DATA_COLLECTOR_AVAILABLE,
        'info_connector': INFO_CONNECTOR_AVAILABLE,
        'data_aggregator': DATA_AGGREGATOR_AVAILABLE,
        'data_exporter': DATA_EXPORTER_AVAILABLE,
        'experiment_integration': EXPERIMENT_INTEGRATION_AVAILABLE,
        'data_persistence': DATA_PERSISTENCE_AVAILABLE,
        'parallel_processor': PARALLEL_PROCESSOR_AVAILABLE,
    }

