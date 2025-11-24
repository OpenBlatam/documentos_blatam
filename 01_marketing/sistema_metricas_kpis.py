#!/usr/bin/env python3
"""
Sistema de Métricas y KPIs - Calcula y visualiza métricas clave
de rendimiento del sistema y documentos generados.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import io

sns.set_style("whitegrid")

class SistemaMetricasKPIs:
    """Sistema de métricas y KPIs"""
    
    def __init__(self):
        self.directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
        self.directorio_metricas = os.path.join(self.directorio, 'Metricas_KPIs')
        os.makedirs(self.directorio_metricas, exist_ok=True)
    
    def analizar_documentos(self):
        """Analiza documentos generados"""
        extensiones = ['.docx', '.xlsx', '.pptx', '.pdf', '.html', '.png']
        
        estadisticas = {
            'total_archivos': 0,
            'por_formato': {},
            'por_fecha': {},
            'tamaño_total_mb': 0,
            'archivos_recientes': 0,
            'archivos_antiguos': 0
        }
        
        fecha_limite_reciente = datetime.now() - timedelta(days=7)
        fecha_limite_antiguo = datetime.now() - timedelta(days=90)
        
        for ext in extensiones:
            archivos = list(Path(self.directorio).glob(f'*{ext}'))
            # Filtrar directorios especiales
            archivos = [f for f in archivos 
                       if 'Backups' not in str(f) and 
                          'Exportaciones' not in str(f) and
                          'Comparaciones' not in str(f) and
                          'Reportes_Ejecutivos' not in str(f) and
                          'Metricas_KPIs' not in str(f)]
            
            estadisticas['por_formato'][ext] = len(archivos)
            estadisticas['total_archivos'] += len(archivos)
            
            for archivo in archivos:
                try:
                    tamaño = archivo.stat().st_size
                    estadisticas['tamaño_total_mb'] += tamaño / 1024 / 1024
                    
                    fecha_mod = datetime.fromtimestamp(archivo.stat().st_mtime)
                    fecha_str = fecha_mod.strftime('%Y-%m-%d')
                    
                    if fecha_str not in estadisticas['por_fecha']:
                        estadisticas['por_fecha'][fecha_str] = 0
                    estadisticas['por_fecha'][fecha_str] += 1
                    
                    if fecha_mod > fecha_limite_reciente:
                        estadisticas['archivos_recientes'] += 1
                    elif fecha_mod < fecha_limite_antiguo:
                        estadisticas['archivos_antiguos'] += 1
                except:
                    pass
        
        return estadisticas
    
    def analizar_scripts(self):
        """Analiza scripts Python"""
        scripts = list(Path(self.directorio).glob('*.py'))
        
        estadisticas = {
            'total_scripts': len(scripts),
            'tamaño_total_kb': 0,
            'scripts_por_tamaño': {'pequeños': 0, 'medianos': 0, 'grandes': 0}
        }
        
        for script in scripts:
            try:
                tamaño = script.stat().st_size
                estadisticas['tamaño_total_kb'] += tamaño / 1024
                
                if tamaño < 10 * 1024:  # < 10 KB
                    estadisticas['scripts_por_tamaño']['pequeños'] += 1
                elif tamaño < 30 * 1024:  # 10-30 KB
                    estadisticas['scripts_por_tamaño']['medianos'] += 1
                else:  # > 30 KB
                    estadisticas['scripts_por_tamaño']['grandes'] += 1
            except:
                pass
        
        return estadisticas
    
    def calcular_kpis(self, estadisticas_docs, estadisticas_scripts):
        """Calcula KPIs del sistema"""
        kpis = {
            'productividad': {
                'documentos_por_dia': estadisticas_docs['total_archivos'] / max(1, len(estadisticas_docs['por_fecha'])),
                'archivos_recientes_7dias': estadisticas_docs['archivos_recientes'],
                'tasa_crecimiento': self._calcular_tasa_crecimiento(estadisticas_docs['por_fecha'])
            },
            'eficiencia': {
                'tamaño_promedio_mb': estadisticas_docs['tamaño_total_mb'] / max(1, estadisticas_docs['total_archivos']),
                'scripts_activos': estadisticas_scripts['total_scripts'],
                'ratio_documentos_scripts': estadisticas_docs['total_archivos'] / max(1, estadisticas_scripts['total_scripts'])
            },
            'calidad': {
                'diversidad_formatos': len([f for f, c in estadisticas_docs['por_formato'].items() if c > 0]),
                'archivos_antiguos': estadisticas_docs['archivos_antiguos'],
                'porcentaje_recientes': (estadisticas_docs['archivos_recientes'] / max(1, estadisticas_docs['total_archivos'])) * 100
            }
        }
        
        return kpis
    
    def _calcular_tasa_crecimiento(self, por_fecha):
        """Calcula tasa de crecimiento"""
        if len(por_fecha) < 2:
            return 0
        
        fechas_ordenadas = sorted(por_fecha.items())
        primeros = sum(v for _, v in fechas_ordenadas[:len(fechas_ordenadas)//2])
        ultimos = sum(v for _, v in fechas_ordenadas[len(fechas_ordenadas)//2:])
        
        if primeros == 0:
            return 0
        
        return ((ultimos - primeros) / primeros) * 100
    
    def crear_visualizacion_kpis(self, estadisticas_docs, estadisticas_scripts, kpis):
        """Crea visualización de KPIs"""
        fig = plt.figure(figsize=(20, 14), facecolor='#F5F5F5')
        gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.35)
        
        # Gráfico 1: Documentos por formato
        ax1 = fig.add_subplot(gs[0, 0])
        formatos = [f.replace('.', '') for f, c in estadisticas_docs['por_formato'].items() if c > 0]
        cantidades = [c for f, c in estadisticas_docs['por_formato'].items() if c > 0]
        colores = ['#4CAF50', '#2196F3', '#9C27B0', '#FF9800', '#F44336', '#00BCD4']
        
        ax1.pie(cantidades, labels=formatos, autopct='%1.1f%%', 
               colors=colores[:len(formatos)], startangle=90,
               textprops={'fontweight': 'bold'})
        ax1.set_title('Documentos por Formato', fontweight='bold', 
                     fontsize=14, pad=20, color='#1F4E78')
        
        # Gráfico 2: KPIs principales
        ax2 = fig.add_subplot(gs[0, 1])
        kpi_nombres = ['Productividad', 'Eficiencia', 'Calidad']
        kpi_valores = [
            kpis['productividad']['documentos_por_dia'],
            kpis['eficiencia']['ratio_documentos_scripts'],
            kpis['calidad']['diversidad_formatos']
        ]
        
        bars = ax2.barh(kpi_nombres, kpi_valores, color=['#4CAF50', '#2196F3', '#9C27B0'],
                       alpha=0.8, edgecolor='white', linewidth=2)
        ax2.set_title('KPIs Principales', fontweight='bold', 
                     fontsize=14, pad=20, color='#1F4E78')
        ax2.set_xlabel('Valor', fontweight='bold', fontsize=12)
        ax2.grid(axis='x', alpha=0.4, linestyle='--')
        ax2.set_facecolor('white')
        
        for bar, val in zip(bars, kpi_valores):
            width = bar.get_width()
            ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}', ha='left', va='center', fontweight='bold', fontsize=11)
        
        # Gráfico 3: Evolución temporal
        ax3 = fig.add_subplot(gs[0, 2])
        if estadisticas_docs['por_fecha']:
            fechas = sorted(estadisticas_docs['por_fecha'].keys())
            valores = [estadisticas_docs['por_fecha'][f] for f in fechas]
            
            ax3.plot(range(len(fechas)), valores, 'o-', linewidth=2.5, markersize=8,
                    color='#2196F3', markerfacecolor='white', markeredgewidth=2)
            ax3.set_title('Evolución de Documentos', fontweight='bold', 
                         fontsize=14, pad=20, color='#1F4E78')
            ax3.set_ylabel('Documentos', fontweight='bold', fontsize=12)
            ax3.set_xlabel('Días', fontweight='bold', fontsize=12)
            ax3.grid(alpha=0.4, linestyle='--')
            ax3.set_facecolor('white')
        
        # Gráfico 4: Tamaño de scripts
        ax4 = fig.add_subplot(gs[1, 0])
        tamanos = estadisticas_scripts['scripts_por_tamaño']
        categorias = list(tamanos.keys())
        valores = list(tamanos.values())
        
        ax4.bar(categorias, valores, color=['#4CAF50', '#FF9800', '#F44336'],
               alpha=0.8, edgecolor='white', linewidth=2)
        ax4.set_title('Scripts por Tamaño', fontweight='bold', 
                     fontsize=14, pad=20, color='#1F4E78')
        ax4.set_ylabel('Cantidad', fontweight='bold', fontsize=12)
        ax4.grid(axis='y', alpha=0.4, linestyle='--')
        ax4.set_facecolor('white')
        
        for bar, val in zip(ax4.patches, valores):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(val)}', ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Gráfico 5: Métricas de calidad
        ax5 = fig.add_subplot(gs[1, 1])
        calidad_metricas = [
            kpis['calidad']['diversidad_formatos'],
            kpis['calidad']['porcentaje_recientes']
        ]
        labels = ['Formatos\nDiversos', 'Archivos\nRecientes (%)']
        
        bars = ax5.bar(labels, calidad_metricas, color=['#9C27B0', '#00BCD4'],
                      alpha=0.8, edgecolor='white', linewidth=2)
        ax5.set_title('Métricas de Calidad', fontweight='bold', 
                     fontsize=14, pad=20, color='#1F4E78')
        ax5.set_ylabel('Valor', fontweight='bold', fontsize=12)
        ax5.grid(axis='y', alpha=0.4, linestyle='--')
        ax5.set_facecolor('white')
        
        for bar, val in zip(bars, calidad_metricas):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Gráfico 6: Resumen ejecutivo
        ax6 = fig.add_subplot(gs[1, 2:])
        ax6.axis('off')
        
        resumen_texto = [
            ['Métrica', 'Valor'],
            ['Total Documentos', f"{estadisticas_docs['total_archivos']}"],
            ['Total Scripts', f"{estadisticas_scripts['total_scripts']}"],
            ['Tamaño Total', f"{estadisticas_docs['tamaño_total_mb']:.2f} MB"],
            ['Documentos Recientes (7d)', f"{estadisticas_docs['archivos_recientes']}"],
            ['Documentos por Día', f"{kpis['productividad']['documentos_por_dia']:.1f}"],
            ['Tasa de Crecimiento', f"{kpis['productividad']['tasa_crecimiento']:.1f}%"],
            ['Ratio Docs/Scripts', f"{kpis['eficiencia']['ratio_documentos_scripts']:.1f}"],
            ['Diversidad Formatos', f"{kpis['calidad']['diversidad_formatos']}"]
        ]
        
        tabla = ax6.table(cellText=resumen_texto[1:], colLabels=resumen_texto[0],
                         cellLoc='center', loc='center',
                         colWidths=[0.5, 0.3])
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(11)
        tabla.scale(1, 2.5)
        
        for i in range(len(resumen_texto[0])):
            tabla[(0, i)].set_facecolor('#1F4E78')
            tabla[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(resumen_texto)):
            for j in range(len(resumen_texto[0])):
                if i % 2 == 0:
                    tabla[(i, j)].set_facecolor('#F5F5F5')
        
        ax6.set_title('Resumen Ejecutivo de Métricas', fontweight='bold', 
                     fontsize=16, pad=20, color='#1F4E78', y=0.95)
        
        # Gráfico 7: Dashboard de KPIs
        ax7 = fig.add_subplot(gs[2, :])
        ax7.axis('off')
        
        kpi_dashboard = [
            ['KPI', 'Categoría', 'Valor', 'Estado'],
            ['Documentos/Día', 'Productividad', f"{kpis['productividad']['documentos_por_dia']:.1f}", 
             '✅' if kpis['productividad']['documentos_por_dia'] > 1 else '⚠️'],
            ['Archivos Recientes', 'Productividad', f"{kpis['productividad']['archivos_recientes_7dias']}", 
             '✅' if kpis['productividad']['archivos_recientes_7dias'] > 5 else '⚠️'],
            ['Tasa Crecimiento', 'Productividad', f"{kpis['productividad']['tasa_crecimiento']:.1f}%", 
             '✅' if kpis['productividad']['tasa_crecimiento'] > 0 else '⚠️'],
            ['Tamaño Promedio', 'Eficiencia', f"{kpis['eficiencia']['tamaño_promedio_mb']:.2f} MB", 
             '✅' if kpis['eficiencia']['tamaño_promedio_mb'] < 5 else '⚠️'],
            ['Scripts Activos', 'Eficiencia', f"{kpis['eficiencia']['scripts_activos']}", '✅'],
            ['Diversidad Formatos', 'Calidad', f"{kpis['calidad']['diversidad_formatos']}", 
             '✅' if kpis['calidad']['diversidad_formatos'] >= 4 else '⚠️'],
            ['% Recientes', 'Calidad', f"{kpis['calidad']['porcentaje_recientes']:.1f}%", 
             '✅' if kpis['calidad']['porcentaje_recientes'] > 30 else '⚠️']
        ]
        
        tabla2 = ax7.table(cellText=kpi_dashboard[1:], colLabels=kpi_dashboard[0],
                           cellLoc='center', loc='center',
                           colWidths=[0.25, 0.25, 0.25, 0.15])
        tabla2.auto_set_font_size(False)
        tabla2.set_fontsize(10)
        tabla2.scale(1, 2.2)
        
        for i in range(len(kpi_dashboard[0])):
            tabla2[(0, i)].set_facecolor('#1F4E78')
            tabla2[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(kpi_dashboard)):
            for j in range(len(kpi_dashboard[0])):
                if i % 2 == 0:
                    tabla2[(i, j)].set_facecolor('#F5F5F5')
        
        ax7.set_title('Dashboard de KPIs del Sistema', fontweight='bold', 
                     fontsize=16, pad=20, color='#1F4E78', y=0.95)
        
        plt.suptitle('SISTEMA DE MÉTRICAS Y KPIs - DASHBOARD COMPLETO', 
                    fontsize=20, fontweight='bold', y=0.98, color='#1F4E78')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor='#F5F5F5', edgecolor='none', pad_inches=0.3)
        buffer.seek(0)
        plt.close()
        
        return buffer

def main():
    """Función principal"""
    sistema = SistemaMetricasKPIs()
    
    print("📊 Analizando métricas y KPIs del sistema...\n")
    
    # Analizar
    estadisticas_docs = sistema.analizar_documentos()
    estadisticas_scripts = sistema.analizar_scripts()
    kpis = sistema.calcular_kpis(estadisticas_docs, estadisticas_scripts)
    
    # Crear visualización
    grafico_buffer = sistema.crear_visualizacion_kpis(estadisticas_docs, estadisticas_scripts, kpis)
    
    # Guardar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_imagen = os.path.join(
        sistema.directorio_metricas,
        f'METRICAS_KPIS_{timestamp}.png'
    )
    with open(archivo_imagen, 'wb') as f:
        f.write(grafico_buffer.read())
    print(f"✓ Gráfico guardado: {archivo_imagen}")
    
    # Guardar JSON
    archivo_json = os.path.join(
        sistema.directorio_metricas,
        f'METRICAS_KPIS_{timestamp}.json'
    )
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump({
            'fecha': datetime.now().isoformat(),
            'estadisticas_documentos': estadisticas_docs,
            'estadisticas_scripts': estadisticas_scripts,
            'kpis': kpis
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f"✓ Datos JSON guardados: {archivo_json}")
    
    print(f"\n✅ Análisis de métricas completado!")
    print(f"📁 Archivos guardados en: {sistema.directorio_metricas}")

if __name__ == "__main__":
    main()

