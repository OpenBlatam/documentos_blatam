#!/usr/bin/env python3
"""
Memory Module - Sistemas de Memoria Avanzados
==============================================

Este módulo contiene implementaciones de sistemas de memoria avanzados
basados en papers de investigación.

Módulos disponibles:
- paper_2506_15841v2: Sistema de memoria episódica y semántica (MEJORADO)
- paper_2509_04439v1: Sistema de memoria jerárquica key-value
- chat_memory_integration: Integración con sistema de chat
- memory_analytics: Analytics, optimización y exportación

Características principales:
- ✅ Persistencia automática
- ✅ Sistema de tags y categorías
- ✅ Priorización de episodios
- ✅ Compresión de memoria
- ✅ Búsqueda semántica mejorada
- ✅ Caché inteligente
- ✅ Analytics avanzados
- ✅ Integración con chat
"""

from typing import TYPE_CHECKING, Optional, Any, Dict

if TYPE_CHECKING:
    pass

try:
    from core.error_handling import safe_execute
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            from core.error_handling import _fallback_safe_execute
            return _fallback_safe_execute(func, default_value, log_errors, *args, **kwargs)
        except ImportError:
            try:
                return func(*args, **kwargs), None
            except Exception as e:
                if log_errors:
                    logger.error(f"Error en {func.__name__}: {e}")
                return default_value, e

# Importar configuraciones
try:
    from .paper_2506_15841v2 import (
        Paper2506_15841v2Config,
        Paper2506_15841v2_MemorySystem,
        TruthGPT_Paper2506_15841v2_Integration
    )
    PAPER_2506_AVAILABLE = True
except ImportError:
    Paper2506_15841v2Config = None
    Paper2506_15841v2_MemorySystem = None
    TruthGPT_Paper2506_15841v2_Integration = None
    PAPER_2506_AVAILABLE = False

try:
    from .paper_2509_04439v1 import (
        Paper2509_04439v1Config,
        Paper2509_04439v1_MemorySystem,
        TruthGPT_Paper2509_04439v1_Integration
    )
    PAPER_2509_AVAILABLE = True
except ImportError:
    Paper2509_04439v1Config = None
    Paper2509_04439v1_MemorySystem = None
    TruthGPT_Paper2509_04439v1_Integration = None
    PAPER_2509_AVAILABLE = False

# Importar integración con chat
try:
    from .chat_memory_integration import ChatMemoryIntegration
    CHAT_INTEGRATION_AVAILABLE = True
except ImportError:
    ChatMemoryIntegration = None
    CHAT_INTEGRATION_AVAILABLE = False

try:
    from .memory_integration import (
        MemoryWithBestTechniques,
        create_memory_with_best_techniques
    )
    BEST_INTEGRATION_AVAILABLE = True
except ImportError:
    BEST_INTEGRATION_AVAILABLE = False
    MemoryWithBestTechniques = None
    create_memory_with_best_techniques = None

