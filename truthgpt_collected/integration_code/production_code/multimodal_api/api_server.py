#!/usr/bin/env python3
"""
Servidor Principal de la API de Generación Multimodal.

API unificada para todos los tipos de generación con:
- Rate limiting inteligente
- Caching optimizado
- Escalabilidad automática
- Monitoring integrado
"""

from typing import Optional, Dict, Any
import uuid
from datetime import datetime

try:
    from fastapi import FastAPI, Request, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.api_utils import create_fastapi_app, api_error_handler
    from core.utils import setup_logger, async_safe_execute
    from core.error_handling import safe_execute
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    def safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            if log_errors:
                logger.error(f"Error en {func.__name__}: {e}")
            return default_value, e
    
    async def async_safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result, None
        except Exception as e:
            if log_errors:
                logger.error(f"Error en {func.__name__}: {e}")
            return default_value, e

from .models import (
    GenerationRequest,
    GenerationResponse,
    TaskStatus,
    TaskStatusResponse,
    HealthResponse,
    BatchGenerationRequest,
    BatchGenerationResponse
)
from .middleware import RateLimiter, RateLimitConfig, CacheManager, CacheConfig, MonitoringMiddleware
from .endpoints import router
from .task_queue import TaskQueue
from .config import config
from .generators import VideoGenerator, ImageGenerator, AudioGenerator
from .storage import StorageManager
from .websocket_manager import connection_manager
from .retry_manager import RetryManager, RetryConfig
from .webhooks import WebhookManager, WebhookEvent
from .metrics import metrics_collector
from .api_docs import API_TAGS, GENERATION_REQUEST_EXAMPLES
from .health_check import HealthChecker, HealthStatus
from .circuit_breaker import CircuitBreakerManager, CircuitBreakerConfig
from .load_balancer import LoadBalancer, LoadBalancingStrategy
from .deduplication import DeduplicationManager
from .optimization import PerformanceOptimizer, OptimizationConfig
from .batch_processor import BatchProcessor, BatchConfig
from .memory_integration import MemoryCacheIntegration
from .versioning import APIVersionManager, APIVersion
from .error_handling import ErrorHandler, error_handler
from .analytics import AnalyticsEngine
from .alerts import AlertManager, AlertSeverity
from .rate_limit_user import UserRateLimiter
from .backup_recovery import BackupManager
from .logging_config import APILoggingConfig
from .performance_tuning import PerformanceOptimizer, PerformanceConfig
from .security_enhancements import SecurityManager
from .notifications import NotificationManager, NotificationChannel
from .reporting import ReportGenerator
from .dynamic_config import DynamicConfigManager
from .quotas import QuotaManager, QuotaType


