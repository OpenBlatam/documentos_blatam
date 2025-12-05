"""
Monitoring provider.
"""

from __future__ import annotations

from typing import Optional

from core.utils import setup_logger

try:
    from monitoring_system import SystemMonitor, get_system_monitor
except ImportError:  # pragma: no cover - optional dependency
    SystemMonitor = None  # type: ignore
    get_system_monitor = None  # type: ignore

logger = setup_logger(__name__)


def build_system_monitor() -> Optional["SystemMonitor"]:
    """Return a configured SystemMonitor instance if the module is available."""

    if get_system_monitor is None:
        logger.warning("Monitoring system not available in current environment")
        return None

    try:
        return get_system_monitor()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to initialize monitoring system: %s", exc, exc_info=True)
        return None


