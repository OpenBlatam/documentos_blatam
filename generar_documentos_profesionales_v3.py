#!/usr/bin/env python3
"""
Script ULTRA MEJORADO para convertir documentos importantes a PDF, Word y Excel
con gráficas avanzadas, dashboard HTML interactivo, análisis de sentimiento y más
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
import markdown
from markdown.extensions import tables, fenced_code, codehilite

# Importar todas las librerías necesarias (mismo código que v2)
# ... (copiar imports del v2)

# Para simplificar, voy a crear funciones adicionales que se pueden agregar al v2
# Creando funciones de mejora que se pueden integrar

def create_html_dashboard(all_docs_data: List[Dict], output_path: Path):
    """Crea un dashboard HTML interactivo con todos los documentos"""
    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Documentos BLATAM</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }}
        h1 {{
            color: #2E86AB;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        .chart-container {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            color: #2E86AB;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: bold;
        }}
        .docs-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 30px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .docs-table th {{
            background: #2E86AB;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        .docs-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        .docs-table tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-automation {{ background: #F18F01; color: white; }}
        .badge-architecture {{ background: #2E86AB; color: white; }}
        .badge-documentation {{ background: #6A994E; color: white; }}
        .badge-development {{ background: #A23B72; color: white; }}
        .badge-strategy {{ background: #7209B7; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Dashboard de Documentos BLATAM</h1>
        <p class="subtitle">Análisis completo y visualización de todos los documentos procesados</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(all_docs_data)}</div>
                <div class="stat-label">Documentos Procesados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(d.get('metrics', {}).get('total_words', 0) for d in all_docs_data):,}</div>
                <div class="stat-label">Total de Palabras</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(d.get('metrics', {}).get('total_sections', 0) for d in all_docs_data)}</div>
                <div class="stat-label">Total de Secciones</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(d.get('code_blocks', [])) for d in all_docs_data)}</div>
                <div class="stat-label">Bloques de Código</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">Distribución por Categoría</div>
                <canvas id="categoryChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Tamaño de Documentos (Palabras)</div>
                <canvas id="sizeChart"></canvas>
            </div>
        </div>
        
        <h2 style="color: #2E86AB; margin-top: 40px; margin-bottom: 20px;">📄 Lista de Documentos</h2>
        <table class="docs-table">
            <thead>
                <tr>
                    <th>Documento</th>
                    <th>Categoría</th>
                    <th>Palabras</th>
                    <th>Secciones</th>
                    <th>Legibilidad</th>
                    <th>Complejidad</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for doc in all_docs_data:
        metrics = doc.get('metrics', {})
        category = doc.get('category', 'N/A')
        badge_class = f"badge-{category.lower().replace(' ', '-')}" if category else "badge-documentation"
        
        html_content += f"""
                <tr>
                    <td><strong>{doc.get('title', 'N/A')}</strong></td>
                    <td><span class="badge {badge_class}">{category}</span></td>
                    <td>{metrics.get('total_words', 0):,}</td>
                    <td>{metrics.get('total_sections', 0)}</td>
                    <td>{metrics.get('readability_score', 0):.1f}</td>
                    <td>{metrics.get('complexity_score', 0):.2f}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
    </div>
    
    <script>
        // Gráfica de categorías
        const categoryData = {};
