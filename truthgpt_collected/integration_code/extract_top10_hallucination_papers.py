#!/usr/bin/env python3
"""
Extractor de Top 10 Papers de Detección y Mitigación de Alucinaciones en LLMs
==============================================================================
Extrae información estructurada de papers sobre hallucination detection y mitigation.
"""

import json
import re
from typing import Dict, List, Any

# Texto proporcionado por el usuario
HALLUCINATION_PAPERS_TEXT = """
HaDeMiF: Hallucination Detection and Mitigation in Large Language Models — Zhou, Zhang, Lee, Ye, Zhang (ICLR 2025)

Proponen dos redes ligeras (un árbol de decisiones dinámico + una MLP) para detectar y calibrar alucinaciones a partir de estados ocultos. 

proceedings.iclr.cc

REFIND: Retrieval-Augmented Factuality Hallucination Detection in Large Language Models — Lee, Yu (2025)

Usan documentos recuperados para analizar sensibilidad del LLM a la evidencia ("Context Sensitivity Ratio") y así detectar spans "alucinados". 

arXiv

You believe your LLM is not delusional? Think again! A study of LLM hallucination on foundation models under perturbation — (2025)

Analiza cómo los LLMs alucinan cuando su contexto o inputs son perturbados, mostrando vulnerabilidad a ruido / cambios. 

SpringerLink

Reducing hallucinations of large language models via hierarchical semantic piece — (2025)

Framework unificado con componentes: parser de salida, verificador de hechos, mitigador. 

SpringerLink

Halu-NLP at SemEval-2024 Task 6: MetaCheckGPT – Multi-task Hallucination Detection usando incertidumbre + meta-modelos — Mehta, Hoblitzell, O'Keefe, Jang, Varma (SemEval 2024)

Usan un meta-regresor (random forest) sobre varios LLMs para predecir cuándo están alucinando de forma "modelo-agnóstica". 

ACL Anthology

A Closer Look at the Self-Verification Abilities of Large Language Models in Logical Reasoning — Hong, Zhang, Pang, Yu, Zhang (NAACL 2024)

Estudian qué tan bien los LLMs pueden verificar sus propios razonamientos lógicos — encuentran limitaciones significativas. 

ACL Anthology

MALTO at SemEval-2025 Task 3: Detecting Hallucinations in LLMs via Uncertainty Quantification y Validación con Modelos Grandes — Savelli, Koudounas, Giobergia (2025)

Combinan análisis de probabilidades con NLI para detectar fragmentos de alucinaciones a nivel de palabra. 

ACL Anthology

Hallucination Detection in LLMs: Fast and Memory-Efficient Fine-tuned Models — Arteaga, Schön, Pielawski (2025)

Proponen entrenar ensembles ligeros (requieren poca memoria) que detecten alucinaciones de forma práctica. 

Proceedings of Machine Learning Research

Hallucination Detection in Large Language Models Using Diversion Decoding — Abdeen, Siddiqui, Ahmed, Singhal, Khan, Modi, Al-Shaer (2025)

Introducen "diversion decoding": desafían al modelo durante la generación para extraer señales de incertidumbre y entrenar un detector. 

NIST

A framework to synthetically generate fine-grained hallucinated data — (2025)

Proponen un método para generar datos "alucinados" etiquetados (diferentes tipos) para entrenar detectores más precisos. 

SpringerLink
"""


