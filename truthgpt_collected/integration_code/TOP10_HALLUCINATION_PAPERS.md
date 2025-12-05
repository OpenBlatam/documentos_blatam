# Top 10 Papers de Detección y Mitigación de Alucinaciones en LLMs

Este documento resume los 10 papers más importantes sobre detección y mitigación de alucinaciones (hallucinations) en Large Language Models.

## 📚 Papers Implementados

### 1. HaDeMiF: Hallucination Detection and Mitigation in Large Language Models
**Autores:** Zhou, Zhang, Lee, Ye, Zhang (2025)  
**Venue:** ICLR 2025  
**URL:** https://proceedings.iclr.cc/paper_files/paper/2025/hash/c98987c5ec4f30920d7190dc699e3daf-Abstract-Conference.html

**Técnica Principal:**
- Dos redes ligeras: árbol de decisiones dinámico + MLP
- Detecta y calibra alucinaciones a partir de estados ocultos
- Enfoque eficiente y ligero

**Implementación:** `papers/research/paper_hademif.py`

**Uso:**
```python
from papers.research.paper_hademif import HaDeMiFModule, HaDeMiFConfig

config = HaDeMiFConfig(hidden_dim=512, detection_threshold=0.5)
module = HaDeMiFModule(config)

output, metadata = module(hidden_states)
# metadata contiene: detection_score, calibration_score, combined_score, is_hallucination
```

---

### 2. REFIND: Retrieval-Augmented Factuality Hallucination Detection
**Autores:** Lee, Yu (2025)  
**Venue:** arXiv 2025  
**URL:** https://arxiv.org/abs/[ID_PENDIENTE]

**Técnica Principal:**
- Usa documentos recuperados para analizar sensibilidad del LLM a la evidencia
- Calcula "Context Sensitivity Ratio" (CSR) para detectar spans alucinados
- Enfoque basado en retrieval para verificación de facticidad

**Implementación:** `papers/research/paper_refind.py`

**Uso:**
```python
from papers.research.paper_refind import REFINDModule, REFINDConfig

config = REFINDConfig(hidden_dim=512, num_retrieved_docs=5)
module = REFINDModule(config)

output, metadata = module(hidden_states, retrieved_docs=docs)
# metadata contiene: context_sensitivity_ratio, hallucinated_spans, span_scores_mean
```

---

### 3. You believe your LLM is not delusional? Think again!
**Autores:** (2025)  
**Venue:** SpringerLink 2025  
**URL:** https://link.springer.com/article/[ID_PENDIENTE]

**Técnica Principal:**
- Analiza cómo los LLMs alucinan cuando su contexto o inputs son perturbados
- Muestra vulnerabilidad a ruido y cambios
- Estudio de robustez y análisis de perturbaciones

**Técnicas Clave:**
- Perturbation Analysis
- Robustness Study
- Vulnerability Analysis

---

### 4. Reducing hallucinations via hierarchical semantic piece
**Autores:** (2025)  
**Venue:** SpringerLink 2025  
**URL:** https://link.springer.com/article/[ID_PENDIENTE]

**Técnica Principal:**
- Framework unificado con componentes: parser de salida, verificador de hechos, mitigador
- Enfoque jerárquico para reducción de alucinaciones

**Técnicas Clave:**
- Hierarchical Framework
- Fact Checker
- Mitigator

---

### 5. MetaCheckGPT: Multi-task Hallucination Detection
**Autores:** Mehta, Hoblitzell, O'Keefe, Jang, Varma (2024)  
**Venue:** SemEval 2024 / ACL Anthology  
**URL:** https://aclanthology.org/[ID_PENDIENTE]

**Técnica Principal:**
- Meta-regresor (random forest) sobre varios LLMs
- Predice cuándo están alucinando de forma "modelo-agnóstica"
- Usa incertidumbre y meta-modelos para detección multi-tarea

**Implementación:** `papers/research/paper_metacheckgpt.py`

**Uso:**
```python
from papers.research.paper_metacheckgpt import MetaCheckGPTModule, MetaCheckGPTConfig

config = MetaCheckGPTConfig(hidden_dim=512, num_llm_models=3)
module = MetaCheckGPTModule(config)

output, metadata = module(hidden_states, llm_outputs=[output1, output2, output3])
# metadata contiene: hallucination_score, uncertainty_mean, num_models, is_hallucination
```

---

### 6. A Closer Look at the Self-Verification Abilities
**Autores:** Hong, Zhang, Pang, Yu, Zhang (2024)  
**Venue:** NAACL 2024 / ACL Anthology  
**URL:** https://aclanthology.org/[ID_PENDIENTE]

