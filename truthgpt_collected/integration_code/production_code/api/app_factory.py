#!/usr/bin/env python3
"""
API App Factory
================

Factory function to create FastAPI app with modular routers and feature flags.
"""

from contextlib import asynccontextmanager
from typing import Optional, List, AsyncIterator, Callable, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.utils import setup_logger
from api.tracing import TracingMiddleware
from api.prometheus_metrics import PrometheusMetricsMiddleware, metrics_endpoint

logger = setup_logger(__name__)

# Import routers
from api.routes import memory, redundancy, pipeline, chat, config, monitoring
from api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage global resources and expose them via app.state.
    
    Initializes pipeline, config manager, monitor, and services during startup.
    Cleans up resources during shutdown.
    
    Args:
        app: FastAPI application instance
    
    Yields:
        None: Application is ready to serve requests
    
    Note:
        Resources are initialized lazily and safely with error handling.
        If a resource fails to initialize, it's logged but doesn't stop the app.
    """
    app.state.pipeline = None
    app.state.config_manager = None
    app.state.monitor = None
    app.state._resource_locks = {}
    app.state._resource_errors = {}

    try:
        # Initialize pipeline if available
        try:
            from integration_pipeline import create_integrated_pipeline
            pipeline = await _ensure_state_resource(
                app,
                "pipeline",
                lambda: create_integrated_pipeline(
                    enable_memory=True,
                    enable_redundancy=True
                ),
                True,
                "pipeline"
            )
            if pipeline:
                logger.info("Pipeline inicializado en lifespan")
        except ImportError:
            logger.warning("Pipeline module not available")
        except Exception as exc:
            logger.error(f"No se pudo inicializar pipeline: {exc}", exc_info=True)

        # Initialize config manager if available
        try:
            from core.config_manager import get_config_manager as load_config_manager
            config_manager = await _ensure_state_resource(
                app,
                "config_manager",
                load_config_manager,
                True,
                "config manager"
            )
            if config_manager:
                logger.info("Config manager inicializado en lifespan")
        except ImportError:
            logger.warning("Config manager module not available")
        except Exception as exc:
            logger.error(f"No se pudo inicializar config manager: {exc}", exc_info=True)

        # Initialize monitor if available
        try:
            from monitoring_system import get_system_monitor
            monitor = await _ensure_state_resource(
                app,
                "monitor",
                get_system_monitor,
                True,
                "monitor"
            )
            if monitor:
                logger.info("Monitor inicializado en lifespan")
        except ImportError:
            logger.warning("Monitor module not available")
        except Exception as exc:
            logger.error(f"No se pudo inicializar monitor: {exc}", exc_info=True)

        # Initialize services
        try:
            from api.dependencies import initialize_services
            initialize_services(
                pipeline=getattr(app.state, "pipeline", None),
                config_manager=getattr(app.state, "config_manager", None),
                monitor=getattr(app.state, "monitor", None)
            )
        except Exception as exc:
            logger.warning(f"Could not initialize services: {exc}")

        yield

    finally:
        # Cleanup
        pipeline = getattr(app.state, "pipeline", None)
        if pipeline and hasattr(pipeline, "shutdown"):
            try:
                pipeline.shutdown()
            except Exception as exc:
                logger.warning(f"Error apagando pipeline: {exc}")

        monitor = getattr(app.state, "monitor", None)
        if monitor and hasattr(monitor, "shutdown"):
            try:
                monitor.shutdown()
            except Exception as exc:
                logger.warning(f"Error apagando monitor: {exc}")


async def _ensure_state_resource(
    app: FastAPI,
    attr_name: str,
    factory: Callable[[], Any],
    enabled: bool,
    resource_label: str,
) -> Optional[Any]:
    """
    Initialize shared resources lazily and safely.
    
    Args:
        app: FastAPI application instance
        attr_name: Attribute name to store resource in app.state
        factory: Factory function to create the resource
        enabled: Whether the resource should be initialized
        resource_label: Human-readable label for logging
    
    Returns:
        Resource instance or None if disabled or initialization failed
    
    Note:
        Uses async locks to prevent race conditions during initialization.
        Errors are stored in app.state._resource_errors for debugging.
    """
    if not enabled:
        return None
    
    resource = getattr(app.state, attr_name, None)
    if resource is not None:
        return resource
    
    import asyncio
    locks = getattr(app.state, "_resource_locks", None)
    if locks is None:
        locks = {}
        app.state._resource_locks = locks
    
    lock = locks.get(attr_name)
    if lock is None:
        lock = asyncio.Lock()
        locks[attr_name] = lock
    
    async with lock:
        resource = getattr(app.state, attr_name, None)
        if resource is not None:
            return resource
        
        try:
            resource = await asyncio.to_thread(factory)
        except Exception as exc:
            logger.error(f"No se pudo inicializar {resource_label}: {exc}", exc_info=True)
            errors = getattr(app.state, "_resource_errors", None)
            if errors is None:
                errors = {}
                app.state._resource_errors = errors
            errors[attr_name] = exc
            return None
        
        setattr(app.state, attr_name, resource)
        errors = getattr(app.state, "_resource_errors", None)
        if errors and attr_name in errors:
            errors.pop(attr_name, None)
        logger.info(f"{resource_label} inicializado correctamente")
        return resource


def create_api_app(
    enable_memory: bool = True,
    enable_redundancy: bool = True,
    enable_pipeline: bool = True,
    enable_chat: bool = True,
    enable_config: bool = True,
    enable_monitor: bool = True,
    enable_auth: bool = False,
    cors_origins: Optional[List[str]] = None,
    app_name: str = "Production Code API",
    version: str = "2.0.0"
) -> FastAPI:
    """
    Factory function to create FastAPI app with modular routers.
    
    Args:
        enable_memory: Enable memory endpoints
        enable_redundancy: Enable redundancy endpoints
        enable_pipeline: Enable pipeline endpoints
        enable_chat: Enable chat endpoints
        enable_config: Enable config endpoints
        enable_monitor: Enable monitor endpoints
        enable_auth: Enable authentication (reads from env/config)
        cors_origins: List of allowed CORS origins (default: ["*"])
        app_name: Application name
        version: Application version
    
    Returns:
        Configured FastAPI app
    """
    # Create app
    app = FastAPI(
        title=app_name,
        description="API REST unificada para todos los módulos",
        version=version,
        lifespan=lifespan
    )
    
    # CORS
    origins = cors_origins if cors_origins is not None else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Tracing middleware (always enabled)
    app.add_middleware(TracingMiddleware)
    
    # Prometheus metrics middleware (always enabled if available)
    try:
        app.add_middleware(PrometheusMetricsMiddleware, app_name=app_name.lower().replace(" ", "_"))
        app.get("/metrics")(metrics_endpoint)
        logger.info("Prometheus metrics enabled")
    except Exception as e:
        logger.warning(f"Could not enable Prometheus metrics: {e}")
    
    # Additional middleware
    try:
        from api.middleware import LoggingMiddleware, MetricsMiddleware, ErrorHandlingMiddleware
        app.add_middleware(LoggingMiddleware)
        app.add_middleware(MetricsMiddleware)
        app.add_middleware(ErrorHandlingMiddleware)
        logger.info("Additional middleware loaded")
    except ImportError:
        logger.warning("Additional middleware not available")
    
    # Register routers based on flags
    if enable_memory:
        app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
        logger.info("Memory router enabled")
    
    if enable_redundancy:
        app.include_router(redundancy.router, prefix="/api/v1/redundancy", tags=["redundancy"])
        logger.info("Redundancy router enabled")
    
    if enable_pipeline:
        app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
        logger.info("Pipeline router enabled")
    
    if enable_chat:
        app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
        logger.info("Chat router enabled")
    
    if enable_config:
        app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
        logger.info("Config router enabled")
    
    if enable_monitor:
        app.include_router(monitoring.router, prefix="/api/v1/monitor", tags=["monitoring"])
        logger.info("Monitor router enabled")
    
    # Health router (always enabled)
    app.include_router(health_router, tags=["health"])
    
    # Root endpoint
    @app.get("/")
    async def root() -> Dict[str, Any]:
        """
        Root endpoint.
        
        Returns:
            Dictionary with application information, enabled features, and available endpoints
        """
        return {
            "name": app_name,
            "version": version,
            "status": "running",
            "features": {
                "memory": enable_memory,
                "redundancy": enable_redundancy,
                "pipeline": enable_pipeline,
                "chat": enable_chat,
                "config": enable_config,
                "monitor": enable_monitor,
                "auth": enable_auth
            },
            "endpoints": {
                "memory": "/api/v1/memory" if enable_memory else None,
                "redundancy": "/api/v1/redundancy" if enable_redundancy else None,
                "pipeline": "/api/v1/pipeline" if enable_pipeline else None,
                "chat": "/api/v1/chat" if enable_chat else None,
                "config": "/api/v1/config" if enable_config else None,
                "monitor": "/api/v1/monitor" if enable_monitor else None,
                "metrics": "/metrics",
                "health": "/health"
            }
        }
    
    logger.info(
        f"API app created",
        features={
            "memory": enable_memory,
            "redundancy": enable_redundancy,
            "pipeline": enable_pipeline,
            "chat": enable_chat,
            "config": enable_config,
            "monitor": enable_monitor,
            "auth": enable_auth
        }
    )
    
    return app

