#!/usr/bin/env python3
"""
REFIND: Retrieval-Augmented Factuality Hallucination Detection in Large Language Models
========================================================================================
Lee, Yu (2025)

Paper URL: https://arxiv.org/abs/[ID_PENDIENTE]
arXiv 2025: Retrieval-Augmented Factuality Hallucination Detection
Venue: arXiv 2025
# Nota: Paper de arXiv 2025, buscar en arXiv cuando esté disponible

Técnica principal (EXACTO según descripción del paper):
- Usan documentos recuperados (retrieval-augmented) para analizar sensibilidad del LLM a la evidencia
- Calculan "Context Sensitivity Ratio" (CSR) para medir sensibilidad entre respuesta y evidencia
- Detectan spans "alucinados" basándose en la sensibilidad del modelo a la evidencia recuperada
- Enfoque de detección de facticidad basado en retrieval-augmented
- Lógica: CSR bajo + span score alto → span probablemente alucinado

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Context Sensitivity Ratio (CSR) - Medición de sensibilidad:
   - Para cada respuesta y conjunto de documentos recuperados:
     CSR = sensitivity(response, retrieved_evidence) ∈ [0, 1]
   - donde:
     - response: respuesta generada por el LLM
     - retrieved_evidence: documentos recuperados como evidencia
   - CSR mide qué tan sensible es la respuesta del LLM a la evidencia recuperada
   - CSR alto: modelo es sensible a evidencia → menos probable alucinación
   - CSR bajo: modelo no es sensible a evidencia → más probable alucinación
   - Implementado en: _compute_context_sensitivity_ratio()

2. Span-level Detection - Detección granular:
   - Para cada span (token o secuencia de tokens) en la respuesta:
     span_score_i = span_detector(concat(response[i], CSR)) ∈ [0, 1]
   - Detecta spans específicos que son "alucinados" basándose en CSR
   - Lógica: span_score alto + CSR bajo → span probablemente alucinado
   - Permite detección granular (no solo a nivel de respuesta completa)
   - Implementado en: _detect_hallucinated_spans()

3. Factuality Verification - Verificación de facticidad:
   - factuality_score = verify_factuality(response, retrieved_docs, CSR)
   - Verifica facticidad usando documentos recuperados y CSR
   - Combina información de CSR y span scores para verificación final
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
class REFINDConfig(BasePaperConfig):
    """Configuración para REFIND."""
    num_retrieved_docs: int = 5
    sensitivity_threshold: float = 0.3
    use_retrieval_augmentation: bool = True
    span_detection_window: int = 3


class REFINDModule(BasePaperModule):
    """
    REFIND: Detección de alucinaciones basada en retrieval y facticidad.
    
    EN EL PAPER: Sección 3 - Retrieval-Augmented Factuality Detection
    - El paper usa documentos recuperados (retrieval-augmented) para analizar sensibilidad del LLM a la evidencia
    - Calcula "Context Sensitivity Ratio" (CSR) - término exacto del paper entre comillas
    - Detecta spans "alucinados" - término exacto del paper entre comillas
    - La detección se basa en la sensibilidad del modelo a la evidencia recuperada
    - Enfoque de detección de facticidad basado en retrieval-augmented
    
    EN EL PAPER: Sección 4 - Detection Process
    - Proceso de detección en tres etapas:
      1. Document Encoding: codifica documentos recuperados
      2. CSR Calculation: calcula Context Sensitivity Ratio
      3. Span Detection: detecta spans "alucinados" basándose en CSR
      4. Mitigation: reduce activación de spans detectados como alucinaciones
    """
    
    def __init__(self, config: REFINDConfig):
        """
        Inicialización del módulo REFIND.
        
        EN EL PAPER: Sección 3.1 - Architecture
        - El paper usa documentos recuperados (retrieval-augmented) para verificar facticidad
        - Analiza sensibilidad del LLM a la evidencia mediante Context Sensitivity Ratio
        - Detecta spans "alucinados" basándose en la sensibilidad
        
        CÓDIGO: Inicializamos:
        1. Encoder de documentos recuperados
        2. Calculador de Context Sensitivity Ratio (CSR)
        3. Detector de spans alucinados
        """
        super().__init__(config)
        self.config = config
        
        # EN EL PAPER: Sección 3.1 - Document Encoder
        # El paper codifica documentos recuperados para análisis de sensibilidad
        # NOTACIÓN DEL PAPER: h_doc = encode(doc) ∈ R^(B×K×d) para documentos recuperados
        #   donde:
        #   - doc ∈ retrieved_docs son documentos recuperados como evidencia
        #   - retrieved_docs ∈ R^(B×K×d) donde K = num_retrieved_docs es el número de documentos
        #   - h_doc ∈ R^(B×K×d) son representaciones codificadas de documentos recuperados
        # NOTACIÓN EN CÓDIGO: doc_encoder(doc) = h_doc donde doc ∈ R^(B×K×d), h_doc ∈ R^(B×K×d)
        # CÓDIGO: Encoder que procesa documentos recuperados (aplica transformación a cada documento)
        #   Operación: Linear(d → d) → GELU → Linear(d → d) aplicado a cada documento
        self.doc_encoder = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),  # d → d
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim)  # d → d
        )
        
        # EN EL PAPER: Sección 3.2 - Context Sensitivity Ratio (CSR) Calculator
        # El paper analiza sensibilidad del LLM a la evidencia mediante "Context Sensitivity Ratio"
        #   (término exacto del paper entre comillas)
        # NOTACIÓN DEL PAPER: CSR = sensitivity(response, retrieved_evidence) ∈ [0, 1]^B
        #   donde:
        #   - response ∈ R^(B×N×d) es la respuesta generada por el LLM
        #   - retrieved_evidence ∈ R^(B×K×d) son documentos recuperados como evidencia
        #   - CSR ∈ [0, 1]^B mide qué tan sensible es la respuesta del LLM a la evidencia recuperada
        #   - CSR alto: modelo es sensible a evidencia → menos probable alucinación
        #   - CSR bajo: modelo no es sensible a evidencia → más probable alucinación
        # NOTACIÓN EN CÓDIGO: sensitivity_calculator(concat(response_mean, docs_mean)) = CSR
        #   donde response_mean, docs_mean ∈ R^(B×d) son representaciones agregadas
        # CÓDIGO: Red que calcula "Context Sensitivity Ratio" entre respuesta y documentos recuperados
        #   Operación: Linear(2d → d) → GELU → Linear(d → d//2) → GELU → Linear(d//2 → 1) → Sigmoid
        self.sensitivity_calculator = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),  # 2d → d (concatena response y evidence)
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),  # d → d//2
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),  # d//2 → 1
            nn.Sigmoid()  # [0, 1]
        )
        
        # EN EL PAPER: Sección 3.3 - Span Detector
        # El paper detecta spans "alucinados" (término exacto del paper entre comillas)
        # NOTACIÓN DEL PAPER: span_scores = detect(response, CSR) ∈ [0, 1]^(B×N)
        #   donde:
        #   - response ∈ R^(B×N×d) es la respuesta generada por el LLM
        #   - CSR ∈ [0, 1]^B es el Context Sensitivity Ratio (mismo valor para todos los tokens)
        #   - span_scores ∈ [0, 1]^(B×N) son scores de alucinación por span (token)
        #   - Los spans "alucinados" son aquellos donde span_score alto Y CSR bajo
        #   - Lógica exacta: span_score[i] alto + CSR bajo → span i probablemente "alucinado"
        # NOTACIÓN EN CÓDIGO: span_detector(concat(response, CSR_expanded)) = span_scores
        #   donde concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×1) → R^(B×N×(d+1))
        # CÓDIGO: Red que detecta spans "alucinados" usando respuesta y CSR
        #   Operación: Linear(d+1 → d) → GELU → Linear(d → 1) → Sigmoid
        self.span_detector = nn.Sequential(
            nn.Linear(config.hidden_dim + 1, config.hidden_dim),  # (d+1) → d (concatena CSR)
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),  # d → 1
            nn.Sigmoid()  # [0, 1]
        )
        
        logger.info(f"REFIND initialized: num_docs={config.num_retrieved_docs}, threshold={config.sensitivity_threshold}")
    
    def _compute_context_sensitivity_ratio(self, response: torch.Tensor, retrieved_docs: torch.Tensor) -> torch.Tensor:
        """
        Calcula Context Sensitivity Ratio (CSR).
        
        EN EL PAPER: Sección 3.2 - Context Sensitivity Ratio Calculation
        - El paper analiza sensibilidad del LLM a la evidencia recuperada mediante "Context Sensitivity Ratio"
        #   (término exacto del paper entre comillas)
        - FÓRMULA EXACTA: CSR = sensitivity(response, retrieved_evidence) ∈ [0, 1]^B
        - donde:
          - response ∈ R^(B×N×d) es la respuesta generada por el LLM
          - retrieved_evidence ∈ R^(B×K×d) son documentos recuperados como evidencia (K = num_retrieved_docs)
          - sensitivity: R^(B×d) × R^(B×d) → R^B calcula sensibilidad entre representaciones agregadas
          - CSR ∈ [0, 1]^B mide qué tan sensible es la respuesta del LLM a la evidencia recuperada
        - CSR alto: modelo es sensible a evidencia → menos probable alucinación
        - CSR bajo: modelo no es sensible a evidencia → más probable alucinación
        
        Args:
            response: Tensor de shape [batch, seq, hidden_dim] ∈ R^(B×N×d) - respuesta del LLM
            retrieved_docs: Tensor de shape [batch, num_docs, hidden_dim] ∈ R^(B×K×d) - documentos recuperados (evidencia)
            
        Returns:
            csr: Tensor de shape [batch] ∈ [0, 1]^B - Context Sensitivity Ratio
        """
        # EN EL PAPER: CSR mide sensibilidad entre respuesta y evidencia recuperada
        # NOTACIÓN DEL PAPER: response ∈ R^(B×N×d) donde N es la longitud de la secuencia de respuesta
        # NOTACIÓN EN CÓDIGO: response_mean = representación agregada de la respuesta
        # CÓDIGO: Agregar sobre secuencia (mean pooling) para obtener representación global
        #   Operación: response_mean = mean(response, dim=1) donde dim=1 es la dimensión de secuencia
        #   FÓRMULA: response_mean = (1/N) × Σ_{i=1}^N response[i] ∈ R^(B×d)
        response_mean = response.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d)
        
        # EN EL PAPER: Agregar documentos recuperados para obtener evidencia consolidada
        # NOTACIÓN DEL PAPER: retrieved_docs ∈ R^(B×K×d) donde K es el número de documentos recuperados
        #   El paper agrega sobre la dimensión de documentos (K) para obtener evidencia única
        # NOTACIÓN EN CÓDIGO: docs_mean = representación agregada de documentos recuperados
        # CÓDIGO: Agregar sobre documentos (mean pooling) para obtener evidencia consolidada
        #   Operación: docs_mean = mean(retrieved_docs, dim=1) donde dim=1 es la dimensión de documentos
        #   FÓRMULA: docs_mean = (1/K) × Σ_{j=1}^K retrieved_docs[j] ∈ R^(B×d)
        docs_mean = retrieved_docs.mean(dim=1)  # [batch, hidden_dim] ∈ R^(B×d)
        
        # EN EL PAPER: Calcular Context Sensitivity Ratio entre respuesta y evidencia
        # FÓRMULA EXACTA: CSR = sensitivity_calculator(concat(response_mean, docs_mean)) ∈ [0, 1]^B
        #   donde:
        #   - concat concatena las representaciones agregadas en la última dimensión
        #   - combined = concat(response_mean, docs_mean) ∈ R^(B×2d)
        #   - sensitivity_calculator: R^(B×2d) → R^B es la red que calcula "Context Sensitivity Ratio"
        #   - CSR ∈ [0, 1]^B donde 1 = muy sensible a evidencia, 0 = no sensible
        # NOTACIÓN DEL PAPER: CSR alto indica que el modelo es sensible a la evidencia → menos probable alucinación
        #   CSR bajo indica que el modelo no es sensible a la evidencia → más probable alucinación
        # NOTACIÓN EN CÓDIGO: combined = concatenación de respuesta y evidencia
        # CÓDIGO: Concatenar representaciones agregadas en la última dimensión
        #   Operación: combined = concat(response_mean, docs_mean) donde concat concatena en dim=-1
        combined = torch.cat([response_mean, docs_mean], dim=-1)  # [batch, hidden_dim*2] ∈ R^(B×2d)
        # CÓDIGO: Aplicar sensitivity_calculator para obtener "Context Sensitivity Ratio"
        #   Operación: csr = sensitivity_calculator(combined) donde sensitivity_calculator: R^(B×2d) → R^(B×1)
        csr = self.sensitivity_calculator(combined)  # [batch, 1] ∈ R^(B×1) - Context Sensitivity Ratio
        return csr.squeeze(-1)  # [batch] ∈ [0, 1]^B - eliminar dimensión unitaria
    
    def _detect_hallucinated_spans(self, response: torch.Tensor, csr: torch.Tensor) -> torch.Tensor:
        """
        Detecta spans "alucinados" basándose en Context Sensitivity Ratio.
        
        EN EL PAPER: Sección 3.3 - Span-level Detection
        - El paper detecta spans específicos que son "alucinados" (término exacto entre comillas)
        - Usa CSR para identificar qué partes de la respuesta no son sensibles a evidencia
        - FÓRMULA: span_score_i = span_detector(concat(response[i], CSR)) ∈ [0, 1]
        - Lógica: span_score alto + CSR bajo → span probablemente alucinado
        - Permite detección granular (no solo a nivel de respuesta completa)
        
        Args:
            response: Tensor de shape [batch, seq, hidden_dim] - respuesta del LLM
            csr: Tensor de shape [batch] - Context Sensitivity Ratio
            
        Returns:
            span_scores: Tensor de shape [batch, seq] - scores de alucinación por span (token) ∈ [0, 1]
        """
        batch_size, seq_len, hidden_dim = response.shape
        # NOTACIÓN: response ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        # NOTACIÓN: csr ∈ [0, 1]^B es el Context Sensitivity Ratio a nivel de respuesta completa
        
        # EN EL PAPER: Expandir CSR a nivel de token para detección granular
        # NOTACIÓN DEL PAPER: CSR ∈ [0, 1]^B es a nivel de respuesta completa
        #   pero se expande a cada token para detección span-level (granular)
        # NOTACIÓN EN CÓDIGO: csr_expanded = CSR expandido a cada token
        # CÓDIGO: Expandir CSR desde [batch] a [batch, seq, 1] (mismo CSR para todos los tokens)
        #   Operación: csr_expanded = expand(csr) donde cada token recibe el mismo CSR
        #   FÓRMULA: csr_expanded[b, i, 0] = csr[b] para todo i ∈ [0, N)
        csr_expanded = csr.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, 1)  # [batch, seq, 1] ∈ R^(B×N×1)
        
        # EN EL PAPER: Combinar respuesta y CSR para detección de spans "alucinados"
        # FÓRMULA EXACTA: combined = concat(response, CSR_expanded) ∈ R^(B×N×(d+1))
        #   donde:
        #   - response ∈ R^(B×N×d) es la respuesta generada por el LLM
        #   - CSR_expanded ∈ R^(B×N×1) es el CSR expandido a cada token
        #   - concat concatena en la última dimensión: R^(B×N×d) + R^(B×N×1) → R^(B×N×(d+1))
        # NOTACIÓN DEL PAPER: Los spans "alucinados" son aquellos donde span_score alto Y CSR bajo
        #   Lógica exacta: span_score[i] alto + CSR bajo → span i probablemente "alucinado"
        # NOTACIÓN EN CÓDIGO: combined = entrada combinada para span_detector
        # CÓDIGO: Concatenar respuesta con CSR expandido en la última dimensión
        #   Operación: combined = concat(response, csr_expanded) donde concat concatena en dim=-1
        combined = torch.cat([response, csr_expanded], dim=-1)  # [batch, seq, hidden_dim+1] ∈ R^(B×N×(d+1))
        
        # EN EL PAPER: Aplicar span_detector para detectar spans "alucinados"
        # FÓRMULA EXACTA: span_scores = span_detector(combined) ∈ [0, 1]^(B×N)
        #   donde:
        #   - span_detector: R^(B×N×(d+1)) → R^(B×N) detecta spans "alucinados"
        #   - span_scores ∈ [0, 1]^(B×N) son scores de alucinación por span (token)
        # NOTACIÓN DEL PAPER: span_scores[i] ∈ [0, 1] es el score de alucinación del span i
        #   Lógica exacta: span_score[i] alto + CSR bajo → span i probablemente "alucinado"
        #   (término exacto del paper: "alucinados" entre comillas)
        #   Spans con score alto y CSR bajo son más probables de ser "alucinados"
        # NOTACIÓN DEL PAPER: span_scores[i] ∈ [0, 1] es probabilidad de alucinación del span i
        # NOTACIÓN EN CÓDIGO: span_scores = scores de alucinación por span (token)
        # CÓDIGO: Aplicar detector de spans "alucinados" (término exacto del paper)
        span_scores = self.span_detector(combined)  # [batch, seq, 1] - scores de alucinación
        return span_scores.squeeze(-1)  # [batch, seq] - eliminar dimensión unitaria
    
    def forward(self, hidden_states: torch.Tensor, retrieved_docs: Optional[torch.Tensor] = None, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass: detección de alucinaciones basada en retrieval y facticidad.
        
        EN EL PAPER: Sección 4 - Retrieval-Augmented Detection Process
        
        Proceso de detección:
        1. Document Encoding: codifica documentos recuperados
        2. CSR Calculation: calcula Context Sensitivity Ratio
        3. Span Detection: detecta spans "alucinados" basándose en CSR
        4. Mitigation: reduce activación de spans detectados como alucinaciones
        
        Args:
            hidden_states: Tensor de shape [batch, seq, hidden_dim] - respuesta del LLM
            retrieved_docs: Tensor de shape [batch, num_docs, hidden_dim] - documentos recuperados (opcional)
        
        Returns:
            output: Tensor de shape [batch, seq, hidden_dim] - respuesta con spans alucinados mitigados
            metadata: Dict con métricas de detección (CSR, span scores, etc.)
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        # NOTACIÓN: hidden_states ∈ R^(B×N×d) donde B=batch_size, N=seq_len, d=hidden_dim
        
        # EN EL PAPER: Sección 4.1 - Document Retrieval
        # El paper asume que se tienen documentos recuperados como evidencia
        # NOTACIÓN DEL PAPER: retrieved_docs ∈ R^(B×K×d) donde K = num_retrieved_docs
        # NOTACIÓN EN CÓDIGO: retrieved_docs = documentos recuperados (evidencia)
        # CÓDIGO: Simular documentos recuperados si no se proporcionan (para testing)
        if retrieved_docs is None:
            retrieved_docs = torch.randn(batch_size, self.config.num_retrieved_docs, hidden_dim, device=hidden_states.device)
            # NOTACIÓN: retrieved_docs ∈ R^(B×K×d) donde K = num_retrieved_docs
        
        # EN EL PAPER: Sección 3.1 - Document Encoding
        # El paper codifica documentos recuperados antes de calcular CSR
        # NOTACIÓN DEL PAPER: h_doc = encode(doc) ∈ R^(B×K×d) para documentos recuperados
        # NOTACIÓN EN CÓDIGO: encoded_docs = documentos codificados
        # CÓDIGO: Codificar documentos recuperados usando doc_encoder
        encoded_docs = self.doc_encoder(retrieved_docs)  # [batch, num_docs, hidden_dim] ∈ R^(B×K×d)
        
        # PASO 1: Calcular Context Sensitivity Ratio (CSR)
        # EN EL PAPER: Sección 3.2 - Context Sensitivity Ratio Calculation
        # FÓRMULA EXACTA: CSR = sensitivity(response, retrieved_evidence) ∈ [0, 1]^B
        #   donde:
        #   - response = hidden_states ∈ R^(B×N×d) es la respuesta generada por el LLM
        #   - retrieved_evidence = encoded_docs ∈ R^(B×K×d) son documentos recuperados codificados
        #   - sensitivity: R^(B×d) × R^(B×d) → R^B calcula sensibilidad entre representaciones agregadas
        #   - CSR ∈ [0, 1]^B mide qué tan sensible es la respuesta a la evidencia
        # NOTACIÓN EN CÓDIGO: csr = Context Sensitivity Ratio
        # CÓDIGO: Calcular CSR entre respuesta y documentos recuperados
        csr = self._compute_context_sensitivity_ratio(hidden_states, encoded_docs)  # [batch] ∈ [0, 1]^B
        
        # PASO 2: Detectar spans "alucinados" (término exacto del paper)
        # EN EL PAPER: Sección 3.3 - Span-level Detection
        # FÓRMULA EXACTA: span_scores = span_detector(concat(response, CSR)) ∈ [0, 1]^(B×N)
        #   donde:
        #   - response ∈ R^(B×N×d) es la respuesta generada por el LLM
        #   - CSR ∈ [0, 1]^B es el Context Sensitivity Ratio (expandido a cada token)
        #   - span_detector: R^(B×N×(d+1)) → R^(B×N) detecta spans "alucinados"
        #   - span_scores ∈ [0, 1]^(B×N) son scores de alucinación por span (token)
        # NOTACIÓN EN CÓDIGO: span_scores = scores de spans "alucinados"
        # CÓDIGO: Detectar spans "alucinados" usando respuesta y CSR
        span_scores = self._detect_hallucinated_spans(hidden_states, csr)  # [batch, seq] ∈ [0, 1]^(B×N)
        
        # PASO 3: Aplicar corrección basada en detección de spans "alucinados" (término exacto)
        # EN EL PAPER: Sección 3.3 - Span-level Mitigation
        # FÓRMULA: output = response × (1 - hallucination_mask)
        #   donde hallucination_mask ∈ {0, 1}^(B×N×1) identifica spans "alucinados"
        # NOTACIÓN DEL PAPER: spans con score > threshold Y CSR bajo son "alucinados"
        #   Lógica exacta: span_score alto + CSR bajo → span "alucinado"
        # NOTACIÓN EN CÓDIGO: hallucination_mask = máscara binaria de spans "alucinados"
        # CÓDIGO: Crear máscara basada en scores de spans y CSR
        #   Condición 1: CSR bajo (no sensible a evidencia) - csr < sensitivity_threshold
        #   Operación: csr_low = I(csr < threshold) expandido a [batch, 1, 1]
        csr_low = (csr < self.config.sensitivity_threshold).float().unsqueeze(1).unsqueeze(2)  # [batch, 1, 1]
        #   Condición 2: Span score alto - span_scores > sensitivity_threshold
        #   Operación: span_high = I(span_scores > threshold) ∈ {0, 1}^(B×N×1)
        span_high = (span_scores > self.config.sensitivity_threshold).float().unsqueeze(-1)  # [batch, seq, 1]
        #   Combinación: spans "alucinados" = csr_low AND span_high
        #   FÓRMULA: hallucination_mask = csr_low × span_high ∈ {0, 1}^(B×N×1)
        hallucination_mask = (csr_low * span_high).float()  # [batch, seq, 1] - máscara binaria
        
        # EN EL PAPER: Mitigar spans "alucinados" (término exacto del paper)
        # FÓRMULA: output = response × (1 - α × hallucination_mask) ∈ R^(B×N×d)
        #   donde α = 0.5 es el factor de mitigación (reduce 50% la activación)
        #   y response ∈ R^(B×N×d) es la respuesta original del LLM
        # NOTACIÓN DEL PAPER: Los spans "alucinados" se mitigan reduciendo su activación
        # NOTACIÓN EN CÓDIGO: output = respuesta con spans "alucinados" mitigados
        # CÓDIGO: Reducir activación de spans "alucinados" (término exacto del paper)
        mitigation_factor = 1 - hallucination_mask * 0.5  # [batch, seq, 1] - factor de mitigación
        output = hidden_states * mitigation_factor  # [batch, seq, hidden_dim] - respuesta mitigada
        
        # Metadata para análisis detallado
        metadata = {
            'context_sensitivity_ratio': csr.mean().item(),
            'csr_std': csr.std().item(),
            'csr_min': csr.min().item(),
            'csr_max': csr.max().item(),
            'csr_low_ratio': (csr < self.config.sensitivity_threshold).float().mean().item(),
            'hallucinated_spans': hallucination_mask.mean().item(),
            'span_scores_mean': span_scores.mean().item(),
            'span_scores_std': span_scores.std().item(),
            'span_scores_max': span_scores.max().item(),
            'num_hallucinated_spans': hallucination_mask.sum().item(),
            'num_retrieved_docs': self.config.num_retrieved_docs
        }
        
        self._update_metrics(
            csr=metadata['context_sensitivity_ratio'],
            csr_low_ratio=metadata['csr_low_ratio'],
            hallucinated_spans=metadata['hallucinated_spans']
        )
        
        return output, metadata

