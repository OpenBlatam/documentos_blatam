#!/usr/bin/env python3
"""
Redundancy Service
==================

Business logic for redundancy operations.
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import torch
from core.utils import setup_logger
from core.error_handling import safe_execute

if TYPE_CHECKING:
    from integration_pipeline import IntegratedPipeline

logger = setup_logger(__name__)


class RedundancyService:
    """Service for redundancy operations."""
    
    def __init__(self, pipeline: "IntegratedPipeline") -> None:
        """
        Initialize redundancy service.
        
        Args:
            pipeline: IntegratedPipeline instance with redundancy module
        
        Raises:
            ValueError: If pipeline is None
        """
        if pipeline is None:
            raise ValueError("Pipeline cannot be None")
        self.pipeline = pipeline
    
    def process_bulk(
        self,
        items: torch.Tensor,
        similarity_threshold: Optional[float] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Process items removing redundancies.
        
        Args:
            items: Items tensor [batch, seq, features]
            similarity_threshold: Optional similarity threshold (ignored, uses config threshold)
        
        Returns:
            Tuple of (unique items, statistics)
        
        Raises:
            ValueError: If redundancy module is not available
            RuntimeError: If processing fails
        """
        if not self.is_available():
            raise ValueError("Redundancy module not available")
        
        # Note: similarity_threshold is configured at initialization
        # If needed, we could update the config, but for now we use the configured threshold
        return safe_execute(
            lambda: self.pipeline.redundancy_suppressor.process_bulk(items),
            error_message="Error processing redundancy"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get redundancy statistics.
        
        Returns:
            Dictionary with redundancy statistics
        
        Raises:
            ValueError: If redundancy module is not available
            RuntimeError: If getting stats fails
        """
        if not self.is_available():
            raise ValueError("Redundancy module not available")
        
        return safe_execute(
            lambda: self.pipeline.redundancy_suppressor.get_metrics(),
            error_message="Error getting redundancy stats"
        )
    
    def is_available(self) -> bool:
        """Check if redundancy module is available."""
        return (
            self.pipeline is not None
            and self.pipeline.enable_redundancy
            and self.pipeline.redundancy_suppressor is not None
        )

    @property
    def redundancy_suppressor(self) -> Optional[Any]:
        """
        Expose redundancy module for read-only metadata access.
        
        Returns:
            Redundancy suppressor instance or None if not available
        """
        return getattr(self.pipeline, "redundancy_suppressor", None)


