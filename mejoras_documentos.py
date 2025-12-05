#!/usr/bin/env python3
"""
Mejoras adicionales para el generador de documentos premium:
- Análisis de sentimiento y tono
- Gráficas de tendencias temporales
- Análisis de complejidad de lectura
- Exportación de datos JSON
- Dashboard interactivo HTML
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import math

# Análisis de complejidad de lectura
def calculate_readability(text):
    """Calcula métricas de legibilidad (Flesch Reading Ease)"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    words = re.findall(r'\b\w+\b', text.lower())
    syllables = sum([count_syllables(word) for word in words])
    
    if len(sentences) == 0 or len(words) == 0:
        return {
            'flesch_score': 0,
            'reading_level': 'N/A',
            'avg_sentence_length': 0,
            'avg_syllables_per_word': 0
        }
    
    # Flesch Reading Ease Score
    asl = len(words) / len(sentences)  # Average Sentence Length
    asw = syllables / len(words)  # Average Syllables per Word
    flesch = 206.835 - (1.015 * asl) - (84.6 * asw)
    
    # Determinar nivel de lectura
    if flesch >= 90:
        level = "Muy Fácil"
    elif flesch >= 80:
        level = "Fácil"
    elif flesch >= 70:
        level = "Bastante Fácil"
    elif flesch >= 60:
        level = "Estándar"
    elif flesch >= 50:
        level = "Bastante Difícil"
    elif flesch >= 30:
        level = "Difícil"
    else:
        level = "Muy Difícil"
    
    return {
        'flesch_score': round(flesch, 2),
        'reading_level': level,
        'avg_sentence_length': round(asl, 2),
        'avg_syllables_per_word': round(asw, 2)
    }

def count_syllables(word):
    """Cuenta sílabas en una palabra (aproximado)"""
    word = word.lower()
    if len(word) <= 3:
        return 1
    word = re.sub(r'[^aeiouy]', '', word)
    word = re.sub(r'[aeiouy]+', 'a', word)
    return max(1, len(word))

# Análisis de sentimiento básico
def analyze_sentiment(text):
    """Análisis básico de sentimiento usando palabras clave"""
    positive_words = ['excelente', 'bueno', 'mejor', 'éxito', 'logro', 'avance', 
                      'mejora', 'optimización', 'eficiente', 'efectivo', 'solución',
                      'innovación', 'calidad', 'superior', 'destacado']
    negative_words = ['problema', 'error', 'fallo', 'dificultad', 'limitación',
                      'desafío', 'riesgo', 'preocupación', 'crítico', 'urgente']
    
    text_lower = text.lower()
    pos_count = sum([1 for word in positive_words if word in text_lower])
    neg_count = sum([1 for word in negative_words if word in text_lower])
    
    total = pos_count + neg_count
    if total == 0:
        sentiment = "Neutral"
        score = 0.5
    else:
        score = pos_count / total
        if score > 0.6:
            sentiment = "Positivo"
        elif score < 0.4:
            sentiment = "Negativo"
        else:
            sentiment = "Neutral"
    
    return {
        'sentiment': sentiment,
        'score': round(score, 2),
        'positive_words': pos_count,
        'negative_words': neg_count
    }

# Análisis de estructura y organización
def analyze_structure(content):
    """Analiza la estructura y organización del documento"""
    lines = content.split('\n')
    
    structure = {
        'has_toc': False,
        'has_summary': False,
        'has_conclusion': False,
        'header_levels': Counter(),
        'list_items': 0,
        'code_blocks': 0,
        'tables': 0,
        'images': 0,
        'links': 0
    }
    
    toc_keywords = ['tabla de contenidos', 'índice', 'indice', 'contenido', 'table of contents']
    summary_keywords = ['resumen', 'summary', 'executive summary', 'resumen ejecutivo']
    conclusion_keywords = ['conclusión', 'conclusion', 'conclusiones', 'resumen final']
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Detectar TOC
        if any(kw in line_lower for kw in toc_keywords):
            structure['has_toc'] = True
        
        # Detectar resumen
        if any(kw in line_lower for kw in summary_keywords):
            structure['has_summary'] = True
        
        # Detectar conclusión
        if any(kw in line_lower for kw in conclusion_keywords):
            structure['has_conclusion'] = True
        
        # Contar headers
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            structure['header_levels'][level] += 1
        
        # Contar listas
        if line.strip().startswith('-') or line.strip().startswith('*') or line.strip().startswith('+'):
            structure['list_items'] += 1
        
        # Contar bloques de código
        if line.strip().startswith('```'):
            structure['code_blocks'] += 1
        
        # Contar tablas
        if '|' in line and line.count('|') >= 2:
            structure['tables'] += 1
        
        # Contar imágenes
        if '![' in line:
            structure['images'] += 1
        
        # Contar enlaces
        if '](' in line:
            structure['links'] += len(re.findall(r'\[([^\]]+)\]\([^\)]+\)', line))
    
    structure['code_blocks'] = structure['code_blocks'] // 2  # Pares de ```
    structure['tables'] = structure['tables'] // 3  # Aproximado
    
    return structure

