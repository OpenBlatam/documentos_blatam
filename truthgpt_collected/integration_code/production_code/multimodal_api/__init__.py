"""
API de Generación Multimodal

API unificada para todos los tipos de generación:
- Text-to-Video
- Text-to-Image
- Text-to-Audio
- Image-to-Video
- Video-to-Video
- Audio-to-Audio
- 3D Generation
- Multimodal Content Generation

Características:
- Endpoint único para múltiples modalidades
- Rate limiting inteligente
- Caching optimizado
- Escalabilidad automática
- WebSockets para updates en tiempo real
- Sistema de webhooks
- Métricas avanzadas
"""

from typing import Optional

__version__ = "2.0.0"
__author__ = "Production Code Team"

# Importaciones principales
try:
    from .api_server import MultimodalAPIServer
    from .models import (
        GenerationRequest,
        GenerationResponse,
        Modality,
        GenerationType,
        TaskStatus
    )
    from .middleware import RateLimiter, CacheManager, MonitoringMiddleware
    from .endpoints import router
    from .task_queue import TaskQueue
    from .config import config, APIConfig
    from .generators import VideoGenerator, ImageGenerator, AudioGenerator
    from .storage import StorageManager
    from .utils import validate_prompt, validate_parameters
    from .webhooks import WebhookManager, WebhookEvent
    from .metrics import metrics_collector
    from .health_check import HealthChecker, HealthStatus
    from .circuit_breaker import CircuitBreakerManager, CircuitBreaker, CircuitBreakerConfig
    from .load_balancer import LoadBalancer, LoadBalancingStrategy
    from .deduplication import DeduplicationManager
    from .optimization import PerformanceOptimizer, OptimizationConfig
    from .batch_processor import BatchProcessor, BatchConfig
    from .memory_integration import MemoryCacheIntegration
    from .versioning import APIVersionManager, APIVersion
    from .error_handling import ErrorHandler, error_handler, APIError, ErrorCategory
    from .analytics import AnalyticsEngine, UsageStats, PerformanceMetrics
    from .alerts import AlertManager, Alert, AlertSeverity, AlertRule
    from .rate_limit_user import UserRateLimiter, UserRateLimit
    from .backup_recovery import BackupManager, BackupMetadata
    from .api_testing import APITester
    from .logging_config import APILoggingConfig, StructuredFormatter
    from .performance_tuning import PerformanceOptimizer, PerformanceConfig
    from .security_enhancements import SecurityManager
    from .notifications import NotificationManager, NotificationChannel, Notification
    from .reporting import ReportGenerator, Report
except ImportError as e:
    # En caso de dependencias faltantes
    import warnings
    warnings.warn(f"Algunas importaciones no están disponibles: {e}")

__all__ = [
    "__version__",
    "__author__",
    "MultimodalAPIServer",
    "GenerationRequest",
    "GenerationResponse",
    "Modality",
    "GenerationType",
    "TaskStatus",
    "RateLimiter",
    "CacheManager",
    "MonitoringMiddleware",
    "TaskQueue",
    "VideoGenerator",
    "ImageGenerator",
    "AudioGenerator",
    "StorageManager",
    "WebhookManager",
    "WebhookEvent",
    "metrics_collector",
    "HealthChecker",
    "HealthStatus",
    "CircuitBreakerManager",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "LoadBalancer",
    "LoadBalancingStrategy",
    "validate_prompt",
    "validate_parameters",
    "config",
    "APIConfig",
    "router",
    "DeduplicationManager",
    "PerformanceOptimizer",
    "OptimizationConfig",
    "BatchProcessor",
    "BatchConfig",
    "MemoryCacheIntegration",
    "APIVersionManager",
    "APIVersion",
    "ErrorHandler",
    "error_handler",
    "APIError",
    "ErrorCategory",
    "AnalyticsEngine",
    "UsageStats",
    "PerformanceMetrics",
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertRule",
    "UserRateLimiter",
    "UserRateLimit",
    "BackupManager",
    "BackupMetadata",
    "APITester",
    "APILoggingConfig",
    "StructuredFormatter",
    "PerformanceOptimizer",
    "PerformanceConfig",
    "SecurityManager",
    "NotificationManager",
    "NotificationChannel",
    "Notification",
    "ReportGenerator",
    "Report",
]
