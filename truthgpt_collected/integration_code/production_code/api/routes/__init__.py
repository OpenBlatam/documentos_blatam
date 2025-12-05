#!/usr/bin/env python3
"""
API Routes
==========

FastAPI route handlers organized by domain.
"""

from fastapi import APIRouter

from .memory import router as memory_router
from .redundancy import router as redundancy_router
from .pipeline import router as pipeline_router
from .chat import router as chat_router
from .config import router as config_router
from .monitoring import router as monitoring_router
from .health import router as health_router
from .documents import router as documents_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(memory_router, prefix="/memory", tags=["memory"])
api_router.include_router(redundancy_router, prefix="/redundancy", tags=["redundancy"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(config_router, prefix="/config", tags=["config"])
api_router.include_router(monitoring_router, prefix="/monitor", tags=["monitoring"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])

# Root routes (no prefix)
root_router = APIRouter()
root_router.include_router(health_router, tags=["health"])

__all__ = ['api_router', 'root_router']