class MultimodalAPIServer:
    """Servidor principal de la API Multimodal."""
    
    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        title: str = "Multimodal Generation API",
        version: str = "1.0.0"
    ):
        """
        Inicializa el servidor API.
        
        Args:
            rate_limit_config: Configuración de rate limiting
            cache_config: Configuración de cache
            title: Título de la API
            version: Versión de la API
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI no está instalado. Instala con: pip install fastapi uvicorn"
            )
        
        # Inicializar componentes
        self.rate_limiter = RateLimiter(rate_limit_config)
        self.cache_manager = CacheManager(cache_config)
        self.monitoring = MonitoringMiddleware()
        
        # Inicializar cola de tareas
        self.task_queue = TaskQueue(max_workers=config.queue_max_workers)
        
        # Inicializar generadores
        self.video_generator = VideoGenerator()
        self.image_generator = ImageGenerator()
        self.audio_generator = AudioGenerator()
        
        # Inicializar almacenamiento
        self.storage = StorageManager(
            base_path=config.storage_path,
            url_prefix=config.storage_url_prefix
        )
        
        # Inicializar retry manager
        self.retry_manager = RetryManager(
            RetryConfig(
                max_attempts=3,
                initial_delay=1.0,
                strategy="exponential"
            )
        )
        
        # Inicializar webhook manager
        self.webhook_manager = WebhookManager()
        
        # Inicializar health checker
        self.health_checker = HealthChecker()
        
        # Inicializar circuit breaker manager
        self.circuit_breaker_manager = CircuitBreakerManager()
        
        # Inicializar load balancer (para futuras distribuciones)
        self.load_balancer = LoadBalancer(
            strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
        )
        
        # Inicializar deduplicación
        self.deduplication_manager = DeduplicationManager(
            similarity_threshold=0.95,
            time_window_seconds=3600,
            enable_semantic_dedup=True
        )
        
        # Inicializar optimizador de rendimiento
        self.performance_optimizer = PerformanceOptimizer(
            OptimizationConfig(
                auto_scale_workers=True,
                enable_cache_warming=True,
                enable_batch_optimization=True
            )
        )
        self.performance_optimizer.start()
        
        # Inicializar batch processor
        self.batch_processor = BatchProcessor(
            BatchConfig(
                max_batch_size=100,
                enable_deduplication=True,
                enable_prioritization=True
            )
        )
        
        # Inicializar integración con memory
        self.memory_integration = MemoryCacheIntegration(
            enable_memory_cache=True
        )
        
        # Inicializar version manager
        self.version_manager = APIVersionManager()
        
        # Inicializar analytics engine
        self.analytics = AnalyticsEngine(retention_days=30)
        
        # Inicializar alert manager
        self.alert_manager = AlertManager()
        
        # Inicializar user rate limiter
        self.user_rate_limiter = UserRateLimiter(
            default_limit=100,
            default_window=60
        )
        
        # Inicializar backup manager
        self.backup_manager = BackupManager(backup_dir="./backups")
        
        # Inicializar logging config
        self.logging_config = APILoggingConfig(
            log_dir="./logs",
            log_level="INFO",
            enable_json_logging=False
        )
        
        # Inicializar performance optimizer
        self.performance_optimizer = PerformanceOptimizer(
            PerformanceConfig(
                enable_caching=True,
                enable_async_processing=True
            )
        )
        
        # Inicializar security manager
        self.security_manager = SecurityManager()
        
        # Inicializar notification manager
        self.notification_manager = NotificationManager()
        
        # Inicializar report generator
        self.report_generator = ReportGenerator()
        
        # Inicializar dynamic config manager
        self.dynamic_config = DynamicConfigManager()
        
        # Inicializar quota manager
        self.quota_manager = QuotaManager()
        
        # Agregar middlewares
        self._setup_middlewares()
        
        # Registrar componentes para health check
        self._register_health_checks()
        
        # Configurar tags de API
        for tag in API_TAGS:
            self.app.openapi_tags = API_TAGS
        
        # Registrar procesadores
        self._register_processors()
        
        # Crear aplicación FastAPI
        self.app = create_fastapi_app(title=title, version=version, enable_cors=True)
        
        # Agregar middleware personalizado
        # Nota: FastAPI requiere que el middleware sea una clase, no una instancia
        # Por lo tanto, creamos funciones wrapper
        @self.app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            identifier = request.client.host if request.client else "unknown"
            priority = int(request.headers.get("X-Priority", "5"))
            result = self.rate_limiter.check_rate_limit(identifier, priority)
            
            if not result.allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Demasiadas solicitudes. Intenta nuevamente más tarde.",
                        "retry_after_seconds": result.retry_after_seconds
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.rate_limiter.config.max_requests),
                        "X-RateLimit-Remaining": str(result.remaining_requests),
                        "X-RateLimit-Reset": str(result.reset_after_seconds),
                        "Retry-After": str(result.retry_after_seconds or 60)
                    }
                )
            
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.config.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(result.remaining_requests)
            response.headers["X-RateLimit-Reset"] = str(result.reset_after_seconds)
            return response
        
        @self.app.middleware("http")
        async def monitoring_middleware(request: Request, call_next):
            start_time = datetime.now()
            try:
                response = await call_next(request)
                duration = (datetime.now() - start_time).total_seconds()
                modality = request.url.path.split("/")[-1] if "/" in request.url.path else "unknown"
                status_type = "error" if response.status_code >= 400 else "success"
                self.monitoring.record_request(modality, duration, status_type)
                return response
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                self.monitoring.record_request("unknown", duration, "error", str(e))
                raise
        
        # Inyectar referencias en endpoints
        import multimodal_api.endpoints as endpoints_module
        endpoints_module.tasks_storage = self.tasks
        endpoints_module.task_queue_ref = self.task_queue
        endpoints_module.deduplication_manager_ref = self.deduplication_manager
        endpoints_module.analytics_ref = self.analytics
        
        # Inyectar webhook manager y analytics en task queue
        self.task_queue._webhook_manager = self.webhook_manager
        self.task_queue._analytics_ref = self.analytics
        
        # Registrar endpoints
        self.app.include_router(router, prefix="/api/v1", tags=["generation"])
        
        # Endpoints adicionales
        self._setup_endpoints()
        
        # WebSocket endpoints
        self._setup_websockets()
        
        # Almacenamiento de tareas (en producción usar Redis/DB)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        
        # Iniciar cola de tareas
        self.task_queue.start()
    
    def _setup_middlewares(self):
        """Configura middlewares adicionales."""
        try:
            from .middleware.analytics_middleware import AnalyticsMiddleware
            from .middleware.alert_middleware import AlertMiddleware
            from .middleware.user_rate_limit_middleware import UserRateLimitMiddleware
            
            # Analytics middleware
            self.app.add_middleware(
                AnalyticsMiddleware,
                analytics_engine=self.analytics
            )
            
            # Alert middleware
            self.app.add_middleware(
                AlertMiddleware,
                alert_manager=self.alert_manager,
                metrics_collector=metrics_collector,
                task_queue=self.task_queue,
                cache_manager=self.cache_manager
            )
            
            # User rate limit middleware
            self.app.add_middleware(
                UserRateLimitMiddleware,
                user_rate_limiter=self.user_rate_limiter,
                auth_manager=self.auth_manager
            )
            
            logger.info("Middlewares adicionales configurados")
        except Exception as e:
            logger.warning(f"No se pudieron configurar algunos middlewares: {e}")
    
    def _register_processors(self):
        """Registra procesadores para cada modalidad."""
        async def video_processor(prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
            """Procesador de video."""
            generation_type = parameters.get("generation_type", "text_to_video")
            
            if generation_type == "text_to_video":
                return await self.video_generator.generate_text_to_video(prompt, parameters)
            elif generation_type == "image_to_video":
                image_path = parameters.get("image_path")
                if not image_path:
                    raise ValueError("image_path requerido para image_to_video")
                return await self.video_generator.generate_image_to_video(
                    image_path, prompt, parameters
                )
            else:
                raise ValueError(f"Tipo de generación no soportado: {generation_type}")
        
        self.task_queue.register_processor("video", video_processor)
        
        async def image_processor(prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
            """Procesador de imagen."""
            generation_type = parameters.get("generation_type", "text_to_image")
            
            if generation_type == "text_to_image":
                return await self.image_generator.generate_text_to_image(prompt, parameters)
            elif generation_type == "image_to_image":
                image_path = parameters.get("image_path")
                if not image_path:
                    raise ValueError("image_path requerido para image_to_image")
                return await self.image_generator.generate_image_to_image(
                    image_path, prompt, parameters
                )
            elif generation_type == "image_upscale":
                image_path = parameters.get("image_path")
                scale = parameters.get("scale_factor", 2)
                if not image_path:
                    raise ValueError("image_path requerido para image_upscale")
                return await self.image_generator.upscale_image(image_path, scale, parameters)
            else:
                raise ValueError(f"Tipo de generación no soportado: {generation_type}")
        
        self.task_queue.register_processor("image", image_processor)
        
        async def audio_processor(prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
            """Procesador de audio."""
            generation_type = parameters.get("generation_type", "text_to_audio")
            
            if generation_type == "text_to_audio":
                return await self.audio_generator.generate_text_to_audio(prompt, parameters)
            elif generation_type == "text_to_music":
                return await self.audio_generator.generate_text_to_music(prompt, parameters)
            elif generation_type == "audio_to_audio":
                audio_path = parameters.get("audio_path")
                transformation = parameters.get("transformation", "enhance")
                if not audio_path:
                    raise ValueError("audio_path requerido para audio_to_audio")
                return await self.audio_generator.transform_audio(
                    audio_path, transformation, parameters
                )
            else:
                raise ValueError(f"Tipo de generación no soportado: {generation_type}")
        
        self.task_queue.register_processor("audio", audio_processor)
    
    def _setup_endpoints(self):
        """Configura endpoints adicionales."""
        
        @self.app.get("/health", response_model=HealthResponse, tags=["monitoring"])
        async def health_check():
            """
            Health check endpoint.
            
            Retorna el estado de salud del sistema incluyendo:
            - Estado general
            - Estadísticas de cache
            - Estadísticas de rate limiting
            - Tareas activas
            - Tamaño de cola
            """
            # Ejecutar health checks de forma segura
            health_result, health_error = await async_safe_execute(
                self.health_checker.check_all,
                default_value={},
                log_errors=False
            )
            
            health_summary = self.health_checker.get_summary() if not health_error else {
                "overall_status": "unknown"
            }
            
            # Obtener estadísticas de forma segura
            cache_stats, _ = safe_execute(
                self.cache_manager.get_stats,
                default_value={},
                log_errors=False
            )
            
            rate_limit_stats, _ = safe_execute(
                self.rate_limiter.get_stats,
                default_value={},
                log_errors=False
            )
            
            monitoring_stats, _ = safe_execute(
                self.monitoring.get_stats,
                default_value={"uptime_seconds": 0, "active_tasks": 0},
                log_errors=False
            )
            
            queue_stats, _ = safe_execute(
                lambda: self.task_queue.get_queue_stats(),
                default_value={"queue_size": 0},
                log_errors=False
            )
            
            return HealthResponse(
                status=health_summary.get("overall_status", "unknown"),
                version="1.0.0",
                uptime_seconds=monitoring_stats.get("uptime_seconds", 0),
                active_tasks=monitoring_stats.get("active_tasks", 0),
                queue_size=queue_stats.get("queue_size", 0),
                cache_stats=cache_stats or {},
                rate_limit_stats=rate_limit_stats or {}
            )
        
        @self.app.get("/health/detailed", tags=["monitoring"])
        async def detailed_health_check():
            """Health check detallado con estado de todos los componentes."""
            await async_safe_execute(
                self.health_checker.check_all,
                default_value={},
                log_errors=False
            )
            
            result, error = safe_execute(
                self.health_checker.get_summary,
                default_value={"error": "Error obteniendo health check"},
                log_errors=False
            )
            
            return result
        
        @self.app.get("/circuit-breakers", tags=["monitoring"])
        async def get_circuit_breakers():
            """Obtiene el estado de todos los circuit breakers."""
            result, error = safe_execute(
                self.circuit_breaker_manager.get_all_states,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo circuit breakers"}
        
        @self.app.get("/load-balancer/stats", tags=["monitoring"])
        async def get_load_balancer_stats():
            """Obtiene estadísticas del load balancer."""
            result, error = safe_execute(
                self.load_balancer.get_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo load balancer stats"}
        
        @self.app.get("/deduplication/stats", tags=["monitoring"])
        async def get_deduplication_stats():
            """Obtiene estadísticas de deduplicación."""
            result, error = safe_execute(
                self.deduplication_manager.get_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo deduplication stats"}
        
        @self.app.post("/deduplication/clear", tags=["monitoring"])
        async def clear_deduplication_cache():
            """Limpia el cache de deduplicación."""
            result, error = safe_execute(
                self.deduplication_manager.clear_cache,
                default_value=None,
                log_errors=False
            )
            if error:
                return {"error": "Error limpiando cache de deduplicación"}
            return {"message": "Cache de deduplicación limpiado"}
        
        @self.app.get("/optimization/suggestions", tags=["monitoring"])
        async def get_optimization_suggestions():
            """Obtiene sugerencias de optimización."""
            result, error = safe_execute(
                self.performance_optimizer.suggest_optimizations,
                default_value=[],
                log_errors=False
            )
            return {
                "suggestions": result if not error else [],
                "timestamp": datetime.now().isoformat(),
                "error": str(error) if error else None
            }
        
        @self.app.get("/memory/stats", tags=["monitoring"])
        async def get_memory_stats():
            """Obtiene estadísticas del sistema de memoria."""
            result, error = safe_execute(
                self.memory_integration.get_memory_stats,
                default_value={"enabled": False},
                log_errors=False
            )
            return result if not error else {"enabled": False, "error": str(error)}
        
        @self.app.post("/memory/consolidate", tags=["monitoring"])
        async def consolidate_memory():
            """Consolida memoria episódica a semántica."""
            result, error = safe_execute(
                self.memory_integration.consolidate_memory,
                default_value=None,
                log_errors=False
            )
            if error:
                return {"error": "Error consolidando memoria", "message": str(error)}
            return {"message": "Memoria consolidada"}
        
        @self.app.get("/version", tags=["monitoring"])
        async def get_api_version():
            """Obtiene información de versiones de la API."""
            result, error = safe_execute(
                self.version_manager.get_version_summary,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo versiones"}
        
        @self.app.get("/errors/stats", tags=["monitoring"])
        async def get_error_stats():
            """Obtiene estadísticas de errores."""
            result, error = safe_execute(
                error_handler.get_error_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo estadísticas de errores"}
        
        @self.app.get("/analytics", tags=["monitoring"])
        async def get_analytics():
            """Obtiene analytics completos."""
            result, error = safe_execute(
                self.analytics.get_summary,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo analytics"}
        
        @self.app.get("/analytics/usage", tags=["monitoring"])
        async def get_usage_analytics(days: int = 7):
            """Obtiene estadísticas de uso."""
            result, error = safe_execute(
                self.analytics.get_usage_stats,
                default_value=None,
                log_errors=False,
                days=days
            )
            if error:
                return {"error": "Error obteniendo estadísticas de uso"}
            return result.__dict__ if result else {}
        
        @self.app.get("/analytics/performance", tags=["monitoring"])
        async def get_performance_analytics(days: int = 7):
            """Obtiene métricas de rendimiento."""
            result, error = safe_execute(
                self.analytics.get_performance_metrics,
                default_value=None,
                log_errors=False,
                days=days
            )
            if error:
                return {"error": "Error obteniendo métricas de rendimiento"}
            return result.__dict__ if result else {}
        
        @self.app.get("/alerts", tags=["monitoring"])
        async def get_alerts():
            """Obtiene alertas activas."""
            result, error = safe_execute(
                self.alert_manager.get_active_alerts,
                default_value=[],
                log_errors=False
            )
            return [a.__dict__ for a in result] if not error else []
        
        @self.app.get("/alerts/history", tags=["monitoring"])
        async def get_alert_history(
            severity: Optional[str] = None,
            hours: int = 24
        ):
            """Obtiene historial de alertas."""
            alert_severity = None
            if severity:
                try:
                    alert_severity = AlertSeverity(severity)
                except ValueError:
                    pass
            
            result, error = safe_execute(
                self.alert_manager.get_alert_history,
                default_value=[],
                log_errors=False,
                severity=alert_severity,
                hours=hours
            )
            return [a.__dict__ for a in result] if not error else []
        
        @self.app.post("/alerts/{alert_id}/resolve", tags=["monitoring"])
        async def resolve_alert(alert_id: str):
            """Resuelve una alerta."""
            result, error = safe_execute(
                self.alert_manager.resolve_alert,
                default_value=None,
                log_errors=False,
                alert_id=alert_id
            )
            if error:
                return {"error": "Error resolviendo alerta"}
            return {"message": f"Alerta {alert_id} resuelta"}
        
        @self.app.get("/alerts/stats", tags=["monitoring"])
        async def get_alert_stats():
            """Obtiene estadísticas de alertas."""
            result, error = safe_execute(
                self.alert_manager.get_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo estadísticas de alertas"}
        
        @self.app.get("/rate-limit/user/{user_id}", tags=["monitoring"])
        async def get_user_rate_limit(user_id: str):
            """Obtiene límite de rate de un usuario."""
            result, error = safe_execute(
                self.user_rate_limiter.get_user_stats,
                default_value=None,
                log_errors=False,
                user_id=user_id
            )
            return result if not error and result else {"error": "Usuario no encontrado"}
        
        @self.app.post("/rate-limit/user/{user_id}", tags=["monitoring"])
        async def set_user_rate_limit(
            user_id: str,
            max_requests: int,
            window_seconds: int
        ):
            """Establece límite de rate para un usuario."""
            result, error = safe_execute(
                self.user_rate_limiter.set_user_limit,
                default_value=None,
                log_errors=False,
                user_id=user_id,
                max_requests=max_requests,
                window_seconds=window_seconds
            )
            if error:
                return {"error": "Error estableciendo límite"}
            return {"message": f"Límite establecido para usuario {user_id}"}
        
        @self.app.get("/rate-limit/users", tags=["monitoring"])
        async def get_all_user_rate_limits():
            """Obtiene límites de rate de todos los usuarios."""
            result, error = safe_execute(
                self.user_rate_limiter.get_all_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo límites"}
        
        @self.app.post("/backup", tags=["admin"])
        async def create_backup(description: Optional[str] = None):
            """Crea un backup del sistema."""
            def _create_backup():
                components = {
                    "tasks": self.tasks,
                    "config": {
                        "rate_limit": self.rate_limiter.get_stats(),
                        "cache": self.cache_manager.get_stats()
                    }
                }
                return self.backup_manager.create_backup(components, description)
            
            result, error = safe_execute(_create_backup, default_value=None, log_errors=False)
            
            if error:
                return {"error": "Error creando backup", "message": str(error)}
            
            return {"backup_id": result, "message": "Backup creado exitosamente"}
        
        @self.app.get("/backup", tags=["admin"])
        async def list_backups():
            """Lista todos los backups."""
            result, error = safe_execute(
                self.backup_manager.list_backups,
                default_value=[],
                log_errors=False
            )
            return result if not error else {"error": "Error listando backups"}
        
        @self.app.get("/backup/{backup_id}", tags=["admin"])
        async def get_backup_info(backup_id: str):
            """Obtiene información de un backup."""
            result, error = safe_execute(
                self.backup_manager.get_backup_info,
                default_value=None,
                log_errors=False,
                backup_id=backup_id
            )
            return result if not error and result else {"error": "Backup no encontrado"}
        
        @self.app.post("/backup/{backup_id}/restore", tags=["admin"])
        async def restore_backup(backup_id: str):
            """Restaura un backup."""
            result, error = safe_execute(
                self.backup_manager.restore_backup,
                default_value=None,
                log_errors=False,
                backup_id=backup_id
            )
            if error:
                return {"error": "Error restaurando backup", "message": str(error)}
            return {"message": f"Backup {backup_id} restaurado exitosamente"}
        
        @self.app.delete("/backup/{backup_id}", tags=["admin"])
        async def delete_backup(backup_id: str):
            """Elimina un backup."""
            result, error = safe_execute(
                self.backup_manager.delete_backup,
                default_value=None,
                log_errors=False,
                backup_id=backup_id
            )
            if error:
                return {"error": "Error eliminando backup", "message": str(error)}
            return {"message": f"Backup {backup_id} eliminado exitosamente"}
        
        @self.app.get("/performance/stats", tags=["monitoring"])
        async def get_performance_stats():
            """Obtiene estadísticas de rendimiento."""
            result, error = safe_execute(
                self.performance_optimizer.get_performance_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo estadísticas de rendimiento"}
        
        @self.app.get("/security/stats", tags=["monitoring"])
        async def get_security_stats():
            """Obtiene estadísticas de seguridad."""
            result, error = safe_execute(
                self.security_manager.get_security_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo estadísticas de seguridad"}
        
        @self.app.post("/notifications", tags=["notifications"])
        async def send_notification(
            channel: str,
            recipient: str,
            subject: str,
            message: str,
            metadata: Optional[Dict[str, Any]] = None
        ):
            """Envía una notificación."""
            try:
                notif_channel = NotificationChannel(channel)
            except ValueError:
                return {"error": f"Canal no válido: {channel}"}
            
            result, error = await async_safe_execute(
                self.notification_manager.send_notification,
                default_value=None,
                log_errors=False,
                channel=notif_channel,
                recipient=recipient,
                subject=subject,
                message=message,
                metadata=metadata
            )
            
            if error:
                return {"error": "Error enviando notificación", "message": str(error)}
            
            return {"notification_id": result, "message": "Notificación enviada"}
        
        @self.app.get("/notifications/{notification_id}", tags=["notifications"])
        async def get_notification(notification_id: str):
            """Obtiene una notificación."""
            result, error = safe_execute(
                self.notification_manager.get_notification,
                default_value=None,
                log_errors=False,
                notification_id=notification_id
            )
            
            if not result:
                return {"error": "Notificación no encontrada"}
            
            return {
                "id": result.id,
                "channel": result.channel.value,
                "recipient": result.recipient,
                "subject": result.subject,
                "message": result.message,
                "sent": result.sent,
                "sent_at": result.sent_at.isoformat() if result.sent_at else None,
                "error": result.error
            }
        
        @self.app.get("/notifications/stats", tags=["notifications"])
        async def get_notification_stats():
            """Obtiene estadísticas de notificaciones."""
            result, error = safe_execute(
                self.notification_manager.get_stats,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo estadísticas"}
        
        @self.app.post("/reports/usage", tags=["reports"])
        async def generate_usage_report(days: int = 7):
            """Genera reporte de uso."""
            result, error = safe_execute(
                self.report_generator.generate_usage_report,
                default_value=None,
                log_errors=False,
                analytics_engine=self.analytics,
                days=days
            )
            
            if error:
                return {"error": "Error generando reporte", "message": str(error)}
            
            return {
                "report_id": result.id,
                "title": result.title,
                "generated_at": result.generated_at.isoformat()
            }
        
        @self.app.post("/reports/security", tags=["reports"])
        async def generate_security_report(days: int = 7):
            """Genera reporte de seguridad."""
            result, error = safe_execute(
                self.report_generator.generate_security_report,
                default_value=None,
                log_errors=False,
                security_manager=self.security_manager,
                days=days
            )
            
            if error:
                return {"error": "Error generando reporte", "message": str(error)}
            
            return {
                "report_id": result.id,
                "title": result.title,
                "generated_at": result.generated_at.isoformat()
            }
        
        @self.app.get("/reports", tags=["reports"])
        async def list_reports(report_type: Optional[str] = None):
            """Lista reportes."""
            result, error = safe_execute(
                self.report_generator.list_reports,
                default_value=[],
                log_errors=False,
                report_type=report_type
            )
            return result if not error else {"error": "Error listando reportes"}
        
        @self.app.get("/reports/{report_id}", tags=["reports"])
        async def get_report(report_id: str, format: str = "json"):
            """Obtiene un reporte."""
            result, error = safe_execute(
                self.report_generator.export_report,
                default_value=None,
                log_errors=False,
                report_id=report_id,
                format=format
            )
            
            if error:
                return {"error": "Error obteniendo reporte", "message": str(error)}
            
            return {"content": result, "format": format}
        
        @self.app.get("/config", tags=["admin"])
        async def get_config():
            """Obtiene la configuración dinámica."""
            result, error = safe_execute(
                self.dynamic_config.get_all,
                default_value={},
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo configuración"}
        
        @self.app.post("/config/{key}", tags=["admin"])
        async def set_config(
            key: str,
            value: Any,
            changed_by: Optional[str] = None,
            reason: Optional[str] = None
        ):
            """Establece un valor de configuración."""
            result, error = safe_execute(
                self.dynamic_config.set,
                default_value=None,
                log_errors=False,
                key=key,
                value=value,
                changed_by=changed_by,
                reason=reason
            )
            if error:
                return {"error": "Error estableciendo configuración", "message": str(error)}
            return {"message": f"Configuración {key} actualizada"}
        
        @self.app.get("/config/history", tags=["admin"])
        async def get_config_history(key: Optional[str] = None):
            """Obtiene historial de cambios de configuración."""
            result, error = safe_execute(
                self.dynamic_config.get_change_history,
                default_value=[],
                log_errors=False,
                key=key
            )
            return result if not error else {"error": "Error obteniendo historial"}
        
        @self.app.post("/quotas/plans", tags=["admin"])
        async def create_quota_plan(
            plan_id: str,
            name: str,
            quotas: Dict[str, float],
            metadata: Optional[Dict[str, Any]] = None
        ):
            """Crea un plan de quotas."""
            # Convertir strings a QuotaType
            quota_types = {}
            for key, value in quotas.items():
                try:
                    quota_type = QuotaType(key)
                    quota_types[quota_type] = value
                except ValueError:
                    return {"error": f"Tipo de quota no válido: {key}"}
            
            result, error = safe_execute(
                self.quota_manager.create_plan,
                default_value=None,
                log_errors=False,
                plan_id=plan_id,
                name=name,
                quotas=quota_types,
                metadata=metadata
            )
            if error:
                return {"error": "Error creando plan", "message": str(error)}
            return {"message": f"Plan {plan_id} creado"}
        
        @self.app.post("/quotas/users/{user_id}", tags=["admin"])
        async def assign_quota_plan(user_id: str, plan_id: str):
            """Asigna un plan a un usuario."""
            result, error = safe_execute(
                self.quota_manager.assign_plan,
                default_value=None,
                log_errors=False,
                user_id=user_id,
                plan_id=plan_id
            )
            if error:
                return {"error": "Error asignando plan", "message": str(error)}
            return {"message": f"Plan {plan_id} asignado a usuario {user_id}"}
        
        @self.app.get("/quotas/users/{user_id}", tags=["monitoring"])
        async def get_user_quotas(user_id: str):
            """Obtiene quotas de un usuario."""
            result, error = safe_execute(
                self.quota_manager.get_user_quotas,
                default_value={},
                log_errors=False,
                user_id=user_id
            )
            return result if not error else {"error": "Error obteniendo quotas"}
        
        @self.app.get("/quotas/plans", tags=["admin"])
        async def get_quota_plans():
            """Obtiene todos los planes de quotas."""
            result, error = safe_execute(
                self.quota_manager.get_plans,
                default_value=[],
                log_errors=False
            )
            return result if not error else {"error": "Error obteniendo planes"}
        
        @self.app.get("/metrics", tags=["monitoring"])
        async def get_metrics():
            """
            Obtiene métricas detalladas del sistema.
            
            Incluye:
            - Contadores de eventos
            - Gauges de estado
            - Histogramas de duración
            - Estadísticas agregadas
            """
            result, error = safe_execute(
                metrics_collector.get_summary,
                default_value={},
                log_errors=False
            )
            
            if error:
                return {
                    "error": "Error obteniendo métricas",
                    "message": str(error)
                }
            
            return result
        
        @self.app.post("/webhooks", tags=["webhooks"])
        async def register_webhook(
            webhook_id: str,
            url: str,
            secret: Optional[str] = None,
            events: Optional[List[str]] = None
        ):
            """
            Registra un nuevo webhook.
            
            Args:
                webhook_id: ID único del webhook
                url: URL de destino
                secret: Secreto para firma (opcional)
                events: Lista de eventos a escuchar (opcional)
            """
            def _register():
                from .webhooks import WebhookEvent
                
                webhook_events = None
                if events:
                    webhook_events = [WebhookEvent(e) for e in events]
                
                return self.webhook_manager.register_webhook(
                    webhook_id=webhook_id,
                    url=url,
                    secret=secret,
                    events=webhook_events
                )
            
            result, error = safe_execute(_register, default_value=None, log_errors=False)
            
            if error:
                api_error = error_handler.handle_error(error, context={"endpoint": "register_webhook"})
                raise error_handler.create_http_exception(api_error)
            
            return {"message": f"Webhook {webhook_id} registrado exitosamente"}
        
        @self.app.get("/webhooks/stats", tags=["webhooks"])
        async def get_webhook_stats(webhook_id: Optional[str] = None):
            """Obtiene estadísticas de webhooks."""
            result, error = safe_execute(
                self.webhook_manager.get_webhook_stats,
                default_value={},
                log_errors=False,
                webhook_id=webhook_id
            )
            
            if error:
                return {"error": "Error obteniendo estadísticas de webhooks"}
            
            return result
    
    def _register_health_checks(self):
        """Registra componentes para health check."""
        
        async def check_cache():
            """Verifica el cache."""
            def _get_cache_stats():
                stats = self.cache_manager.get_stats()
                return {
                    "status": "healthy" if stats.get("hit_rate", 0) >= 0 else "degraded",
                    "message": f"Cache hit rate: {stats.get('hit_rate', 0):.2f}%",
                    "details": stats
                }
            
            result, error = safe_execute(_get_cache_stats, default_value=None, log_errors=False)
            
            if error:
                return {
                    "status": "unhealthy",
                    "message": f"Cache error: {str(error)}"
                }
            
            return result
        
        async def check_task_queue():
            """Verifica la cola de tareas."""
            def _get_queue_stats():
                stats = self.task_queue.get_queue_stats()
                return {
                    "status": "healthy" if stats.get("queue_size", 0) < 1000 else "degraded",
                    "message": f"Queue size: {stats.get('queue_size', 0)}",
                    "details": stats
                }
            
            result, error = safe_execute(_get_queue_stats, default_value=None, log_errors=False)
            
            if error:
                return {
                    "status": "unhealthy",
                    "message": f"Queue error: {str(error)}"
                }
            
            return result
        
        async def check_storage():
            """Verifica el almacenamiento."""
            def _get_storage_stats():
                stats = self.storage.get_storage_stats()
                return {
                    "status": "healthy",
                    "message": f"Storage: {stats.get('total_files', 0)} files",
                    "details": stats
                }
            
            result, error = safe_execute(_get_storage_stats, default_value=None, log_errors=False)
            
            if error:
                return {
                    "status": "unhealthy",
                    "message": f"Storage error: {str(error)}"
                }
            
            return result
        
        # Registrar checks
        self.health_checker.register_component("cache", check_cache, critical=True)
        self.health_checker.register_component("task_queue", check_task_queue, critical=True)
        self.health_checker.register_component("storage", check_storage, critical=False)
        
        @self.app.get("/api/v1/task/{task_id}", response_model=TaskStatusResponse)
        async def get_task_status(task_id: str):
            """Obtiene el estado de una tarea."""
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tarea {task_id} no encontrada"
                )
            
            task = self.tasks[task_id]
            return TaskStatusResponse(
                task_id=task_id,
                status=task["status"],
                progress=task.get("progress"),
                result=task.get("result"),
                error=task.get("error"),
                created_at=task["created_at"],
                updated_at=task.get("updated_at", task["created_at"])
            )
    
    def _setup_websockets(self):
        """Configura endpoints WebSocket."""
        
        @self.app.websocket("/ws/task/{task_id}")
        async def websocket_task_updates(websocket: WebSocket, task_id: str):
            """WebSocket para updates de una tarea específica."""
            await connection_manager.connect(websocket, task_id)
            try:
                while True:
                    # Mantener conexión viva y escuchar mensajes
                    data = await websocket.receive_text()
                    # Opcional: procesar mensajes del cliente
                    await websocket.send_json({
                        "type": "ack",
                        "message": "Mensaje recibido"
                    })
            except WebSocketDisconnect:
                connection_manager.disconnect(websocket)
        
        @self.app.websocket("/ws/updates")
        async def websocket_general_updates(websocket: WebSocket):
            """WebSocket para updates generales."""
            await connection_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    await websocket.send_json({
                        "type": "ack",
                        "message": "Mensaje recibido"
                    })
            except WebSocketDisconnect:
                connection_manager.disconnect(websocket)
    
    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False
    ):
        """
        Ejecuta el servidor.
        
        Args:
            host: Host para el servidor
            port: Puerto para el servidor
            reload: Si True, recarga automática en desarrollo
        """
        try:
            import uvicorn
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                reload=reload
            )
        except ImportError:
            raise ImportError(
                "uvicorn no está instalado. Instala con: pip install uvicorn"
            )


# Los middlewares ahora se definen como funciones dentro de _setup_middleware

