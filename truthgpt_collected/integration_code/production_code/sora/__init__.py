"""
Sora - Generación de Video y Contenido Multimodal con IA
========================================================

Este módulo contiene implementaciones de productos tipo Sora 2 para generación
de video, audio, imagen y contenido multimodal usando la infraestructura de
production_code.

Mejoras v2.0:
- Validación robusta con Pydantic
- Optimizaciones de rendimiento (flash attention, mixed precision)
- Utilidades de exportación de video
- Mejor manejo de errores
- Soporte para múltiples formatos
- Integración con Memory y Redundancy (NUEVO)
- Analytics avanzados (NUEVO)
- Optimización automática (NUEVO)

Módulos principales:
- sora_base: Clases base para generación de video
- text_to_video: Generación de video desde texto
- image_to_video: Animación de imágenes estáticas
- video_utils: Utilidades para procesamiento y exportación
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
    from .sora_base import (
        SoraConfig,
        SoraModule,
        VideoGenerationConfig,
        VideoGenerationModule,
        TemporalAttention,
        SpatialConvBlock
    )
    SORA_BASE_AVAILABLE = True
except ImportError:
    SoraConfig = None
    SoraModule = None
    VideoGenerationConfig = None
    VideoGenerationModule = None
    TemporalAttention = None
    SpatialConvBlock = None
    SORA_BASE_AVAILABLE = False

try:
    from .text_to_video import (
        TextToVideoConfig,
        TextToVideoModule,
        TextEncoder
    )
    TEXT_TO_VIDEO_AVAILABLE = True
except ImportError:
    TextToVideoConfig = None
    TextToVideoModule = None
    TextEncoder = None
    TEXT_TO_VIDEO_AVAILABLE = False

try:
    from .image_to_video import (
        ImageToVideoConfig,
        ImageToVideoModule,
        ImageEncoder
    )
    IMAGE_TO_VIDEO_AVAILABLE = True
except ImportError:
    ImageToVideoConfig = None
    ImageToVideoModule = None
    ImageEncoder = None
    IMAGE_TO_VIDEO_AVAILABLE = False

try:
    from .video_to_video import (
        VideoToVideoConfig,
        VideoToVideoModule
    )
    VIDEO_TO_VIDEO_AVAILABLE = True
except ImportError:
    VideoToVideoConfig = None
    VideoToVideoModule = None
    VIDEO_TO_VIDEO_AVAILABLE = False

try:
    from .diffusion_scheduler import (
        DiffusionScheduler,
        NoiseScheduler,
        SchedulerType
    )
    SCHEDULER_AVAILABLE = True
except ImportError:
    DiffusionScheduler = None
    NoiseScheduler = None
    SchedulerType = None
    SCHEDULER_AVAILABLE = False

try:
    from .video_utils import (
        normalize_video,
        denormalize_video,
        video_to_numpy,
        save_video_frames,
        save_video_opencv,
        create_video_gif,
        resize_video,
        extract_frame,
        concatenate_videos,
        add_temporal_noise,
        temporal_smooth
    )
    VIDEO_UTILS_AVAILABLE = True
except ImportError:
    normalize_video = None
    denormalize_video = None
    video_to_numpy = None
    save_video_frames = None
    save_video_opencv = None
    create_video_gif = None
    resize_video = None
    extract_frame = None
    concatenate_videos = None
    add_temporal_noise = None
    temporal_smooth = None
    VIDEO_UTILS_AVAILABLE = False

try:
    from .performance_utils import (
        benchmark_video_generation,
        optimize_model_for_inference,
        profile_memory_usage,
        estimate_model_size,
        compile_model,
        measure_latency,
        optimize_batch_size,
        torch_inference_mode,
        torch_autocast
    )
    PERFORMANCE_UTILS_AVAILABLE = True
except ImportError:
    benchmark_video_generation = None
    optimize_model_for_inference = None
    profile_memory_usage = None
    estimate_model_size = None
    compile_model = None
    measure_latency = None
    optimize_batch_size = None
    torch_inference_mode = None
    torch_autocast = None
    PERFORMANCE_UTILS_AVAILABLE = False

try:
    from .api_server import SoraAPIServer, create_app
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    SoraAPIServer = None
    create_app = None

try:
    from .experiment_integration import (
        SoraExperimentTracker,
        track_video_generation
    )
    EXPERIMENT_TRACKING_AVAILABLE = True
except ImportError:
    SoraExperimentTracker = None
    track_video_generation = None
    EXPERIMENT_TRACKING_AVAILABLE = False

try:
    from .rate_limiter import (
        RateLimiter,
        APIMetrics
    )
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RateLimiter = None
    APIMetrics = None
    RATE_LIMITER_AVAILABLE = False

try:
    from .advanced_processing import (
        apply_color_grading,
        apply_temporal_filter,
        apply_optical_flow_smoothing,
        extract_keyframes,
        create_video_summary,
        blend_videos,
        add_transitions,
        stabilize_video,
        enhance_video_quality
    )
    ADVANCED_PROCESSING_AVAILABLE = True
except ImportError:
    apply_color_grading = None
    apply_temporal_filter = None
    apply_optical_flow_smoothing = None
    extract_keyframes = None
    create_video_summary = None
    blend_videos = None
    add_transitions = None
    stabilize_video = None
    enhance_video_quality = None
    ADVANCED_PROCESSING_AVAILABLE = False

try:
    from .video_cache import VideoCache
    VIDEO_CACHE_AVAILABLE = True
except ImportError:
    VideoCache = None
    VIDEO_CACHE_AVAILABLE = False

try:
    from .batch_processing import BatchProcessor
    BATCH_PROCESSING_AVAILABLE = True
except ImportError:
    BatchProcessor = None
    BATCH_PROCESSING_AVAILABLE = False

try:
    from .async_queue import (
        AsyncVideoQueue,
        VideoGenerationTask,
        TaskStatus
    )
    ASYNC_QUEUE_AVAILABLE = True
except ImportError:
    AsyncVideoQueue = None
    VideoGenerationTask = None
    TaskStatus = None
    ASYNC_QUEUE_AVAILABLE = False

try:
    from .webhooks import (
        WebhookManager,
        Webhook,
        WebhookEvent
    )
    WEBHOOKS_AVAILABLE = True
except ImportError:
    WebhookManager = None
    Webhook = None
    WebhookEvent = None
    WEBHOOKS_AVAILABLE = False

try:
    from .video_quality import VideoQualityAnalyzer
    VIDEO_QUALITY_AVAILABLE = True
except ImportError:
    VideoQualityAnalyzer = None
    VIDEO_QUALITY_AVAILABLE = False

try:
    from .presets import (
        PresetManager,
        PresetType
    )
    PRESETS_AVAILABLE = True
except ImportError:
    PresetManager = None
    PresetType = None
    PRESETS_AVAILABLE = False

try:
    from .validation import (
        SoraValidator,
        ValidationError as SoraValidationError
    )
    VALIDATION_AVAILABLE = True
except ImportError:
    SoraValidator = None
    SoraValidationError = None
    VALIDATION_AVAILABLE = False

try:
    from .error_handling import (
        SoraError,
        ConfigurationError,
        GenerationError,
        ValidationError as SoraValidationError2,
        ResourceError,
        handle_errors,
        handle_async_errors,
        ErrorRecovery
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    SoraError = None
    ConfigurationError = None
    GenerationError = None
    SoraValidationError2 = None
    ResourceError = None
    handle_errors = None
    handle_async_errors = None
    ErrorRecovery = None
    ERROR_HANDLING_AVAILABLE = False

try:
    from .monitoring import (
        SoraMonitor,
        AlertThreshold,
        MetricSnapshot
    )
    MONITORING_AVAILABLE = True
except ImportError:
    SoraMonitor = None
    AlertThreshold = None
    MetricSnapshot = None
    MONITORING_AVAILABLE = False

try:
    from .testing_utils import SoraTestHelper
    TESTING_UTILS_AVAILABLE = True
except ImportError:
    SoraTestHelper = None
    TESTING_UTILS_AVAILABLE = False

try:
    from .production_utils import (
        ProductionConfig,
        HealthChecker,
        ProductionLogger,
        create_production_environment
    )
    PRODUCTION_UTILS_AVAILABLE = True
except ImportError:
    ProductionConfig = None
    HealthChecker = None
    ProductionLogger = None
    create_production_environment = None
    PRODUCTION_UTILS_AVAILABLE = False

try:
    from .deployment_manager import SoraDeploymentManager
    DEPLOYMENT_MANAGER_AVAILABLE = True
except ImportError:
    SoraDeploymentManager = None
    DEPLOYMENT_MANAGER_AVAILABLE = False

# Integración con otros módulos
try:
    from .sora_integration import (
        SoraWithMemory,
        SoraWithRedundancySuppression,
        SoraIntegrated,
        create_sora_with_memory,
        create_sora_with_redundancy,
        create_sora_integrated
    )
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    SoraWithMemory = None
    SoraWithRedundancySuppression = None
    SoraIntegrated = None
    create_sora_with_memory = None
    create_sora_with_redundancy = None
    create_sora_integrated = None

# Analytics y optimización
try:
    from .sora_analytics import (
        SoraAnalytics,
        SoraOptimizer,
        SoraExporter
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    SoraAnalytics = None
    SoraOptimizer = None
    SoraExporter = None

__all__ = [
    # Base classes
    'SoraConfig',
    'SoraModule',
    'VideoGenerationConfig',
    'VideoGenerationModule',
    'TemporalAttention',
    'SpatialConvBlock',
    # Text to Video
    'TextToVideoConfig',
    'TextToVideoModule',
    'TextEncoder',
    # Image to Video
    'ImageToVideoConfig',
    'ImageToVideoModule',
    'ImageEncoder',
    # Video to Video
    'VideoToVideoConfig',
    'VideoToVideoModule',
    # Diffusion Schedulers
    'DiffusionScheduler',
    'NoiseScheduler',
    'SchedulerType',
    # Video Utils
    'normalize_video',
    'denormalize_video',
    'video_to_numpy',
    'save_video_frames',
    'save_video_opencv',
    'create_video_gif',
    'resize_video',
    'extract_frame',
    'concatenate_videos',
    'add_temporal_noise',
    'temporal_smooth',
    # Performance Utils
    'benchmark_video_generation',
    'optimize_model_for_inference',
    'profile_memory_usage',
    'estimate_model_size',
    'compile_model',
    'measure_latency',
    'optimize_batch_size',
    'torch_inference_mode',
    'torch_autocast',
    # API Server
    'SoraAPIServer',
    'create_app',
    # Experiment Tracking
    'SoraExperimentTracker',
    'track_video_generation',
    # Rate Limiting
    'RateLimiter',
    'APIMetrics',
    # Advanced Processing
    'apply_color_grading',
    'apply_temporal_filter',
    'apply_optical_flow_smoothing',
    'extract_keyframes',
    'create_video_summary',
    'blend_videos',
    'add_transitions',
    'stabilize_video',
    'enhance_video_quality',
    # Video Cache
    'VideoCache',
    # Batch Processing
    'BatchProcessor',
    # Async Queue
    'AsyncVideoQueue',
    'VideoGenerationTask',
    'TaskStatus',
    # Webhooks
    'WebhookManager',
    'Webhook',
    'WebhookEvent',
    # Video Quality
    'VideoQualityAnalyzer',
    # Presets
    'PresetManager',
    'PresetType',
    # Validation
    'SoraValidator',
    'SoraValidationError',
    # Error Handling
    'SoraError',
    'ConfigurationError',
    'GenerationError',
    'ResourceError',
    'handle_errors',
    'handle_async_errors',
    'ErrorRecovery',
    # Monitoring
    'SoraMonitor',
    'AlertThreshold',
    'MetricSnapshot',
    # Testing Utils
    'SoraTestHelper',
    # Production Utils
    'ProductionConfig',
    'HealthChecker',
    'ProductionLogger',
    'create_production_environment',
    # Deployment
    'SoraDeploymentManager',
    # Integration
    'SoraWithMemory',
    'SoraWithRedundancySuppression',
    'SoraIntegrated',
    'SoraWithBestTechniques',
    'create_sora_with_memory',
    'create_sora_with_redundancy',
    'create_sora_integrated',
    'create_sora_with_best_techniques',
    # Factory functions
    'create_video_generator',
    'get_available_modules',
    'recommend_video_config',
]

__version__ = '2.0.0'


def create_video_generator(
    generator_type: str = "text_to_video",
    **config_kwargs
) -> Optional[Any]:
    """
    Factory function para crear generadores de video.
    
    Args:
        generator_type: Tipo de generador. Opciones:
            - "text_to_video": Generación desde texto
            - "image_to_video": Animación de imágenes
            - "video_to_video": Transformación de videos
            - "base": Módulo base de generación
        **config_kwargs: Argumentos de configuración específicos del tipo
    
    Returns:
        Instancia del generador de video o None si hay error
    
    Raises:
        ValueError: Si generator_type no es válido
    
    Examples:
        >>> generator = create_video_generator("text_to_video", num_frames=16)
        >>> generator = create_video_generator("image_to_video", image_size=(512, 512))
        >>> generator = create_video_generator("video_to_video", style="cinematic")
    """
    if not isinstance(generator_type, str) or not generator_type.strip():
        raise ValueError(f"generator_type debe ser una cadena no vacía, recibido: {generator_type}")
    
    generator_type = generator_type.lower()
    valid_types = ["text_to_video", "image_to_video", "video_to_video", "base"]
    
    if generator_type not in valid_types:
        raise ValueError(f"generator_type debe ser uno de {valid_types}, recibido: {generator_type}")
    
    def _create_generator():
        if generator_type == "text_to_video" and TEXT_TO_VIDEO_AVAILABLE:
            config = TextToVideoConfig(**config_kwargs)
            return TextToVideoModule(config)
        
        elif generator_type == "image_to_video" and IMAGE_TO_VIDEO_AVAILABLE:
            config = ImageToVideoConfig(**config_kwargs)
            return ImageToVideoModule(config)
        
        elif generator_type == "video_to_video" and VIDEO_TO_VIDEO_AVAILABLE:
            config = VideoToVideoConfig(**config_kwargs)
            return VideoToVideoModule(config)
        
        elif generator_type == "base" and SORA_BASE_AVAILABLE:
            config = VideoGenerationConfig(**config_kwargs)
            return VideoGenerationModule(config)
        
        else:
            available = [t for t in valid_types if globals().get(f"{t.upper().replace('_', '_')}_AVAILABLE", False)]
            logger.error(
                "Tipo de generador no disponible",
                generator_type=generator_type,
                available_types=available
            )
            return None
    
    result, error = safe_execute(_create_generator, default_value=None, log_errors=True)
    
    if error:
        logger.error(
            "Error creando generador de video",
            generator_type=generator_type,
            error=str(error)
        )
    
    return result


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene la lista de módulos y utilidades disponibles.
    
    Returns:
        Diccionario con módulos y su disponibilidad
    
    Examples:
        >>> available = get_available_modules()
        >>> print(available)
        {'text_to_video': True, 'image_to_video': True, 'api': True, ...}
    """
    return {
        'sora_base': SORA_BASE_AVAILABLE,
        'text_to_video': TEXT_TO_VIDEO_AVAILABLE,
        'image_to_video': IMAGE_TO_VIDEO_AVAILABLE,
        'video_to_video': VIDEO_TO_VIDEO_AVAILABLE,
        'scheduler': SCHEDULER_AVAILABLE,
        'video_utils': VIDEO_UTILS_AVAILABLE,
        'performance_utils': PERFORMANCE_UTILS_AVAILABLE,
        'api': API_AVAILABLE,
        'experiment_tracking': EXPERIMENT_TRACKING_AVAILABLE,
        'rate_limiter': RATE_LIMITER_AVAILABLE,
        'advanced_processing': ADVANCED_PROCESSING_AVAILABLE,
    }


