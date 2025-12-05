#!/usr/bin/env python3
"""
Code Module - Optimización y Análisis de Código
================================================

Este módulo contiene implementaciones para optimización y análisis de código
basadas en papers de investigación.

Módulos disponibles:
- paper_2508_06471: Code Structure Encoder y Code Optimizer

Características principales:
- ✅ Code Structure Encoding
- ✅ Code Optimization
- ✅ Análisis de estructura de código
- ✅ Factory functions para creación fácil
"""

from typing import TYPE_CHECKING, Optional, Any, Dict

if TYPE_CHECKING:
    pass

try:
    from core.utils import setup_logger
    from core.error_handling import safe_execute
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            if log_errors:
                logger.error(f"Error en {func.__name__}: {e}")
            return default_value, e

try:
    from .paper_2508_06471 import (
        Paper2508_06471Config,
        CodeStructureEncoder,
        Paper2508_06471_CodeOptimizer,
        TruthGPT_Paper2508_06471_Integration
    )
    PAPER_2508_06471_AVAILABLE = True
except ImportError:
    Paper2508_06471Config = None
    CodeStructureEncoder = None
    Paper2508_06471_CodeOptimizer = None
    TruthGPT_Paper2508_06471_Integration = None
    PAPER_2508_06471_AVAILABLE = False

__all__ = [
    # Configuraciones
    'Paper2508_06471Config',
    # Componentes
    'CodeStructureEncoder',
    # Módulos
    'Paper2508_06471_CodeOptimizer',
    'TruthGPT_Paper2508_06471_Integration',
    # Utilidades
    'create_code_module',
    'get_available_modules',
    'recommend_code_method',
]

__version__ = '2.0.0'


def create_code_module(
    module_type: str = "code_optimizer",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear módulos de código.
    
    Args:
        module_type: Tipo de módulo:
            - "code_optimizer": Optimizador de código
            - "code_encoder": Encoder de estructura de código
            - "integration": Integración completa
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Instancia del módulo o None si hay error
    
    Raises:
        ValueError: Si module_type no es válido
    
    Examples:
        >>> module = create_code_module("code_optimizer", hidden_dim=512)
        >>> encoder = create_code_module("code_encoder", hidden_dim=256)
    """
    if not isinstance(module_type, str) or not module_type.strip():
        raise ValueError(f"module_type debe ser una cadena no vacía, recibido: {module_type}")
    
    module_type = module_type.lower()
    valid_types = ["code_optimizer", "code_encoder", "integration"]
    
    if module_type not in valid_types:
        raise ValueError(f"module_type debe ser uno de {valid_types}, recibido: {module_type}")
    
    if not PAPER_2508_06471_AVAILABLE:
        logger.error("Paper 2508.06471 no disponible")
        return None
    
    def _create_module():
        if module_type == "code_optimizer":
            config = Paper2508_06471Config(**config_kwargs)
            return Paper2508_06471_CodeOptimizer(config)
        
        elif module_type == "code_encoder":
            config = Paper2508_06471Config(**config_kwargs)
            return CodeStructureEncoder(config)
        
        elif module_type == "integration":
            config = Paper2508_06471Config(**config_kwargs)
            return TruthGPT_Paper2508_06471_Integration(config)
        
        else:
            logger.error(
                "Tipo de módulo no disponible",
                module_type=module_type,
                valid_types=valid_types
            )
            return None
    
    result, error = safe_execute(_create_module, default_value=None, log_errors=True)
    
    if error:
        logger.error(
            "Error creando módulo de código",
            module_type=module_type,
            error=str(error)
        )
    
    return result


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
        'paper_2508_06471': PAPER_2508_06471_AVAILABLE,
    }


def recommend_code_method(
    use_case: str = "optimization",
    task: str = "general"
) -> Optional[str]:
    """
    Recomienda un método de código según el caso de uso.
    
    Args:
        use_case: Caso de uso ("optimization", "encoding", "analysis")
        task: Tarea específica ("general", "refactoring", "structure_analysis")
    
    Returns:
        Nombre del método recomendado o None
    
    Raises:
        ValueError: Si los parámetros no son válidos
    
    Examples:
        >>> method = recommend_code_method("optimization")
        >>> method = recommend_code_method("encoding", task="structure_analysis")
    """
    valid_use_cases = ["optimization", "encoding", "analysis"]
    if use_case not in valid_use_cases:
        raise ValueError(f"use_case debe ser uno de {valid_use_cases}, recibido: {use_case}")
    
    valid_tasks = ["general", "refactoring", "structure_analysis"]
    if task not in valid_tasks:
        raise ValueError(f"task debe ser uno de {valid_tasks}, recibido: {task}")
    
    available = get_available_modules()
    
    if not available.get('paper_2508_06471'):
        return None
    
    if use_case == "optimization":
        return 'code_optimizer'
    
    elif use_case == "encoding" or task == "structure_analysis":
        return 'code_encoder'
    
    elif use_case == "analysis":
        return 'integration'
    
    return 'code_optimizer'

