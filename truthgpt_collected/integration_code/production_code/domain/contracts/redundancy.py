"""
Contracts for redundancy/suppression modules.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, Tuple

import torch


class RedundancyModule(Protocol):
    """Contract for modules that remove redundancy from batched tensors."""

    def process_bulk(
        self,
        items: torch.Tensor,
        *,
        similarity_threshold: float | None = None,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        ...

    def get_metrics(self) -> Dict[str, Any]:
        ...


