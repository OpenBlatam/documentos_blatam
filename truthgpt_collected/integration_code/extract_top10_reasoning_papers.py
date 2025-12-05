#!/usr/bin/env python3
"""
Extractor de Top 10 Papers de Reasoning en LLMs
================================================
Extrae información estructurada de papers sobre razonamiento (chain, tree, graph of thoughts).
"""

import json
import re
from typing import Dict, List, Any

# Texto proporcionado por el usuario
REASONING_PAPERS_TEXT = """
SOLAR: Scalable Optimization of Large-scale Architecture for Reasoning — Chen, Li, Luo, Bolimera, Ahmed, Srinivasan, Gokhale, Savvides (2025). Introduce un framework para adaptar dinámicamente entre chain, tree y graph de pensamiento para mejorar precisión y eficiencia. 

arXiv

Adaptive Graph of Thoughts: Test-Time Adaptive Reasoning — Pandey, Ghukasyan, Goktas, Radha (2025). Usan un DAG dinámico para razonar solo donde es necesario, uniendo chain, tree y graph en inferencia. 

arXiv

What Makes a Good Reasoning Chain? Uncovering Structural Patterns in Long Chain-of-Thought Reasoning — LCoT2Tree, (2025). Analiza patrones estructurales (exploración, backtracking, verificación) en cadenas de razonamiento largo para predecir cuándo son correctas. 

ACL Anthology

Disentangling Memory and Reasoning Ability in Large Language Models — Yao, Yu, Zhang, Narasimhan, et al. (2025). Estudia cómo separar la capacidad de memoria de la capacidad de razonamiento en LLMs para ver qué parte del razonamiento es "memoria latente" vs "pensamiento activo". 

ACL Anthology

Self-guided Knowledgeable Network of Thoughts (kNoT) — Chen, Yeh, Chen, Yang, Ming-Syan (2024). Introduce una red de "pensamientos" como nodo de un grafo (no solo cadena o árbol), permitiendo planes de razonamiento más complejos y flexibles. 

arXiv

Graph Chain-of-Thought: Augmenting Large Language Models by Reasoning on Graphs — Jin, Xie, Zhang, et al. (2024). Propone razonar sobre grafos de conocimiento; cada paso del modelo interactúa con un grafo para generar pensamiento más estructurado. 

arXiv

Demystifying Chains, Trees, and Graphs of Thoughts — Besta, Memedi, Zhang, et al. (2024). Análisis teórico y estructural de las diferentes formas de pensamiento (chain, tree, graph) para entender qué paradigmas funcionan mejor según la tarea. 

emergentmind.com

Forest-of-Thought: Scaling Test-Time Compute for Enhancing LLM Reasoning — Bi, Han, Liu, Tang, Wang (2024). Introducen un framework que mantiene múltiples árboles de razonamiento en paralelo ("forest"), activando solo los más relevantes para mejorar precisión/eficiencia. 

Kingy AI

Beyond Chain-of-Thought: Effective Graph-of-Thought Reasoning in Language Models — Yao, Li, Zhao (2024). Propone un encoder para grafo de pensamientos que se fusiona con la entrada original para permitir razonamiento no secuencial. 

bohrium.dp.tech

Table as Thought: Exploring Structured Thoughts in LLM Reasoning — framework presentado en TRL 2025. Proponen organizar "pensamientos" en una estructura de tabla para razonar con LLMs, una nueva forma de estructurar la inferencia. 

ACL Anthology
"""


