#!/usr/bin/env python3
"""
Monitoring Service
==================

Business logic for monitoring operations.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from core.utils import setup_logger
from core.error_handling import safe_execute

if TYPE_CHECKING:
    from monitoring_system import SystemMonitor

logger = setup_logger(__name__)


class MonitoringService:
    """Service for monitoring operations."""
    
    def __init__(self, monitor: Optional["SystemMonitor"]) -> None:
        """
        Initialize monitoring service.
        
        Args:
            monitor: SystemMonitor instance (can be None for optional monitoring)
        
        Note:
            Monitor can be None, in which case is_available() will return False
        """
        self.monitor = monitor
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get system status.
        
        Returns:
            Dictionary with system status
        
        Raises:
            ValueError: If monitor is not initialized
            RuntimeError: If getting status fails
        """
        if not self.is_available():
            raise ValueError("Monitor not initialized")
        
        return safe_execute(
            lambda: self.monitor.get_system_status(),
            error_message="Error getting system status"
        )
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get health checks.
        
        Returns:
            Dictionary with health information
        
        Raises:
            ValueError: If monitor is not initialized
            RuntimeError: If getting health fails
        """
        if not self.is_available():
            raise ValueError("Monitor not initialized")
        
        return safe_execute(
            lambda: self.monitor.health_monitor.get_overall_health(),
            error_message="Error getting health"
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics.
        
        Returns:
            Dictionary with metrics
        
        Raises:
            ValueError: If monitor is not initialized
            RuntimeError: If getting metrics fails
        """
        if not self.is_available():
            raise ValueError("Monitor not initialized")
        
        return safe_execute(
            lambda: self.monitor.metrics_collector.get_all_metrics(),
            error_message="Error getting metrics"
        )
    
    def is_available(self) -> bool:
        """Check if monitor is available."""
        return self.monitor is not None