**Técnica Principal:**
- Estudia qué tan bien los LLMs pueden verificar sus propios razonamientos lógicos
- Encuentra limitaciones significativas en auto-verificación

**Técnicas Clave:**
- Self-Verification
- Logical Reasoning Analysis
- Capability Assessment

---

### 7. MALTO: Detecting Hallucinations via Uncertainty + NLI
**Autores:** Savelli, Koudounas, Giobergia (2025)  
**Venue:** SemEval 2025 / ACL Anthology  
**URL:** https://aclanthology.org/[ID_PENDIENTE]

**Técnica Principal:**
- Combina análisis de probabilidades con NLI (Natural Language Inference)
- Detecta fragmentos de alucinaciones a nivel de palabra
- Usa modelos grandes para validación

**Implementación:** `papers/research/paper_malto.py`

**Uso:**
```python
from papers.research.paper_malto import MALTOModule, MALTOConfig

config = MALTOConfig(hidden_dim=512, uncertainty_threshold=0.5)
module = MALTOModule(config)

output, metadata = module(hidden_states, context=context)
# metadata contiene: uncertainty_mean, nli_contradiction_score, word_hallucination_ratio
```

---

### 8. Fast and Memory-Efficient Fine-tuned Models
**Autores:** Arteaga, Schön, Pielawski (2025)  
**Venue:** Proceedings of Machine Learning Research 2025  
**URL:** https://proceedings.mlr.press/[ID_PENDIENTE]

**Técnica Principal:**
- Propone entrenar ensembles ligeros (requieren poca memoria)
- Detectan alucinaciones de forma práctica y eficiente

**Técnicas Clave:**
- Lightweight Ensembles
- Memory Efficient Training
- Practical Detection

---

### 9. Hallucination Detection Using Diversion Decoding
**Autores:** Abdeen, Siddiqui, Ahmed, Singhal, Khan, Modi, Al-Shaer (2025)  
**Venue:** NIST 2025  
**URL:** https://nist.gov/[ID_PENDIENTE]

**Técnica Principal:**
- Introduce "diversion decoding": desafían al modelo durante la generación
- Extrae señales de incertidumbre para entrenar un detector
- Detección durante el proceso de generación

**Técnicas Clave:**
- Diversion Decoding
- Uncertainty Signals
- Generation-time Detection

---

### 10. A framework to synthetically generate fine-grained hallucinated data
**Autores:** (2025)  
**Venue:** SpringerLink 2025  
**URL:** https://link.springer.com/article/[ID_PENDIENTE]

**Técnica Principal:**
- Propone método para generar datos "alucinados" etiquetados
- Diferentes tipos de alucinaciones para entrenar detectores más precisos
- Generación sintética de datos de entrenamiento

**Técnicas Clave:**
- Synthetic Data Generation
- Fine-grained Labeling
- Training Data Creation

---

## 🔄 Comparación de Técnicas

| Técnica | Detección | Mitigación | Eficiencia | Nivel de Granularidad |
|---------|-----------|------------|------------|----------------------|
| HaDeMiF | ✅ | ✅ | Alta | Token/Sentence |
| REFIND | ✅ | Parcial | Media | Span-level |
| MetaCheckGPT | ✅ | Parcial | Media | Model-level |
| MALTO | ✅ | Parcial | Media | Word-level |
| Diversion Decoding | ✅ | No | Alta | Generation-time |
| Self-Verification | ✅ | No | Baja | Reasoning-level |

## 🎯 Mejores Prácticas

1. **Para detección ligera:** Usar HaDeMiF o modelos memory-efficient
2. **Para verificación de hechos:** Usar REFIND o frameworks jerárquicos
3. **Para detección multi-modelo:** Usar MetaCheckGPT
4. **Para detección fina:** Usar MALTO (word-level)
5. **Para detección durante generación:** Usar Diversion Decoding
6. **Para análisis de capacidades:** Estudiar Self-Verification

## 📊 Métricas Reportadas

- **Precisión de Detección:** Variable según técnica (60-90% típicamente)
- **Eficiencia:** HaDeMiF y modelos ligeros muestran mejor eficiencia
- **Granularidad:** MALTO permite detección a nivel de palabra
- **Robustez:** REFIND y MetaCheckGPT muestran mejor generalización

---

**Nota:** Los URLs de los papers son placeholders. Se deben actualizar cuando los papers estén disponibles públicamente.

