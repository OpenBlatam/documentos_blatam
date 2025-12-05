#!/usr/bin/env python3
"""
Inference Module - Sistemas de Inferencia Optimizados
======================================================

Este módulo contiene implementaciones de sistemas de inferencia optimizados
basados en papers de investigación para acelerar la generación de LLMs.

Módulos disponibles:
- paper_vllm: vLLM con PagedAttention y continuous batching (~4.6k tokens/s)
- paper_tensorrt_llm: TensorRT-LLM con optimizaciones NVIDIA (~40k tokens/s)
- paper_kivi: Cuantización asimétrica 2-bit para KV cache
- paper_specache: Speculative prefetching para KV cache
- paper_layerkv: Gestión de KV cache por capas
- paper_cake_kv: CAKE KV cache management
- paper_cake_eviction: CAKE eviction strategies
- paper_deja_vu: Sparse attention y MLP optimizados
- paper_squeezed_attention: Compresión de atención
- paper_aspd: Adaptive Serial-Parallel Decoding
- paper_quest: Query-aware page selection
- paper_serverless_llm: Optimizaciones para serverless LLM
- paper_sparse_accelerate: Aceleración mediante sparse attention
- paper_anpd: Adaptive N-gram Parallel Decoding
- paper_faster_cascades: Cascadas más rápidas con speculative decoding

Características principales:
- ✅ Optimización de KV cache
- ✅ Continuous batching
- ✅ Speculative decoding
- ✅ Cuantización eficiente
- ✅ Sparse attention
- ✅ Paged attention
- ✅ Factory functions para creación fácil
- ✅ Selección automática de método óptimo
"""

from typing import TYPE_CHECKING, Optional, Dict, Any

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

# Importar configuraciones y módulos de vLLM
try:
    from .paper_vllm import VLLMConfig, VLLMModule
    VLLM_AVAILABLE = True
except ImportError:
    VLLMConfig = None
    VLLMModule = None
    VLLM_AVAILABLE = False

# Importar configuraciones y módulos de TensorRT-LLM
try:
    from .paper_tensorrt_llm import TensorRTLLMConfig, TensorRTLLMModule
    TENSORRT_LLM_AVAILABLE = True
except ImportError:
    TensorRTLLMConfig = None
    TensorRTLLMModule = None
    TENSORRT_LLM_AVAILABLE = False

# Importar configuraciones y módulos de KIVI
try:
    from .paper_kivi import KIVIConfig, KIVIModule
    KIVI_AVAILABLE = True
except ImportError:
    KIVIConfig = None
    KIVIModule = None
    KIVI_AVAILABLE = False

# Importar configuraciones y módulos de SpeCache
try:
    from .paper_specache import SpeCacheConfig, SpeCacheModule
    SPECACHE_AVAILABLE = True
except ImportError:
    SpeCacheConfig = None
    SpeCacheModule = None
    SPECACHE_AVAILABLE = False

# Importar configuraciones y módulos de LayerKV
try:
    from .paper_layerkv import LayerKVConfig, LayerKVModule
    LAYERKV_AVAILABLE = True
except ImportError:
    LayerKVConfig = None
    LayerKVModule = None
    LAYERKV_AVAILABLE = False

# Importar configuraciones y módulos de CAKE KV
try:
    from .paper_cake_kv import CakeKVConfig, CakeKVModule
    CAKE_KV_AVAILABLE = True
except ImportError:
    CakeKVConfig = None
    CakeKVModule = None
    CAKE_KV_AVAILABLE = False

# Importar configuraciones y módulos de CAKE Eviction
try:
    from .paper_cake_eviction import CakeEvictionConfig, CakeEvictionModule
    CAKE_EVICTION_AVAILABLE = True
except ImportError:
    CakeEvictionConfig = None
    CakeEvictionModule = None
    CAKE_EVICTION_AVAILABLE = False

# Importar configuraciones y módulos de DejaVu
try:
    from .paper_deja_vu import DejaVuConfig, DejaVuModule
    DEJAVU_AVAILABLE = True
except ImportError:
    DejaVuConfig = None
    DejaVuModule = None
    DEJAVU_AVAILABLE = False

# Importar configuraciones y módulos de Squeezed Attention
try:
    from .paper_squeezed_attention import SqueezedAttentionConfig, SqueezedAttentionModule
    SQUEEZED_ATTENTION_AVAILABLE = True
