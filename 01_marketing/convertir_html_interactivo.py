#!/usr/bin/env python3
"""
Script para crear dashboards HTML interactivos con gráficos dinámicos,
tablas interactivas y visualizaciones avanzadas usando Plotly y otras librerías.
"""

import os
import json
from datetime import datetime
import pandas as pd
import numpy as np

# Intentar importar plotly, si no está, usar matplotlib
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly no disponible, usando gráficos estáticos")

def crear_html_dashboard_interactivo(archivo_md, archivo_html):
    """Crea dashboard HTML interactivo con Plotly"""
    print(f"Creando HTML interactivo para {os.path.basename(archivo_md)}...")
    
    # Datos de ejemplo
    datos = {
        'Meses': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        'Inversión': [500, 600, 700, 700, 800, 900],
        'Ventas': [1200, 1500, 2000, 2800, 3200, 3800],
        'ROI': [240, 250, 286, 400, 400, 422]
    }
    df = pd.DataFrame(datos)
    
    if PLOTLY_AVAILABLE:
        # Crear subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Evolución ROI', 'Distribución de Inversión', 
                          'Comparativa Mensual', 'Tendencias'),
            specs=[[{"type": "scatter"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Gráfico 1: ROI
        fig.add_trace(
            go.Scatter(x=df['Meses'], y=df['ROI'], mode='lines+markers',
                      name='ROI', line=dict(color='#4CAF50', width=3),
                      marker=dict(size=10)),
            row=1, col=1
        )
        
        # Gráfico 2: Pie
        fig.add_trace(
            go.Pie(labels=['Nano', 'Micro', 'Macro'], values=[30, 50, 20],
                   marker_colors=['#FF9800', '#2196F3', '#9C27B0']),
            row=1, col=2
        )
        
        # Gráfico 3: Barras
        fig.add_trace(
            go.Bar(x=df['Meses'], y=df['Inversión'], name='Inversión',
                   marker_color='#F44336'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=df['Meses'], y=df['Ventas'], name='Ventas',
                   marker_color='#4CAF50'),
            row=2, col=1
        )
        
        # Gráfico 4: Tendencias
        fig.add_trace(
            go.Scatter(x=df['Meses'], y=df['Inversión'], mode='lines+markers',
                      name='Inversión', line=dict(color='#F44336')),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['Meses'], y=df['Ventas'], mode='lines+markers',
                      name='Ventas', line=dict(color='#4CAF50')),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text=f"Dashboard Interactivo - {archivo_md.replace('.md', '')}",
            title_x=0.5,
            showlegend=True,
            template='plotly_white'
        )
        
        grafico_html = fig.to_html(include_plotlyjs='cdn')
    else:
        grafico_html = '<div style="text-align:center; padding:50px;"><h2>Gráficos interactivos requieren Plotly</h2></div>'
    
    # Crear HTML completo
    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Interactivo - {archivo_md.replace('.md', '')}</title>
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
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1F4E78 0%, #2E7D32 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .kpis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f5f5f5;
        }}
        
        .kpi-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }}
        
        .kpi-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .kpi-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #1F4E78;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            background: #1F4E78;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        @media (max-width: 768px) {{
            .kpis {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard Interactivo</h1>
            <p>{archivo_md.replace('.md', '').replace('_', ' ').title()}</p>
            <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">
                Generado: {datetime.now().strftime('%d de %B de %Y %H:%M')}
            </p>
        </div>
        
        <div class="kpis">
            <div class="kpi-card">
                <div class="kpi-label">💰 Total Inversión</div>
                <div class="kpi-value">$2,500</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">📈 ROI</div>
                <div class="kpi-value">200%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">🤝 Colaboraciones</div>
                <div class="kpi-value">8</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">📧 Tasa Respuesta</div>
                <div class="kpi-value">25%</div>
            </div>
        </div>
        
        <div class="content">
            <div class="chart-container">
                {grafico_html}
            </div>
            
            <div class="chart-container">
                <h2 style="margin-bottom: 20px; color: #1F4E78;">📋 Tabla de Datos</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #1F4E78; color: white;">
                            <th style="padding: 12px; text-align: left;">Mes</th>
                            <th style="padding: 12px; text-align: right;">Inversión</th>
                            <th style="padding: 12px; text-align: right;">Ventas</th>
                            <th style="padding: 12px; text-align: right;">ROI</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Agregar filas de tabla
    for _, row in df.iterrows():
        html_content += f"""
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px; font-weight: 600;">{row['Meses']}</td>
                            <td style="padding: 10px; text-align: right;">${row['Inversión']:,}</td>
                            <td style="padding: 10px; text-align: right; color: #4CAF50; font-weight: 600;">${row['Ventas']:,}</td>
                            <td style="padding: 10px; text-align: right; color: #2196F3; font-weight: 600;">{row['ROI']}%</td>
                        </tr>
"""
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 - Dashboard Generado Automáticamente</p>
            <p style="margin-top: 5px; font-size: 0.9em; opacity: 0.8;">
                Versión Ultra Premium 2.0
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(archivo_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML interactivo creado: {archivo_html}")

def main():
    """Función principal"""
    archivos = [
        'PRESUPUESTO_PRICING.md',
        'DASHBOARD_METRICAS.md',
        'ANALISIS_COMPETITIVO.md',
    ]
    
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    
    print("🌐 Creando dashboards HTML interactivos...\n")
    
    for archivo_md in archivos:
        ruta_md = os.path.join(directorio, archivo_md)
        if os.path.exists(ruta_md):
            archivo_html = ruta_md.replace('.md', '_INTERACTIVO.html')
            crear_html_dashboard_interactivo(ruta_md, archivo_html)
    
    print("\n✅ Dashboards HTML creados!")
    print("📊 Características:")
    print("   • Gráficos interactivos con Plotly")
    print("   • Diseño responsive")
    print("   • KPIs destacados")
    print("   • Tablas de datos")
    print("   • Estilo moderno y profesional")

if __name__ == "__main__":
    main()



