#!/usr/bin/env python3
"""
Extractor Mejorado de Top 10 Papers de Detección y Mitigación de Alucinaciones en LLMs
======================================================================================
Extrae información estructurada y exacta de papers sobre hallucination detection y mitigation.
"""

import json
import re
from typing import Dict, List, Any

# Texto proporcionado por el usuario - estructura exacta
HALLUCINATION_PAPERS = [
    {
        "title": "HaDeMiF: Hallucination Detection and Mitigation in Large Language Models",
        "authors": ["Zhou", "Zhang", "Lee", "Ye", "Zhang"],
        "year": 2025,
        "venue": "ICLR 2025",
        "venue_source": "proceedings.iclr.cc",
        "description": "Proponen dos redes ligeras (un árbol de decisiones dinámico + una MLP) para detectar y calibrar alucinaciones a partir de estados ocultos.",
        "url": "https://proceedings.iclr.cc/paper_files/paper/2025/hash/c98987c5ec4f30920d7190dc699e3daf-Abstract-Conference.html",
        "key_techniques": ["Dynamic Decision Tree", "MLP", "Lightweight Networks", "Calibration"],
        "reported_improvements": {
            "detection_accuracy": "Mejora en detección",
            "calibration": "Calibración de alucinaciones",
            "parameter_overhead": "< 2% de parámetros adicionales"
        }
    },
    {
        "title": "REFIND: Retrieval-Augmented Factuality Hallucination Detection in Large Language Models",
        "authors": ["Lee", "Yu"],
        "year": 2025,
        "venue": "arXiv 2025",
        "venue_source": "arXiv",
        "description": "Usan documentos recuperados para analizar sensibilidad del LLM a la evidencia (\"Context Sensitivity Ratio\") y así detectar spans \"alucinados\".",
        "url": "https://arxiv.org/abs/[ID_PENDIENTE]",
        "key_techniques": ["Retrieval-Augmented", "Context Sensitivity Ratio", "Span Detection", "Factuality Verification"],
        "reported_improvements": {
            "factuality_detection": "Detección de facticidad mejorada",
            "span_level_detection": "Detección a nivel de span"
        }
    },
    {
        "title": "You believe your LLM is not delusional? Think again! A study of LLM hallucination on foundation models under perturbation",
        "authors": [],
        "year": 2025,
        "venue": "SpringerLink 2025",
        "venue_source": "SpringerLink",
        "description": "Analiza cómo los LLMs alucinan cuando su contexto o inputs son perturbados, mostrando vulnerabilidad a ruido / cambios.",
        "url": "https://link.springer.com/article/[ID_PENDIENTE]",
        "key_techniques": ["Perturbation Analysis", "Robustness Study", "Vulnerability Analysis"],
        "reported_improvements": {
            "understanding": "Análisis de vulnerabilidades a perturbaciones"
        }
    },
    {
        "title": "Reducing hallucinations of large language models via hierarchical semantic piece",
        "authors": [],
        "year": 2025,
        "venue": "SpringerLink 2025",
        "venue_source": "SpringerLink",
        "description": "Framework unificado con componentes: parser de salida, verificador de hechos, mitigador.",
        "url": "https://link.springer.com/article/[ID_PENDIENTE]",
        "key_techniques": ["Hierarchical Framework", "Output Parser", "Fact Checker", "Mitigator"],
        "reported_improvements": {
            "hallucination_reduction": "Reducción de alucinaciones mediante framework jerárquico"
        }
    },
    {
        "title": "Halu-NLP at SemEval-2024 Task 6: MetaCheckGPT – Multi-task Hallucination Detection usando incertidumbre + meta-modelos",
        "authors": ["Mehta", "Hoblitzell", "O'Keefe", "Jang", "Varma"],
        "year": 2024,
        "venue": "SemEval 2024 / ACL Anthology",
        "venue_source": "ACL Anthology",
        "description": "Usan un meta-regresor (random forest) sobre varios LLMs para predecir cuándo están alucinando de forma \"modelo-agnóstica\".",
        "url": "https://aclanthology.org/[ID_PENDIENTE]",
        "key_techniques": ["Random Forest", "Meta-Regressor", "Model-Agnostic", "Multi-task Detection", "Uncertainty"],
        "reported_improvements": {
            "multi_task_detection": "Detección multi-tarea modelo-agnóstica"
        }
    },
    {
        "title": "A Closer Look at the Self-Verification Abilities of Large Language Models in Logical Reasoning",
        "authors": ["Hong", "Zhang", "Pang", "Yu", "Zhang"],
        "year": 2024,
        "venue": "NAACL 2024 / ACL Anthology",
        "venue_source": "ACL Anthology",
        "description": "Estudian qué tan bien los LLMs pueden verificar sus propios razonamientos lógicos — encuentran limitaciones significativas.",
        "url": "https://aclanthology.org/[ID_PENDIENTE]",
        "key_techniques": ["Self-Verification", "Logical Reasoning", "Capability Assessment"],
        "reported_improvements": {
            "understanding": "Análisis de capacidades y limitaciones de auto-verificación"
        }
    },
    {
        "title": "MALTO at SemEval-2025 Task 3: Detecting Hallucinations in LLMs via Uncertainty Quantification y Validación con Modelos Grandes",
        "authors": ["Savelli", "Koudounas", "Giobergia"],
        "year": 2025,
        "venue": "SemEval 2025 / ACL Anthology",
        "venue_source": "ACL Anthology",
        "description": "Combinan análisis de probabilidades con NLI para detectar fragmentos de alucinaciones a nivel de palabra.",
        "url": "https://aclanthology.org/[ID_PENDIENTE]",
        "key_techniques": ["Uncertainty Quantification", "Natural Language Inference", "Word-level Detection", "Large Model Validation"],
        "reported_improvements": {
            "fine_grained_detection": "Detección a nivel de palabra",
            "nli_validation": "Validación con NLI"
        }
    },
    {
        "title": "Hallucination Detection in LLMs: Fast and Memory-Efficient Fine-tuned Models",
        "authors": ["Arteaga", "Schön", "Pielawski"],
        "year": 2025,
        "venue": "Proceedings of Machine Learning Research 2025",
        "venue_source": "Proceedings of Machine Learning Research",
        "description": "Proponen entrenar ensembles ligeros (requieren poca memoria) que detecten alucinaciones de forma práctica.",
        "url": "https://proceedings.mlr.press/[ID_PENDIENTE]",
        "key_techniques": ["Lightweight Ensembles", "Memory Efficient", "Fast Training", "Practical Detection"],
        "reported_improvements": {
            "efficiency": "Modelos ligeros y eficientes en memoria",
            "speed": "Detección rápida"
        }
    },
    {
        "title": "Hallucination Detection in Large Language Models Using Diversion Decoding",
        "authors": ["Abdeen", "Siddiqui", "Ahmed", "Singhal", "Khan", "Modi", "Al-Shaer"],
        "year": 2025,
        "venue": "NIST 2025",
        "venue_source": "NIST",
        "description": "Introducen \"diversion decoding\": desafían al modelo durante la generación para extraer señales de incertidumbre y entrenar un detector.",
        "url": "https://nist.gov/[ID_PENDIENTE]",
        "key_techniques": ["Diversion Decoding", "Uncertainty Signals", "Generation-time Detection", "Adversarial Challenges"],
        "reported_improvements": {
            "detection_during_generation": "Detección durante generación",
            "uncertainty_extraction": "Extracción de señales de incertidumbre"
        }
    },
    {
        "title": "A framework to synthetically generate fine-grained hallucinated data",
        "authors": [],
        "year": 2025,
        "venue": "SpringerLink 2025",
        "venue_source": "SpringerLink",
        "description": "Proponen un método para generar datos \"alucinados\" etiquetados (diferentes tipos) para entrenar detectores más precisos.",
        "url": "https://link.springer.com/article/[ID_PENDIENTE]",
        "key_techniques": ["Synthetic Data Generation", "Fine-grained Labeling", "Training Data Creation", "Hallucination Typology"],
        "reported_improvements": {
            "training_data": "Generación de datos de entrenamiento etiquetados",
            "detector_accuracy": "Mejora en precisión de detectores"
        }
    }
]


def main():
    """Función principal."""
    # Guardar JSON
    output_file = 'scraped_papers/top10_hallucination_papers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(HALLUCINATION_PAPERS, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Extraídos {len(HALLUCINATION_PAPERS)} papers de hallucination detection")
    print(f"📁 Guardado en: {output_file}")
    print()
    
    # Mostrar resumen
    for i, paper in enumerate(HALLUCINATION_PAPERS, 1):
        print(f"{i}. {paper['title']}")
        if paper['authors']:
            print(f"   Autores: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"   Año: {paper['year']}")
        print(f"   Venue: {paper['venue']}")
        print(f"   URL: {paper['url']}")
        print(f"   Técnicas: {', '.join(paper['key_techniques'][:3])}{'...' if len(paper['key_techniques']) > 3 else ''}")
        print()


if __name__ == '__main__':
    main()



