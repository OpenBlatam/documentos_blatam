#!/usr/bin/env python3
"""
Mejoras avanzadas adicionales para el generador de documentos:
- Análisis de coherencia y cohesión
- Análisis de estructura de enlaces
- Detección de patrones
- Análisis de tendencias
- Exportación a más formatos
"""

import re
import json
from collections import Counter, defaultdict
from datetime import datetime
import math

def analyze_coherence(content):
    """Analiza la coherencia del documento basado en transiciones y conectores"""
    # Palabras de transición comunes
    transitions = {
        'adición': ['además', 'también', 'asimismo', 'igualmente', 'por otra parte', 'de igual manera'],
        'contraste': ['sin embargo', 'no obstante', 'pero', 'aunque', 'a pesar de', 'en cambio'],
        'causa': ['porque', 'debido a', 'gracias a', 'a causa de', 'puesto que', 'ya que'],
        'consecuencia': ['por lo tanto', 'así que', 'en consecuencia', 'por consiguiente', 'de ahí que'],
        'temporal': ['después', 'luego', 'posteriormente', 'más tarde', 'entonces', 'finalmente'],
        'ejemplo': ['por ejemplo', 'como', 'tal como', 'a saber', 'es decir', 'en otras palabras']
    }
    
    content_lower = content.lower()
    transition_counts = {}
    total_transitions = 0
    
    for category, words in transitions.items():
        count = sum([content_lower.count(word) for word in words])
        transition_counts[category] = count
        total_transitions += count
    
    # Score de coherencia (0-100)
    # Más transiciones = mejor coherencia (hasta un punto)
    words = len(re.findall(r'\b\w+\b', content))
    transition_density = (total_transitions / max(words, 1)) * 1000
    
    # Normalizar a 0-100
    coherence_score = min(100, max(0, (transition_density / 5) * 100))
    
    return {
        'coherence_score': round(coherence_score, 2),
        'transition_density': round(transition_density, 2),
        'transition_counts': transition_counts,
        'total_transitions': total_transitions
    }

def analyze_link_structure(content):
    """Analiza la estructura de enlaces internos y externos"""
    # Enlaces markdown
    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
    
    internal_links = []
    external_links = []
    anchor_links = []
    
    for text, url in links:
        if url.startswith('#'):
            anchor_links.append((text, url))
        elif url.startswith('http://') or url.startswith('https://'):
            external_links.append((text, url))
        elif not url.startswith('mailto:') and not url.startswith('tel:'):
            internal_links.append((text, url))
    
    # Análisis de anclas (enlaces a secciones)
    anchors = [url for _, url in anchor_links]
    anchor_targets = Counter([a.lstrip('#').lower().replace('-', ' ') for a in anchors])
    
    return {
        'total_links': len(links),
        'internal_links': len(internal_links),
        'external_links': len(external_links),
        'anchor_links': len(anchor_links),
        'most_linked_sections': dict(anchor_targets.most_common(10)),
        'link_diversity': len(set([url for _, url in links])) / max(len(links), 1)
    }

def detect_patterns(content):
    """Detecta patrones comunes en el documento"""
    patterns = {
        'has_code_examples': bool(re.search(r'```[\s\S]*?```', content)),
        'has_tables': bool(re.search(r'\|.*\|', content)),
        'has_lists': bool(re.search(r'^[\s]*[-*+]\s', content, re.MULTILINE)),
        'has_quotes': bool(re.search(r'^>', content, re.MULTILINE)),
        'has_todos': bool(re.search(r'\[[ xX]\]', content)),
        'has_metadata': bool(re.search(r'^---[\s\S]*?---', content)),
        'has_math': bool(re.search(r'\$.*?\$', content)),
        'has_diagrams': bool(re.search(r'```(mermaid|graph|sequence)', content, re.IGNORECASE)),
    }
    
    # Contar patrones
    pattern_count = sum(1 for v in patterns.values() if v)
    pattern_diversity = pattern_count / len(patterns)
    
    return {
        'patterns': patterns,
        'pattern_count': pattern_count,
        'pattern_diversity': round(pattern_diversity, 2)
    }

