"""
Agents Papers - Papers sobre Agentes LLM Autónomos
"""

from .paper_simura import SimuRAModule, SimuRAConfig
from .paper_concurrent_modular_agent import ConcurrentModularAgentModule, ConcurrentModularAgentConfig
from .paper_formal_llm import FormalLLMModule, FormalLLMConfig
from .paper_mars import MARSModule, MARSConfig

__all__ = [
    'SimuRAModule',
    'SimuRAConfig',
    'ConcurrentModularAgentModule',
    'ConcurrentModularAgentConfig',
    'FormalLLMModule',
    'FormalLLMConfig',
    'MARSModule',
    'MARSConfig'
]



