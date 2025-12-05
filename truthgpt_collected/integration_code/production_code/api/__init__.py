#!/usr/bin/env python3
"""
API Layer
=========

FastAPI routes and dependencies for the REST API.
"""

from .dependencies import (
    get_pipeline_service,
    get_memory_service,
    get_redundancy_service,
    get_chat_service,
    get_config_service,
    get_monitoring_service
)

__all__ = [
    'get_pipeline_service',
    'get_memory_service',
    'get_redundancy_service',
    'get_chat_service',
    'get_config_service',
    'get_monitoring_service'
]