def analyze_trends(content_lines):
    """Analiza tendencias a lo largo del documento"""
    # Dividir en secciones (aproximado)
    sections = []
    current_section = []
    
    for line in content_lines:
        if line.strip().startswith('#'):
            if current_section:
                sections.append(current_section)
            current_section = [line]
        else:
            current_section.append(line)
    if current_section:
        sections.append(current_section)
    
    # Analizar cada sección
    section_metrics = []
    for i, section in enumerate(sections):
        section_text = '\n'.join(section)
        words = len(re.findall(r'\b\w+\b', section_text))
        code_blocks = section_text.count('```') // 2
        links = len(re.findall(r'\[([^\]]+)\]\([^\)]+\)', section_text))
        
        section_metrics.append({
            'section': i + 1,
            'words': words,
            'code_blocks': code_blocks,
            'links': links,
            'density': words / max(len(section), 1)
        })
    
    # Calcular tendencias
    if len(section_metrics) > 1:
        word_trend = 'increasing' if section_metrics[-1]['words'] > section_metrics[0]['words'] else 'decreasing'
        code_trend = 'increasing' if section_metrics[-1]['code_blocks'] > section_metrics[0]['code_blocks'] else 'stable'
    else:
        word_trend = 'stable'
        code_trend = 'stable'
    
    return {
        'section_count': len(sections),
        'section_metrics': section_metrics,
        'word_trend': word_trend,
        'code_trend': code_trend,
        'avg_words_per_section': sum([m['words'] for m in section_metrics]) / max(len(section_metrics), 1)
    }

def calculate_engagement_score(content, stats):
    """Calcula un score de engagement basado en múltiples factores"""
    score = 0
    max_score = 100
    
    # Factor 1: Longitud apropiada (20 puntos)
    word_count = stats.get('total_words', 0)
    if 500 <= word_count <= 5000:
        score += 20
    elif 200 <= word_count < 500 or 5000 < word_count <= 10000:
        score += 15
    elif word_count > 10000:
        score += 10
    
    # Factor 2: Estructura (20 puntos)
    sections = stats.get('total_sections', 0)
    if 3 <= sections <= 20:
        score += 20
    elif sections > 20:
        score += 15
    
    # Factor 3: Elementos visuales (20 puntos)
    images = stats.get('images', 0)
    tables = stats.get('tables', 0)
    if images > 0:
        score += 10
    if tables > 0:
        score += 10
    
    # Factor 4: Enlaces (15 puntos)
    links = stats.get('links', 0)
    if links >= 5:
        score += 15
    elif links >= 2:
        score += 10
    elif links >= 1:
        score += 5
    
    # Factor 5: Código y ejemplos (15 puntos)
    code_blocks = stats.get('code_blocks', 0)
    if code_blocks > 0:
        score += 15
    elif code_blocks == 0 and '```' in content:
        score += 5
    
    # Factor 6: Legibilidad (10 puntos)
    readability = stats.get('readability_score', 50)
    if readability >= 60:
        score += 10
    elif readability >= 50:
        score += 7
    elif readability >= 40:
        score += 5
    
    return min(max_score, score)

def generate_markdown_report(doc_name, all_analyses):
    """Genera un reporte en formato Markdown"""
    report = f"""# 📊 Reporte de Análisis: {doc_name}

**Generado el:** {datetime.now().strftime('%d de %B de %Y a las %H:%M')}

---

## 📈 Métricas Principales

"""
    
    if 'stats' in all_analyses:
        stats = all_analyses['stats']
        report += f"""
- **Palabras:** {stats.get('total_words', 0):,}
- **Secciones:** {stats.get('total_sections', 0)}
- **Bloques de Código:** {stats.get('code_blocks', 0)}
- **Enlaces:** {stats.get('links', 0)}
- **Imágenes:** {stats.get('images', 0)}
- **Tablas:** {stats.get('tables', 0)}
"""
    
    if 'readability' in all_analyses:
        readability = all_analyses['readability']
        report += f"""
## 📖 Legibilidad

- **Score Flesch:** {readability.get('flesch_score', 0):.2f}
- **Nivel de Lectura:** {readability.get('reading_level', 'N/A')}
- **Longitud Promedio de Oraciones:** {readability.get('avg_sentence_length', 0):.2f} palabras
"""
    
    if 'coherence' in all_analyses:
        coherence = all_analyses['coherence']
        report += f"""
## 🔗 Coherencia

- **Score de Coherencia:** {coherence.get('coherence_score', 0):.2f}/100
- **Densidad de Transiciones:** {coherence.get('transition_density', 0):.2f}
- **Total de Transiciones:** {coherence.get('total_transitions', 0)}
"""
    
    if 'link_structure' in all_analyses:
        links = all_analyses['link_structure']
        report += f"""
## 🔗 Estructura de Enlaces

- **Total de Enlaces:** {links.get('total_links', 0)}
- **Enlaces Internos:** {links.get('internal_links', 0)}
- **Enlaces Externos:** {links.get('external_links', 0)}
- **Enlaces a Anclas:** {links.get('anchor_links', 0)}
- **Diversidad de Enlaces:** {links.get('link_diversity', 0):.2%}
"""
    
    if 'patterns' in all_analyses:
        patterns = all_analyses['patterns']
        report += f"""
## 🎨 Patrones Detectados

- **Ejemplos de Código:** {'✅' if patterns.get('has_code_examples') else '❌'}
- **Tablas:** {'✅' if patterns.get('has_tables') else '❌'}
- **Listas:** {'✅' if patterns.get('has_lists') else '❌'}
- **Citas:** {'✅' if patterns.get('has_quotes') else '❌'}
- **TODOs:** {'✅' if patterns.get('has_todos') else '❌'}
- **Diversidad de Patrones:** {patterns.get('pattern_diversity', 0):.2%}
"""
    
    if 'engagement' in all_analyses:
        engagement = all_analyses['engagement']
        report += f"""
## ⭐ Score de Engagement

**Score Total:** {engagement}/100

Este score evalúa qué tan atractivo y útil es el documento para los lectores.
"""
    
    report += "\n---\n\n*Reporte generado automáticamente*"
    
    return report