def extract_paper_info(text: str) -> List[Dict[str, Any]]:
    """Extrae información estructurada de cada paper."""
    papers = []
    
    # Dividir por líneas vacías dobles o títulos
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
                # Remover puntos finales
                title = title.rstrip('.')
                
                # Extraer autores (después de — o :)
                authors_match = re.search(r'[—:]\s*([^(]+)\s*\((\d{4})\)', section)
                authors = []
                year = None
                
                if authors_match:
                    authors_str = authors_match.group(1).strip()
                    year = int(authors_match.group(2))
                    
                    # Separar autores por comas
                    authors = [a.strip() for a in authors_str.split(',')]
                    # Limpiar "et al." y otros
                    authors = [a for a in authors if a and not a.lower() in ['et al', 'et al.']]
                
                # Extraer descripción (después del año)
                desc_match = re.search(r'\((\d{4})\)\.\s*(.+?)(?:\n|$)', section, re.DOTALL)
                description = ""
                if desc_match:
                    description = desc_match.group(2).strip()
                
                current_paper = {
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'description': description,
                    'venue': None,
                    'url': None,
                    'key_techniques': [],
                    'reported_improvements': {}
                }
        
        # Detectar venue/source
        elif section.upper() in ['ARXIV', 'ACL ANTHOLOGY', 'EMERGENTMIND.COM', 'KINGY AI', 'BOHRIUM.DP.TECH']:
            if current_paper:
                venue = section.strip()
                current_paper['venue'] = venue
                
                # URLs placeholder (se buscarán después)
                if venue.upper() == 'ARXIV':
                    current_paper['url'] = 'https://arxiv.org/abs/[ID_PENDIENTE]'
                elif venue.upper() == 'ACL ANTHOLOGY':
                    current_paper['url'] = 'https://aclanthology.org/[ID_PENDIENTE]'
                elif venue.upper() == 'EMERGENTMIND.COM':
                    current_paper['url'] = 'https://emergentmind.com/[ID_PENDIENTE]'
                elif venue.upper() == 'KINGY AI':
                    current_paper['url'] = 'https://kingy.ai/[ID_PENDIENTE]'
                elif venue.upper() == 'BOHRIUM.DP.TECH':
                    current_paper['url'] = 'https://bohrium.dp.tech/[ID_PENDIENTE]'
    
    # Agregar último paper
    if current_paper:
        papers.append(current_paper)
    
    # Post-procesamiento: extraer técnicas clave de las descripciones
    for paper in papers:
        desc = paper['description'].lower()
        techniques = []
        
        # Detectar técnicas mencionadas
        if 'chain' in desc or 'cadena' in desc:
            techniques.append('Chain-of-Thought')
        if 'tree' in desc or 'árbol' in desc:
            techniques.append('Tree-of-Thought')
        if 'graph' in desc or 'grafo' in desc:
            techniques.append('Graph-of-Thought')
        if 'dag' in desc:
            techniques.append('DAG Reasoning')
        if 'adapt' in desc or 'adaptativo' in desc:
            techniques.append('Adaptive Reasoning')
        if 'forest' in desc:
            techniques.append('Forest-of-Thought')
        if 'table' in desc or 'tabla' in desc:
            techniques.append('Table-of-Thought')
        if 'memory' in desc or 'memoria' in desc:
            techniques.append('Memory-Rasoning Disentanglement')
        if 'network' in desc or 'red' in desc:
            techniques.append('Network-of-Thoughts')
        if 'backtracking' in desc:
            techniques.append('Backtracking')
        if 'verification' in desc or 'verificación' in desc:
            techniques.append('Verification')
        
        paper['key_techniques'] = list(set(techniques))
    
    return papers


def main():
    """Función principal."""
    papers = extract_paper_info(REASONING_PAPERS_TEXT)
    
    # Mejorar información específica
    for i, paper in enumerate(papers):
        # Añadir información específica conocida
        if 'SOLAR' in paper['title']:
            paper['key_techniques'].extend(['Dynamic Architecture', 'Multi-Paradigm Reasoning'])
            paper['reported_improvements'] = {
                'accuracy_improvement': 'Variable según tarea',
                'efficiency_improvement': 'Mejora adaptativa'
            }
        elif 'Adaptive Graph of Thoughts' in paper['title']:
            paper['key_techniques'].extend(['Test-Time Adaptation', 'Dynamic DAG'])
            paper['reported_improvements'] = {
                'reasoning_quality': 'Mejora selectiva',
                'compute_efficiency': 'Reduce computación innecesaria'
            }
        elif 'What Makes a Good Reasoning Chain' in paper['title']:
            paper['key_techniques'].extend(['Structural Pattern Analysis', 'LCoT2Tree'])
            paper['reported_improvements'] = {
                'prediction_accuracy': 'Mejora en predicción de cadenas correctas'
            }
        elif 'Disentangling Memory' in paper['title']:
            paper['key_techniques'].extend(['Memory Analysis', 'Reasoning Analysis'])
            paper['reported_improvements'] = {
                'understanding': 'Separación memoria vs razonamiento'
            }
        elif 'kNoT' in paper['title'] or 'Knowledgeable Network' in paper['title']:
            paper['key_techniques'].extend(['Knowledge Graph', 'Network Structure'])
            paper['reported_improvements'] = {
                'reasoning_complexity': 'Soporta razonamiento más complejo'
            }
        elif 'Graph Chain-of-Thought' in paper['title']:
            paper['key_techniques'].extend(['Knowledge Graph Reasoning', 'Graph Interaction'])
            paper['reported_improvements'] = {
                'structured_reasoning': 'Razonamiento más estructurado'
            }
        elif 'Demystifying' in paper['title']:
            paper['key_techniques'].extend(['Theoretical Analysis', 'Paradigm Comparison'])
            paper['reported_improvements'] = {
                'understanding': 'Análisis comparativo de paradigmas'
            }
        elif 'Forest-of-Thought' in paper['title']:
            paper['key_techniques'].extend(['Parallel Trees', 'Selective Activation'])
            paper['reported_improvements'] = {
                'accuracy': 'Mejora con múltiples árboles',
                'efficiency': 'Solo activa árboles relevantes'
            }
        elif 'Beyond Chain-of-Thought' in paper['title']:
            paper['key_techniques'].extend(['Graph Encoder', 'Non-Sequential Reasoning'])
            paper['reported_improvements'] = {
                'reasoning_flexibility': 'Razonamiento no secuencial'
            }
        elif 'Table as Thought' in paper['title']:
            paper['key_techniques'].extend(['Tabular Structure', 'Structured Inference'])
            paper['reported_improvements'] = {
                'reasoning_organization': 'Nueva forma de estructurar inferencia'
            }
    
    # Guardar JSON
    output_file = 'scraped_papers/top10_reasoning_papers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Extraídos {len(papers)} papers de reasoning")
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