def recommend_video_config(
    use_case: str = "general",
    quality_priority: str = "balanced",
    performance_priority: str = "balanced"
) -> Dict[str, Any]:
    """
    Recomienda una configuración de video según el caso de uso.
    
    Args:
        use_case: Caso de uso. Opciones:
            - "general": Uso general
            - "high_quality": Alta calidad
            - "fast": Generación rápida
            - "memory_efficient": Eficiente en memoria
        quality_priority: Prioridad de calidad ("high", "medium", "low", "balanced")
        performance_priority: Prioridad de rendimiento ("speed", "quality", "balanced")
    
    Returns:
        Diccionario con recomendaciones de configuración
    
    Examples:
        >>> config = recommend_video_config("high_quality")
        >>> config = recommend_video_config("fast", performance_priority="speed")
    """
    recommendations = {}
    
    if use_case == "high_quality" or quality_priority == "high":
        recommendations.update({
            'num_frames': 32,
            'resolution': (1024, 1024),
            'num_inference_steps': 50,
            'guidance_scale': 7.5,
            'use_flash_attention': True,
        })
    
    elif use_case == "fast" or performance_priority == "speed":
        recommendations.update({
            'num_frames': 16,
            'resolution': (512, 512),
            'num_inference_steps': 20,
            'guidance_scale': 5.0,
            'use_flash_attention': True,
            'use_mixed_precision': True,
        })
    
    elif use_case == "memory_efficient":
        recommendations.update({
            'num_frames': 16,
            'resolution': (512, 512),
            'num_inference_steps': 25,
            'guidance_scale': 6.0,
            'use_gradient_checkpointing': True,
            'use_mixed_precision': True,
        })
    
    else:
        recommendations.update({
            'num_frames': 24,
            'resolution': (768, 768),
            'num_inference_steps': 30,
            'guidance_scale': 6.5,
            'use_flash_attention': True,
        })
    
    return recommendations

