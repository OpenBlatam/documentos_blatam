#!/usr/bin/env python3
"""
Self-guided Knowledgeable Network of Thoughts (kNoT)
====================================================
Chen, Yeh, Chen, Yang, Ming-Syan (2024)

Paper URL: https://arxiv.org/abs/[ID_PENDIENTE]
# Nota: Paper de arXiv 2024, buscar en arXiv con título "Self-guided Knowledgeable Network of Thoughts" o "kNoT"
arXiv 2024: Self-guided Knowledgeable Network of Thoughts

Técnica principal:
- Introduce red de "pensamientos" como nodos de un grafo
- Permite planes de razonamiento más complejos y flexibles
- No solo cadena o árbol, sino grafo completo

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Construcción de Red de Pensamientos:
   - G = (V, E) donde V son pensamientos y E son conexiones
   - Implementado en: _build_thought_network()

2. Guía Auto-Supervisada:
   - guide = self_guide(G, query)
   - Implementado en: _self_guide()

3. Razonamiento en Red:
   - output = reason_on_network(G, query)
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
class KNoTConfig(BasePaperConfig):
    """Configuración para kNoT."""
    max_thoughts: int = 15  # Máximo número de pensamientos (nodos)
    network_density: float = 0.4  # Densidad de conexiones
    use_self_guidance: bool = True
    knowledge_integration: bool = True


class KNoTModule(BasePaperModule):
    """
    kNoT: Self-guided Knowledgeable Network of Thoughts.
    
    EN EL PAPER: Sección 3 - Network of Thoughts Architecture
    - El paper construye una red de pensamientos (no solo cadena/árbol)
    - Cada nodo es un pensamiento con conocimiento integrado
    - Guía auto-supervisada para navegar la red
    """
    
    def __init__(self, config: KNoTConfig):
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Thought Encoder
        # NOTACIÓN DEL PAPER: h_thought = thought_encoder(x)
        self.thought_encoder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.2 - Knowledge Integrator
        # NOTACIÓN DEL PAPER: h_knowledge = knowledge_integrator(h, knowledge)
        self.knowledge_integrator = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.3 - Connection Predictor
        # NOTACIÓN DEL PAPER: connection(i, j) = connection_predictor(h_i, h_j)
        self.connection_predictor = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),
            nn.Sigmoid()
        )
        
        # EN EL PAPER: Sección 3.4 - Self-Guide Module
        # NOTACIÓN DEL PAPER: guide = self_guide(G, query)
        self.self_guide = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, config.max_thoughts),
            nn.Softmax(dim=-1)
        )
        
        # EN EL PAPER: Sección 3.5 - Reasoning Module
        # NOTACIÓN DEL PAPER: output = reason_on_network(G)
        self.reasoning_module = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        logger.info(f"kNoT initialized: max_thoughts={config.max_thoughts}, density={config.network_density}")
    
    def _build_thought_network(self, hidden_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Construye red de pensamientos.
        
        EN EL PAPER: Sección 3.2 - Network Construction
        FÓRMULA: G = (V, E) donde V son pensamientos y E son conexiones
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        num_thoughts = min(seq_len, self.config.max_thoughts)
        
        # Codificar pensamientos
        thought_inputs = hidden_states[:, :num_thoughts, :].mean(dim=0)  # [num_thoughts, hidden_dim]
        thought_embeddings = self.thought_encoder(thought_inputs)  # [num_thoughts, hidden_dim]
        
        # Construir conexiones
        adjacency = torch.zeros(num_thoughts, num_thoughts, device=hidden_states.device)
        for i in range(num_thoughts):
            for j in range(i + 1, num_thoughts):
                pair_embedding = torch.cat([thought_embeddings[i], thought_embeddings[j]])
                connection_score = self.connection_predictor(pair_embedding).squeeze()
                if connection_score > (1.0 - self.config.network_density):
                    adjacency[i, j] = 1.0
                    adjacency[j, i] = 1.0  # No dirigido
        
        return thought_embeddings, adjacency
    
    def _self_guide(self, thought_embeddings: torch.Tensor, query: torch.Tensor) -> torch.Tensor:
        """
        Guía auto-supervisada para navegar la red.
        
        EN EL PAPER: Sección 3.4 - Self-Guided Navigation
        FÓRMULA: guide = self_guide(G, query)
        """
        # Promediar pensamientos para obtener representación global
        network_embedding = thought_embeddings.mean(dim=0)  # [hidden_dim]
        
        # Combinar con query
        combined = network_embedding + query.mean(dim=1).mean(dim=0)  # [hidden_dim]
        
        # Generar guía
        guide = self.self_guide(combined)  # [max_thoughts]
        return guide
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento en red de pensamientos.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Construir red de pensamientos
        thought_embeddings, adjacency = self._build_thought_network(hidden_states)
        num_thoughts = thought_embeddings.shape[0]
        num_connections = adjacency.sum().item() / 2  # Dividir por 2 (no dirigido)
        
        # PASO 2: Guía auto-supervisada
        if self.config.use_self_guidance:
            guide = self._self_guide(thought_embeddings, hidden_states)
        else:
            guide = torch.ones(self.config.max_thoughts, device=hidden_states.device) / self.config.max_thoughts
        
        # PASO 3: Integrar conocimiento si está habilitado
        if self.config.knowledge_integration:
            # Simular integración de conocimiento
            knowledge_embedding = thought_embeddings.mean(dim=0, keepdim=True)  # [1, hidden_dim]
            combined = torch.cat([thought_embeddings, knowledge_embedding.expand(num_thoughts, -1)], dim=-1)
            thought_embeddings = self.knowledge_integrator(combined)
        
        # PASO 4: Razonamiento en red
        reasoning_output = self.reasoning_module(thought_embeddings)  # [num_thoughts, hidden_dim]
        
        # Aplicar guía
        guided_output = (guide[:num_thoughts].unsqueeze(-1) * reasoning_output).sum(dim=0)  # [hidden_dim]
        
        # Expandir a batch y secuencia
        output = guided_output.unsqueeze(0).unsqueeze(0).expand(batch_size, seq_len, -1)
        
        metadata = {
            'num_thoughts': num_thoughts,
            'num_connections': int(num_connections),
            'network_density': num_connections / (num_thoughts * (num_thoughts - 1) / 2) if num_thoughts > 1 else 0.0,
            'guide_entropy': -(guide * (guide + 1e-8).log()).sum().item()
        }
        
        self._update_metrics(
            num_thoughts=num_thoughts,
            num_connections=int(num_connections)
        )
        
        return output, metadata

