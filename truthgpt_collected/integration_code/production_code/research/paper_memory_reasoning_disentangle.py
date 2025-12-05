#!/usr/bin/env python3
"""
Disentangling Memory and Reasoning Ability in Large Language Models
====================================================================
Yao, Yu, Zhang, Narasimhan, et al. (2025)

Paper URL: https://aclanthology.org/[ID_PENDIENTE]
# Nota: Paper de ACL Anthology 2025, buscar "Disentangling Memory and Reasoning Ability in Large Language Models"
ACL Anthology 2025: Disentangling Memory and Reasoning Ability

Técnica principal:
- Separa capacidad de memoria de capacidad de razonamiento en LLMs
- Identifica qué parte del razonamiento es "memoria latente" vs "pensamiento activo"
- Permite entender mejor las capacidades de los modelos

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Separación Memoria-Razonamiento:
   - h_total = h_memory + h_reasoning
   - Implementado en: _disentangle()

2. Medición de Memoria Latente:
   - memory_score = f_memory(h)
   - Implementado en: _measure_memory()

3. Medición de Razonamiento Activo:
   - reasoning_score = f_reasoning(h)
   - Implementado en: _measure_reasoning()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from core.paper_base import BasePaperModule, BasePaperConfig
from core.utils import setup_logger

logger = setup_logger(__name__)
@dataclass
class MemoryReasoningDisentangleConfig(BasePaperConfig):
    """Configuración para Memory-Reasoning Disentanglement."""
    disentanglement_weight: float = 0.5  # Peso para separación
    memory_threshold: float = 0.5
    reasoning_threshold: float = 0.5
    use_orthogonal_projection: bool = True
    
    def validate(self):
        """Valida la configuración."""
        super().validate()


class MemoryReasoningDisentangleModule(BasePaperModule):
    """
    Disentangling Memory and Reasoning: Separa memoria de razonamiento.
    
    EN EL PAPER: Sección 3 - Disentanglement Framework
    - El paper separa representaciones de memoria y razonamiento
    - Identifica qué parte es memoria latente vs pensamiento activo
    """
    
    def __init__(self, config: MemoryReasoningDisentangleConfig):
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Memory Encoder
        # NOTACIÓN DEL PAPER: h_memory = memory_encoder(h)
        self.memory_encoder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.2 - Reasoning Encoder
        # NOTACIÓN DEL PAPER: h_reasoning = reasoning_encoder(h)
        self.reasoning_encoder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.3 - Memory Scorer
        # NOTACIÓN DEL PAPER: memory_score = f_memory(h)
        self.memory_scorer = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # EN EL PAPER: Sección 3.4 - Reasoning Scorer
        # NOTACIÓN DEL PAPER: reasoning_score = f_reasoning(h)
        self.reasoning_scorer = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        logger.info("Memory-Reasoning Disentanglement initialized")
    
    def _disentangle(self, hidden_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Separa memoria de razonamiento.
        
        EN EL PAPER: Sección 3.1 - Disentanglement
        FÓRMULA: h_memory = memory_encoder(h), h_reasoning = reasoning_encoder(h)
        """
        h_memory = self.memory_encoder(hidden_states)
        h_reasoning = self.reasoning_encoder(hidden_states)
        
        # EN EL PAPER: Proyección ortogonal para asegurar separación
        if self.config.use_orthogonal_projection:
            # FÓRMULA: h_reasoning = h_reasoning - proj(h_reasoning, h_memory)
            # Para hacer h_reasoning ortogonal a h_memory
            memory_norm = h_memory.norm(dim=-1, keepdim=True) + 1e-8
            projection = (h_reasoning * h_memory).sum(dim=-1, keepdim=True) / (memory_norm ** 2)
            h_reasoning = h_reasoning - projection * h_memory
        
        return h_memory, h_reasoning
    
    def _measure_memory(self, h_memory: torch.Tensor) -> torch.Tensor:
        """
        Mide componente de memoria.
        
        EN EL PAPER: Sección 3.3 - Memory Measurement
        FÓRMULA: memory_score = memory_scorer(h_memory)
        """
        memory_input = h_memory.mean(dim=1)  # [batch, hidden_dim]
        memory_score = self.memory_scorer(memory_input)  # [batch, 1]
        return memory_score.squeeze(-1)  # [batch]
    
    def _measure_reasoning(self, h_reasoning: torch.Tensor) -> torch.Tensor:
        """
        Mide componente de razonamiento.
        
        EN EL PAPER: Sección 3.4 - Reasoning Measurement
        FÓRMULA: reasoning_score = reasoning_scorer(h_reasoning)
        """
        reasoning_input = h_reasoning.mean(dim=1)  # [batch, hidden_dim]
        reasoning_score = self.reasoning_scorer(reasoning_input)  # [batch, 1]
        return reasoning_score.squeeze(-1)  # [batch]
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: separación memoria-razonamiento.
        
        EN EL PAPER: Sección 4 - Disentanglement Process
        
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado de shape [batch_size, seq_len, hidden_dim]
            - metadata: Diccionario con métricas e información adicional
        """
        # Validar inputs
        self.validate_inputs(hidden_states, **kwargs)
        
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Separar memoria y razonamiento
        h_memory, h_reasoning = self._disentangle(hidden_states)
        
        # PASO 2: Medir componentes
        memory_score = self._measure_memory(h_memory)
        reasoning_score = self._measure_reasoning(h_reasoning)
        
        # PASO 3: Combinar para output
        # FÓRMULA: h_output = α × h_memory + (1-α) × h_reasoning
        alpha = self.config.disentanglement_weight
        output = alpha * h_memory + (1 - alpha) * h_reasoning
        
        metadata = {
            'memory_score': memory_score.mean().item(),
            'reasoning_score': reasoning_score.mean().item(),
            'memory_ratio': memory_score.mean().item() / (memory_score.mean().item() + reasoning_score.mean().item() + 1e-8),
            'reasoning_ratio': reasoning_score.mean().item() / (memory_score.mean().item() + reasoning_score.mean().item() + 1e-8)
        }
        
        self._update_metrics(
            memory_score=metadata['memory_score'],
            reasoning_score=metadata['reasoning_score']
        )
        
        return output, metadata

