"""
Domain layer aggregating pure logic and contracts.

The concrete implementations live under existing packages such as `core/`,
`memory/`, `redundancy/`, etc.  This shortcut package simply exposes shared
protocols so the upper layers can depend on stable contracts.
"""

from .contracts import (  # noqa: F401
    MemoryModule,
    RedundancyModule,
    ChatEngineContract,
    PipelineOrchestrator,
)