except ImportError:
    SqueezedAttentionConfig = None
    SqueezedAttentionModule = None
    SQUEEZED_ATTENTION_AVAILABLE = False

# Importar configuraciones y módulos de ASPD
try:
    from .paper_aspd import ASPDConfig, ASPDModule
    ASPD_AVAILABLE = True
except ImportError:
    ASPDConfig = None
    ASPDModule = None
    ASPD_AVAILABLE = False

# Importar configuraciones y módulos de Quest
try:
    from .paper_quest import QuestConfig, QuestModule
    QUEST_AVAILABLE = True
except ImportError:
    QuestConfig = None
    QuestModule = None
    QUEST_AVAILABLE = False

# Importar configuraciones y módulos de Serverless LLM
try:
    from .paper_serverless_llm import ServerlessLLMConfig, ServerlessLLMModule
    SERVERLESS_LLM_AVAILABLE = True
except ImportError:
    ServerlessLLMConfig = None
    ServerlessLLMModule = None
    SERVERLESS_LLM_AVAILABLE = False

# Importar configuraciones y módulos de Sparse Accelerate
try:
    from .paper_sparse_accelerate import SparseAccelerateConfig, SparseAccelerateModule
    SPARSE_ACCELERATE_AVAILABLE = True
except ImportError:
    SparseAccelerateConfig = None
    SparseAccelerateModule = None
    SPARSE_ACCELERATE_AVAILABLE = False

# Importar configuraciones y módulos de ANPD
try:
    from .paper_anpd import ANPDConfig, ANPDModule
    ANPD_AVAILABLE = True
except ImportError:
    ANPDConfig = None
    ANPDModule = None
    ANPD_AVAILABLE = False

# Importar configuraciones y módulos de Faster Cascades
try:
    from .paper_faster_cascades import FasterCascadesConfig, FasterCascadesModule
    FASTER_CASCADES_AVAILABLE = True
except ImportError:
    FasterCascadesConfig = None
    FasterCascadesModule = None
    FASTER_CASCADES_AVAILABLE = False

__all__ = [
    # Configuraciones - vLLM
    'VLLMConfig',
    'VLLMModule',
    # Configuraciones - TensorRT-LLM
    'TensorRTLLMConfig',
    'TensorRTLLMModule',
    # Configuraciones - KIVI
    'KIVIConfig',
    'KIVIModule',
    # Configuraciones - SpeCache
    'SpeCacheConfig',
    'SpeCacheModule',
    # Configuraciones - LayerKV
    'LayerKVConfig',
    'LayerKVModule',
    # Configuraciones - CAKE KV
    'CakeKVConfig',
    'CakeKVModule',
    # Configuraciones - CAKE Eviction
    'CakeEvictionConfig',
    'CakeEvictionModule',
    # Configuraciones - DejaVu
    'DejaVuConfig',
    'DejaVuModule',
    # Configuraciones - Squeezed Attention
    'SqueezedAttentionConfig',
    'SqueezedAttentionModule',
    # Configuraciones - ASPD
    'ASPDConfig',
    'ASPDModule',
    # Configuraciones - Quest
    'QuestConfig',
    'QuestModule',
    # Configuraciones - Serverless LLM
    'ServerlessLLMConfig',
    'ServerlessLLMModule',
    # Configuraciones - Sparse Accelerate
    'SparseAccelerateConfig',
    'SparseAccelerateModule',
    # Configuraciones - ANPD
    'ANPDConfig',
    'ANPDModule',
    # Configuraciones - Faster Cascades
    'FasterCascadesConfig',
    'FasterCascadesModule',
    # Utilidades
    'create_inference_module',
    'get_available_modules',
    'recommend_inference_method',
]

__version__ = '2.0.0'


