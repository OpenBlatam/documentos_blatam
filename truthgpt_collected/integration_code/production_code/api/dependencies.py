#!/usr/bin/env python3
"""
Dependency Injection
====================

FastAPI dependencies for service injection.
"""

from typing import Optional, TYPE_CHECKING
from fastapi import Depends, Request
from functools import lru_cache

from services import (
    PipelineService,
    MemoryService,
    RedundancyService,
    ChatService,
    ConfigService,
    MonitoringService
)

if TYPE_CHECKING:
    from core.config_manager import ConfigManager
    from monitoring_system import SystemMonitor
    from integration_pipeline import IntegratedPipeline

# Global service instances (initialized in application factory)
_pipeline_service: Optional[PipelineService] = None
_memory_service: Optional[MemoryService] = None
_redundancy_service: Optional[RedundancyService] = None
_chat_service: Optional[ChatService] = None
_config_service: Optional[ConfigService] = None
_monitoring_service: Optional[MonitoringService] = None


def initialize_services(
    pipeline: "IntegratedPipeline",
    config_manager: "ConfigManager",
    monitor: Optional["SystemMonitor"] = None
) -> None:
    """
    Initialize all services with dependency injection.
    
    This function should be called during application startup to initialize
    all service instances that will be used throughout the application.
    
    Args:
        pipeline: IntegratedPipeline instance for pipeline operations
        config_manager: ConfigManager instance for configuration management
        monitor: Optional SystemMonitor instance for monitoring. If None,
                monitoring service will not be initialized.
    
    Raises:
        RuntimeError: If services are already initialized (prevents re-initialization)
        ValueError: If required services are None
    
    Example:
        >>> from integration_pipeline import create_integrated_pipeline
        >>> from core.config_manager import get_config_manager
        >>> from monitoring_system import get_system_monitor
        >>> 
        >>> pipeline = create_integrated_pipeline()
        >>> config = get_config_manager()
        >>> monitor = get_system_monitor()
        >>> initialize_services(pipeline, config, monitor)
    """
    global _pipeline_service, _memory_service, _redundancy_service
    global _chat_service, _config_service, _monitoring_service
    
    if _pipeline_service is not None:
        raise RuntimeError("Services already initialized. Cannot re-initialize.")
    
    if pipeline is None:
        raise ValueError("Pipeline cannot be None")
    if config_manager is None:
        raise ValueError("ConfigManager cannot be None")
    
    _pipeline_service = PipelineService(pipeline)
    _memory_service = MemoryService(pipeline)
    _redundancy_service = RedundancyService(pipeline)
    _chat_service = ChatService(pipeline)
    _config_service = ConfigService(config_manager)
    
    # Monitoring service is optional
    if monitor is not None:
        _monitoring_service = MonitoringService(monitor)
    else:
        _monitoring_service = None


def get_pipeline_service() -> PipelineService:
    """
    Get pipeline service instance via dependency injection.
    
    Returns:
        PipelineService instance for pipeline operations
    
    Raises:
        RuntimeError: If services have not been initialized
    
    Note:
        This function is designed to be used with FastAPI's Depends().
        Services must be initialized via initialize_services() during
        application startup.
    """
    if _pipeline_service is None:
        raise RuntimeError(
            "Services not initialized. "
            "Call initialize_services() during application startup."
        )
    return _pipeline_service


def get_memory_service() -> MemoryService:
    """
    Get memory service instance via dependency injection.
    
    Returns:
        MemoryService instance for memory operations
    
    Raises:
        RuntimeError: If services have not been initialized
    
    Note:
        This function is designed to be used with FastAPI's Depends().
    """
    if _memory_service is None:
        raise RuntimeError(
            "Services not initialized. "
            "Call initialize_services() during application startup."
        )
    return _memory_service


def get_redundancy_service() -> RedundancyService:
    """Get redundancy service instance."""
    if _redundancy_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _redundancy_service


def get_chat_service() -> ChatService:
    """Get chat service instance."""
    if _chat_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _chat_service


def get_config_service() -> ConfigService:
    """Get config service instance."""
    if _config_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _config_service


def get_monitoring_service() -> Optional[MonitoringService]:
    """
    Get monitoring service instance via dependency injection.
    
    Returns:
        MonitoringService instance if available, None otherwise
    
    Note:
        Monitoring service is optional. If not initialized during startup,
        this function returns None instead of raising an error.
    """
    return _monitoring_service


def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state."""
    return getattr(request.state, 'request_id', None)
