#!/usr/bin/env python3
"""
Dashboard Maestro de Documentos - Crea un dashboard HTML completo que muestra
todos los documentos generados con estadísticas, enlaces y visualizaciones.
"""

import os
import glob
from datetime import datetime
from pathlib import Path

def obtener_estadisticas_documentos(directorio):
    """Obtiene estadísticas de todos los documentos generados"""
    
    tipos = {
        'Word (.docx)': '*.docx',
        'Excel (.xlsx)': '*.xlsx',
        'PowerPoint (.pptx)': '*.pptx',
        'PDF (.pdf)': '*.pdf',
        'HTML (.html)': '*INTERACTIVO*.html',
        'Imágenes (.png)': '*ESTADISTICO*.png',
    }
    
    estadisticas = {}
    total_tamaño = 0
    total_archivos = 0
    
    for tipo, patron in tipos.items():
        archivos = glob.glob(os.path.join(directorio, patron))
        # Filtrar archivos comprimidos y temporales
        archivos = [f for f in archivos if not any(x in f for x in ['.zip', '~', 'temp'])]
        
        if archivos:
            tamaño_total = sum(os.path.getsize(f) for f in archivos)
            estadisticas[tipo] = {
                'cantidad': len(archivos),
                'tamaño_total': tamaño_total,
                'tamaño_promedio': tamaño_total / len(archivos),
                'archivos': [os.path.basename(f) for f in archivos[:10]]  # Primeros 10
            }
            total_tamaño += tamaño_total
            total_archivos += len(archivos)
    
    return estadisticas, total_tamaño, total_archivos

def crear_dashboard_html(directorio, estadisticas, total_tamaño, total_archivos):
    """Crea dashboard HTML maestro"""
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Maestro - Documentos Generados</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1F4E78 0%, #2E7D32 100%);
            color: white;
            padding: 50px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.3em;
            opacity: 0.9;
        }}
        
        .stats-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            padding: 40px;
            background: #f5f5f5;
        }}
        
        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }}
        
        .stat-icon {{
            font-size: 3em;
            margin-bottom: 15px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #1F4E78;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            font-size: 1.1em;
            color: #666;
            font-weight: 600;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #1F4E78;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #1F4E78;
        }}
        
        .files-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .file-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #1F4E78;
            transition: all 0.3s;
        }}
        
        .file-card:hover {{
            background: #f0f0f0;
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .file-name {{
            font-weight: bold;
            color: #1F4E78;
            margin-bottom: 10px;
            word-break: break-word;
        }}
        
        .file-info {{
            font-size: 0.9em;
            color: #666;
        }}
        
        .file-link {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 15px;
            background: #1F4E78;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 0.9em;
            transition: background 0.3s;
        }}
        
        .file-link:hover {{
            background: #2E7D32;
        }}
        
        .footer {{
            background: #1F4E78;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        @media (max-width: 768px) {{
            .stats-overview {{
                grid-template-columns: 1fr;
            }}
            
            .files-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard Maestro de Documentos</h1>
            <p>Sistema de Conversión Premium 2.0</p>
            <p style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">
                Generado: {datetime.now().strftime('%d de %B de %Y %H:%M:%S')}
            </p>
        </div>
        
        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-value">{total_archivos}</div>
                <div class="stat-label">Total Documentos</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-value">{total_tamaño/1024/1024:.1f} MB</div>
                <div class="stat-label">Tamaño Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">{len(estadisticas)}</div>
                <div class="stat-label">Formatos Diferentes</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📅</div>
                <div class="stat-value">{datetime.now().strftime('%d/%m')}</div>
                <div class="stat-label">Fecha Actual</div>
            </div>
        </div>
        
        <div class="content">
"""
    
    # Agregar secciones por tipo
    for tipo, datos in estadisticas.items():
        html += f"""
            <div class="section">
                <h2 class="section-title">{tipo} ({datos['cantidad']} archivos - {datos['tamaño_total']/1024/1024:.2f} MB)</h2>
                <div class="files-grid">
"""
        
        for archivo in datos['archivos']:
            tamaño_archivo = datos['tamaño_promedio']
            html += f"""
                    <div class="file-card">
                        <div class="file-name">{archivo}</div>
                        <div class="file-info">
                            Tamaño: {tamaño_archivo/1024:.1f} KB
                        </div>
                        <a href="{archivo}" class="file-link" target="_blank">Abrir →</a>
                    </div>
"""
        
        if datos['cantidad'] > len(datos['archivos']):
            html += f"""
                    <div class="file-card" style="background: #e3f2fd; border-left-color: #2196F3;">
                        <div class="file-name">... y {datos['cantidad'] - len(datos['archivos'])} archivos más</div>
                    </div>
"""
        
        html += """
                </div>
            </div>
"""
    
    html += """
        </div>
        
        <div class="footer">
            <p>© 2025 - Sistema de Conversión Premium 2.0</p>
            <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">
                Todos los documentos generados automáticamente con las mejores prácticas
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    archivo_html = os.path.join(directorio, 'DASHBOARD_MAESTRO_DOCUMENTOS.html')
    with open(archivo_html, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Dashboard maestro creado: {archivo_html}")

def main():
    """Función principal"""
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    
    print("📊 Generando Dashboard Maestro de Documentos...\n")
    
    estadisticas, total_tamaño, total_archivos = obtener_estadisticas_documentos(directorio)
    
    print(f"📈 Estadísticas encontradas:")
    print(f"   • Total archivos: {total_archivos}")
    print(f"   • Tamaño total: {total_tamaño/1024/1024:.2f} MB")
    print(f"   • Formatos: {len(estadisticas)}\n")
    
    crear_dashboard_html(directorio, estadisticas, total_tamaño, total_archivos)
    
    print("\n✅ Dashboard maestro generado!")
    print("🌐 Abre DASHBOARD_MAESTRO_DOCUMENTOS.html en tu navegador")

if __name__ == "__main__":
    main()



