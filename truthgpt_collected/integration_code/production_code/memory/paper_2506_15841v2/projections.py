#!/usr/bin/env python3
"""
Proyecciones Neurales para Memoria
===================================

Módulo que maneja las proyecciones neurales para memoria episódica y semántica.
"""

import torch
import torch.nn as nn
from typing import Optional

from core.utils import setup_logger

logger = setup_logger(__name__)


class MemoryProjections(nn.Module):
    """Maneja todas las proyecciones neurales del sistema de memoria."""
    
    def __init__(self, memory_dim: int, enable_semantic_search: bool = True):
        super().__init__()
        self.memory_dim = memory_dim
        
        self.episodic_projection = nn.Linear(memory_dim, memory_dim)
        self.semantic_projection = nn.Linear(memory_dim, memory_dim)
        
        nn.init.xavier_uniform_(self.episodic_projection.weight)
        nn.init.xavier_uniform_(self.semantic_projection.weight)
        if self.episodic_projection.bias is not None:
            nn.init.zeros_(self.episodic_projection.bias)
        if self.semantic_projection.bias is not None:
            nn.init.zeros_(self.semantic_projection.bias)
        
        if enable_semantic_search:
            self.semantic_encoder = nn.Linear(memory_dim, memory_dim)
            nn.init.xavier_uniform_(self.semantic_encoder.weight)
        else:
            self.semantic_encoder = None
    
    def project_episodic(self, x: torch.Tensor) -> torch.Tensor:
        """Proyecta tensor para memoria episódica."""
        return self.episodic_projection(x)
    
    def project_semantic(self, x: torch.Tensor) -> torch.Tensor:
        """Proyecta tensor para memoria semántica."""
        return self.semantic_projection(x)
    
    def encode_semantic(self, x: torch.Tensor) -> torch.Tensor:
        """Codifica tensor para búsqueda semántica."""
        if self.semantic_encoder is None:
            return x
        return self.semantic_encoder(x)

