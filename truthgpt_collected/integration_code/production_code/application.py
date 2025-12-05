#!/usr/bin/env python3
"""
Application Factory
===================

Creates and configures the FastAPI application with proper lifecycle management.
"""

from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.utils import setup_logger
from api.routes import api_router, root_router
from api.dependencies import initialize_services
from api.middleware import RequestIDMiddleware, LoggingMiddleware, ErrorHandlingMiddleware

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown of the application.
    Initializes pipeline, config manager, monitor, and services during startup.
    Cleans up resources during shutdown.
    
    Args:
        app: FastAPI application instance
    
    Yields:
        None: Application is ready to serve requests
    
    Raises:
        RuntimeError: If startup fails (pipeline, config, or monitor initialization fails)
    
    Note:
        This is an async context manager used by FastAPI's lifespan parameter.
        All initialization happens during startup, and cleanup happens during shutdown.
    """
    logger.info("Starting application...")
    
    try:
        from integration_pipeline import create_integrated_pipeline
        from core.config_manager import get_config_manager
        from monitoring_system import get_system_monitor
        
        pipeline = create_integrated_pipeline(
            enable_memory=True,
            enable_redundancy=True
        )
        
        config_manager = get_config_manager()
        monitor = get_system_monitor()
        
        initialize_services(pipeline, config_manager, monitor)
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("Shutting down application...")
    logger.info("Application shut down complete")


def create_app(
    title: str = "Production Code API",
    description: str = "API REST unificada para todos los módulos",
    version: str = "2.0.0",
    cors_origins: Optional[List[str]] = None
) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        title: API title
        description: API description
        version: API version
        cors_origins: CORS allowed origins (default: ["*"])
    
    Returns:
        Configured FastAPI application
    
    Raises:
        RuntimeError: If application initialization fails
    
    Example:
        >>> app = create_app()
        >>> # Use with uvicorn: uvicorn.run(app)
    """
    if cors_origins is None:
        cors_origins = ["*"]
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Order matters: RequestID first, then logging, then error handling
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    app.include_router(api_router)
    app.include_router(root_router)
    
    logger.info(f"FastAPI application created: {title} v{version}")
    
    return app


_app_instance: Optional[FastAPI] = None


def get_app() -> FastAPI:
    """
    Get application instance (singleton pattern).
    
    Returns:
        FastAPI application instance
    """
    global _app_instance
    if _app_instance is None:
        _app_instance = create_app()
    return _app_instance

