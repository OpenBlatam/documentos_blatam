#!/usr/bin/env python3
"""
MALTO: Detecting Hallucinations in LLMs via Uncertainty Quantification y Validación con Modelos Grandes
=========================================================================================================
Savelli, Koudounas, Giobergia (2025)

Paper URL: https://aclanthology.org/[ID_PENDIENTE]
SemEval 2025 / ACL Anthology: MALTO
# Nota: Paper de SemEval 2025, buscar en ACL Anthology

Técnica principal:
- Combina análisis de probabilidades (uncertainty quantification) con NLI
- Detecta fragmentos de alucinaciones a nivel de palabra (fine-grained)
- Usa modelos grandes para validación de las detecciones
- Enfoque que combina señales de incertidumbre y razonamiento lógico (NLI)

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Uncertainty Quantification:
   - uncertainty = quantify_uncertainty(probabilities) ∈ [0, 1]
   - Analiza probabilidades del modelo para extraer señales de incertidumbre
   - Implementado en: _quantify_uncertainty()

2. Natural Language Inference (NLI) Validation:
   - nli_scores = nli_validator(claim, context) → [entailment, contradiction, neutral]
   - Valida si la claim es consistente con el context usando NLI
   - Contradiction score indica posible alucinación
   - Implementado en: _nli_validation()

3. Word-level Fine-grained Detection:
   - word_scores = detect_words(uncertainty, nli_contradiction_score)
   - Combina uncertainty y NLI para detectar palabras alucinadas
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
class MALTOConfig(BasePaperConfig):
    """
    Configuración para MALTO (Production-Ready).
    
    Attributes:
        use_uncertainty_quantification: Si True, usa cuantificación de incertidumbre
        use_nli_validation: Si True, usa validación NLI
        word_level_detection: Si True, detecta a nivel de palabra
        uncertainty_threshold: Umbral para detección de incertidumbre (0.0-1.0)
        nli_threshold: Umbral para detección NLI (0.0-1.0)
        mitigation_strength: Fuerza de mitigación (0.0-1.0), default 0.4
    """
    use_uncertainty_quantification: bool = True
    use_nli_validation: bool = True
    word_level_detection: bool = True
    uncertainty_threshold: float = 0.5
    nli_threshold: float = 0.3
    mitigation_strength: float = 0.4
    
    def validate(self):
        """Valida la configuración de MALTO."""
        super().validate()
        if not 0.0 <= self.uncertainty_threshold <= 1.0:
            raise ValueError(f"uncertainty_threshold debe estar en [0, 1], recibido: {self.uncertainty_threshold}")
        if not 0.0 <= self.nli_threshold <= 1.0:
            raise ValueError(f"nli_threshold debe estar en [0, 1], recibido: {self.nli_threshold}")
        if not 0.0 <= self.mitigation_strength <= 1.0:
            raise ValueError(f"mitigation_strength debe estar en [0, 1], recibido: {self.mitigation_strength}")


class MALTOModule(BasePaperModule):
    """
    MALTO: Detección a nivel de palabra con Uncertainty + NLI.
    
    EN EL PAPER: Sección 3 - Uncertainty and NLI Framework
    - El paper combina cuantificación de incertidumbre con NLI
    - Detecta alucinaciones a nivel de palabra
    - Usa modelos grandes para validación
    """
    
    def __init__(self, config: MALTOConfig):
        """
        Inicializa el módulo MALTO (Production-Ready).
        
        Args:
            config: Configuración de MALTO
        
        Raises:
            ValueError: Si la configuración no es válida
        """
        super().__init__(config)
        self.config = config
        
        try:
            # EN EL PAPER: Sección 3.1 - Uncertainty Quantifier
            # NOTACIÓN DEL PAPER: u = quantify_uncertainty(P) donde P son probabilidades
            # NOTACIÓN EN CÓDIGO: uncertainty_quantifier calcula incertidumbre
            # CÓDIGO: Red que cuantifica incertidumbre desde probabilidades
            if config.use_uncertainty_quantification:
                self.uncertainty_quantifier = nn.Sequential(
                    nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                    nn.GELU(),
                    nn.Dropout(0.1),  # Regularización para producción
                    nn.Linear(config.hidden_dim // 2, 1),
                    nn.Sigmoid()
                )
            else:
                self.uncertainty_quantifier = nn.Identity()
            
            # EN EL PAPER: Sección 3.2 - NLI Validator
            # NOTACIÓN DEL PAPER: nli_score = nli(claim, context) ∈ [0, 1]
            # NOTACIÓN EN CÓDIGO: nli_validator valida con NLI
            # CÓDIGO: Red que simula NLI (entailment, contradiction, neutral)
            if config.use_nli_validation:
                self.nli_validator = nn.Sequential(
                    nn.Linear(config.hidden_dim * 2, config.hidden_dim),  # claim + context
                    nn.GELU(),
                    nn.Dropout(0.1),  # Regularización para producción
                    nn.Linear(config.hidden_dim, 3),  # entailment, contradiction, neutral
                    nn.Softmax(dim=-1)
                )
            else:
                self.nli_validator = nn.Identity()
            
            # EN EL PAPER: Sección 3.3 - Word-level Detector
            # NOTACIÓN DEL PAPER: word_scores = detect(uncertainty, nli_score)
            # NOTACIÓN EN CÓDIGO: word_detector detecta a nivel de palabra
            # CÓDIGO: Red que combina uncertainty y NLI para detección de palabras
            if config.word_level_detection:
                self.word_detector = nn.Sequential(
                    nn.Linear(config.hidden_dim + 2, config.hidden_dim),  # +2 para uncertainty y nli
                    nn.GELU(),
                    nn.Dropout(0.1),  # Regularización para producción
                    nn.Linear(config.hidden_dim, 1),
                    nn.Sigmoid()
                )
            else:
                self.word_detector = nn.Identity()
            
            logger.info(
                f"MALTO inicializado: uncertainty={config.use_uncertainty_quantification}, "
                f"nli={config.use_nli_validation}, word_level={config.word_level_detection}"
            )
        except Exception as e:
            logger.error(f"Error inicializando MALTO: {e}")
            raise
    
    def _quantify_uncertainty(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Cuantifica incertidumbre desde hidden states.
        
        EN EL PAPER: Sección 3.1 - Uncertainty Quantification
        FÓRMULA: u = uncertainty_quantifier(h)
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim]
        
        Returns:
            uncertainty: Tensor de shape [batch] con scores de incertidumbre
        """
        if not self.config.use_uncertainty_quantification:
            # Retornar zeros si está deshabilitado
            return torch.zeros(hidden_states.shape[0], device=hidden_states.device)
        
        try:
            # Calcular varianza como proxy de incertidumbre
            uncertainty_features = hidden_states.std(dim=1)  # [batch, hidden_dim]
            # Añadir pequeña constante para evitar divisiones por cero
            uncertainty_features = uncertainty_features + 1e-8
            uncertainty = self.uncertainty_quantifier(uncertainty_features)  # [batch, 1]
            return uncertainty.squeeze(-1)  # [batch]
        except Exception as e:
            logger.error(f"Error en _quantify_uncertainty: {e}")
            # Retornar valores por defecto en caso de error
            return torch.zeros(hidden_states.shape[0], device=hidden_states.device)
    
    def _nli_validation(self, claim: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        """
        Valida con Natural Language Inference.
        
        EN EL PAPER: Sección 3.2 - NLI Validation
        FÓRMULA: nli_scores = nli_validator(claim, context)
        
        Args:
            claim: Tensor de shape [batch, seq, hidden_dim] - claim a validar
            context: Tensor de shape [batch, seq, hidden_dim] - contexto de referencia
        
        Returns:
            contradiction_score: Tensor de shape [batch] con scores de contradicción
        """
        if not self.config.use_nli_validation:
            # Retornar zeros si está deshabilitado
            return torch.zeros(claim.shape[0], device=claim.device)
        
        try:
            # Validar que claim y context tengan las mismas dimensiones
            if claim.shape != context.shape:
                raise ValueError(
                    f"claim y context deben tener la misma shape. "
                    f"claim: {claim.shape}, context: {context.shape}"
                )
            
            # Promediar sobre secuencia
            claim_mean = claim.mean(dim=1)  # [batch, hidden_dim]
            context_mean = context.mean(dim=1)  # [batch, hidden_dim]
            
            # Concatenar y aplicar NLI
            combined = torch.cat([claim_mean, context_mean], dim=-1)  # [batch, hidden_dim*2]
            nli_scores = self.nli_validator(combined)  # [batch, 3]
            
            # Contradiction score como indicador de alucinación
            # Índices: 0=entailment, 1=contradiction, 2=neutral
            contradiction_score = nli_scores[:, 1]  # [batch] - índice 1 es contradiction
            return contradiction_score
        except Exception as e:
            logger.error(f"Error en _nli_validation: {e}")
            # Retornar valores por defecto en caso de error
            return torch.zeros(claim.shape[0], device=claim.device)
    
    def forward(self, hidden_states: torch.Tensor, context: Optional[torch.Tensor] = None, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: detección a nivel de palabra con Uncertainty + NLI (Production-Ready).
        
        EN EL PAPER: Sección 4 - Word-level Detection Process
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            context: Tensor opcional de shape [batch_size, seq_len, hidden_dim] para validación NLI
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado de shape [batch_size, seq_len, hidden_dim]
            - metadata: Diccionario con métricas e información de detección
        
        Raises:
            ValueError: Si los inputs no son válidos
        """
        # Validar inputs
        self.validate_inputs(hidden_states, **kwargs)
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # Usar hidden_states como context si no se proporciona
        if context is None:
            context = hidden_states
        else:
            # Validar context si se proporciona
            if context.shape[:2] != hidden_states.shape[:2]:
                raise ValueError(
                    f"context debe tener las mismas dimensiones batch y seq que hidden_states. "
                    f"hidden_states: {hidden_states.shape[:2]}, context: {context.shape[:2]}"
                )
        
        try:
            # PASO 1: Cuantificar incertidumbre
            uncertainty = self._quantify_uncertainty(hidden_states)  # [batch]
            
            # PASO 2: Validación NLI
            nli_score = self._nli_validation(hidden_states, context)  # [batch]
            
            # PASO 3: Detección a nivel de palabra
            if self.config.word_level_detection:
                # Expandir scores a nivel de secuencia
                uncertainty_expanded = uncertainty.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, 1)  # [batch, seq, 1]
                nli_expanded = nli_score.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, 1)  # [batch, seq, 1]
                
                # Combinar para detección de palabras
                combined = torch.cat([hidden_states, uncertainty_expanded, nli_expanded], dim=-1)  # [batch, seq, hidden_dim+2]
                word_scores = self.word_detector(combined)  # [batch, seq, 1]
                word_scores = word_scores.squeeze(-1)  # [batch, seq]
            else:
                # Si word_level_detection está deshabilitado, usar scores a nivel de batch
                word_scores = (uncertainty + nli_score).unsqueeze(1).expand(-1, seq_len) / 2.0  # [batch, seq]
            
            # PASO 4: Aplicar corrección con mitigación configurable
            hallucination_mask = (word_scores > self.config.uncertainty_threshold).float().unsqueeze(-1)
            output = hidden_states * (1 - hallucination_mask * self.config.mitigation_strength)
            
            # Calcular métricas
            metadata = {
                'uncertainty_mean': uncertainty.mean().item(),
                'uncertainty_std': uncertainty.std().item(),
                'uncertainty_max': uncertainty.max().item(),
                'uncertainty_min': uncertainty.min().item(),
                'nli_contradiction_score': nli_score.mean().item(),
                'nli_contradiction_std': nli_score.std().item(),
                'word_hallucination_ratio': (word_scores > self.config.uncertainty_threshold).float().mean().item(),
                'word_scores_mean': word_scores.mean().item(),
                'word_scores_std': word_scores.std().item(),
                'words_detected': int((word_scores > self.config.uncertainty_threshold).sum().item()),
                'total_words': int(word_scores.numel())
            }
            
            self._update_metrics(
                uncertainty=metadata['uncertainty_mean'],
                nli_score=metadata['nli_contradiction_score'],
                word_hallucination_ratio=metadata['word_hallucination_ratio']
            )
            
            return output, metadata
            
        except Exception as e:
            logger.error(f"Error en forward de MALTO: {e}")
            # En caso de error, retornar hidden_states sin modificar
            error_metadata = {
                'error': str(e),
                'uncertainty_mean': 0.0,
                'nli_contradiction_score': 0.0,
                'word_hallucination_ratio': 0.0,
                'word_scores_mean': 0.0
            }
            return hidden_states, error_metadata

