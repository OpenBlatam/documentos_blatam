#!/usr/bin/env python3
"""
Best Techniques Papers Module
===============================

Este módulo contiene implementaciones de las mejores técnicas de varios papers
de investigación para mejorar el rendimiento de modelos.

Papers incluidos:
- 2506.10848v2: Adaptive Layer Normalization and Gated Attention
- 2510.04871v1: Ensemble Attention with Weighted Combination

Características principales:
- ✅ Adaptive Layer Normalization
- ✅ Gated Attention
- ✅ Ensemble Attention
- ✅ Factory functions para creación fácil
- ✅ Recomendaciones automáticas
"""

from typing import TYPE_CHECKING, Optional, Any, Dict

if TYPE_CHECKING:
    pass

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

try:
    from .paper_2506_10848v2 import (
        Paper2506_10848v2Config,
        AdaptiveLayerNorm,
        GatedAttention,
        Paper2506_10848v2_BestTechniques,
        TruthGPT_Paper2506_10848v2_Integration
    )
    PAPER_2506_10848_AVAILABLE = True
except ImportError:
    Paper2506_10848v2Config = None
    AdaptiveLayerNorm = None
    GatedAttention = None
    Paper2506_10848v2_BestTechniques = None
    TruthGPT_Paper2506_10848v2_Integration = None
    PAPER_2506_10848_AVAILABLE = False

try:
    from .paper_2510_04871v1 import (
        Paper2510_04871v1Config,
        EnsembleAttention,
        Paper2510_04871v1_BestTechniques,
        TruthGPT_Paper2510_04871v1_Integration
    )
    PAPER_2510_04871_AVAILABLE = True
except ImportError:
    Paper2510_04871v1Config = None
    EnsembleAttention = None
    Paper2510_04871v1_BestTechniques = None
    TruthGPT_Paper2510_04871v1_Integration = None
    PAPER_2510_04871_AVAILABLE = False

try:
    from .compare_papers import (
        PaperComparator,
        ComparisonResult
    )
    COMPARISON_AVAILABLE = True
except ImportError:
    PaperComparator = None
    ComparisonResult = None
    COMPARISON_AVAILABLE = False

__all__ = [
    # Paper 2506.10848v2
    'Paper2506_10848v2Config',
    'AdaptiveLayerNorm',
    'GatedAttention',
    'Paper2506_10848v2_BestTechniques',
    'TruthGPT_Paper2506_10848v2_Integration',
    # Paper 2510.04871v1
    'Paper2510_04871v1Config',
    'EnsembleAttention',
    'Paper2510_04871v1_BestTechniques',
    'TruthGPT_Paper2510_04871v1_Integration',
    # Comparison
    'PaperComparator',
    'ComparisonResult',
    # Utilidades
    'create_best_techniques_module',
    'get_available_modules',
    'recommend_best_technique',
]

__version__ = '2.0.0'


def create_best_techniques_module(
    paper_type: str = "2506_10848v2",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear módulos de mejores técnicas.
    
    Args:
        paper_type: Tipo de paper ("2506_10848v2" o "2510_04871v1")
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Instancia del módulo o None si hay error
    
    Raises:
        ValueError: Si paper_type no es válido
    
    Examples:
        >>> module = create_best_techniques_module("2506_10848v2", hidden_dim=512)
        >>> module = create_best_techniques_module("2510_04871v1", hidden_dim=768)
    """
    if not isinstance(paper_type, str) or not paper_type.strip():
        raise ValueError(f"paper_type debe ser una cadena no vacía, recibido: {paper_type}")
    
    paper_type = paper_type.lower()
    valid_types = ["2506_10848v2", "2510_04871v1"]
    
    if paper_type not in valid_types:
        raise ValueError(f"paper_type debe ser uno de {valid_types}, recibido: {paper_type}")
    
    try:
        if paper_type == "2506_10848v2" and PAPER_2506_10848_AVAILABLE:
            config = Paper2506_10848v2Config(**config_kwargs)
            return Paper2506_10848v2_BestTechniques(config)
        
        elif paper_type == "2510_04871v1" and PAPER_2510_04871_AVAILABLE:
            config = Paper2510_04871v1Config(**config_kwargs)
            return Paper2510_04871v1_BestTechniques(config)
        
        else:
            logger.error(f"Paper type no disponible: {paper_type}")
            return None
    except Exception as e:
        logger.error(f"Error creando módulo de mejores técnicas (paper_type={paper_type}): {e}", exc_info=True)
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
        'paper_2506_10848v2': PAPER_2506_10848_AVAILABLE,
        'paper_2510_04871v1': PAPER_2510_04871_AVAILABLE,
    }


def recommend_best_technique(
    use_case: str = "general",
    priority: str = "balanced"
) -> Optional[str]:
    """
    Recomienda la mejor técnica según el caso de uso.
    
    Args:
        use_case: Caso de uso. Opciones:
            - "general": Uso general
            - "attention": Mejora de atención
            - "normalization": Mejora de normalización
            - "ensemble": Ensemble de técnicas
        priority: Prioridad ("balanced", "performance", "quality")
    
    Returns:
        Nombre del paper recomendado o None
    
    Raises:
        ValueError: Si los parámetros no son válidos
    
    Examples:
        >>> technique = recommend_best_technique("attention")
        >>> technique = recommend_best_technique("normalization", priority="performance")
    """
    valid_use_cases = ["general", "attention", "normalization", "ensemble"]
    if use_case not in valid_use_cases:
        raise ValueError(f"use_case debe ser uno de {valid_use_cases}, recibido: {use_case}")
    
    valid_priorities = ["balanced", "performance", "quality"]
    if priority not in valid_priorities:
        raise ValueError(f"priority debe ser uno de {valid_priorities}, recibido: {priority}")
    available = get_available_modules()
    
    if use_case == "attention" or use_case == "ensemble":
        if available.get('paper_2510_04871v1'):
            return '2510_04871v1'
        elif available.get('paper_2506_10848v2'):
            return '2506_10848v2'
    
    elif use_case == "normalization":
        if available.get('paper_2506_10848v2'):
            return '2506_10848v2'
    
    elif use_case == "general":
        if priority == "performance" and available.get('paper_2506_10848v2'):
            return '2506_10848v2'
        elif available.get('paper_2510_04871v1'):
            return '2510_04871v1'
        elif available.get('paper_2506_10848v2'):
            return '2506_10848v2'
    
    for paper in ['2506_10848v2', '2510_04871v1']:
        key = f'paper_{paper}'
        if available.get(key):
            return paper
    
    return None

