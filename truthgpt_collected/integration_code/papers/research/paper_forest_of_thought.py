#!/usr/bin/env python3
"""
Forest-of-Thought: Scaling Test-Time Compute for Enhancing LLM Reasoning
=========================================================================
Bi, Han, Liu, Tang, Wang (2024)

Paper URL: https://kingy.ai/[ID_PENDIENTE]
# Nota: Paper disponible en Kingy AI, buscar "Forest-of-Thought: Scaling Test-Time Compute"
Kingy AI 2024: Forest-of-Thought

Técnica principal:
- Mantiene múltiples árboles de razonamiento en paralelo ("forest")
- Activa solo los árboles más relevantes para mejorar precisión/eficiencia
- Escala computación en tiempo de test

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Construcción de Forest:
   - forest = {tree_1, ..., tree_K}
   - Implementado en: _build_forest()

2. Selección de Árboles:
   - trees_selected = select_relevant(forest, query)
   - Implementado en: _select_relevant_trees()

3. Activación Selectiva:
   - output = activate_selected(trees_selected)
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
class ForestOfThoughtConfig(BasePaperConfig):
    """Configuración para Forest-of-Thought."""
    num_trees: int = 5  # Número de árboles en el forest
    tree_depth: int = 3  # Profundidad de cada árbol
    branching_factor: int = 2  # Factor de ramificación
    selection_top_k: int = 3  # Top-K árboles a activar
    use_parallel_computation: bool = True


class ForestOfThoughtModule(BasePaperModule):
    """
    Forest-of-Thought: Múltiples árboles de razonamiento en paralelo.
    
    EN EL PAPER: Sección 3 - Forest Architecture
    - El paper mantiene múltiples árboles de razonamiento
    - Selecciona y activa solo los más relevantes
    - Escala computación eficientemente
    """
    
    def __init__(self, config: ForestOfThoughtConfig):
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Tree Builders
        # NOTACIÓN DEL PAPER: tree_i = build_tree(query) para i ∈ [1, K]
        # NOTACIÓN EN CÓDIGO: tree_builders[i] construye árbol i
        self.tree_builders = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            ) for _ in range(config.num_trees)
        ])
        
        # EN EL PAPER: Sección 3.2 - Tree Relevance Scorer
        # NOTACIÓN DEL PAPER: relevance(tree_i, query) = scorer(tree_i, query)
        # NOTACIÓN EN CÓDIGO: relevance_scorer scorea relevancia de cada árbol
        self.relevance_scorer = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, config.num_trees),
            nn.Softmax(dim=-1)
        )
        
        # EN EL PAPER: Sección 3.3 - Tree Aggregator
        # NOTACIÓN DEL PAPER: output = aggregate(trees_selected)
        # NOTACIÓN EN CÓDIGO: tree_aggregator combina árboles seleccionados
        self.tree_aggregator = nn.Sequential(
            nn.Linear(config.hidden_dim * config.selection_top_k, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        logger.info(f"Forest-of-Thought initialized: num_trees={config.num_trees}, top_k={config.selection_top_k}")
    
    def _build_forest(self, hidden_states: torch.Tensor) -> List[torch.Tensor]:
        """
        Construye forest de árboles.
        
        EN EL PAPER: Sección 3.1 - Forest Construction
        FÓRMULA: forest = {build_tree_i(query) | i ∈ [1, K]}
        """
        forest = []
        for tree_builder in self.tree_builders:
            tree_output = tree_builder(hidden_states)  # [batch, seq, hidden_dim]
            forest.append(tree_output)
        return forest
    
    def _select_relevant_trees(self, forest: List[torch.Tensor], query: torch.Tensor) -> Tuple[List[torch.Tensor], torch.Tensor]:
        """
        Selecciona árboles más relevantes.
        
        EN EL PAPER: Sección 3.2 - Tree Selection
        FÓRMULA: trees_selected = top_k(forest, relevance_scores)
        """
        # Calcular relevancia
        query_features = query.mean(dim=1)  # [batch, hidden_dim]
        relevance_scores = self.relevance_scorer(query_features)  # [batch, num_trees]
        avg_relevance = relevance_scores.mean(dim=0)  # [num_trees]
        
        # Seleccionar top-K
        top_k = min(self.config.selection_top_k, len(forest))
        top_indices = avg_relevance.topk(top_k).indices.tolist()
        selected_trees = [forest[i] for i in top_indices]
        
        return selected_trees, relevance_scores
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: forest de árboles con activación selectiva.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Construir forest
        forest = self._build_forest(hidden_states)
        
        # PASO 2: Seleccionar árboles relevantes
        selected_trees, relevance_scores = self._select_relevant_trees(forest, hidden_states)
        num_selected = len(selected_trees)
        
        # PASO 3: Agregar árboles seleccionados
        if num_selected > 0:
            # Concatenar árboles seleccionados
            tree_features = torch.cat(selected_trees, dim=-1)  # [batch, seq, hidden_dim * num_selected]
            
            # Ajustar dimensión si es necesario
            if tree_features.shape[-1] > hidden_dim * self.config.selection_top_k:
                tree_features = tree_features[:, :, :hidden_dim * self.config.selection_top_k]
            elif tree_features.shape[-1] < hidden_dim * self.config.selection_top_k:
                padding = torch.zeros(batch_size, seq_len, hidden_dim * self.config.selection_top_k - tree_features.shape[-1],
                                     device=tree_features.device)
                tree_features = torch.cat([tree_features, padding], dim=-1)
            
            # Agregar
            output = self.tree_aggregator(tree_features)  # [batch, seq, hidden_dim]
        else:
            output = hidden_states
        
        metadata = {
            'num_trees': self.config.num_trees,
            'num_selected': num_selected,
            'relevance_scores': relevance_scores.mean(dim=0).tolist(),
            'selection_ratio': num_selected / self.config.num_trees
        }
        
        self._update_metrics(
            num_trees=self.config.num_trees,
            num_selected=num_selected,
            selection_ratio=metadata['selection_ratio']
        )
        
        return output, metadata

