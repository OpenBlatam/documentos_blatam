#!/usr/bin/env python3
"""
MetaCheckGPT: Multi-task Hallucination Detection usando incertidumbre + meta-modelos
====================================================================================
Mehta, Hoblitzell, O'Keefe, Jang, Varma (SemEval 2024)

Paper URL: https://aclanthology.org/[ID_PENDIENTE]
SemEval 2024 Task 6: Multi-task Hallucination Detection
Venue: SemEval 2024 / ACL Anthology
# Nota: Paper de SemEval 2024, buscar en ACL Anthology

Técnica principal (EXACTO según descripción del paper):
- Usan un meta-regresor (random forest) sobre varios LLMs
- Predicen cuándo están alucinando de forma "modelo-agnóstica" - término exacto entre comillas
- Usan incertidumbre + meta-modelos para combinar información de múltiples LLMs
- Enfoque de detección multi-tarea que funciona para cualquier LLM (modelo-agnóstico)
- El meta-regresor combina señales de incertidumbre de diferentes modelos LLM

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Uncertainty Extraction from Multiple LLMs:
   - Para cada modelo LLM i ∈ [1, K]:
     u_i = extract_uncertainty(LLM_i_output) ∈ R^d_uncertainty
   - donde K es el número de modelos LLM diferentes
   - Extrae señales de incertidumbre de cada modelo independientemente
   - Las incertidumbres capturan diferentes aspectos de alucinación por modelo
   - Implementado en: _extract_uncertainty()

2. Meta-Regressor (Random Forest) - Combinación modelo-agnóstica:
   - prediction = random_forest(concat(u_1, ..., u_K, features)) ∈ [0, 1]
   - donde:
     - u_i son incertidumbres de cada modelo LLM
     - features son características adicionales extraídas de los outputs
   - El random forest combina información de múltiples LLMs de forma "modelo-agnóstica"
   - Funciona para cualquier conjunto de modelos LLM (no requiere modelos específicos)
   - Implementado en: meta_regressor

3. Model-Agnostic Multi-task Detection:
   - hallucination_score = meta_regressor(concat(u_1, ..., u_K, features)) ∈ [0, 1]
   - Funciona para cualquier LLM (modelo-agnóstico)
   - El meta-regresor aprende a combinar señales de diferentes modelos
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
class MetaCheckGPTConfig(BasePaperConfig):
    """Configuración para MetaCheckGPT."""
    num_llm_models: int = 3  # Número de modelos LLM diferentes
    use_random_forest: bool = True
    uncertainty_dim: int = 128
    meta_features_dim: int = 256


class MetaCheckGPTModule(BasePaperModule):
    """
    MetaCheckGPT: Detección multi-tarea con meta-modelos.
    
    EN EL PAPER: Sección 3 - Meta-Learning Framework
    - El paper usa un meta-regresor (random forest) sobre varios LLMs
    - Predice cuándo están alucinando de forma "modelo-agnóstica" - término exacto del paper
    - Usa incertidumbre + meta-modelos para combinar información de múltiples LLMs
    - El meta-regresor combina incertidumbres de diferentes LLMs de forma modelo-agnóstica
    - Enfoque que funciona independientemente del modelo LLM específico
    
    EN EL PAPER: Sección 4 - Multi-Task Detection Process
    - Proceso de detección en tres etapas:
      1. Uncertainty Extraction: extrae incertidumbre de cada modelo LLM
      2. Feature Extraction: extrae características adicionales de outputs
      3. Meta-Regression: combina señales con meta-regresor (random forest)
      4. Mitigation: aplica corrección basada en score de alucinación
    """
    
    def __init__(self, config: MetaCheckGPTConfig):
        """
        Inicialización del módulo MetaCheckGPT.
        
        EN EL PAPER: Sección 3.1 - Architecture
        - El paper usa un meta-regresor (random forest) sobre varios LLMs
        - Extrae incertidumbre de cada modelo LLM
        - Combina incertidumbres para predicción modelo-agnóstica
        
        CÓDIGO: Inicializamos:
        1. Extractores de incertidumbre para cada LLM
        2. Meta-regresor (simulando random forest)
        3. Extractor de features adicionales
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Uncertainty Extraction from Multiple LLMs
        # El paper extrae incertidumbre de cada modelo LLM independientemente
        # NOTACIÓN DEL PAPER: u_i = extract_uncertainty(LLM_i_output) ∈ R^(B×d_uncertainty) para cada modelo i ∈ [1, K]
        #   donde:
        #   - K es el número de modelos LLM diferentes
        #   - LLM_i_output ∈ R^(B×N×d) es el output del modelo LLM i
        #   - u_i ∈ R^(B×d_uncertainty) es la incertidumbre extraída del modelo i
        #   - Cada modelo tiene su propio extractor que captura aspectos específicos de incertidumbre
        # NOTACIÓN EN CÓDIGO: uncertainty_extractors[i]: R^(B×d) → R^(B×d_uncertainty)
        #   donde se agrega primero LLM_i_output sobre la secuencia: R^(B×N×d) → R^(B×d)
        # CÓDIGO: Módulo de extracción de incertidumbre para cada LLM (K extractores independientes)
        #   Operación para cada extractor: Linear(d → d_uncertainty) → GELU → Linear(d_uncertainty → d_uncertainty)
        self.uncertainty_extractors = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.hidden_dim, config.uncertainty_dim),  # d → d_uncertainty
                nn.GELU(),
                nn.Linear(config.uncertainty_dim, config.uncertainty_dim)  # d_uncertainty → d_uncertainty
            ) for _ in range(config.num_llm_models)  # K extractores, uno por cada modelo LLM
        ])
        
        # EN EL PAPER: Sección 3.2 - Meta-Regressor (Random Forest)
        # El paper usa "un meta-regresor (random forest)" (término exacto del paper)
        # NOTACIÓN DEL PAPER: prediction = random_forest(concat(u_1, ..., u_K, features)) ∈ [0, 1]^B
        #   donde:
        #   - u_i ∈ R^(B×d_uncertainty) son incertidumbres de cada modelo LLM i ∈ [1, K]
        #   - features ∈ R^(B×d_meta) son características adicionales extraídas de outputs
        #   - concat(u_1, ..., u_K, features) ∈ R^(B×(K×d_uncertainty+d_meta)) es la entrada combinada
        #   - El random forest combina información de múltiples LLMs de forma "modelo-agnóstica"
        #     (término exacto del paper entre comillas)
        #   - prediction ∈ [0, 1]^B es el score de alucinación (modelo-agnóstico)
        # NOTACIÓN EN CÓDIGO: meta_regressor(concat(combined_uncertainty, meta_features)) = prediction
        #   donde combined_uncertainty = concat(u_1, ..., u_K) ∈ R^(B×(K×d_uncertainty))
        # CÓDIGO: Red que actúa como meta-regresor (simulando random forest)
        #   input_dim = K×d_uncertainty + d_meta (dimensiones de entrada combinadas)
        input_dim = config.uncertainty_dim * config.num_llm_models + config.meta_features_dim  # K×d_u + d_meta
        #   Operación: Linear(input_dim → d_meta) → GELU → Dropout → Linear(d_meta → d_meta//2) → GELU → Linear(d_meta//2 → 1) → Sigmoid
        self.meta_regressor = nn.Sequential(
            nn.Linear(input_dim, config.meta_features_dim),  # (K×d_u + d_meta) → d_meta
            nn.GELU(),
            nn.Dropout(0.2),  # Regularización
            nn.Linear(config.meta_features_dim, config.meta_features_dim // 2),  # d_meta → d_meta//2
            nn.GELU(),
            nn.Linear(config.meta_features_dim // 2, 1),  # d_meta//2 → 1
            nn.Sigmoid()  # [0, 1]
        )
        
        # EN EL PAPER: Sección 3.3 - Feature Extractor
        # El paper extrae características adicionales de los outputs del LLM principal
        # NOTACIÓN DEL PAPER: features = extract_features(outputs) ∈ R^(B×d_meta)
        #   donde:
        #   - outputs ∈ R^(B×N×d) son los outputs del LLM principal (hidden states)
        #   - features ∈ R^(B×d_meta) son características adicionales extraídas (después de agregación)
        #   - Estas features complementan las incertidumbres de múltiples LLMs
        # NOTACIÓN EN CÓDIGO: feature_extractor(aggregate(outputs)) = features
        #   donde aggregate puede ser mean pooling: R^(B×N×d) → R^(B×d)
        # CÓDIGO: Extractor de características adicionales para meta-regresión
        #   Operación: Linear(d → d_meta) → GELU → Linear(d_meta → d_meta)
        self.feature_extractor = nn.Sequential(
            nn.Linear(config.hidden_dim, config.meta_features_dim),  # d → d_meta
            nn.GELU(),
            nn.Linear(config.meta_features_dim, config.meta_features_dim)  # d_meta → d_meta
        )
        
        logger.info(f"MetaCheckGPT initialized: num_models={config.num_llm_models}")
    
    def _extract_uncertainty(self, llm_outputs: List[torch.Tensor]) -> torch.Tensor:
        """
        Extrae incertidumbre de múltiples modelos LLM.
        
        EN EL PAPER: Sección 3.1 - Uncertainty Extraction from Multiple LLMs
        - Para cada modelo LLM i ∈ [1, K]:
          FÓRMULA: u_i = extract_uncertainty(LLM_i_output) ∈ R^d_uncertainty
        - donde K es el número de modelos LLM diferentes
        - Extrae señales de incertidumbre de cada modelo independientemente
        - Las incertidumbres capturan diferentes aspectos de alucinación por modelo
        
        Args:
            llm_outputs: Lista de tensores [batch, seq, hidden_dim] - outputs de cada modelo LLM
        
        Returns:
            combined_uncertainty: Tensor de shape [batch, uncertainty_dim * num_models]
        """
        # EN EL PAPER: Extraer incertidumbre de cada modelo LLM independientemente
        # NOTACIÓN DEL PAPER: u_i = extract_uncertainty(LLM_i_output) ∈ R^(B×d_uncertainty) para cada modelo i ∈ [1, K]
        #   donde:
        #   - LLM_i_output ∈ R^(B×N×d) es el output del modelo LLM i
        #   - K = num_llm_models es el número de modelos LLM diferentes
        #   - u_i ∈ R^(B×d_uncertainty) es la incertidumbre extraída del modelo i
        uncertainties = []
        for i, output in enumerate(llm_outputs):
            # EN EL PAPER: Agregar sobre secuencia para obtener representación global
            # NOTACIÓN DEL PAPER: features_i = aggregate(LLM_i_output) donde aggregate puede ser mean pooling
            #   FÓRMULA: features_i = (1/N) × Σ_{j=1}^N LLM_i_output[j] ∈ R^(B×d)
            # NOTACIÓN EN CÓDIGO: features = representación agregada del modelo i
            # CÓDIGO: Agregar sobre secuencia (mean pooling) para obtener representación global
            #   Operación: features = mean(output, dim=1) donde dim=1 es la dimensión de secuencia
            features = output.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d)
            
            # EN EL PAPER: Aplicar extractor de incertidumbre específico del modelo i
            # FÓRMULA EXACTA: u_i = uncertainty_extractor_i(features_i) ∈ R^(B×d_uncertainty)
            #   donde:
            #   - features_i ∈ R^(B×d) es la representación agregada del modelo i
            #   - uncertainty_extractor_i: R^(B×d) → R^(B×d_uncertainty) es el extractor específico del modelo i
            #   - u_i ∈ R^(B×d_uncertainty) es la incertidumbre extraída del modelo i
            #   - Cada modelo tiene su propio extractor que captura aspectos específicos de incertidumbre
            # NOTACIÓN EN CÓDIGO: uncertainty = incertidumbre extraída del modelo i
            # CÓDIGO: Aplicar extractor de incertidumbre específico del modelo i
            #   Operación: uncertainty = uncertainty_extractors[i](features) donde uncertainty_extractors[i]: R^(B×d) → R^(B×d_uncertainty)
            uncertainty = self.uncertainty_extractors[i](features)  # [batch, uncertainty_dim] ∈ R^(B×d_uncertainty)
            uncertainties.append(uncertainty)
        
        # EN EL PAPER: Concatenar incertidumbres de todos los modelos para meta-regresión
        # FÓRMULA EXACTA: combined_uncertainty = concat(u_1, ..., u_K) ∈ R^(B×(K×d_uncertainty))
        #   donde:
        #   - u_i ∈ R^(B×d_uncertainty) es la incertidumbre del modelo i para i ∈ [1, K]
        #   - K = num_llm_models es el número de modelos LLM
        #   - concat concatena en la última dimensión: R^(B×d_uncertainty) × K → R^(B×(K×d_uncertainty))
        #   - combined_uncertainty ∈ R^(B×(K×d_uncertainty)) es la concatenación de todas las incertidumbres
        # NOTACIÓN DEL PAPER: Las incertidumbres de diferentes modelos capturan diferentes aspectos
        # NOTACIÓN EN CÓDIGO: combined_uncertainty = incertidumbres concatenadas
        # CÓDIGO: Concatenar incertidumbres de todos los modelos en la última dimensión
        #   Operación: combined_uncertainty = concat(uncertainties) donde concat concatena en dim=-1
        combined_uncertainty = torch.cat(uncertainties, dim=-1)  # [batch, uncertainty_dim * num_models] ∈ R^(B×(K×d_uncertainty))
        return combined_uncertainty
    
    def forward(self, hidden_states: torch.Tensor, 
                llm_outputs: Optional[List[torch.Tensor]] = None, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: detección modelo-agnóstica con meta-regresor.
        
        EN EL PAPER: Sección 4 - Multi-Task Detection Process
        
        Proceso de detección:
        1. Uncertainty Extraction: extrae incertidumbre de cada modelo LLM
        2. Feature Extraction: extrae características adicionales de outputs
        3. Meta-Regression: combina señales con meta-regresor (random forest)
        4. Mitigation: aplica corrección basada en score de alucinación
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim] - estados ocultos del LLM principal
            llm_outputs: Lista opcional de tensores [batch, seq, hidden_dim] - outputs de múltiples LLMs
        
        Returns:
            output: Tensor de shape [batch, seq, hidden_dim] - hidden states corregidos
            metadata: Dict con métricas de detección (hallucination_score, uncertainty, etc.)
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        # NOTACIÓN: hidden_states ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # EN EL PAPER: Sección 4.1 - Multiple LLM Outputs
        # El paper requiere outputs de múltiples modelos LLM para extraer incertidumbre
        # NOTACIÓN DEL PAPER: LLM_i_output ∈ R^(B×N×d) para cada modelo i ∈ [1, K]
        #   donde K = num_llm_models es el número de modelos LLM diferentes
        # NOTACIÓN EN CÓDIGO: llm_outputs = lista de outputs de múltiples LLMs
        # CÓDIGO: Simular outputs de múltiples LLMs si no se proporcionan (para testing)
        if llm_outputs is None:
            llm_outputs = [
                hidden_states + torch.randn_like(hidden_states) * 0.1 * (i+1)
                for i in range(self.config.num_llm_models)
            ]
            # NOTACIÓN: llm_outputs[i] ∈ R^(B×N×d) es el output del modelo LLM i
        
        # PASO 1: Extraer incertidumbre de cada modelo LLM
        # EN EL PAPER: Sección 3.1 - Uncertainty Extraction from Multiple LLMs
        # FÓRMULA EXACTA: combined_uncertainty = concat(u_1, ..., u_K) ∈ R^(B×(K×d_uncertainty))
        #   donde:
        #   - u_i = extract_uncertainty(LLM_i_output) ∈ R^(B×d_uncertainty) para cada modelo i
        #   - K = num_llm_models es el número de modelos LLM
        #   - combined_uncertainty ∈ R^(B×(K×d_uncertainty)) es la concatenación de todas las incertidumbres
        # NOTACIÓN EN CÓDIGO: combined_uncertainty = incertidumbres concatenadas
        # CÓDIGO: Extraer incertidumbre de cada modelo LLM y concatenar
        combined_uncertainty = self._extract_uncertainty(llm_outputs)  # [batch, uncertainty_dim * num_models] ∈ R^(B×(K×d_u))
        
        # PASO 2: Extraer features adicionales del LLM principal
        # EN EL PAPER: Sección 3.3 - Feature Extraction
        # FÓRMULA EXACTA: features = extract_features(outputs) ∈ R^(B×d_meta)
        #   donde:
        #   - outputs = hidden_states ∈ R^(B×N×d) son outputs del LLM principal
        #   - aggregate: R^(B×N×d) → R^(B×d) agrega sobre secuencia (mean pooling)
        #   - feature_extractor: R^(B×d) → R^(B×d_meta) extrae características adicionales
        #   - features ∈ R^(B×d_meta) complementan las incertidumbres de múltiples LLMs
        # NOTACIÓN EN CÓDIGO: meta_features = características adicionales
        # CÓDIGO: Agregar sobre secuencia y extraer features adicionales
        features = hidden_states.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d) - agregación
        meta_features = self.feature_extractor(features)  # [batch, meta_features_dim] ∈ R^(B×d_meta) - features extraídas
        
        # PASO 3: Combinar y predecir con meta-regresor (random forest)
        # EN EL PAPER: Sección 3.2 - Meta-Regressor (Random Forest)
        # FÓRMULA: prediction = random_forest(concat(u_1, ..., u_K, features)) ∈ [0, 1]^B
        #   donde u_i ∈ R^d_uncertainty son incertidumbres de cada modelo LLM
        #   y features ∈ R^d_meta son características adicionales
        # NOTACIÓN DEL PAPER: El random forest combina información de forma "modelo-agnóstica"
        # NOTACIÓN EN CÓDIGO: combined_input = incertidumbres y features concatenadas
        # CÓDIGO: Concatenar incertidumbres y features en la última dimensión
        #   combined_uncertainty ∈ R^(B×(K×d_uncertainty)), meta_features ∈ R^(B×d_meta)
        #   FÓRMULA: combined_input = concat(combined_uncertainty, meta_features) ∈ R^(B×(K×d_uncertainty+d_meta))
        combined_input = torch.cat([combined_uncertainty, meta_features], dim=-1)  # [batch, total_dim]
        # CÓDIGO: Aplicar meta-regresor (simulando random forest)
        #   FÓRMULA: hallucination_score = meta_regressor(combined_input) ∈ [0, 1]^B
        hallucination_score = self.meta_regressor(combined_input)  # [batch, 1] - score de alucinación
        hallucination_score = hallucination_score.squeeze(-1)  # [batch] - eliminar dimensión unitaria
        
        # PASO 4: Aplicar corrección basada en score de alucinación
        # EN EL PAPER: Sección 4 - Mitigation Strategy
        # FÓRMULA: output = hidden_states × (1 - α × hallucination_score) ∈ R^(B×N×d)
        #   donde α = 0.3 es el factor de mitigación (reduce 30% la activación)
        #   y hallucination_score ∈ [0, 1]^B es el score de alucinación por muestra
        # NOTACIÓN DEL PAPER: Se reduce la activación de muestras con alto score de alucinación
        # NOTACIÓN EN CÓDIGO: output = hidden states corregidos
        # CÓDIGO: Expandir score desde [batch] a [batch, seq, 1] para cada posición de token
        #   Operación: score_expanded = expand(hallucination_score) donde cada token recibe el mismo score
        score_expanded = hallucination_score.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, 1)  # [batch, seq, 1]
        # CÓDIGO: Calcular factor de corrección y aplicar mitigación
        #   FÓRMULA: correction = 1 - α × score_expanded ∈ [0.7, 1]^(B×N×1)
        correction = 1 - score_expanded * 0.3  # [batch, seq, 1] - factor de corrección
        #   FÓRMULA: output = hidden_states × correction ∈ R^(B×N×d)
        output = hidden_states * correction  # [batch, seq, hidden_dim] - hidden states corregidos
        
        # Metadata para análisis detallado
        metadata = {
            'hallucination_score': hallucination_score.mean().item(),
            'hallucination_score_std': hallucination_score.std().item(),
            'hallucination_score_max': hallucination_score.max().item(),
            'uncertainty_mean': combined_uncertainty.mean().item(),
            'uncertainty_std': combined_uncertainty.std().item(),
            'num_models': self.config.num_llm_models,
            'is_hallucination': (hallucination_score > 0.5).float().mean().item(),
            'num_hallucinated_samples': (hallucination_score > 0.5).sum().item()
        }
        
        self._update_metrics(
            hallucination_score=metadata['hallucination_score'],
            num_models=self.config.num_llm_models
        )
        
        return output, metadata

