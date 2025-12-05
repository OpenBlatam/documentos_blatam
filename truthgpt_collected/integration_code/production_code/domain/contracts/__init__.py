"""
Domain contracts (Protocols/ABCs) that describe the expected behaviour of
core modules. Application and presentation layers depend on these interfaces
instead of concrete implementations so modules can be swapped freely.
"""

from .memory import MemoryModule  # noqa: F401
from .redundancy import RedundancyModule  # noqa: F401
from .chat import ChatEngineContract  # noqa: F401
from .pipeline import PipelineOrchestrator  # noqa: F401

__all__ = [
    "MemoryModule",
    "RedundancyModule",
    "ChatEngineContract",
    "PipelineOrchestrator",
]