def extract_paper_info(text: str) -> List[Dict[str, Any]]:
    """Extrae información estructurada de cada paper."""
    papers = []
    
    # Dividir por líneas vacías dobles
    sections = re.split(r'\n\n+', text.strip())
    
    current_paper = None
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Detectar si es un título de paper (contiene "—" o ":")
        if '—' in section or (':' in section and len(section) < 200):
            # Guardar paper anterior si existe
            if current_paper:
                papers.append(current_paper)
            
            # Extraer título
            title_match = re.match(r'^([^—]+)', section)
            if not title_match:
                title_match = re.match(r'^([^:]+)', section)
            
            if title_match:
                title = title_match.group(1).strip()
                title = title.rstrip('.')
                
                # Extraer autores (después de — o :)
                authors_match = re.search(r'[—:]\s*([^(]+)\s*\(([^)]+)\)', section)
                authors = []
                venue_year = None
                
                if authors_match:
                    authors_str = authors_match.group(1).strip()
                    venue_year = authors_match.group(2).strip()
                    
                    # Separar autores por comas
                    authors = [a.strip() for a in authors_str.split(',')]
                    authors = [a for a in authors if a and not a.lower() in ['et al', 'et al.']]
                
                # Extraer año del venue_year
                year_match = re.search(r'(\d{4})', venue_year) if venue_year else None
                year = int(year_match.group(1)) if year_match else None
                
                # Extraer descripción (después del año o venue)
                desc_match = re.search(r'\)\.\s*(.+?)(?:\n|$)', section, re.DOTALL)
                description = ""
                if desc_match:
                    description = desc_match.group(1).strip()
                
                current_paper = {
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'venue': venue_year,
                    'description': description,
                    'url': None,
                    'key_techniques': [],
                    'reported_improvements': {}
                }
        
        # Detectar venue/source
        elif section.upper() in ['PROCEEDINGS.ICLR.CC', 'ARXIV', 'SPRINGERLINK', 'ACL ANTHOLOGY', 'PROCEEDINGS OF MACHINE LEARNING RESEARCH', 'NIST']:
            if current_paper:
                venue = section.strip()
                current_paper['venue'] = venue
                
                # URLs placeholder
                if venue.upper() == 'PROCEEDINGS.ICLR.CC':
                    current_paper['url'] = 'https://openreview.net/forum?id=[ID_PENDIENTE]'
                elif venue.upper() == 'ARXIV':
                    current_paper['url'] = 'https://arxiv.org/abs/[ID_PENDIENTE]'
                elif venue.upper() == 'SPRINGERLINK':
                    current_paper['url'] = 'https://link.springer.com/article/[ID_PENDIENTE]'
                elif venue.upper() == 'ACL ANTHOLOGY':
                    current_paper['url'] = 'https://aclanthology.org/[ID_PENDIENTE]'
                elif venue.upper() == 'PROCEEDINGS OF MACHINE LEARNING RESEARCH':
                    current_paper['url'] = 'https://proceedings.mlr.press/[ID_PENDIENTE]'
                elif venue.upper() == 'NIST':
                    current_paper['url'] = 'https://nist.gov/[ID_PENDIENTE]'
    
    # Agregar último paper
    if current_paper:
        papers.append(current_paper)
    
    # Post-procesamiento: extraer técnicas clave
    for paper in papers:
        desc = paper['description'].lower()
        techniques = []
        
        # Detectar técnicas mencionadas
        if 'tree' in desc or 'árbol' in desc or 'decision' in desc:
            techniques.append('Decision Tree')
        if 'mlp' in desc:
            techniques.append('MLP')
        if 'retrieval' in desc or 'recuperado' in desc:
            techniques.append('Retrieval-Augmented')
        if 'sensitivity' in desc or 'sensibilidad' in desc:
            techniques.append('Context Sensitivity')
        if 'perturbation' in desc or 'perturbado' in desc:
            techniques.append('Perturbation Analysis')
        if 'verification' in desc or 'verificación' in desc or 'verificador' in desc:
            techniques.append('Fact Verification')
        if 'meta' in desc or 'meta-modelo' in desc:
            techniques.append('Meta-Learning')
        if 'uncertainty' in desc or 'incertidumbre' in desc:
            techniques.append('Uncertainty Quantification')
        if 'nli' in desc:
            techniques.append('Natural Language Inference')
        if 'ensemble' in desc:
            techniques.append('Ensemble Methods')
        if 'diversion' in desc or 'decoding' in desc:
            techniques.append('Diversion Decoding')
        if 'synthetic' in desc or 'sintético' in desc or 'generate' in desc:
            techniques.append('Synthetic Data Generation')
        if 'self-verification' in desc or 'self verification' in desc:
            techniques.append('Self-Verification')
        
        paper['key_techniques'] = list(set(techniques))
    
    return papers


