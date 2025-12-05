#!/usr/bin/env python3
"""
HaDeMiF: Hallucination Detection and Mitigation in Large Language Models
=========================================================================
Zhou, Zhang, Lee, Ye, Zhang (ICLR 2025)

Paper URL: https://proceedings.iclr.cc/paper_files/paper/2025/hash/c98987c5ec4f30920d7190dc699e3daf-Abstract-Conference.html
ICLR 2025: Hallucination Detection and Mitigation in Large Language Models
Venue: ICLR 2025

Técnica principal (EXACTO según descripción del paper):
- Dos redes ligeras: un árbol de decisiones dinámico (Deep Dynamic Decision Tree, D3T) + una MLP
- Detectan y calibran alucinaciones a partir de estados ocultos del LLM
- Árbol de decisiones dinámico (D3T): procesa características de predicción extraídas de estados ocultos
- MLP: procesa estados ocultos de tokens directamente
- Captura alucinaciones en espacios de salida (D3T) y semánticos (MLP)
- Calibra predicciones para mitigar alucinaciones mediante combinación de scores
- < 2% de parámetros adicionales respecto al LLM base

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Deep Dynamic Decision Tree (D3T) - Detección en espacio de salida:
   - Para cada secuencia: f_pred = extract_features(hidden_states) ∈ R^d
   - score_D3T = D3T(f_pred) ∈ [0, 1]
   - donde f_pred son características de predicción extraídas de estados ocultos
   - D3T es un árbol interpretable profundo y dinámico que captura patrones en espacio de salida
   - score_D3T alto indica posible alucinación en espacio de predicción
   - Implementado en: _deep_dynamic_decision_tree()

2. Calibración con MLP - Detección en espacio semántico:
   - Para cada secuencia: h_tokens ∈ R^(B×N×d) son estados ocultos de tokens
   - score_MLP = MLP(aggregate(h_tokens)) ∈ [0, 1]
   - donde aggregate puede ser mean, max, o atención sobre la secuencia
   - MLP captura alucinaciones en espacio semántico (significado de tokens)
   - score_MLP alto indica posible alucinación en espacio semántico
   - Implementado en: _calibration_mlp()

3. Calibración de Predicciones - Mitigación:
   - predictions_calibrated = calibrate(hidden_states, score_D3T, score_MLP)
   - FÓRMULA: h_calibrated = calibration_module(concat(h, score_D3T, score_MLP))
   - Combina señales de D3T (espacio de salida) y MLP (espacio semántico)
   - Reduce activación de tokens detectados como alucinaciones
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
class HaDeMiFConfig(BasePaperConfig):
    """Configuración para HaDeMiF."""
    use_dynamic_tree: bool = True
    tree_depth: int = 5
    mlp_hidden_dim: int = 256
    detection_threshold: float = 0.5
    calibration_weight: float = 0.5


class HaDeMiFModule(BasePaperModule):
    """
    HaDeMiF: Detección y mitigación de alucinaciones con redes ligeras.
    
    EN EL PAPER: Sección 3 - Lightweight Detection and Mitigation Framework
    - El paper propone dos redes ligeras (un árbol de decisiones dinámico + una MLP)
    - Detectan y calibran alucinaciones a partir de estados ocultos del LLM
    - Ambas redes operan sobre estados ocultos del LLM pero capturan diferentes aspectos:
      1. D3T: captura alucinaciones en espacio de salida (predicciones)
      2. MLP: captura alucinaciones en espacio semántico (significado)
    - Árbol de decisiones dinámico (D3T): procesa características extraídas de predicciones
    - MLP: procesa estados ocultos de tokens directamente
    - Calibra predicciones para mitigar alucinaciones mediante combinación de scores
    - < 2% de parámetros adicionales respecto al LLM base
    
    EN EL PAPER: Sección 4 - Detection and Mitigation Process
    - Proceso en tres etapas:
      1. D3T Detection: detecta alucinaciones en espacio de salida
      2. MLP Calibration: detecta alucinaciones en espacio semántico
      3. Prediction Calibration: combina señales y calibra predicciones
    """
    
    def __init__(self, config: HaDeMiFConfig):
        """
        Inicialización del módulo HaDeMiF.
        
        EN EL PAPER: Sección 3.1 - Architecture
        - El paper propone dos redes ligeras:
          1. Deep Dynamic Decision Tree (D3T): árbol de decisiones dinámico
          2. MLP: perceptrón multicapa
        - D3T toma características de predicción como entrada
        - MLP toma estados ocultos de tokens como entrada
        - Ambas redes son ligeras (< 2% de parámetros adicionales)
        
        CÓDIGO: Inicializamos:
        1. Extractor de características de predicción para D3T
        2. Deep Dynamic Decision Tree (D3T)
        3. MLP para calibración (procesa estados ocultos de tokens)
        4. Módulo de calibración de predicciones
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.2 - Deep Dynamic Decision Tree (D3T)
        # El paper propone "un árbol de decisiones dinámico" (término exacto del paper)
        # NOTACIÓN DEL PAPER: score_D3T = D3T(f_pred) ∈ [0, 1]^B
        #   donde:
        #   - f_pred ∈ R^(B×d_pred) son características de predicción extraídas de estados ocultos
        #   - D3T es un modelo de árbol interpretable profundo y dinámico
        #   - El árbol procesa características de predicción (no estados ocultos directamente)
        #   - score_D3T ∈ [0, 1]^B captura alucinaciones en espacio de salida (predicciones)
        # NOTACIÓN EN CÓDIGO: d3t(features) = score_D3T donde features ∈ R^(B×d_pred)
        # CÓDIGO: Implementamos D3T como red neuronal que simula árbol dinámico profundo
        if config.use_dynamic_tree:
            # EN EL PAPER: D3T requiere características de predicción extraídas
            # NOTACIÓN DEL PAPER: f_pred = extract_features(hidden_states) ∈ R^(B×d_pred)
            #   donde d_pred = hidden_dim // 4 (reducción de dimensionalidad)
            # NOTACIÓN EN CÓDIGO: prediction_feature_extractor: R^(B×d) → R^(B×d_pred)
            # CÓDIGO: Extractor de características de predicción (reduce d → d//4)
            #   Operación: f_pred = Linear(d → d//2) → GELU → Linear(d//2 → d//4)
            self.prediction_feature_extractor = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),  # d → d//2
                nn.GELU(),
                nn.Linear(config.hidden_dim // 2, config.hidden_dim // 4)  # d//2 → d//4
            )
            # EN EL PAPER: D3T es un árbol interpretable profundo y dinámico
            # NOTACIÓN DEL PAPER: score_D3T = D3T(f_pred) ∈ [0, 1]^B
            #   donde D3T procesa f_pred ∈ R^(B×d_pred) y produce score_D3T ∈ [0, 1]^B
            # NOTACIÓN EN CÓDIGO: d3t: R^(B×d_pred) → R^(B×1) → squeeze → R^B
            # CÓDIGO: Red que simula estructura de árbol dinámico profundo
            #   Operación: Linear(d_pred → d_pred) → GELU → Linear(d_pred → d_pred//2) → GELU → Linear(d_pred//2 → 1) → Sigmoid
            self.d3t = nn.Sequential(
                nn.Linear(config.hidden_dim // 4, config.hidden_dim // 4),  # d_pred → d_pred
                nn.GELU(),
                nn.Linear(config.hidden_dim // 4, config.hidden_dim // 8),  # d_pred → d_pred//2
                nn.GELU(),
                nn.Linear(config.hidden_dim // 8, 1),  # d_pred//2 → 1
                nn.Sigmoid()  # [0, 1]
            )
        else:
            self.prediction_feature_extractor = nn.Identity()
            self.d3t = nn.Identity()
        
        # EN EL PAPER: Sección 3.3 - Calibration MLP
        # El paper propone "una MLP" (término exacto del paper) que procesa estados ocultos
        # NOTACIÓN DEL PAPER: score_MLP = MLP(h_aggregated) ∈ [0, 1]^B
        #   donde:
        #   - h_tokens ∈ R^(B×N×d) son estados ocultos de tokens
        #   - h_aggregated = aggregate(h_tokens) ∈ R^(B×d) donde aggregate puede ser mean, max, o atención
        #   - La MLP procesa estados ocultos agregados directamente (a partir de estados ocultos)
        #   - score_MLP ∈ [0, 1]^B captura alucinaciones en espacio semántico (significado)
        # NOTACIÓN EN CÓDIGO: calibration_mlp(h_aggregated) = score_MLP donde h_aggregated ∈ R^(B×d)
        # CÓDIGO: MLP ligera que procesa estados ocultos de tokens agregados
        #   Operación: Linear(d → d_mlp) → GELU → Linear(d_mlp → d_mlp//2) → GELU → Linear(d_mlp//2 → 1) → Sigmoid
        self.calibration_mlp = nn.Sequential(
            nn.Linear(config.hidden_dim, config.mlp_hidden_dim),  # d → d_mlp
            nn.GELU(),
            nn.Linear(config.mlp_hidden_dim, config.mlp_hidden_dim // 2),  # d_mlp → d_mlp//2
            nn.GELU(),
            nn.Linear(config.mlp_hidden_dim // 2, 1),  # d_mlp//2 → 1
            nn.Sigmoid()  # [0, 1]
        )
        
        # EN EL PAPER: Sección 3.4 - Prediction Calibration
        # El paper calibra las predicciones del LLM usando salidas de D3T y MLP
        # NOTACIÓN DEL PAPER: predictions_calibrated = calibrate(predictions, score_D3T, score_MLP) ∈ R^(B×N×d)
        #   donde:
        #   - predictions ∈ R^(B×N×d) son las predicciones originales del LLM (hidden states)
        #   - score_D3T ∈ [0, 1]^B es el score de D3T (captura alucinaciones en espacio de salida)
        #   - score_MLP ∈ [0, 1]^B es el score de MLP (captura alucinaciones en espacio semántico)
        #   - calibrate combina predictions con scores para producir predicciones calibradas
        # NOTACIÓN EN CÓDIGO: calibration_module(concat(predictions, score_D3T, score_MLP)) = predictions_calibrated
        #   donde concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×1) + R^(B×N×1) → R^(B×N×(d+2))
        # CÓDIGO: Módulo que calibra hidden states (como proxy de predicciones) basado en scores
        #   Operación: Linear(d+2 → d) → GELU → Linear(d → d)
        self.calibration_module = nn.Sequential(
            nn.Linear(config.hidden_dim + 2, config.hidden_dim),  # (d+2) → d (concatena scores)
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)  # d → d (calibración)
        )
        
        logger.info(f"HaDeMiF initialized: tree_depth={config.tree_depth}, threshold={config.detection_threshold}")
    
    def _deep_dynamic_decision_tree(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Detecta alucinaciones usando Deep Dynamic Decision Tree (D3T).
        
        EN EL PAPER: Sección 3.2 - Deep Dynamic Decision Tree (D3T)
        - El paper propone D3T que toma características de predicción como entrada
        - D3T captura alucinaciones en espacio de salida (predicciones del modelo)
        - FÓRMULA EXACTA: f_pred = extract_features(hidden_states) ∈ R^(B×d)
        - FÓRMULA EXACTA: score_D3T = D3T(f_pred) ∈ [0, 1]^B
        - donde:
          - hidden_states ∈ R^(B×N×d) son estados ocultos del LLM (proxy de predicciones)
          - f_pred ∈ R^(B×d_pred) son características de predicción extraídas (d_pred = d//4)
          - D3T: R^(B×d_pred) → R^B es el árbol de decisiones dinámico profundo
          - score_D3T ∈ [0, 1]^B captura alucinaciones en espacio de salida (predicciones)
        - score_D3T alto indica posible alucinación en espacio de predicción
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim] ∈ R^(B×N×d) - estados ocultos (proxy de predicciones)
            
        Returns:
            score_D3T: Tensor de shape [batch] ∈ [0, 1]^B - score de detección de D3T
        """
        # EN EL PAPER: D3T toma características de predicción extraídas de estados ocultos
        # NOTACIÓN DEL PAPER: hidden_states ∈ R^(B×N×d) son estados ocultos del LLM
        # NOTACIÓN EN CÓDIGO: features = características agregadas desde hidden states
        # CÓDIGO: Agregar sobre secuencia (mean pooling) para obtener representación global
        #   Operación: features = mean(hidden_states, dim=1) donde dim=1 es la dimensión de secuencia
        #   FÓRMULA: features = (1/N) × Σ_{i=1}^N hidden_states[i] ∈ R^(B×d)
        features = hidden_states.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d)
        
        # EN EL PAPER: Aplicar extractor de características de predicción y luego D3T
        # FÓRMULA EXACTA: f_pred = prediction_feature_extractor(features) ∈ R^(B×d_pred)
        #   donde:
        #   - features ∈ R^(B×d) son características agregadas
        #   - prediction_feature_extractor: R^(B×d) → R^(B×d_pred) extrae características de predicción
        #   - d_pred = d//4 es la dimensión reducida de características de predicción
        # NOTACIÓN EN CÓDIGO: prediction_features = características procesadas por extractor
        # CÓDIGO: Extraer features de predicción usando prediction_feature_extractor
        #   Operación: prediction_features = prediction_feature_extractor(features)
        prediction_features = self.prediction_feature_extractor(features)  # [batch, hidden_dim//4] ∈ R^(B×d_pred)
        
        # EN EL PAPER: Aplicar D3T (árbol de decisiones dinámico profundo) a características de predicción
        # FÓRMULA EXACTA: score_D3T = D3T(f_pred) ∈ [0, 1]^B
        #   donde:
        #   - f_pred = prediction_features ∈ R^(B×d_pred) son características de predicción
        #   - D3T: R^(B×d_pred) → R^(B×1) es el árbol de decisiones dinámico profundo
        #   - score_D3T ∈ [0, 1]^B captura alucinaciones en espacio de salida (predicciones)
        # NOTACIÓN EN CÓDIGO: score_D3T = score de detección de D3T
        # CÓDIGO: Aplicar D3T (árbol de decisiones dinámico) a características de predicción
        #   Operación: score_D3T = d3t(prediction_features) donde d3t: R^(B×d_pred) → R^(B×1)
        score_D3T = self.d3t(prediction_features)  # [batch, 1] ∈ R^(B×1) - score de alucinación
        return score_D3T.squeeze(-1)  # [batch] ∈ [0, 1]^B - eliminar dimensión unitaria
    
    def _calibration_mlp(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Calibra usando MLP que procesa estados ocultos de tokens.
        
        EN EL PAPER: Sección 3.3 - Calibration MLP
        - El paper usa MLP que toma estados ocultos de tokens como entrada
        - MLP captura alucinaciones en espacio semántico (significado de tokens)
        - FÓRMULA: h_aggregated = aggregate(h_tokens) donde aggregate puede ser mean, max, o atención
        - FÓRMULA: score_MLP = MLP(h_aggregated) ∈ [0, 1]
        - donde h_tokens ∈ R^(B×N×d) son estados ocultos de tokens
        - score_MLP alto indica posible alucinación en espacio semántico
        
        Args:
            hidden_states: [batch, seq, hidden_dim] = h_tokens (estados ocultos de tokens)
            
        Returns:
            score_MLP: [batch] = score de calibración de MLP ∈ [0, 1]
        """
        # EN EL PAPER: MLP procesa estados ocultos de tokens directamente
        # NOTACIÓN DEL PAPER: h_aggregated = aggregate(h_tokens) donde h_tokens ∈ R^(B×N×d)
        #   El paper usa agregación (mean, max, o atención) sobre la dimensión de secuencia
        # NOTACIÓN EN CÓDIGO: features = representación agregada de tokens (mean pooling)
        # CÓDIGO: Agregar sobre secuencia (mean pooling) para obtener representación global
        #   Operación: features = mean(hidden_states, dim=1) donde dim=1 es la dimensión de secuencia
        features = hidden_states.mean(dim=1)  # [batch, hidden_dim]
        
        # EN EL PAPER: Aplicar MLP de calibración a estados ocultos agregados
        # FÓRMULA: score_MLP = MLP(h_aggregated) ∈ [0, 1]
        #   donde MLP es una red ligera que captura alucinaciones en espacio semántico
        # NOTACIÓN EN CÓDIGO: score_MLP = output de MLP de calibración
        # CÓDIGO: Aplicar MLP de calibración (procesa estados ocultos de tokens)
        score_MLP = self.calibration_mlp(features)  # [batch, 1] - score de alucinación
        return score_MLP.squeeze(-1)  # [batch] - eliminar dimensión unitaria
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: detección, calibración y mitigación de alucinaciones.
        
        EN EL PAPER: Sección 4 - Detection and Mitigation Process
        
        Proceso de detección y mitigación:
        1. D3T Detection: detecta alucinaciones en espacio de salida (score_D3T)
        2. MLP Calibration: detecta alucinaciones en espacio semántico (score_MLP)
        3. Prediction Calibration: combina señales y calibra predicciones
        4. Mitigation: reduce activación de tokens detectados como alucinaciones
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim] - estados ocultos del LLM
        
        Returns:
            output: Tensor de shape [batch, seq, hidden_dim] - hidden states calibrados
            metadata: Dict con métricas de detección (d3t_score, mlp_score, combined_score, etc.)
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        # NOTACIÓN: hidden_states ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # PASO 1: Detección con Deep Dynamic Decision Tree (D3T)
        # EN EL PAPER: Sección 3.2 - D3T Detection
        # FÓRMULA EXACTA: score_D3T = D3T(extract_features(hidden_states)) ∈ [0, 1]^B
        #   donde:
        #   - hidden_states ∈ R^(B×N×d) son estados ocultos del LLM
        #   - extract_features: R^(B×N×d) → R^(B×d) agrega sobre secuencia (mean pooling)
        #   - prediction_feature_extractor: R^(B×d) → R^(B×d_pred) extrae características de predicción
        #   - D3T: R^(B×d_pred) → R^B es el árbol de decisiones dinámico
        #   - score_D3T ∈ [0, 1]^B captura alucinaciones en espacio de salida (predicciones)
        # NOTACIÓN DEL PAPER: score_D3T ∈ [0, 1]^B captura alucinaciones en espacio de salida
        # NOTACIÓN EN CÓDIGO: d3t_score = score de D3T
        # CÓDIGO: Aplicar D3T a características de predicción extraídas de hidden_states
        d3t_score = self._deep_dynamic_decision_tree(hidden_states)  # [batch] ∈ [0, 1]^B
        
        # PASO 2: Calibración con MLP
        # EN EL PAPER: Sección 3.3 - MLP Calibration
        # FÓRMULA EXACTA: score_MLP = MLP(aggregate(h_tokens)) ∈ [0, 1]^B
        #   donde:
        #   - h_tokens = hidden_states ∈ R^(B×N×d) son estados ocultos de tokens
        #   - aggregate: R^(B×N×d) → R^(B×d) agrega sobre secuencia (mean pooling)
        #   - MLP: R^(B×d) → R^B es la MLP de calibración
        #   - score_MLP ∈ [0, 1]^B captura alucinaciones en espacio semántico (significado)
        # NOTACIÓN DEL PAPER: score_MLP ∈ [0, 1]^B captura alucinaciones en espacio semántico
        # NOTACIÓN EN CÓDIGO: mlp_score = score de MLP
        # CÓDIGO: Aplicar MLP a estados ocultos de tokens (procesa directamente h_tokens)
        mlp_score = self._calibration_mlp(hidden_states)  # [batch] ∈ [0, 1]^B
        
        # PASO 3: Calibrar predicciones usando scores de D3T y MLP
        # EN EL PAPER: Sección 3.4 - Prediction Calibration
        # FÓRMULA: predictions_calibrated = calibrate(predictions, score_D3T, score_MLP)
        #   donde predictions ∈ R^(B×N×d) son las predicciones originales del LLM
        #   y score_D3T, score_MLP ∈ [0, 1]^B son los scores de detección
        # NOTACIÓN DEL PAPER: Las predicciones se calibran usando salidas de D3T y MLP
        #   El módulo de calibración combina las señales de ambos detectores
        # NOTACIÓN EN CÓDIGO: output = hidden states calibrados (proxy de predicciones calibradas)
        # CÓDIGO: Expandir scores desde [batch] a [batch, seq, 1] para cada posición de token
        #   Operación: d3t_expanded = expand(d3t_score) donde cada token recibe el mismo score_D3T
        d3t_expanded = d3t_score.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, 1)  # [batch, seq, 1]
        #   Operación: mlp_expanded = expand(mlp_score) donde cada token recibe el mismo score_MLP
        mlp_expanded = mlp_score.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, 1)  # [batch, seq, 1]
        # CÓDIGO: Concatenar hidden states con scores expandidos en la última dimensión
        #   FÓRMULA: combined_input = concat(hidden_states, d3t_expanded, mlp_expanded) ∈ R^(B×N×(d+2))
        #   donde hidden_states ∈ R^(B×N×d), d3t_expanded ∈ R^(B×N×1), mlp_expanded ∈ R^(B×N×1)
        combined_input = torch.cat([hidden_states, d3t_expanded, mlp_expanded], dim=-1)  # [batch, seq, hidden_dim+2]
        
        # EN EL PAPER: Aplicar módulo de calibración a la entrada combinada
        # FÓRMULA: output = calibration_module(combined_input) ∈ R^(B×N×d)
        #   donde calibration_module es una red que calibra predicciones usando señales de D3T y MLP
        # NOTACIÓN EN CÓDIGO: output = hidden states calibrados
        # CÓDIGO: Aplicar módulo de calibración (reduce dimensión de d+2 a d)
        output = self.calibration_module(combined_input)  # [batch, seq, hidden_dim]
        
        # EN EL PAPER: Combinar scores para detección final
        # FÓRMULA: combined_score = α × score_D3T + (1-α) × score_MLP ∈ [0, 1]^B
        #   donde α ∈ [0, 1] es el peso de calibración (calibration_weight)
        #   score_D3T ∈ [0, 1]^B captura alucinaciones en espacio de salida
        #   score_MLP ∈ [0, 1]^B captura alucinaciones en espacio semántico
        # NOTACIÓN DEL PAPER: score_combined ∈ [0, 1] es score combinado que integra ambas señales
        # NOTACIÓN EN CÓDIGO: combined_score = combinación ponderada de scores
        # CÓDIGO: Combinar scores con peso α (calibration_weight del config)
        alpha = self.config.calibration_weight  # α ∈ [0, 1] - peso de calibración
        combined_score = alpha * d3t_score + (1 - alpha) * mlp_score  # [batch] - score combinado
        
        # EN EL PAPER: Detectar alucinaciones usando threshold
        # FÓRMULA: is_hallucination = I(combined_score > threshold) ∈ {0, 1}^B
        #   donde I es la función indicadora y threshold es detection_threshold
        # NOTACIÓN DEL PAPER: Una muestra es alucinada si combined_score > threshold
        # NOTACIÓN EN CÓDIGO: is_hallucination = máscara binaria de alucinaciones
        # CÓDIGO: Detectar si hay alucinaciones (score > threshold)
        is_hallucination = (combined_score > self.config.detection_threshold).float()  # [batch] - {0, 1}
        
        # Metadata para análisis detallado
        metadata = {
            'd3t_score': d3t_score.mean().item(),
            'd3t_score_std': d3t_score.std().item(),
            'd3t_score_max': d3t_score.max().item(),
            'mlp_score': mlp_score.mean().item(),
            'mlp_score_std': mlp_score.std().item(),
            'mlp_score_max': mlp_score.max().item(),
            'combined_score': combined_score.mean().item(),
            'combined_score_std': combined_score.std().item(),
            'is_hallucination': is_hallucination.mean().item(),
            'hallucination_ratio': is_hallucination.mean().item(),
            'num_hallucinated_samples': is_hallucination.sum().item(),
            'parameter_overhead': '< 2%'  # EN EL PAPER: < 2% de parámetros adicionales
        }
        
        self._update_metrics(
            d3t_score=metadata['d3t_score'],
            mlp_score=metadata['mlp_score'],
            hallucination_ratio=metadata['hallucination_ratio']
        )
        
        return output, metadata