# Análisis de temas y categorías
def analyze_topics(content):
    """Identifica temas principales del documento"""
    # Palabras clave por categoría
    categories = {
        'tecnología': ['tecnología', 'tecnico', 'código', 'code', 'software', 'sistema', 
                      'aplicación', 'programa', 'desarrollo', 'implementación', 'api',
                      'arquitectura', 'framework', 'plataforma', 'servicio'],
        'negocio': ['negocio', 'empresa', 'estrategia', 'mercado', 'cliente', 'ventas',
                   'marketing', 'producto', 'servicio', 'revenue', 'ingresos', 'negocio'],
        'proceso': ['proceso', 'flujo', 'workflow', 'procedimiento', 'metodología',
                   'mejora', 'optimización', 'eficiencia', 'automatización'],
        'datos': ['datos', 'data', 'análisis', 'analytics', 'métrica', 'kpi', 'reporte',
                 'información', 'base de datos', 'database'],
        'seguridad': ['seguridad', 'security', 'privacidad', 'autenticación', 'autorización',
                     'encriptación', 'vulnerabilidad', 'riesgo'],
        'ia': ['inteligencia artificial', 'ia', 'ai', 'machine learning', 'ml', 'neural',
              'modelo', 'algoritmo', 'predicción', 'análisis predictivo']
    }
    
    content_lower = content.lower()
    topic_scores = {}
    
    for category, keywords in categories.items():
        score = sum([content_lower.count(keyword) for keyword in keywords])
        if score > 0:
            topic_scores[category] = score
    
    # Top 3 temas
    top_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        'topics': dict(top_topics),
        'primary_topic': top_topics[0][0] if top_topics else 'general',
        'topic_diversity': len(topic_scores)
    }

# Generar reporte JSON completo
def generate_json_report(doc_name, content, stats, readability, sentiment, structure, topics):
    """Genera un reporte JSON completo del análisis"""
    report = {
        'document': doc_name,
        'generated_at': datetime.now().isoformat(),
        'statistics': {
            'words': stats.get('total_words', 0),
            'sections': stats.get('total_sections', 0),
            'code_blocks': stats.get('code_blocks', 0),
            'links': stats.get('links', 0),
            'images': stats.get('images', 0),
            'tables': stats.get('tables', 0)
        },
        'readability': readability,
        'sentiment': sentiment,
        'structure': {
            'has_toc': structure['has_toc'],
            'has_summary': structure['has_summary'],
            'has_conclusion': structure['has_conclusion'],
            'header_distribution': dict(structure['header_levels']),
            'list_items': structure['list_items'],
            'code_blocks': structure['code_blocks'],
            'tables': structure['tables'],
            'images': structure['images'],
            'links': structure['links']
        },
        'topics': topics,
        'quality_score': calculate_quality_score(stats, readability, structure)
    }
    
    return report

def calculate_quality_score(stats, readability, structure):
    """Calcula un score de calidad del documento (0-100)"""
    score = 0
    
    # Puntos por estructura (30 puntos)
    if structure['has_toc']:
        score += 5
    if structure['has_summary']:
        score += 5
    if structure['has_conclusion']:
        score += 5
    if structure['header_levels']:
        score += 5
    if structure['list_items'] > 10:
        score += 5
    if structure['code_blocks'] > 0:
        score += 5
    
    # Puntos por contenido (40 puntos)
    if stats.get('total_words', 0) > 1000:
        score += 10
    if stats.get('total_sections', 0) > 5:
        score += 10
    if stats.get('links', 0) > 5:
        score += 10
    if stats.get('tables', 0) > 0:
        score += 10
    
    # Puntos por legibilidad (30 puntos)
    flesch = readability.get('flesch_score', 0)
    if flesch >= 60:
        score += 15
    elif flesch >= 50:
        score += 10
    elif flesch >= 40:
        score += 5
    
    if readability.get('avg_sentence_length', 0) < 20:
        score += 10
    elif readability.get('avg_sentence_length', 0) < 30:
        score += 5
    
    return min(100, score)

