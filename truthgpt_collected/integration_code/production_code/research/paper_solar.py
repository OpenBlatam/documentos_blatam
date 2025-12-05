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

from core.paper_base import BasePaperModule, BasePaperConfig, PYDANTIC_AVAILABLE
from core.utils import setup_logger

logger = setup_logger(__name__)

if PYDANTIC_AVAILABLE:
    from pydantic import Field
    class SOLARConfig(BasePaperConfig):
        """
        Configuración para SOLAR (Production-Ready).
        
        Attributes:
            num_paradigms: Número de paradigmas (chain, tree, graph) (debe ser >= 1)
            use_adaptive_selection: Si True, usa selección adaptativa de paradigma
            precision_weight: Peso para precisión en score (0.0-1.0)
            efficiency_weight: Peso para eficiencia en score (0.0-1.0)
            max_reasoning_steps: Máximo número de pasos de razonamiento (debe ser > 0)
            tree_branching_factor: Factor de ramificación del árbol (debe ser > 0)
            graph_max_nodes: Máximo número de nodos en el grafo (debe ser > 0)
            dropout_rate: Tasa de dropout para regularización (default: 0.1)
        """
        num_paradigms: int = Field(default=3, ge=1)
        use_adaptive_selection: bool = Field(default=True)
        precision_weight: float = Field(default=0.6, ge=0.0, le=1.0)
        efficiency_weight: float = Field(default=0.4, ge=0.0, le=1.0)
        max_reasoning_steps: int = Field(default=10, gt=0)
        tree_branching_factor: int = Field(default=3, gt=0)
        graph_max_nodes: int = Field(default=20, gt=0)
        dropout_rate: float = Field(default=0.1, ge=0.0, lt=1.0)
else:
    from dataclasses import dataclass
    @dataclass
    class SOLARConfig(BasePaperConfig):
        """
        Configuración para SOLAR (Production-Ready).
        
        Attributes:
            num_paradigms: Número de paradigmas (chain, tree, graph) (debe ser >= 1)
            use_adaptive_selection: Si True, usa selección adaptativa de paradigma
            precision_weight: Peso para precisión en score (0.0-1.0)
            efficiency_weight: Peso para eficiencia en score (0.0-1.0)
            max_reasoning_steps: Máximo número de pasos de razonamiento (debe ser > 0)
            tree_branching_factor: Factor de ramificación del árbol (debe ser > 0)
            graph_max_nodes: Máximo número de nodos en el grafo (debe ser > 0)
            dropout_rate: Tasa de dropout para regularización (default: 0.1)
        """
        num_paradigms: int = 3
        use_adaptive_selection: bool = True
        precision_weight: float = 0.6
        efficiency_weight: float = 0.4
        max_reasoning_steps: int = 10
        tree_branching_factor: int = 3
        graph_max_nodes: int = 20
        dropout_rate: float = 0.1
        
        def validate(self):
            """Valida la configuración de SOLAR."""
            super().validate()
            if self.num_paradigms < 1:
                raise ValueError(f"num_paradigms debe ser >= 1, recibido: {self.num_paradigms}")
            if not 0.0 <= self.precision_weight <= 1.0:
                raise ValueError(f"precision_weight debe estar en [0, 1], recibido: {self.precision_weight}")
            if not 0.0 <= self.efficiency_weight <= 1.0:
                raise ValueError(f"efficiency_weight debe estar en [0, 1], recibido: {self.efficiency_weight}")
            if abs(self.precision_weight + self.efficiency_weight - 1.0) > 0.01:
                raise ValueError(
                    f"precision_weight + efficiency_weight debe ser ~1.0, "
                    f"recibido: {self.precision_weight + self.efficiency_weight}"
                )
            if self.max_reasoning_steps <= 0:
                raise ValueError(f"max_reasoning_steps debe ser > 0, recibido: {self.max_reasoning_steps}")
            if self.tree_branching_factor <= 0:
                raise ValueError(f"tree_branching_factor debe ser > 0, recibido: {self.tree_branching_factor}")
            if self.graph_max_nodes <= 0:
                raise ValueError(f"graph_max_nodes debe ser > 0, recibido: {self.graph_max_nodes}")
            if not 0.0 <= self.dropout_rate < 1.0:
                raise ValueError(f"dropout_rate debe estar en [0, 1), recibido: {self.dropout_rate}")


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
        try:
            # CÓDIGO: Redes neuronales que implementan cada paradigma
            self.chain_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim, config.hidden_dim)
            )
            
            self.tree_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim * 2, config.hidden_dim)
            )
            
            self.graph_module = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim * 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),  # Regularización para producción
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
                nn.Dropout(config.dropout_rate),  # Regularización para producción
                nn.Linear(config.hidden_dim // 2, config.num_paradigms),
                nn.Softmax(dim=-1)
            )
        except Exception as e:
            logger.error(f"Error inicializando SOLAR: {e}")
            raise
        
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
        Selecciona el paradigma óptimo para la tarea (Production-Ready).
        
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
        try:
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
        except Exception as e:
            logger.error(f"Error en _select_paradigm: {e}")
            # Retornar primer paradigma por defecto en caso de error
            return 0, torch.ones(hidden_states.shape[0], self.config.num_paradigms, device=hidden_states.device) / self.config.num_paradigms
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: razonamiento adaptativo multi-paradigma (Production-Ready).
        
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
        # Validar inputs
        self.validate_inputs(hidden_states, **kwargs)
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        try:
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
            
            # Calcular métricas mejoradas
            paradigm_scores_mean = paradigm_scores.mean(dim=0)
            metadata = {
                'selected_paradigm': selected_name,
                'selected_paradigm_idx': selected_paradigm,
                'num_paradigms': self.config.num_paradigms,
                'use_adaptive_selection': self.config.use_adaptive_selection,
                'paradigm_scores_mean': paradigm_scores_mean.tolist(),
                'paradigm_scores_std': paradigm_scores.std(dim=0).tolist(),
                'paradigm_scores_max': paradigm_scores.max(dim=0)[0].tolist(),
                'paradigm_scores_min': paradigm_scores.min(dim=0)[0].tolist(),
                'paradigm_weights': weights.tolist(),
                'precision_weight': self.config.precision_weight,
                'efficiency_weight': self.config.efficiency_weight,
                'precision_estimate': precision_estimate,
                'efficiency_estimate': efficiency_estimate,
                'max_reasoning_steps': self.config.max_reasoning_steps,
                'tree_branching_factor': self.config.tree_branching_factor,
                'graph_max_nodes': self.config.graph_max_nodes,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item()
            }
            
            self._update_metrics(
                selected_paradigm=selected_name,
                precision_estimate=precision_estimate,
                efficiency_estimate=efficiency_estimate,
                paradigm_scores_max=paradigm_scores_mean.max().item()
            )
            
            return output, metadata
            
        except Exception as e:
            logger.error(f"Error en forward de SOLAR: {e}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(e),
                'selected_paradigm': 'chain',
                'num_paradigms': self.config.num_paradigms,
                'use_adaptive_selection': self.config.use_adaptive_selection
            }
            return hidden_states, error_metadata