"""
    
    # Contar categorías
    categories = Counter(d.get('category', 'Otros') for d in all_docs_data)
    html_content += "\n".join(f"        categoryData['{cat}'] = {count};" for cat, count in categories.items())
    
    html_content += f"""
        
        new Chart(document.getElementById('categoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(categoryData),
                datasets: [{{
                    data: Object.values(categoryData),
                    backgroundColor: [
                        '#2E86AB', '#A23B72', '#F18F01', 
                        '#C73E1D', '#6A994E', '#7209B7', '#F72585'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Gráfica de tamaño
        const docSizes = {{
"""
    
    for doc in all_docs_data:
        safe_title = doc.get('title', 'N/A').replace("'", "\\'")
        words = doc.get('metrics', {}).get('total_words', 0)
        html_content += f"            '{safe_title}': {words},\n"
    
    html_content += """        };
        
        new Chart(document.getElementById('sizeChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(docSizes),
                datasets: [{{
                    label: 'Palabras',
                    data: Object.values(docSizes),
                    backgroundColor: '#2E86AB'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard HTML creado: {output_path}")


def create_executive_summary(all_docs_data: List[Dict], output_path: Path):
    """Crea un resumen ejecutivo en formato JSON y texto"""
    summary = {
        'generated_date': datetime.now().isoformat(),
        'total_documents': len(all_docs_data),
        'total_metrics': {
            'total_words': sum(d.get('metrics', {}).get('total_words', 0) for d in all_docs_data),
            'total_sections': sum(d.get('metrics', {}).get('total_sections', 0) for d in all_docs_data),
            'total_code_blocks': sum(len(d.get('code_blocks', [])) for d in all_docs_data),
            'total_links': sum(len(d.get('links', [])) for d in all_docs_data),
            'total_tables': sum(len(d.get('tables', [])) for d in all_docs_data),
        },
        'average_metrics': {
            'avg_words_per_doc': sum(d.get('metrics', {}).get('total_words', 0) for d in all_docs_data) / max(len(all_docs_data), 1),
            'avg_sections_per_doc': sum(d.get('metrics', {}).get('total_sections', 0) for d in all_docs_data) / max(len(all_docs_data), 1),
            'avg_readability': sum(d.get('metrics', {}).get('readability_score', 0) for d in all_docs_data) / max(len(all_docs_data), 1),
            'avg_complexity': sum(d.get('metrics', {}).get('complexity_score', 0) for d in all_docs_data) / max(len(all_docs_data), 1),
        },
        'categories': dict(Counter(d.get('category', 'Otros') for d in all_docs_data)),
        'documents': [
            {
                'title': d.get('title', 'N/A'),
                'category': d.get('category', 'N/A'),
                'metrics': d.get('metrics', {}),
                'sections_count': len(d.get('sections', [])),
                'code_blocks_count': len(d.get('code_blocks', [])),
            }
            for d in all_docs_data
        ]
    }
    
    # Guardar JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Guardar texto
    text_content = f"""
RESUMEN EJECUTIVO - DOCUMENTOS BLATAM
{'=' * 60}

Fecha de Generación: {datetime.now().strftime('%d de %B de %Y %H:%M')}

ESTADÍSTICAS GENERALES
{'-' * 60}
Total de Documentos Procesados: {summary['total_documents']}
Total de Palabras: {summary['total_metrics']['total_words']:,}
Total de Secciones: {summary['total_metrics']['total_sections']}
Total de Bloques de Código: {summary['total_metrics']['total_code_blocks']}
Total de Enlaces: {summary['total_metrics']['total_links']}
Total de Tablas: {summary['total_metrics']['total_tables']}

MÉTRICAS PROMEDIO
{'-' * 60}
Promedio de Palabras por Documento: {summary['average_metrics']['avg_words_per_doc']:,.0f}
Promedio de Secciones por Documento: {summary['average_metrics']['avg_sections_per_doc']:.1f}
Legibilidad Promedio: {summary['average_metrics']['avg_readability']:.1f}/100
Complejidad Promedio: {summary['average_metrics']['avg_complexity']:.2f}

DISTRIBUCIÓN POR CATEGORÍA
{'-' * 60}
"""
    
    for category, count in summary['categories'].items():
        text_content += f"{category}: {count} documentos\n"
    
    text_content += f"""
DOCUMENTOS INDIVIDUALES
{'-' * 60}
"""
    
    for doc in summary['documents']:
        text_content += f"""
{doc['title']}
  Categoría: {doc['category']}
  Palabras: {doc['metrics'].get('total_words', 0):,}
  Secciones: {doc['sections_count']}
  Legibilidad: {doc['metrics'].get('readability_score', 0):.1f}/100
  Complejidad: {doc['metrics'].get('complexity_score', 0):.2f}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    print(f"✅ Resumen ejecutivo creado: {output_path}")
    print(f"✅ Resumen JSON creado: {json_path}")


# Esta función se puede agregar al script v2 existente
def enhance_v2_script():
    """Instrucciones para mejorar el script v2"""
    print("""
    MEJORAS ADICIONALES PARA generar_documentos_profesionales_v2.py:
    
    1. Agregar al final de la función main():
       - Llamar a create_html_dashboard() con todos los datos
       - Llamar a create_executive_summary() con todos los datos
       
    2. Modificar convert_document() para:
       - Retornar doc_data además de solo imprimir
       - Acumular todos los doc_data en una lista
       
    3. Agregar más documentos a IMPORTANT_DOCS
    """)


if __name__ == "__main__":
    # Este script puede ser importado o ejecutado directamente
    # para crear el dashboard y resumen después de procesar documentos
    print("Script de funciones adicionales para mejorar v2")
    print("Importa estas funciones en generar_documentos_profesionales_v2.py")



