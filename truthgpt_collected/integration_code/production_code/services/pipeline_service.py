#!/usr/bin/env python3
"""
Pipeline Service
===============

Business logic for pipeline operations.
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import torch
from core.utils import setup_logger
from core.error_handling import safe_execute

if TYPE_CHECKING:
    from integration_pipeline import IntegratedPipeline

logger = setup_logger(__name__)


class PipelineService:
    """Service for pipeline operations."""
    
    def __init__(self, pipeline: "IntegratedPipeline") -> None:
        """
        Initialize pipeline service.
        
        Args:
            pipeline: IntegratedPipeline instance
        
        Raises:
            ValueError: If pipeline is None
        """
        if pipeline is None:
            raise ValueError("Pipeline cannot be None")
        self.pipeline = pipeline
    
    def process(
        self,
        data: torch.Tensor,
        use_memory: bool = True,
        use_redundancy: bool = True
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Process data through pipeline.
        
        Args:
            data: Input tensor
            use_memory: Use memory module
            use_redundancy: Use redundancy module
        
        Returns:
            Tuple of (output tensor, metadata)
        
        Raises:
            ValueError: If pipeline is not initialized
            RuntimeError: If processing fails
        """
        if self.pipeline is None:
            raise ValueError("Pipeline not initialized")
        
        return safe_execute(
            lambda: self.pipeline.process_pipeline(
                data,
                use_memory=use_memory,
                use_redundancy=use_redundancy
            ),
            error_message="Error processing pipeline"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary with pipeline statistics
        
        Raises:
            ValueError: If pipeline is not initialized
            RuntimeError: If getting stats fails
        """
        if self.pipeline is None:
            raise ValueError("Pipeline not initialized")
        
        return safe_execute(
            lambda: self.pipeline.get_pipeline_stats(),
            error_message="Error getting pipeline stats"
        )
    
    def is_available(self) -> bool:
        """Check if pipeline is available."""
        return self.pipeline is not None


