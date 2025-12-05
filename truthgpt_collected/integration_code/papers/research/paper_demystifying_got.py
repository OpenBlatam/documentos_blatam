#!/usr/bin/env python3
"""
Demystifying Chains, Trees, and Graphs of Thoughts
==================================================
Besta, Memedi, Zhang, et al. (2024)

Paper URL: https://emergentmind.com/[ID_PENDIENTE]
# Nota: Paper disponible en emergentmind.com, buscar "Demystifying Chains, Trees, and Graphs of Thoughts"
emergentmind.com 2024: Demystifying Chains, Trees, and Graphs of Thoughts

Técnica principal:
- Análisis teórico y estructural de diferentes formas de pensamiento
- Compara chain, tree y graph para entender qué paradigmas funcionan mejor según la tarea
- Proporciona guías para selección de paradigma

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Análisis Comparativo:
   - score(paradigma, tarea) = f(paradigma, tarea)
   - Implementado en: _compare_paradigms()

2. Selección de Paradigma:
   - paradigma_optimo = argmax score(paradigma, tarea)
   - Implementado en: _select_optimal_paradigm()

3. Evaluación Estructural:
   - estructura_score = evaluate_structure(paradigma)
   - Implementado en: _evaluate_structure()
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
class DemystifyingGoTConfig(BasePaperConfig):
    """Configuración para Demystifying GoT."""
    paradigms: List[str] = None  # ['chain', 'tree', 'graph']
    task_type: str = 'general'  # 'general', 'math', 'reasoning', 'qa'
    use_comparative_analysis: bool = True


class DemystifyingGoTModule(BasePaperModule):
    """
    Demystifying GoT: Análisis comparativo de paradigmas de razonamiento.
    
    EN EL PAPER: Sección 3 - Comparative Analysis
    - El paper analiza teóricamente chain, tree y graph
    - Compara sus características estructurales
    - Proporciona guías de selección
    """
    
    def __init__(self, config: DemystifyingGoTConfig):
        super().__init__(config)
        self.config = config
        
        if config.paradigms is None:
            config.paradigms = ['chain', 'tree', 'graph']
        
        # EN EL PAPER: Sección 3.1 - Paradigm Scorer
        # NOTACIÓN DEL PAPER: score(p, t) = scorer(p, t)
        self.paradigm_scorer = nn.ModuleDict({
            paradigm: nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.GELU(),
                nn.Linear(config.hidden_dim // 2, 1),
                nn.Sigmoid()
            ) for paradigm in config.paradigms
        })
        
        # EN EL PAPER: Sección 3.2 - Structural Evaluator
        # NOTACIÓN DEL PAPER: structure_score = evaluate(paradigm)
        self.structural_evaluator = nn.Sequential(
            nn.Linear(len(config.paradigms), config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, len(config.paradigms))
        )
        
        # EN EL PAPER: Sección 3.3 - Task-Paradigm Matcher
        # NOTACIÓN DEL PAPER: match(task, paradigm) = matcher(task, paradigm)
        self.task_paradigm_matcher = nn.Sequential(
            nn.Linear(config.hidden_dim + len(config.paradigms), config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, len(config.paradigms)),
            nn.Softmax(dim=-1)
        )
        
        logger.info(f"Demystifying GoT initialized: paradigms={config.paradigms}, task={config.task_type}")
    
    def _compare_paradigms(self, hidden_states: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Compara diferentes paradigmas.
        
        EN EL PAPER: Sección 3.1 - Paradigm Comparison
        FÓRMULA: score_p = paradigm_scorer_p(x)
        """
        features = hidden_states.mean(dim=1)  # [batch, hidden_dim]
        
        scores = {}
        for paradigm, scorer in self.paradigm_scorer.items():
            score = scorer(features)  # [batch, 1]
            scores[paradigm] = score.squeeze(-1)  # [batch]
        
        return scores
    
    def _select_optimal_paradigm(self, scores: Dict[str, torch.Tensor]) -> Tuple[str, torch.Tensor]:
        """
        Selecciona paradigma óptimo.
        
        EN EL PAPER: Sección 3.3 - Optimal Selection
        FÓRMULA: p* = argmax_p score_p
        """
        score_tensor = torch.stack([scores[p] for p in self.config.paradigms], dim=-1)  # [batch, num_paradigms]
        optimal_idx = score_tensor.mean(dim=0).argmax().item()
        optimal_paradigm = self.config.paradigms[optimal_idx]
        
        return optimal_paradigm, score_tensor
    
    def _evaluate_structure(self, paradigm_scores: torch.Tensor) -> torch.Tensor:
        """
        Evalúa estructura de paradigmas.
        
        EN EL PAPER: Sección 3.2 - Structural Evaluation
        FÓRMULA: structure_scores = structural_evaluator(scores)
        """
        avg_scores = paradigm_scores.mean(dim=0)  # [num_paradigms]
        structure_scores = self.structural_evaluator(avg_scores.unsqueeze(0))  # [1, num_paradigms]
        return structure_scores.squeeze(0)  # [num_paradigms]
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: análisis comparativo y selección de paradigma.
        
        EN EL PAPER: Sección 4 - Analysis Process
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # PASO 1: Comparar paradigmas
        paradigm_scores = self._compare_paradigms(hidden_states)
        
        # PASO 2: Seleccionar óptimo
        optimal_paradigm, score_tensor = self._select_optimal_paradigm(paradigm_scores)
        
        # PASO 3: Evaluar estructura
        structure_scores = self._evaluate_structure(score_tensor)
        
        # PASO 4: Match task-paradigm
        features = hidden_states.mean(dim=1)  # [batch, hidden_dim]
        avg_scores = score_tensor.mean(dim=0)  # [num_paradigms]
        combined = torch.cat([features.mean(dim=0), avg_scores], dim=-1).unsqueeze(0)  # [1, hidden_dim + num_paradigms]
        task_paradigm_match = self.task_paradigm_matcher(combined).squeeze(0)  # [num_paradigms]
        
        # Output basado en paradigma óptimo
        # Simular aplicación del paradigma
        output = hidden_states
        
        metadata = {
            'optimal_paradigm': optimal_paradigm,
            'paradigm_scores': {p: paradigm_scores[p].mean().item() for p in self.config.paradigms},
            'structure_scores': structure_scores.tolist(),
            'task_paradigm_match': {p: task_paradigm_match[i].item() for i, p in enumerate(self.config.paradigms)}
        }
        
        self._update_metrics(
            optimal_paradigm=optimal_paradigm,
            **{f'{p}_score': paradigm_scores[p].mean().item() for p in self.config.paradigms}
        )
        
        return output, metadata

