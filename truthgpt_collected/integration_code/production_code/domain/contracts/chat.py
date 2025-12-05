"""
Chat engine contract.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol


class ChatEngineContract(Protocol):
    """Contract implemented by chat engines exposed to the application layer."""

    def chat(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...


