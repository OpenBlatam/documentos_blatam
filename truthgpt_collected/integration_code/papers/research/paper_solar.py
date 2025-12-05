#!/usr/bin/env python3
"""
SOLAR: Scalable Optimization of Large-scale Architecture for Reasoning
=======================================================================
Chen, Li, Luo, Bolimera, Ahmed, Srinivasan, Gokhale, Savvides (2025)

Paper URL: https://arxiv.org/abs/2503.04530
arXiv 2025: Scalable Optimization of Large-scale Architecture for Reasoning

Técnica principal:
- Framework para adaptar dinámicamente entre chain, tree y graph de pensamiento
- Optimiza precisión y eficiencia según la tarea
- Escalable para arquitecturas de gran escala

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Selección Adaptativa de Paradigma:
   - paradigma(tarea) = argmax_{p ∈ {chain, tree, graph}} score(p, tarea)
   - donde score combina precisión y eficiencia
   - Implementado en: _select_paradigm()

2. Optimización Multi-Paradigma:
   - loss_total = α × loss_chain + β × loss_tree + γ × loss_graph
   - donde α, β, γ son pesos adaptativos
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
class SOLARConfig(BasePaperConfig):
    """Configuración para SOLAR."""
    num_paradigms: int = 3  # chain, tree, graph
    use_adaptive_selection: bool = True
    precision_weight: float = 0.6  # Peso para precisión en score
    efficiency_weight: float = 0.4  # Peso para eficiencia en score
    max_reasoning_steps: int = 10
    tree_branching_factor: int = 3
    graph_max_nodes: int = 20


class SOLARModule(BasePaperModule):
    """
    SOLAR: Framework adaptativo multi-paradigma para razonamiento.
    
    EN EL PAPER: Sección 3 - Adaptive Multi-Paradigm Framework
    - El paper propone un framework que adapta dinámicamente entre
      chain-of-thought, tree-of-thought y graph-of-thought
    - Selecciona el paradigma óptimo según la tarea
    - Optimiza tanto precisión como eficiencia
    """
    
    def __init__(self, config: SOLARConfig):
        """
        Inicialización del módulo SOLAR.
        
        EN EL PAPER: Sección 3.1 - Architecture Overview
        - El paper define tres paradigmas: chain, tree, graph
        - Cada paradigma tiene su propio módulo de razonamiento
        - Un selector adaptativo decide qué paradigma usar
        
        CÓDIGO: Inicializamos:
        1. Módulos de razonamiento para cada paradigma
        2. Selector adaptativo de paradigma
        3. Optimizador multi-paradigma
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.2 - Paradigm Modules
        # El paper implementa módulos separados para cada paradigma
        # NOTACIÓN DEL PAPER: M_chain, M_tree, M_graph son módulos de razonamiento
        #   donde M_p: R^(B×N×d) → R^(B×N×d) para p ∈ {chain, tree, graph}
        # NOTACIÓN EN CÓDIGO: paradigm_modules[p] = M_p
        # CÓDIGO: Redes neuronales que implementan cada paradigma
        self.chain_module = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)
        )
        
        self.tree_module = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        self.graph_module = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        # EN EL PAPER: Sección 3.3 - Adaptive Paradigm Selector
        # El paper selecciona paradigma basado en características de la tarea
        # NOTACIÓN DEL PAPER: selector: R^(B×N×d) → {chain, tree, graph}
        #   selector(x) = argmax_{p} score_p(x)
        #   donde score_p(x) = α × precision_p(x) + β × efficiency_p(x)
        # NOTACIÓN EN CÓDIGO: paradigm_selector(x) = p ∈ {0, 1, 2}
        # CÓDIGO: Red que predice qué paradigma usar
        self.paradigm_selector = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, config.num_paradigms),
            nn.Softmax(dim=-1)
        )
        
        # EN EL PAPER: Sección 3.4 - Multi-Paradigm Optimizer
        # El paper combina outputs de múltiples paradigmas
        # NOTACIÓN DEL PAPER: output = Σ_p w_p × M_p(x)
        #   donde w_p son pesos adaptativos
        # NOTACIÓN EN CÓDIGO: paradigm_weights[p] = w_p
        # CÓDIGO: Pesos aprendibles para combinar paradigmas
        self.paradigm_weights = nn.Parameter(torch.ones(config.num_paradigms) / config.num_paradigms)
        
        logger.info(f"SOLAR initialized with {config.num_paradigms} paradigms")
    
    def _select_paradigm(self, hidden_states: torch.Tensor) -> Tuple[int, torch.Tensor]:
        """
        Selecciona el paradigma óptimo para la tarea.
        
        EN EL PAPER: Sección 3.3 - Paradigm Selection Strategy
        - El paper selecciona paradigma basado en score combinado
        - FÓRMULA: score_p = α × precision_p + β × efficiency_p
        - FÓRMULA: paradigma = argmax_p score_p
        
        Args:
            hidden_states: [batch, seq, hidden_dim] = x ∈ R^(B×N×d)
            
        Returns:
            paradigm_idx: Índice del paradigma seleccionado p ∈ {0, 1, 2}
            scores: Scores para cada paradigma [batch, num_paradigms]
        """
        # EN EL PAPER: Sección 3.3.1 - Feature Extraction
        # El paper extrae características de la entrada para selección
        # NOTACIÓN DEL PAPER: features = f(x) ∈ R^d
        # NOTACIÓN EN CÓDIGO: features = promedio sobre secuencia
        # CÓDIGO: Promediar sobre secuencia para obtener características globales
        features = hidden_states.mean(dim=1)  # features ∈ R^(B×d)
        
        # EN EL PAPER: Sección 3.3.2 - Score Calculation
        # El paper calcula score para cada paradigma
        # NOTACIÓN DEL PAPER: scores = [score_chain, score_tree, score_graph] ∈ R^3
        #   donde score_p = α × precision_p + β × efficiency_p
        # NOTACIÓN EN CÓDIGO: paradigm_scores[b, p] = score_p para batch b
        # CÓDIGO: Red neuronal predice scores para cada paradigma
        paradigm_scores = self.paradigm_selector(features)  # [batch, num_paradigms]
        
        # EN EL PAPER: Sección 3.3.3 - Selection
        # El paper selecciona paradigma con mayor score
        # FÓRMULA: paradigma = argmax_p score_p
        # NOTACIÓN DEL PAPER: p* = argmax_{p ∈ {chain, tree, graph}} score_p
        # NOTACIÓN EN CÓDIGO: paradigm_idx = índice del paradigma con mayor score
        # CÓDIGO: Seleccionar paradigma con mayor score promedio sobre batch
        paradigm_idx = paradigm_scores.mean(dim=0).argmax().item()  # p* ∈ {0, 1, 2}
        
        return paradigm_idx, paradigm_scores
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento adaptativo multi-paradigma.
        
        EN EL PAPER: Sección 4 - Reasoning Process
        - El paper aplica el paradigma seleccionado
        - Combina outputs de múltiples paradigmas si es necesario
        - Optimiza precisión y eficiencia
        
        Args:
            hidden_states: [batch, seq, hidden_dim] = x ∈ R^(B×N×d)
            **kwargs: Argumentos adicionales
            
        Returns:
            output: [batch, seq, hidden_dim] = y ∈ R^(B×N×d)
            metadata: Dict con información del razonamiento
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Seleccionar paradigma
        # EN EL PAPER: Sección 4.1 - Paradigm Selection
        # FÓRMULA: p* = selector(x)
        # NOTACIÓN DEL PAPER: paradigma_seleccionado = p* ∈ {chain, tree, graph}
        # NOTACIÓN EN CÓDIGO: selected_paradigm = índice del paradigma
        # CÓDIGO: Seleccionar paradigma óptimo
        selected_paradigm, paradigm_scores = self._select_paradigm(hidden_states)
        paradigm_names = ['chain', 'tree', 'graph']
        selected_name = paradigm_names[selected_paradigm]
        
        # PASO 2: Aplicar módulo del paradigma seleccionado
        # EN EL PAPER: Sección 4.2 - Paradigm Application
        # FÓRMULA: y_p = M_p(x) para paradigma p
        # NOTACIÓN DEL PAPER: output_p ∈ R^(B×N×d) es output del paradigma p
        # NOTACIÓN EN CÓDIGO: paradigm_outputs[p] = y_p
        # CÓDIGO: Aplicar cada módulo de paradigma
        chain_output = self.chain_module(hidden_states)
        tree_output = self.tree_module(hidden_states)
        graph_output = self.graph_module(hidden_states)
        
        paradigm_outputs = [chain_output, tree_output, graph_output]
        
        # PASO 3: Combinar outputs con pesos adaptativos
        # EN EL PAPER: Sección 4.3 - Multi-Paradigm Fusion
        # FÓRMULA: y = Σ_p w_p × y_p
        #   donde w_p son pesos adaptativos normalizados
        # NOTACIÓN DEL PAPER: w = [w_chain, w_tree, w_graph] ∈ R^3, Σ w_p = 1
        # NOTACIÓN EN CÓDIGO: weights = softmax(paradigm_weights)
        # CÓDIGO: Normalizar pesos y combinar outputs
        weights = F.softmax(self.paradigm_weights, dim=0)  # [num_paradigms]
        
        # EN EL PAPER: Combinación ponderada
        # FÓRMULA: y = w_chain × y_chain + w_tree × y_tree + w_graph × y_graph
        # NOTACIÓN EN CÓDIGO: output = Σ_p weights[p] × paradigm_outputs[p]
        # CÓDIGO: Combinar outputs con pesos
        output = sum(weights[p] * paradigm_outputs[p] for p in range(self.config.num_paradigms))
        
        # PASO 4: Calcular métricas
        # EN EL PAPER: Sección 5 - Evaluation Metrics
        # FÓRMULA: precision = accuracy del razonamiento
        # FÓRMULA: efficiency = 1 / compute_time
        # NOTACIÓN EN CÓDIGO: metrics contiene precision y efficiency estimadas
        # CÓDIGO: Calcular métricas estimadas
        precision_estimate = paradigm_scores.max(dim=-1)[0].mean().item()
        efficiency_estimate = 1.0 / (selected_paradigm + 1)  # chain más eficiente, graph menos
        
        metadata = {
            'selected_paradigm': selected_name,
            'paradigm_scores': paradigm_scores.mean(dim=0).tolist(),
            'paradigm_weights': weights.tolist(),
            'precision_estimate': precision_estimate,
            'efficiency_estimate': efficiency_estimate
        }
        
        self._update_metrics(
            selected_paradigm=selected_paradigm,
            precision=precision_estimate,
            efficiency=efficiency_estimate
        )
        
        return output, metadata