def main():
    """Función principal."""
    papers = extract_paper_info(HALLUCINATION_PAPERS_TEXT)
    
    # Mejorar información específica
    for i, paper in enumerate(papers):
        # Añadir información específica conocida
        if 'HaDeMiF' in paper['title']:
            paper['key_techniques'].extend(['Dynamic Decision Tree', 'Lightweight Networks'])
            paper['reported_improvements'] = {
                'detection_accuracy': 'Mejora en detección',
                'calibration': 'Calibración de alucinaciones'
            }
        elif 'REFIND' in paper['title']:
            paper['key_techniques'].extend(['Retrieval-Augmented', 'Context Sensitivity Ratio'])
            paper['reported_improvements'] = {
                'factuality_detection': 'Detección de facticidad mejorada'
            }
        elif 'delusional' in paper['title'].lower() or 'perturbation' in paper['description'].lower():
            paper['key_techniques'].extend(['Perturbation Analysis', 'Robustness Study'])
            paper['reported_improvements'] = {
                'understanding': 'Análisis de vulnerabilidades'
            }
        elif 'hierarchical semantic' in paper['title'].lower():
            paper['key_techniques'].extend(['Hierarchical Framework', 'Fact Checker', 'Mitigator'])
            paper['reported_improvements'] = {
                'hallucination_reduction': 'Reducción de alucinaciones'
            }
        elif 'MetaCheckGPT' in paper['title'] or 'Halu-NLP' in paper['title']:
            paper['key_techniques'].extend(['Random Forest', 'Model-Agnostic'])
            paper['reported_improvements'] = {
                'multi_task_detection': 'Detección multi-tarea'
            }
        elif 'Self-Verification' in paper['title']:
            paper['key_techniques'].extend(['Self-Verification', 'Logical Reasoning'])
            paper['reported_improvements'] = {
                'understanding': 'Análisis de capacidades de auto-verificación'
            }
        elif 'MALTO' in paper['title']:
            paper['key_techniques'].extend(['Uncertainty Quantification', 'NLI', 'Word-level Detection'])
            paper['reported_improvements'] = {
                'fine_grained_detection': 'Detección a nivel de palabra'
            }
        elif 'Fast and Memory-Efficient' in paper['title']:
            paper['key_techniques'].extend(['Lightweight Ensembles', 'Memory Efficient'])
            paper['reported_improvements'] = {
                'efficiency': 'Modelos ligeros y eficientes'
            }
        elif 'Diversion Decoding' in paper['title']:
            paper['key_techniques'].extend(['Diversion Decoding', 'Uncertainty Signals'])
            paper['reported_improvements'] = {
                'detection_during_generation': 'Detección durante generación'
            }
        elif 'synthetically generate' in paper['title'].lower():
            paper['key_techniques'].extend(['Synthetic Data Generation', 'Fine-grained Labeling'])
            paper['reported_improvements'] = {
                'training_data': 'Generación de datos de entrenamiento'
            }
    
    # Guardar JSON
    output_file = 'scraped_papers/top10_hallucination_papers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Extraídos {len(papers)} papers de hallucination detection")
    print(f"📁 Guardado en: {output_file}")
    print()
    
    # Mostrar resumen
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title']}")
        print(f"   Autores: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"   Año: {paper['year']}")
        print(f"   Técnicas: {', '.join(paper['key_techniques'][:3])}{'...' if len(paper['key_techniques']) > 3 else ''}")
        print()


if __name__ == '__main__':
    main()



