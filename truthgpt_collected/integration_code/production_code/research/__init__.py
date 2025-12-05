#!/usr/bin/env python3
"""
Research Module - Implementaciones de Papers de Investigación
==============================================================

Este módulo contiene implementaciones de papers de investigación avanzados
para razonamiento, contexto largo, y técnicas experimentales.

Características principales:
- ✅ Múltiples papers de investigación implementados
- ✅ Técnicas de razonamiento avanzadas
- ✅ Manejo de contexto largo
- ✅ Factory functions para creación fácil
- ✅ Funciones de utilidad para descubrimiento

Nota: Este módulo contiene implementaciones experimentales y de investigación.
Para producción, considere usar los módulos especializados (inference, memory, etc.).
"""

from typing import TYPE_CHECKING, Optional, Any, Dict, List

if TYPE_CHECKING:
    from typing import Any

try:
    from core.utils import setup_logger
    from core.error_handling import safe_execute
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        from core.error_handling import _fallback_safe_execute
        return _fallback_safe_execute(func, default_value, log_errors, *args, **kwargs)

__all__ = [
    'get_available_papers',
    'list_research_papers',
    'get_paper_info',
]

__version__ = '2.0.0'


def get_available_papers() -> Dict[str, bool]:
    """
    Obtiene la lista de papers disponibles en el módulo research.
    
    Returns:
        Diccionario con papers y su disponibilidad
    
    Examples:
        >>> available = get_available_papers()
        >>> print(available)
    """
    papers = [
        'paper_2505_05315v2',
        'paper_2505_11140v1',
        'paper_2510_26788v1',
        'paper_absolute_zero',
        'paper_adagrope',
        'paper_adaptive_got',
        'paper_advanced_math_benchmark',
        'paper_am_thinking',
        'paper_beyond_cot',
        'paper_blackbox_distillation',
        'paper_cepe',
        'paper_crft',
        'paper_demystifying_got',
        'paper_dynaact',
        'paper_efficient_long_context',
        'paper_enigmata',
        'paper_focusllm',
        'paper_forest_of_thought',
        'paper_graph_cot',
        'paper_hademif',
        'paper_hybrid_quantum_transformer',
        'paper_k2think',
        'paper_knot',
        'paper_ladder',
        'paper_lcot2tree',
        'paper_learning_dynamics',
        'paper_lift',
        'paper_llm_ensemble',
        'paper_longembed',
        'paper_longreward',
        'paper_longrope',
        'paper_longrope2',
        'paper_malto',
        'paper_memory_reasoning_disentangle',
        'paper_meta_cot',
        'paper_metacheckgpt',
        'paper_mixture_of_reasonings',
        'paper_planu',
        'paper_qwen3',
        'paper_rdolt',
        'paper_refind',
        'paper_rl_of_thoughts',
        'paper_seed1_5_vl',
        'paper_semantic_compression',
        'paper_sft_rl_generalization',
        'paper_solar',
        'paper_spoc',
        'paper_table_as_thought',
        'paper_ultimate_long_context',
    ]
    
    available = {}
    for paper in papers:
        def _import_paper():
            import importlib
            module_name = f'research.{paper}'
            importlib.import_module(module_name)
            return True
        
        result, error = safe_execute(_import_paper, default_value=False, log_errors=False)
        available[paper] = result if result else False
    
    return available


def list_research_papers() -> List[Dict[str, Any]]:
    """
    Lista todos los papers de investigación disponibles con información básica.
    
    Returns:
        Lista de diccionarios con información de cada paper
    
    Examples:
        >>> papers = list_research_papers()
        >>> for paper in papers:
        ...     print(f"{paper['name']}: {paper['available']}")
    """
    available = get_available_papers()
    papers = []
    
    for paper_name, is_available in available.items():
        papers.append({
            'name': paper_name,
            'available': is_available,
            'module': f'research.{paper_name}'
        })
    
    return papers


def get_paper_info(paper_name: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene información sobre un paper específico.
    
    Args:
        paper_name: Nombre del paper (sin el prefijo 'paper_')
    
    Returns:
        Diccionario con información del paper o None si no está disponible
    
    Raises:
        ValueError: Si paper_name no es una cadena válida
    
    Examples:
        >>> info = get_paper_info("longrope")
        >>> print(info)
    """
    if not isinstance(paper_name, str) or not paper_name.strip():
        raise ValueError(f"paper_name debe ser una cadena no vacía, recibido: {paper_name}")
    
    full_name = f'paper_{paper_name}' if not paper_name.startswith('paper_') else paper_name
    
    available = get_available_papers()
    if not available.get(full_name, False):
        return None
    
    def _get_paper_info():
        import importlib
        module = importlib.import_module(f'research.{full_name}')
        return {
            'name': full_name,
            'available': True,
            'module': module,
            'module_path': f'research.{full_name}'
        }
    
    result, error = safe_execute(_get_paper_info, default_value=None, log_errors=False)
    
    if error:
        return None
    
    return result