def export_to_csv(data, output_path):
    """Exporta datos a CSV"""
    import csv
    
    if isinstance(data, dict):
        # Convertir dict a lista de filas
        rows = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            rows.append([str(key), str(value)])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Métrica', 'Valor'])
            writer.writerows(rows)
    else:
        # Si es una lista de dicts
        if data and isinstance(data[0], dict):
            fieldnames = data[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
    
    print(f"✅ CSV exportado: {output_path}")

def create_topic_network(topics_list):
    """Crea una representación de red de temas"""
    # Contar co-ocurrencias de temas
    topic_pairs = []
    for i, topic1 in enumerate(topics_list):
        for topic2 in topics_list[i+1:]:
            if topic1 != topic2:
                topic_pairs.append((min(topic1, topic2), max(topic1, topic2)))
    
    pair_counts = Counter(topic_pairs)
    
    return {
        'nodes': list(set(topics_list)),
        'edges': [{'source': pair[0], 'target': pair[1], 'weight': count} 
                  for pair, count in pair_counts.most_common(20)],
        'top_connections': dict(pair_counts.most_common(10))
    }

def analyze_document_quality(content, all_stats):
    """Análisis integral de calidad del documento"""
    quality_factors = {
        'completeness': 0,  # ¿Tiene todas las secciones necesarias?
        'clarity': 0,       # ¿Es claro y legible?
        'structure': 0,    # ¿Está bien estructurado?
        'engagement': 0,   # ¿Es atractivo?
        'usefulness': 0    # ¿Es útil?
    }
    
    # Completeness (0-20)
    required_sections = ['introducción', 'contenido', 'conclusión', 'resumen']
    content_lower = content.lower()
    found_sections = sum([1 for section in required_sections if section in content_lower])
    quality_factors['completeness'] = (found_sections / len(required_sections)) * 20
    
    # Clarity (0-20)
    readability = all_stats.get('readability_score', 50)
    quality_factors['clarity'] = min(20, (readability / 100) * 20)
    
    # Structure (0-20)
    sections = all_stats.get('total_sections', 0)
    if 3 <= sections <= 20:
        quality_factors['structure'] = 20
    elif sections > 20:
        quality_factors['structure'] = 15
    elif sections > 0:
        quality_factors['structure'] = 10
    
    # Engagement (0-20)
    quality_factors['engagement'] = all_stats.get('engagement_score', 0) / 5
    
    # Usefulness (0-20)
    links = all_stats.get('links', 0)
    code_blocks = all_stats.get('code_blocks', 0)
    tables = all_stats.get('tables', 0)
    usefulness_score = min(20, (links * 2) + (code_blocks * 3) + (tables * 2))
    quality_factors['usefulness'] = usefulness_score
    
    total_quality = sum(quality_factors.values())
    
    return {
        'factors': quality_factors,
        'total_score': round(total_quality, 2),
        'grade': get_quality_grade(total_quality)
    }

def get_quality_grade(score):
    """Convierte score numérico a calificación"""
    if score >= 90:
        return 'A+ (Excelente)'
    elif score >= 80:
        return 'A (Muy Bueno)'
    elif score >= 70:
        return 'B (Bueno)'
    elif score >= 60:
        return 'C (Aceptable)'
    elif score >= 50:
        return 'D (Necesita Mejora)'
    else:
        return 'F (Insuficiente)'

if __name__ == "__main__":
    print("🔧 Módulo de mejoras avanzadas cargado correctamente")



