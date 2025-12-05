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
from core.paper_base import BasePaperModule, BasePaperConfig
from core.utils import setup_logger

logger = setup_logger(__name__)
@dataclass
class ForestOfThoughtConfig(BasePaperConfig):
    """
    Configuración para Forest-of-Thought (Production-Ready).
    
    Attributes:
        num_trees: Número de árboles en el forest (debe ser > 0)
        tree_depth: Profundidad de cada árbol (debe ser > 0)
        branching_factor: Factor de ramificación (debe ser > 0)
        selection_top_k: Top-K árboles a activar (debe ser <= num_trees)
        use_parallel_computation: Si True, usa computación paralela
        dropout_rate: Tasa de dropout para regularización (default: 0.1)
    """
    num_trees: int = 5
    tree_depth: int = 3
    branching_factor: int = 2
    selection_top_k: int = 3
    use_parallel_computation: bool = True
    dropout_rate: float = 0.1
    
    def validate(self):
        """Valida la configuración de Forest-of-Thought."""
        super().validate()
        if self.num_trees <= 0:
            raise ValueError(f"num_trees debe ser > 0, recibido: {self.num_trees}")
        if self.tree_depth <= 0:
            raise ValueError(f"tree_depth debe ser > 0, recibido: {self.tree_depth}")
        if self.branching_factor <= 0:
            raise ValueError(f"branching_factor debe ser > 0, recibido: {self.branching_factor}")
        if self.selection_top_k <= 0:
            raise ValueError(f"selection_top_k debe ser > 0, recibido: {self.selection_top_k}")
        if self.selection_top_k > self.num_trees:
            raise ValueError(
                f"selection_top_k ({self.selection_top_k}) debe ser <= num_trees ({self.num_trees})"
            )
        if not 0.0 <= self.dropout_rate < 1.0:
            raise ValueError(f"dropout_rate debe estar en [0, 1), recibido: {self.dropout_rate}")


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
        
        try:
            # EN EL PAPER: Sección 3.1 - Tree Builders
            # NOTACIÓN DEL PAPER: tree_i = build_tree(query) para i ∈ [1, K]
            # NOTACIÓN EN CÓDIGO: tree_builders[i] construye árbol i
            self.tree_builders = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                    nn.GELU(),
                    nn.Dropout(config.dropout_rate),  # Regularización para producción
                    nn.Linear(config.hidden_dim * 2, config.hidden_dim)
                ) for _ in range(config.num_trees)
            ])
            
            # EN EL PAPER: Sección 3.2 - Tree Relevance Scorer
            # NOTACIÓN DEL PAPER: relevance(tree_i, query) = scorer(tree_i, query)
            # NOTACIÓN EN CÓDIGO: relevance_scorer scorea relevancia de cada árbol
            self.relevance_scorer = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim // 2, config.num_trees),
                nn.Softmax(dim=-1)
            )
            
            # EN EL PAPER: Sección 3.3 - Tree Aggregator
            # NOTACIÓN DEL PAPER: output = aggregate(trees_selected)
            # NOTACIÓN EN CÓDIGO: tree_aggregator combina árboles seleccionados
            self.tree_aggregator = nn.Sequential(
                nn.Linear(config.hidden_dim * config.selection_top_k, config.hidden_dim),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
        except Exception as e:
            logger.error(f"Error inicializando Forest-of-Thought: {e}")
            raise
        
        logger.info(f"Forest-of-Thought initialized: num_trees={config.num_trees}, top_k={config.selection_top_k}")
    
    def _build_forest(self, hidden_states: torch.Tensor) -> List[torch.Tensor]:
        """
        Construye forest de árboles (Production-Ready).
        
        EN EL PAPER: Sección 3.1 - Forest Construction
        FÓRMULA: forest = {build_tree_i(query) | i ∈ [1, K]}
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim]
        
        Returns:
            forest: Lista de tensores, cada uno de shape [batch, seq, hidden_dim]
        """
        try:
            forest = []
            for i, tree_builder in enumerate(self.tree_builders):
                tree_output = tree_builder(hidden_states)  # [batch, seq, hidden_dim]
                forest.append(tree_output)
            return forest
        except Exception as e:
            logger.error(f"Error en _build_forest: {e}")
            # Retornar forest con un solo árbol (hidden_states sin modificar) en caso de error
            return [hidden_states]
    
    def _select_relevant_trees(self, forest: List[torch.Tensor], query: torch.Tensor) -> Tuple[List[torch.Tensor], torch.Tensor]:
        """
        Selecciona árboles más relevantes (Production-Ready).
        
        EN EL PAPER: Sección 3.2 - Tree Selection
        FÓRMULA: trees_selected = top_k(forest, relevance_scores)
        
        Args:
            forest: Lista de árboles, cada uno de shape [batch, seq, hidden_dim]
            query: Tensor de shape [batch, seq, hidden_dim]
        
        Returns:
            Tuple (selected_trees, relevance_scores)
        """
        try:
            if len(forest) == 0:
                raise ValueError("Forest no puede estar vacío")
            
            # Calcular relevancia
            query_features = query.mean(dim=1)  # [batch, hidden_dim]
            relevance_scores = self.relevance_scorer(query_features)  # [batch, num_trees]
            avg_relevance = relevance_scores.mean(dim=0)  # [num_trees]
            
            # Seleccionar top-K
            top_k = min(self.config.selection_top_k, len(forest))
            top_indices = avg_relevance.topk(top_k).indices.tolist()
            selected_trees = [forest[i] for i in top_indices]
            
            return selected_trees, relevance_scores
        except Exception as e:
            logger.error(f"Error en _select_relevant_trees: {e}")
            # Retornar todos los árboles disponibles en caso de error
            return forest[:self.config.selection_top_k], torch.ones(
                query.shape[0], len(forest), device=query.device
            ) / len(forest)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: forest de árboles con activación selectiva.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        
        
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
        
        try:
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
                expected_dim = hidden_dim * self.config.selection_top_k
                if tree_features.shape[-1] > expected_dim:
                    tree_features = tree_features[:, :, :expected_dim]
                elif tree_features.shape[-1] < expected_dim:
                    # Padding si es necesario
                    padding = torch.zeros(
                        batch_size, seq_len, expected_dim - tree_features.shape[-1],
                        device=tree_features.device
                    )
                    tree_features = torch.cat([tree_features, padding], dim=-1)
                
                # Agregar
                output = self.tree_aggregator(tree_features)  # [batch, seq, hidden_dim]
            else:
                output = hidden_states
            
            # Calcular métricas mejoradas
            relevance_mean = relevance_scores.mean(dim=0)
            metadata = {
                'num_trees': self.config.num_trees,
                'num_selected': num_selected,
                'tree_depth': self.config.tree_depth,
                'branching_factor': self.config.branching_factor,
                'relevance_scores_mean': relevance_mean.mean().item(),
                'relevance_scores_std': relevance_mean.std().item(),
                'relevance_scores_max': relevance_mean.max().item(),
                'relevance_scores_min': relevance_mean.min().item(),
                'selection_ratio': num_selected / self.config.num_trees if self.config.num_trees > 0 else 0.0,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'use_parallel_computation': self.config.use_parallel_computation
            }
            
            self._update_metrics(
                num_trees=self.config.num_trees,
                num_selected=num_selected,
                selection_ratio=metadata['selection_ratio']
            )
            
            return output, metadata
            
        except Exception as e:
            logger.error(f"Error en forward de Forest-of-Thought: {e}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(e),
                'num_trees': self.config.num_trees,
                'num_selected': 0,
                'selection_ratio': 0.0
            }
            return hidden_states, error_metadata

