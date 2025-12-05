"""
Contracts for memory-related modules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Sequence, Tuple

import torch


class MemoryModule(Protocol):
    """Contract that any episodic memory implementation must satisfy."""

    def store_episode(
        self,
        episode: torch.Tensor,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Sequence[str]] = None,
        priority: float = 1.0,
    ) -> bool:
        ...

    def retrieve_episodes(
        self,
        query: torch.Tensor,
        *,
        k: int = 10,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        ...

    def get_episodic_stats(self) -> Dict[str, Any]:
        ...

    @property
    def episodic_memory(self) -> Sequence[Any]:
        ...


