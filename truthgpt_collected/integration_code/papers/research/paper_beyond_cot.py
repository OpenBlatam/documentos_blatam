#!/usr/bin/env python3
"""
Beyond Chain-of-Thought: Effective Graph-of-Thought Reasoning in Language Models
==================================================================================
Yao, Li, Zhao (2024)

Paper URL: https://bohrium.dp.tech/[ID_PENDIENTE]
# Nota: Paper disponible en bohrium.dp.tech, buscar "Beyond Chain-of-Thought: Effective Graph-of-Thought"
bohrium.dp.tech 2024: Beyond Chain-of-Thought

Técnica principal:
- Propone encoder para grafo de pensamientos
- Se fusiona con la entrada original para permitir razonamiento no secuencial
- Extiende chain-of-thought a graph-of-thought

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Graph Encoder:
   - h_graph = graph_encoder(G)
   - Implementado en: _encode_graph()

2. Fusion con Entrada:
   - h_fused = fuse(h_original, h_graph)
   - Implementado en: _fuse_with_input()

3. Razonamiento No-Secuencial:
   - output = reason_non_sequential(h_fused)
   - Implementado en: forward()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

from ..core.paper_base import BasePaperModule, BasePaperConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BeyondCoTConfig(BasePaperConfig):
    """Configuración para Beyond Chain-of-Thought."""
    graph_nodes: int = 12
    use_graph_encoder: bool = True
    fusion_method: str = 'attention'  # 'attention', 'concat', 'add'
    non_sequential_layers: int = 2


class BeyondCoTModule(BasePaperModule):
    """
    Beyond Chain-of-Thought: Graph-of-Thought con encoder.
    
    EN EL PAPER: Sección 3 - Graph Encoder Architecture
    - El paper propone encoder para grafo de pensamientos
    - Fusiona con entrada original
    - Permite razonamiento no secuencial
    """
    
    def __init__(self, config: BeyondCoTConfig):
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Graph Encoder
        # NOTACIÓN DEL PAPER: h_graph = graph_encoder(G)
        if config.use_graph_encoder:
            self.graph_encoder = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
        else:
            self.graph_encoder = nn.Identity()
        
        # EN EL PAPER: Sección 3.2 - Fusion Module
        # NOTACIÓN DEL PAPER: h_fused = fuse(h_original, h_graph)
        if config.fusion_method == 'attention':
            self.fusion_attention = nn.MultiheadAttention(config.hidden_dim, num_heads=4)
        elif config.fusion_method == 'concat':
            self.fusion_module = nn.Sequential(
                nn.Linear(config.hidden_dim * 2, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        else:  # add
            self.fusion_module = nn.Identity()
        
        # EN EL PAPER: Sección 3.3 - Non-Sequential Reasoning
        # NOTACIÓN DEL PAPER: output = reason_non_sequential(h_fused)
        self.non_sequential_reasoning = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            ) for _ in range(config.non_sequential_layers)
        ])
        
        logger.info(f"Beyond CoT initialized: graph_nodes={config.graph_nodes}, fusion={config.fusion_method}")
    
    def _encode_graph(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Codifica grafo de pensamientos.
        
        EN EL PAPER: Sección 3.1 - Graph Encoding
        FÓRMULA: h_graph = graph_encoder(G)
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        num_nodes = min(seq_len, self.config.graph_nodes)
        
        # Extraer nodos del grafo
        graph_nodes = hidden_states[:, :num_nodes, :].mean(dim=0)  # [num_nodes, hidden_dim]
        
        # Codificar
        graph_encoded = self.graph_encoder(graph_nodes)  # [num_nodes, hidden_dim]
        
        return graph_encoded
    
    def _fuse_with_input(self, original: torch.Tensor, graph: torch.Tensor) -> torch.Tensor:
        """
        Fusiona entrada original con grafo.
        
        EN EL PAPER: Sección 3.2 - Input-Graph Fusion
        FÓRMULA: h_fused = fuse(h_original, h_graph)
        """
        batch_size, seq_len, hidden_dim = original.shape
        
        if self.config.fusion_method == 'attention':
            # Usar atención
            # MultiheadAttention espera [seq_len, batch, hidden_dim]
            original_t = original.transpose(0, 1)  # [seq_len, batch, hidden_dim]
            graph_expanded = graph.unsqueeze(1).expand(-1, batch_size, -1)  # [nodes, batch, hidden_dim]
            fused, _ = self.fusion_attention(original_t, graph_expanded, graph_expanded)
            fused = fused.transpose(0, 1)  # [batch, seq_len, hidden_dim]
            return fused
        elif self.config.fusion_method == 'concat':
            # Concatenar
            graph_mean = graph.mean(dim=0, keepdim=True).expand(batch_size, seq_len, -1)  # [batch, seq, hidden]
            combined = torch.cat([original, graph_mean], dim=-1)  # [batch, seq, hidden*2]
            return self.fusion_module(combined)
        else:  # add
            # Sumar
            graph_mean = graph.mean(dim=0, keepdim=True).expand(batch_size, seq_len, -1)
            return original + graph_mean
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento no-secuencial con graph encoder.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Codificar grafo
        graph_encoded = self._encode_graph(hidden_states)
        
        # PASO 2: Fusionar con entrada
        fused = self._fuse_with_input(hidden_states, graph_encoded)
        
        # PASO 3: Aplicar razonamiento no-secuencial
        output = fused
        for reasoning_layer in self.non_sequential_reasoning:
            output = reasoning_layer(output)
        
        metadata = {
            'graph_nodes': graph_encoded.shape[0],
            'fusion_method': self.config.fusion_method,
            'non_sequential_layers': self.config.non_sequential_layers
        }
        
        self._update_metrics(
            graph_nodes=graph_encoded.shape[0],
            fusion_applied=True
        )
        
        return output, metadata