# Generar dashboard HTML
def generate_html_dashboard(reports, output_path):
    """Genera un dashboard HTML interactivo con todos los análisis"""
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Análisis de Documentos</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
        .card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .metric {{
            font-size: 2em;
            font-weight: bold;
            color: #764ba2;
            margin: 10px 0;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .quality-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }}
        .excellent {{ background: #4CAF50; color: white; }}
        .good {{ background: #8BC34A; color: white; }}
        .fair {{ background: #FFC107; color: black; }}
        .poor {{ background: #F44336; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Dashboard de Análisis de Documentos</h1>
        <p class="subtitle">Generado el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}</p>
        
        <div class="grid">
"""
    
    # Agregar métricas generales
    total_words = sum([r['statistics']['words'] for r in reports])
    total_docs = len(reports)
    avg_quality = sum([r['quality_score'] for r in reports]) / total_docs if reports else 0
    
    html += f"""
            <div class="card">
                <h3>📈 Resumen General</h3>
                <div class="metric">{total_docs}</div>
                <p>Documentos Analizados</p>
                <div class="metric">{total_words:,}</div>
                <p>Palabras Totales</p>
                <div class="metric">{avg_quality:.1f}/100</div>
                <p>Calidad Promedio</p>
            </div>
"""
    
    # Tabla de documentos
    html += """
        </div>
        
        <h2 style="margin-top: 30px; color: #667eea;">📋 Análisis por Documento</h2>
        <table>
            <thead>
                <tr>
                    <th>Documento</th>
                    <th>Palabras</th>
                    <th>Secciones</th>
                    <th>Legibilidad</th>
                    <th>Sentimiento</th>
                    <th>Calidad</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for report in reports:
        quality_class = 'excellent' if report['quality_score'] >= 80 else 'good' if report['quality_score'] >= 60 else 'fair' if report['quality_score'] >= 40 else 'poor'
        html += f"""
                <tr>
                    <td><strong>{report['document']}</strong></td>
                    <td>{report['statistics']['words']:,}</td>
                    <td>{report['statistics']['sections']}</td>
                    <td>{report['readability']['reading_level']} ({report['readability']['flesch_score']:.1f})</td>
                    <td>{report['sentiment']['sentiment']} ({report['sentiment']['score']:.2f})</td>
                    <td><span class="quality-badge {quality_class}">{report['quality_score']}/100</span></td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <div class="chart-container">
            <canvas id="qualityChart"></canvas>
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('qualityChart').getContext('2d');
        const reports = """ + json.dumps(reports, indent=2) + """;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: reports.map(r => r.document.split('/').pop()),
                datasets: [{
                    label: 'Score de Calidad',
                    data: reports.map(r => r.quality_score),
                    backgroundColor: reports.map(r => {
                        const score = r.quality_score;
                        if (score >= 80) return '#4CAF50';
                        if (score >= 60) return '#8BC34A';
                        if (score >= 40) return '#FFC107';
                        return '#F44336';
                    }),
                    borderColor: '#333',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Score de Calidad por Documento',
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard HTML generado: {output_path}")

# Función principal de mejoras
def apply_enhancements(doc_path, content):
    """Aplica todas las mejoras de análisis a un documento"""
    stats = {
        'total_words': len(re.findall(r'\b\w+\b', content)),
        'total_sections': len(re.findall(r'^#+\s+', content, re.MULTILINE)),
        'code_blocks': content.count('```') // 2,
        'links': len(re.findall(r'\[([^\]]+)\]\([^\)]+\)', content)),
        'images': len(re.findall(r'!\[([^\]]*)\]\([^\)]+\)', content)),
        'tables': len([t for t in content.split('\n') if '|' in t and t.count('|') >= 2]) // 3
    }
    
    readability = calculate_readability(content)
    sentiment = analyze_sentiment(content)
    structure = analyze_structure(content)
    topics = analyze_topics(content)
    
    return {
        'stats': stats,
        'readability': readability,
        'sentiment': sentiment,
        'structure': structure,
        'topics': topics
    }

if __name__ == "__main__":
    print("🔧 Módulo de mejoras cargado correctamente")
    print("Importa este módulo en generar_documentos_premium.py para usar las funciones")