def create_inference_module(
    method: str = "vllm",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear módulos de inferencia.
    
    Args:
        method: Método de inferencia a usar. Opciones:
            - "vllm": vLLM con PagedAttention
            - "tensorrt_llm": TensorRT-LLM optimizado
            - "kivi": KIVI con cuantización 2-bit
            - "specache": SpeCache con prefetching
            - "layerkv": LayerKV con gestión por capas
            - "cake_kv": CAKE KV cache
            - "cake_eviction": CAKE eviction
            - "deja_vu": DejaVu con sparse attention
            - "squeezed_attention": Squeezed Attention
            - "aspd": Adaptive Serial-Parallel Decoding
            - "quest": Quest con query-aware selection
            - "serverless_llm": Serverless LLM optimizado
            - "sparse_accelerate": Sparse Accelerate
            - "anpd": Adaptive N-gram Parallel Decoding
            - "faster_cascades": Faster Cascades
        **config_kwargs: Argumentos de configuración específicos del método
    
    Returns:
        Instancia del módulo de inferencia o None si hay error
    
    Raises:
        ValueError: Si method no es válido
    
    Examples:
        >>> module = create_inference_module("vllm", hidden_dim=512, page_size=16)
        >>> module = create_inference_module("tensorrt_llm", hidden_dim=768)
        >>> module = create_inference_module("kivi", quantization_bits=2)
    """
    if not method or not isinstance(method, str):
        raise ValueError(f"method debe ser una cadena no vacía, recibido: {method}")
    
    method_lower = method.lower()
    valid_methods = [
        'vllm', 'tensorrt_llm', 'kivi', 'specache', 'layerkv', 'cake_kv',
        'cake_eviction', 'deja_vu', 'squeezed_attention', 'aspd', 'quest',
        'serverless_llm', 'sparse_accelerate', 'anpd', 'faster_cascades'
    ]
    
    if method_lower not in valid_methods:
        raise ValueError(f"method debe ser uno de {valid_methods}, recibido: {method}")
    
    try:
        if method_lower == "vllm" and VLLM_AVAILABLE:
            config = VLLMConfig(**config_kwargs)
            return VLLMModule(config)
        
        elif method_lower == "tensorrt_llm" and TENSORRT_LLM_AVAILABLE:
            config = TensorRTLLMConfig(**config_kwargs)
            return TensorRTLLMModule(config)
        
        elif method_lower == "kivi" and KIVI_AVAILABLE:
            config = KIVIConfig(**config_kwargs)
            return KIVIModule(config)
        
        elif method_lower == "specache" and SPECACHE_AVAILABLE:
            config = SpeCacheConfig(**config_kwargs)
            return SpeCacheModule(config)
        
        elif method_lower == "layerkv" and LAYERKV_AVAILABLE:
            config = LayerKVConfig(**config_kwargs)
            return LayerKVModule(config)
        
        elif method_lower == "cake_kv" and CAKE_KV_AVAILABLE:
            config = CakeKVConfig(**config_kwargs)
            return CakeKVModule(config)
        
        elif method_lower == "cake_eviction" and CAKE_EVICTION_AVAILABLE:
            config = CakeEvictionConfig(**config_kwargs)
            return CakeEvictionModule(config)
        
        elif method_lower == "deja_vu" and DEJAVU_AVAILABLE:
            config = DejaVuConfig(**config_kwargs)
            return DejaVuModule(config)
        
        elif method_lower == "squeezed_attention" and SQUEEZED_ATTENTION_AVAILABLE:
            config = SqueezedAttentionConfig(**config_kwargs)
            return SqueezedAttentionModule(config)
        
        elif method_lower == "aspd" and ASPD_AVAILABLE:
            config = ASPDConfig(**config_kwargs)
            return ASPDModule(config)
        
        elif method_lower == "quest" and QUEST_AVAILABLE:
            config = QuestConfig(**config_kwargs)
            return QuestModule(config)
        
        elif method_lower == "serverless_llm" and SERVERLESS_LLM_AVAILABLE:
            config = ServerlessLLMConfig(**config_kwargs)
            return ServerlessLLMModule(config)
        
        elif method_lower == "sparse_accelerate" and SPARSE_ACCELERATE_AVAILABLE:
            config = SparseAccelerateConfig(**config_kwargs)
            return SparseAccelerateModule(config)
        
        elif method_lower == "anpd" and ANPD_AVAILABLE:
            config = ANPDConfig(**config_kwargs)
            return ANPDModule(config)
        
        elif method_lower == "faster_cascades" and FASTER_CASCADES_AVAILABLE:
            config = FasterCascadesConfig(**config_kwargs)
            return FasterCascadesModule(config)
        
        else:
            available_methods = [
                name for name, available in [
                    ('vllm', VLLM_AVAILABLE), ('tensorrt_llm', TENSORRT_LLM_AVAILABLE),
                    ('kivi', KIVI_AVAILABLE), ('specache', SPECACHE_AVAILABLE),
                    ('layerkv', LAYERKV_AVAILABLE), ('cake_kv', CAKE_KV_AVAILABLE),
                    ('cake_eviction', CAKE_EVICTION_AVAILABLE), ('deja_vu', DEJAVU_AVAILABLE),
                    ('squeezed_attention', SQUEEZED_ATTENTION_AVAILABLE), ('aspd', ASPD_AVAILABLE),
                    ('quest', QUEST_AVAILABLE), ('serverless_llm', SERVERLESS_LLM_AVAILABLE),
                    ('sparse_accelerate', SPARSE_ACCELERATE_AVAILABLE), ('anpd', ANPD_AVAILABLE),
                    ('faster_cascades', FASTER_CASCADES_AVAILABLE)
                ] if available
            ]
            logger.error(
                f"Método de inferencia no disponible: {method_lower} "
                f"(available_methods={available_methods})"
            )
            return None
    except Exception as e:
        logger.error(
            f"Error creando módulo de inferencia (method={method}): {e}",
            exc_info=True
        )
        return None


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene la lista de módulos disponibles.
    
    Returns:
        Diccionario con métodos y su disponibilidad
    
    Examples:
        >>> available = get_available_modules()
        >>> print(available)
        {'vllm': True, 'tensorrt_llm': True, ...}
    """
    return {
        'vllm': VLLM_AVAILABLE,
        'tensorrt_llm': TENSORRT_LLM_AVAILABLE,
        'kivi': KIVI_AVAILABLE,
        'specache': SPECACHE_AVAILABLE,
        'layerkv': LAYERKV_AVAILABLE,
        'cake_kv': CAKE_KV_AVAILABLE,
        'cake_eviction': CAKE_EVICTION_AVAILABLE,
        'deja_vu': DEJAVU_AVAILABLE,
        'squeezed_attention': SQUEEZED_ATTENTION_AVAILABLE,
        'aspd': ASPD_AVAILABLE,
        'quest': QUEST_AVAILABLE,
        'serverless_llm': SERVERLESS_LLM_AVAILABLE,
        'sparse_accelerate': SPARSE_ACCELERATE_AVAILABLE,
        'anpd': ANPD_AVAILABLE,
        'faster_cascades': FASTER_CASCADES_AVAILABLE,
    }


def recommend_inference_method(
    priority: str = "throughput",
    memory_constraint: Optional[float] = None,
    use_gpu: bool = True
) -> Optional[str]:
    """
    Recomienda el mejor método de inferencia según los requisitos.
    
    Args:
        priority: Prioridad principal. Opciones:
            - "throughput": Máximo throughput (tokens/s)
            - "memory": Mínimo uso de memoria
            - "latency": Mínima latencia
            - "balanced": Balance entre todos los factores
        memory_constraint: Constraint de memoria en GB (opcional)
        use_gpu: Si se puede usar GPU
    
    Returns:
        Nombre del método recomendado o None
    
    Examples:
        >>> method = recommend_inference_method("throughput", use_gpu=True)
        >>> method = recommend_inference_method("memory", memory_constraint=8.0)
        >>> method = recommend_inference_method("balanced")
    """
    available = get_available_modules()
    
    if priority == "throughput":
        if use_gpu and available.get('tensorrt_llm'):
            return 'tensorrt_llm'
        elif available.get('vllm'):
            return 'vllm'
        elif available.get('faster_cascades'):
            return 'faster_cascades'
    
    elif priority == "memory":
        if available.get('kivi'):
            return 'kivi'
        elif available.get('squeezed_attention'):
            return 'squeezed_attention'
        elif available.get('cake_eviction'):
            return 'cake_eviction'
        elif available.get('layerkv'):
            return 'layerkv'
    
    elif priority == "latency":
        if available.get('aspd'):
            return 'aspd'
        elif available.get('anpd'):
            return 'anpd'
        elif available.get('specache'):
            return 'specache'
        elif available.get('quest'):
            return 'quest'
    
    elif priority == "balanced":
        if available.get('vllm'):
            return 'vllm'
        elif available.get('specache'):
            return 'specache'
        elif available.get('layerkv'):
            return 'layerkv'
    
    if memory_constraint is not None and memory_constraint < 8.0:
        if available.get('kivi'):
            return 'kivi'
        elif available.get('squeezed_attention'):
            return 'squeezed_attention'
    
    if available.get('vllm'):
        return 'vllm'
    
    for method in ['tensorrt_llm', 'specache', 'layerkv', 'kivi']:
        if available.get(method):
            return method
    
    return None

