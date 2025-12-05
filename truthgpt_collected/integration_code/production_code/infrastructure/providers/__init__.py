"""
Infrastructure providers expose factories that bind domain contracts to
real dependencies (FastAPI, Ray, monitoring backends, etc.).
"""

from .pipeline_provider import build_integrated_pipeline  # noqa: F401
from .monitoring_provider import build_system_monitor  # noqa: F401

__all__ = [
    "build_integrated_pipeline",
    "build_system_monitor",
]