# Importar analytics
try:
    from .memory_analytics import (
        MemoryAnalytics,
        MemoryOptimizer,
        MemoryExporter
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    MemoryAnalytics = None
    MemoryOptimizer = None
    MemoryExporter = None
    ANALYTICS_AVAILABLE = False

__all__ = [
    # Configuraciones
    'Paper2506_15841v2Config',
    'Paper2509_04439v1Config',
    # Sistemas de memoria
    'Paper2506_15841v2_MemorySystem',
    'Paper2509_04439v1_MemorySystem',
    # Integraciones
    'TruthGPT_Paper2506_15841v2_Integration',
    'TruthGPT_Paper2509_04439v1_Integration',
    # Integración con chat
    'ChatMemoryIntegration',
    # Integración con Best Techniques
    'MemoryWithBestTechniques',
    'create_memory_with_best_techniques',
    # Analytics y optimización
    'MemoryAnalytics',
    'MemoryOptimizer',
    'MemoryExporter',
    # Utilidades
    'create_memory_system',
    'create_chat_with_memory',
    'get_available_modules',
]

# Importar utilidades
try:
    from .memory_utils import (
        create_episode_from_text,
        batch_store_episodes,
        compare_episodes,
        find_similar_episodes,
        export_memory_to_dict,
        import_memory_from_dict,
        merge_memory_systems,
        get_memory_health_report
    )
    UTILS_AVAILABLE = True
    __all__.extend([
        'create_episode_from_text',
        'batch_store_episodes',
        'compare_episodes',
        'find_similar_episodes',
        'export_memory_to_dict',
        'import_memory_from_dict',
        'merge_memory_systems',
        'get_memory_health_report'
    ])
except ImportError:
    UTILS_AVAILABLE = False

__version__ = '2.0.0'


def create_memory_system(
    paper_type: str = "2506_15841v2",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear sistemas de memoria.
    
    Args:
        paper_type: Tipo de paper ("2506_15841v2" o "2509_04439v1")
        **config_kwargs: Argumentos de configuración
    
    Returns:
        Instancia del sistema de memoria o None si hay error
    
    Raises:
        ValueError: Si paper_type no es válido
    
    Examples:
        >>> memory = create_memory_system("2506_15841v2", memory_dim=512)
        >>> memory = create_memory_system("2509_04439v1", memory_dim=256)
    """
    if not isinstance(paper_type, str) or not paper_type.strip():
        raise ValueError(f"paper_type debe ser una cadena no vacía, recibido: {paper_type}")
    
    valid_paper_types = ["2506_15841v2", "2509_04439v1"]
    if paper_type not in valid_paper_types:
        raise ValueError(f"paper_type debe ser uno de {valid_paper_types}, recibido: {paper_type}")
    
    try:
        if paper_type == "2506_15841v2" and PAPER_2506_AVAILABLE:
            config = Paper2506_15841v2Config(**config_kwargs)
            return Paper2506_15841v2_MemorySystem(config)
        
        elif paper_type == "2509_04439v1" and PAPER_2509_AVAILABLE:
            config = Paper2509_04439v1Config(**config_kwargs)
            return Paper2509_04439v1_MemorySystem(config)
        
        else:
            logger.error(f"Paper type no disponible: {paper_type} (available_2506={PAPER_2506_AVAILABLE}, available_2509={PAPER_2509_AVAILABLE})")
            return None
    except Exception as e:
        logger.error(f"Error creando sistema de memoria (paper_type={paper_type}): {e}", exc_info=True)
        return None


def create_chat_with_memory(
    chat_provider: str = "openai",
    memory_paper: str = "2506_15841v2",
    **kwargs
) -> Optional[Any]:
    """
    Factory function para crear chat engine con memoria integrada.
    
    Args:
        chat_provider: Proveedor de chat ("openai", "anthropic", "local")
        memory_paper: Tipo de paper de memoria ("2506_15841v2" o "2509_04439v1")
        **kwargs: Argumentos adicionales para chat y memoria
    
    Returns:
        Instancia de ChatMemoryIntegration o None si hay error
    
    Raises:
        ValueError: Si los parámetros no son válidos
    
    Examples:
        >>> chat = create_chat_with_memory(
        ...     chat_provider="openai",
        ...     memory_paper="2506_15841v2",
        ...     memory_dim=512
        ... )
    """
    valid_providers = ["openai", "anthropic", "local"]
    if chat_provider not in valid_providers:
        raise ValueError(f"chat_provider debe ser uno de {valid_providers}, recibido: {chat_provider}")
    
    valid_memory_papers = ["2506_15841v2", "2509_04439v1"]
    if memory_paper not in valid_memory_papers:
        raise ValueError(f"memory_paper debe ser uno de {valid_memory_papers}, recibido: {memory_paper}")
    
    try:
        if not CHAT_INTEGRATION_AVAILABLE:
            logger.error("ChatMemoryIntegration no disponible")
            return None
        
        from core.chat_engine import ChatEngine
        
        chat_kwargs = {
            'provider': chat_provider,
            'model': kwargs.pop('model', None),
            'api_key': kwargs.pop('api_key', None),
            'system_prompt': kwargs.pop('system_prompt', None),
            'max_history_tokens': kwargs.pop('max_history_tokens', 4000),
            'temperature': kwargs.pop('temperature', 0.7),
            'max_tokens': kwargs.pop('max_tokens', 2000)
        }
        
        chat_engine = ChatEngine(**chat_kwargs)
        
        if memory_paper == "2506_15841v2" and PAPER_2506_AVAILABLE:
            memory_config = Paper2506_15841v2Config(**kwargs)
        elif memory_paper == "2509_04439v1" and PAPER_2509_AVAILABLE:
            memory_config = Paper2509_04439v1Config(**kwargs)
        else:
            logger.error(
                f"Paper de memoria no disponible: {memory_paper} "
                f"(available_2506={PAPER_2506_AVAILABLE}, available_2509={PAPER_2509_AVAILABLE})"
            )
            return None
        
        return ChatMemoryIntegration(chat_engine, memory_config)
    except Exception as e:
        logger.error(
            f"Error creando chat con memoria (chat_provider={chat_provider}, memory_paper={memory_paper}): {e}",
            exc_info=True
        )
        return None


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene la lista de módulos y utilidades disponibles.
    
    Returns:
        Diccionario con módulos y su disponibilidad
    
    Examples:
        >>> available = get_available_modules()
        >>> print(available)
        {'paper_2506_15841v2': True, 'paper_2509_04439v1': True, 'chat_integration': True, 'analytics': True, 'utils': True}
    """
    return {
        'paper_2506_15841v2': PAPER_2506_AVAILABLE,
        'paper_2509_04439v1': PAPER_2509_AVAILABLE,
        'chat_integration': CHAT_INTEGRATION_AVAILABLE,
        'analytics': ANALYTICS_AVAILABLE,
        'utils': UTILS_AVAILABLE,
    }
