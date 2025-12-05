#!/usr/bin/env python3
"""
Memory Service
==============

Business logic for memory operations.
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import torch
from core.utils import setup_logger
from core.error_handling import safe_execute

if TYPE_CHECKING:
    from integration_pipeline import IntegratedPipeline

logger = setup_logger(__name__)


class MemoryService:
    """Service for memory operations."""
    
    def __init__(self, pipeline: "IntegratedPipeline") -> None:
        """
        Initialize memory service.
        
        Args:
            pipeline: IntegratedPipeline instance with memory module
        
        Raises:
            ValueError: If pipeline is None
        """
        if pipeline is None:
            raise ValueError("Pipeline cannot be None")
        self.pipeline = pipeline
    
    def store_episode(
        self,
        episode: torch.Tensor,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: float = 1.0
    ) -> bool:
        """
        Store episode in memory.
        
        Args:
            episode: Episode tensor
            metadata: Optional metadata
            tags: Optional tags
            priority: Priority value (0.0-10.0)
        
        Returns:
            True if successful
        
        Raises:
            ValueError: If episode is invalid or memory module unavailable
        """
        self._validate_episode(episode)
        self._validate_priority(priority)
        memory_module = self._require_memory_module()
        
        result, error = safe_execute(
            lambda: memory_module.store_episode(
                episode,
                metadata=metadata,
                tags=tags,
                priority=priority
            ),
            default_value=False
        )
        
        if error is not None:
            logger.error(f"Error storing episode: {error}")
            raise ValueError(f"Failed to store episode: {error}") from error
        
        return result
    
    def retrieve_episodes(
        self,
        query: torch.Tensor,
        k: int = 10
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Retrieve episodes from memory.
        
        Args:
            query: Query tensor
            k: Number of episodes to retrieve (1-1000)
        
        Returns:
            Tuple of (retrieved episodes, weights)
        
        Raises:
            ValueError: If query is invalid, k is out of range, or memory module unavailable
        """
        self._validate_query(query)
        self._validate_k(k)
        memory_module = self._require_memory_module()
        
        result, error = safe_execute(
            lambda: memory_module.retrieve_episodes(query, k=k),
            default_value=(torch.empty(0), torch.empty(0))
        )
        
        if error is not None:
            logger.error(f"Error retrieving episodes: {error}")
            raise ValueError(f"Failed to retrieve episodes: {error}") from error
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        
        Raises:
            ValueError: If memory module unavailable
        """
        memory_module = self._require_memory_module()
        
        result, error = safe_execute(
            lambda: memory_module.get_episodic_stats(),
            default_value={}
        )
        
        if error is not None:
            logger.error(f"Error getting memory stats: {error}")
            raise ValueError(f"Failed to get memory stats: {error}") from error
        
        return result
    
    def get_episode_count(self) -> int:
        """
        Get total number of stored episodes.
        
        Returns:
            Number of episodes in memory (0 if unavailable)
        """
        if not self.is_available():
            return 0
        
        memory_module = self.memory_module
        if memory_module is None:
            return 0
        
        episodic_memory = getattr(memory_module, "episodic_memory", None)
        if episodic_memory is None:
            return 0
        
        try:
            return len(episodic_memory)
        except (TypeError, AttributeError):
            return 0
    
    def is_available(self) -> bool:
        """Check if memory module is available."""
        return (
            self.pipeline is not None
            and getattr(self.pipeline, "enable_memory", False)
            and getattr(self.pipeline, "memory_system", None) is not None
        )
    
    @property
    def memory_module(self) -> Optional[Any]:
        """
        Get the underlying memory module.
        
        Returns:
            Memory module instance or None if not available
        """
        if self.pipeline is None:
            return None
        return getattr(self.pipeline, "memory_system", None)
    
    def _require_memory_module(self) -> Any:
        """
        Get memory module or raise if unavailable.
        
        Returns:
            Memory module instance
        
        Raises:
            ValueError: If memory module is not available
        """
        if not self.is_available():
            raise ValueError("Memory module not available")
        memory_module = self.memory_module
        if memory_module is None:
            raise ValueError("Memory system not initialized")
        return memory_module
    
    def _validate_episode(self, episode: torch.Tensor) -> None:
        """Validate episode tensor."""
        if not isinstance(episode, torch.Tensor):
            raise ValueError(f"Episode must be a torch.Tensor, got {type(episode).__name__}")
        if episode.numel() == 0:
            raise ValueError("Episode cannot be empty")
        if torch.isnan(episode).any() or torch.isinf(episode).any():
            raise ValueError("Episode contains NaN or Inf values")
    
    def _validate_query(self, query: torch.Tensor) -> None:
        """Validate query tensor."""
        if not isinstance(query, torch.Tensor):
            raise ValueError(f"Query must be a torch.Tensor, got {type(query).__name__}")
        if query.numel() == 0:
            raise ValueError("Query cannot be empty")
        if torch.isnan(query).any() or torch.isinf(query).any():
            raise ValueError("Query contains NaN or Inf values")
    
    def _validate_priority(self, priority: float) -> None:
        """Validate priority value."""
        if not isinstance(priority, (int, float)):
            raise ValueError(f"Priority must be numeric, got {type(priority).__name__}")
        if not (0.0 <= priority <= 10.0):
            raise ValueError(f"Priority must be between 0.0 and 10.0, got {priority}")
    
    def _validate_k(self, k: int) -> None:
        """Validate k parameter."""
        if not isinstance(k, int):
            raise ValueError(f"k must be an integer, got {type(k).__name__}")
        if k < 1 or k > 1000:
            raise ValueError(f"k must be between 1 and 1000, got {k}")
