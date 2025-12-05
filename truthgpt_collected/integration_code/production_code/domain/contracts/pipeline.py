"""
Contracts for orchestrated pipelines that combine multiple domain modules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Tuple, TYPE_CHECKING

import torch

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from .memory import MemoryModule
    from .redundancy import RedundancyModule
    from .chat import ChatEngineContract


class PipelineOrchestrator(Protocol):
    """Contract exposed by the integrated pipeline to the application layer."""

    def process_pipeline(
        self,
        data: torch.Tensor,
        *,
        use_memory: bool = True,
        use_redundancy: bool = True,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        ...

    def get_pipeline_stats(self) -> Dict[str, Any]:
        ...

    def process_with_memory(
        self,
        data: torch.Tensor,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        ...

    def process_with_redundancy(
        self,
        data: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        ...

    def chat_with_memory(
        self,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    @property
    def memory_system(self) -> Optional["MemoryModule"]:
        ...

    @property
    def redundancy_suppressor(self) -> Optional["RedundancyModule"]:
        ...

    @property
    def chat_engine(self) -> Optional["ChatEngineContract"]:
        ...

    @property
    def enable_memory(self) -> bool:
        ...

    @property
    def enable_redundancy(self) -> bool:
        ...

    @property
    def enable_chat(self) -> bool:
        ...


