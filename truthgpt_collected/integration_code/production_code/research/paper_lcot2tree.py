#!/usr/bin/env python3
"""
What Makes a Good Reasoning Chain? Uncovering Structural Patterns in Long Chain-of-Thought Reasoning
======================================================================================================
LCoT2Tree (2025)

Paper URL: https://aclanthology.org/[ID_PENDIENTE]
# Nota: Paper de ACL Anthology 2025, buscar "What Makes a Good Reasoning Chain? Uncovering Structural Patterns"
ACL Anthology 2025: What Makes a Good Reasoning Chain?

Técnica principal:
- Analiza patrones estructurales (exploración, backtracking, verificación) en cadenas de razonamiento largo
- Predice cuándo las cadenas son correctas
- Convierte cadenas largas en árboles para mejor análisis

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Análisis de Patrones Estructurales:
   - pattern(cadena) = {exploración, backtracking, verificación}
   - Implementado en: _analyze_structural_patterns()

2. Predicción de Correctitud:
   - P(correcta | cadena) = f(patrones(cadena))
   - Implementado en: _predict_correctness()

3. Conversión Chain-to-Tree:
   - tree = LCoT2Tree(cadena)
   - Implementado en: _convert_to_tree()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from core.paper_base import BasePaperModule, BasePaperConfig
from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)
@dataclass
class LCoT2TreeConfig(BasePaperConfig):
    """
    Configuración para LCoT2Tree (Production-Ready).
    
    Attributes:
        max_chain_length: Longitud máxima de cadena (debe ser > 0)
        pattern_types: Tipos de patrones a detectar (default: ['exploration', 'backtracking', 'verification'])
        correctness_threshold: Umbral de correctitud (0.0-1.0)
        use_tree_conversion: Si True, convierte cadena a árbol
        tree_branching_factor: Factor de ramificación del árbol (debe ser > 0)
        dropout_rate: Tasa de dropout para regularización (default: 0.1)
    """
    max_chain_length: int = 50
    pattern_types: List[str] = None
    correctness_threshold: float = 0.7
    use_tree_conversion: bool = True
    tree_branching_factor: int = 2
    dropout_rate: float = 0.1
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.pattern_types is None:
            self.pattern_types = ['exploration', 'backtracking', 'verification']
    
    def validate(self):
        """Valida la configuración de LCoT2Tree."""
        super().validate()
        if self.max_chain_length <= 0:
            raise ValueError(f"max_chain_length debe ser > 0, recibido: {self.max_chain_length}")
        if not self.pattern_types or len(self.pattern_types) == 0:
            raise ValueError("pattern_types no puede estar vacío")
        valid_patterns = ['exploration', 'backtracking', 'verification']
        for pattern in self.pattern_types:
            if pattern not in valid_patterns:
                raise ValueError(
                    f"pattern '{pattern}' no es válido. Debe ser uno de {valid_patterns}"
                )
        if not 0.0 <= self.correctness_threshold <= 1.0:
            raise ValueError(f"correctness_threshold debe estar en [0, 1], recibido: {self.correctness_threshold}")
        if self.tree_branching_factor <= 0:
            raise ValueError(f"tree_branching_factor debe ser > 0, recibido: {self.tree_branching_factor}")
        if not 0.0 <= self.dropout_rate < 1.0:
            raise ValueError(f"dropout_rate debe estar en [0, 1), recibido: {self.dropout_rate}")


class LCoT2TreeModule(BasePaperModule):
    """
    LCoT2Tree: Análisis de patrones estructurales en cadenas de razonamiento.
    
    EN EL PAPER: Sección 3 - Structural Pattern Analysis
    - El paper identifica patrones estructurales en cadenas largas
    - Analiza exploración, backtracking y verificación
    - Predice correctitud basado en patrones
    """
    
    def __init__(self, config: LCoT2TreeConfig):
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Pattern Detector
        # NOTACIÓN DEL PAPER: pattern_detector: cadena → {exploración, backtracking, verificación}
        # NOTACIÓN EN CÓDIGO: pattern_detector(x) = patrones detectados
        self.pattern_detector = nn.ModuleDict({
            pattern: nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.GELU(),
                nn.Dropout(config.dropout_rate),
                nn.Linear(config.hidden_dim // 2, 1),
                nn.Sigmoid()
            ) for pattern in config.pattern_types
        })
        
        # EN EL PAPER: Sección 3.2 - Correctness Predictor
        # NOTACIÓN DEL PAPER: P(correcta | patrones) = f(patrones)
        # NOTACIÓN EN CÓDIGO: correctness_predictor(patrones) = probabilidad
        self.correctness_predictor = nn.Sequential(
            nn.Linear(len(config.pattern_types), config.hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # EN EL PAPER: Sección 3.3 - Chain-to-Tree Converter
        # NOTACIÓN DEL PAPER: tree = convert(cadena)
        # NOTACIÓN EN CÓDIGO: tree_converter convierte cadena a árbol
        self.tree_converter = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim)
        )
        
        logger.info(f"LCoT2Tree initialized: patterns={config.pattern_types}")
    
    def _analyze_structural_patterns(self, hidden_states: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Analiza patrones estructurales en la cadena.
        
        EN EL PAPER: Sección 3.1 - Pattern Detection
        FÓRMULA: pattern_score = pattern_detector(x)
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # Calcular scores para cada patrón
        patterns = {}
        for pattern_name, detector in self.pattern_detector.items():
            # Promediar sobre secuencia para obtener score global
            pattern_input = hidden_states.mean(dim=1)  # [batch, hidden_dim]
            pattern_score = detector(pattern_input)  # [batch, 1]
            patterns[pattern_name] = pattern_score.squeeze(-1)  # [batch]
        
        return patterns
    
    def _predict_correctness(self, patterns: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Predice si la cadena es correcta basado en patrones.
        
        EN EL PAPER: Sección 3.2 - Correctness Prediction
        FÓRMULA: P(correcta) = correctness_predictor(patrones)
        """
        # Concatenar scores de patrones
        pattern_scores = torch.stack([patterns[p] for p in self.config.pattern_types], dim=-1)  # [batch, num_patterns]
        
        # Predecir correctitud
        correctness = self.correctness_predictor(pattern_scores)  # [batch, 1]
        return correctness.squeeze(-1)  # [batch]
    
    def _convert_to_tree(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Convierte cadena a estructura de árbol.
        
        EN EL PAPER: Sección 3.3 - Chain-to-Tree Conversion
        FÓRMULA: tree = LCoT2Tree(cadena)
        """
        # Aplicar conversión (simplificada)
        tree_output = self.tree_converter(hidden_states)
        return tree_output
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: análisis de patrones y predicción de correctitud.
        
        EN EL PAPER: Sección 4 - Reasoning Chain Analysis
        
        
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
        
        def _forward_analysis():
            # PASO 1: Analizar patrones estructurales
            patterns = self._analyze_structural_patterns(hidden_states)
            
            # PASO 2: Predecir correctitud
            correctness = self._predict_correctness(patterns)
            
            # PASO 3: Convertir a árbol si está habilitado
            if self.config.use_tree_conversion:
                output = self._convert_to_tree(hidden_states)
            else:
                output = hidden_states
            
            # Calcular métricas mejoradas
            avg_correctness = correctness.mean().item()
            pattern_scores = {p: patterns[p].mean().item() for p in self.config.pattern_types}
            is_correct = avg_correctness > self.config.correctness_threshold
            
            metadata = {
                'correctness_score': avg_correctness,
                'correctness_threshold': self.config.correctness_threshold,
                'is_correct': is_correct,
                'pattern_scores': pattern_scores,
                'pattern_types': self.config.pattern_types,
                'max_chain_length': self.config.max_chain_length,
                'use_tree_conversion': self.config.use_tree_conversion,
                'tree_branching_factor': self.config.tree_branching_factor,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item()
            }
            
            self._update_metrics(
                correctness=avg_correctness,
                is_correct=is_correct,
                **pattern_scores
            )
            
            return output, metadata
        
        result, error = safe_execute(_forward_analysis, default_value=None, log_errors=False)
        
        if error:
            logger.error(f"Error en forward de LCoT2Tree: {error}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(error),
                'correctness_score': 0.0,
                'is_correct': False,
                'pattern_scores': {p: 0.0 for p in self.config.pattern_types},
                'pattern_types': self.config.pattern_types
            }
            return hidden_states, error_metadata
        
        if result is None:
            error_metadata = {
                'error': 'Unknown error in forward',
                'correctness_score': 0.0,
                'is_correct': False,
                'pattern_scores': {p: 0.0 for p in self.config.pattern_types},
                'pattern_types': self.config.pattern_types
            }
            return hidden_states, error_metadata
        
        return result

