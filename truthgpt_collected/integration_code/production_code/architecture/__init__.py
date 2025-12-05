#!/usr/bin/env python3
"""
Architecture Module - Arquitecturas de Modelos Avanzadas
========================================================

Este módulo contiene implementaciones de arquitecturas de modelos avanzadas
basadas en papers de investigación.

Módulos disponibles:
- paper_deepseek_v3: Arquitectura DeepSeek V3 con Multi-Head Latent Attention y MoE

Características principales:
- ✅ Multi-Head Latent Attention
- ✅ Mixture of Experts (MoE)
- ✅ Arquitecturas escalables
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
    from .paper_deepseek_v3 import (
        DeepSeekV3Config,
        MultiHeadLatentAttention,
        MixtureOfExperts,
        DeepSeekV3Module
    )
    DEEPSEEK_V3_AVAILABLE = True
except ImportError:
    DeepSeekV3Config = None
    MultiHeadLatentAttention = None
    MixtureOfExperts = None
    DeepSeekV3Module = None
    DEEPSEEK_V3_AVAILABLE = False

__all__ = [
    # Configuraciones
    'DeepSeekV3Config',
    # Componentes
    'MultiHeadLatentAttention',
    'MixtureOfExperts',
    # Módulos
    'DeepSeekV3Module',
    # Utilidades
    'create_architecture_module',
    'get_available_modules',
    'recommend_architecture',
]

__version__ = '2.0.0'


def create_architecture_module(
    architecture_type: str = "deepseek_v3",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear módulos de arquitectura.
    
    Args:
        architecture_type: Tipo de arquitectura ("deepseek_v3")
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Instancia del módulo de arquitectura o None si hay error
    
    Raises:
        ValueError: Si architecture_type no es válido
    
    Examples:
        >>> module = create_architecture_module("deepseek_v3", hidden_dim=2048)
        >>> module = create_architecture_module("deepseek_v3", num_experts=8)
    """
    if not isinstance(architecture_type, str) or not architecture_type.strip():
        raise ValueError(f"architecture_type debe ser una cadena no vacía, recibido: {architecture_type}")
    
    architecture_type = architecture_type.lower()
    valid_types = ["deepseek_v3"]
    
    if architecture_type not in valid_types:
        raise ValueError(f"architecture_type debe ser uno de {valid_types}, recibido: {architecture_type}")
    
    def _create_module():
        if architecture_type == "deepseek_v3" and DEEPSEEK_V3_AVAILABLE:
            config = DeepSeekV3Config(**config_kwargs)
            return DeepSeekV3Module(config)
        
        else:
            available = get_available_modules()
            logger.error(
                "Arquitectura no disponible",
                architecture_type=architecture_type,
                available_modules=available
            )
            return None
    
    result, error = safe_execute(_create_module, default_value=None, log_errors=True)
    
    if error:
        logger.error(
            "Error creando módulo de arquitectura",
            architecture_type=architecture_type,
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
        'deepseek_v3': DEEPSEEK_V3_AVAILABLE,
    }


def recommend_architecture(
    use_case: str = "general",
    scale: str = "medium"
) -> Optional[str]:
    """
    Recomienda una arquitectura según el caso de uso.
    
    Args:
        use_case: Caso de uso ("general", "large_scale", "efficient")
        scale: Escala ("small", "medium", "large")
    
    Returns:
        Nombre de la arquitectura recomendada o None
    
    Raises:
        ValueError: Si los parámetros no son válidos
    
    Examples:
        >>> arch = recommend_architecture("large_scale", scale="large")
        >>> arch = recommend_architecture("efficient", scale="small")
    """
    valid_use_cases = ["general", "large_scale", "efficient"]
    if use_case not in valid_use_cases:
        raise ValueError(f"use_case debe ser uno de {valid_use_cases}, recibido: {use_case}")
    
    valid_scales = ["small", "medium", "large"]
    if scale not in valid_scales:
        raise ValueError(f"scale debe ser uno de {valid_scales}, recibido: {scale}")
    available = get_available_modules()
    
    if use_case == "large_scale" or scale == "large":
        if available.get('deepseek_v3'):
            return 'deepseek_v3'
    
    elif use_case == "efficient" or scale == "small":
        if available.get('deepseek_v3'):
            return 'deepseek_v3'
    
    elif use_case == "general":
        if available.get('deepseek_v3'):
            return 'deepseek_v3'
    
    for arch in ['deepseek_v3']:
        if available.get(arch):
            return arch
    
    return None

