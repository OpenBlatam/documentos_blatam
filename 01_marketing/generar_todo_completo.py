#!/usr/bin/env python3
"""
Script Maestro - Ejecuta TODAS las conversiones y genera TODOS los documentos
en una sola ejecución con reporte completo final.
"""

import os
import subprocess
import sys
import glob
from datetime import datetime
import json

def ejecutar_todos_los_scripts():
    """Ejecuta todos los scripts de conversión en orden"""
    
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    
    scripts = [
        ('convertir_md_a_documentos_profesionales.py', 'Conversión Profesional'),
        ('convertir_todos_archivos_avanzado.py', 'Conversión Avanzada'),
        ('convertir_mejorado_premium.py', 'Conversión Premium'),
        ('convertir_completo_ultra_premium.py', 'Conversión Ultra Premium'),
        ('convertir_html_interactivo.py', 'Dashboards HTML'),
        ('mejoras_avanzadas_analisis.py', 'Análisis Estadístico'),
        ('analisis_predictivo_avanzado.py', 'Análisis Predictivo'),
        ('sistema_plantillas_avanzado.py', 'Plantillas Personalizadas'),
        ('dashboard_maestro_documentos.py', 'Dashboard Maestro'),
        ('optimizador_y_compresor.py', 'Optimización y Compresión'),
    ]
    
    resultados = []
    inicio_total = datetime.now()
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "GENERACIÓN COMPLETA DE DOCUMENTOS" + " "*15 + "║")
    print("║" + " "*20 + "Sistema Premium 2.0" + " "*25 + "║")
    print("╚" + "="*68 + "╝")
    print(f"\n📅 Inicio: {inicio_total.strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    for script, descripcion in scripts:
        script_path = os.path.join(directorio, script)
        if os.path.exists(script_path):
            inicio = datetime.now()
            print(f"🔄 Ejecutando: {descripcion}...")
            
            try:
                resultado = subprocess.run(
                    [sys.executable, script_path],
                    cwd=directorio,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                fin = datetime.now()
                duracion = (fin - inicio).total_seconds()
                
                if resultado.returncode == 0:
                    print(f"   ✅ Completado en {duracion:.1f}s\n")
                    resultados.append({
                        'script': script,
                        'descripcion': descripcion,
                        'exito': True,
                        'duracion': duracion,
                        'timestamp': inicio.isoformat()
                    })
                else:
                    print(f"   ⚠️  Completado con advertencias en {duracion:.1f}s\n")
                    resultados.append({
                        'script': script,
                        'descripcion': descripcion,
                        'exito': False,
                        'duracion': duracion,
                        'error': resultado.stderr[:200] if resultado.stderr else 'Unknown error',
                        'timestamp': inicio.isoformat()
                    })
            except subprocess.TimeoutExpired:
                print(f"   ⏱️  Tiempo agotado (>10 min)\n")
                resultados.append({
                    'script': script,
                    'descripcion': descripcion,
                    'exito': False,
                    'error': 'Timeout',
                    'timestamp': inicio.isoformat()
                })
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
                resultados.append({
                    'script': script,
                    'descripcion': descripcion,
                    'exito': False,
                    'error': str(e),
                    'timestamp': inicio.isoformat()
                })
        else:
            print(f"⚠️  Script no encontrado: {script}\n")
            resultados.append({
                'script': script,
                'descripcion': descripcion,
                'exito': False,
                'error': 'Script no encontrado',
                'timestamp': datetime.now().isoformat()
            })
    
    fin_total = datetime.now()
    duracion_total = (fin_total - inicio_total).total_seconds()
    
    return resultados, duracion_total

def generar_reporte_final(directorio, resultados, duracion_total):
    """Genera reporte final completo"""
    
    # Contar archivos generados
    formatos = {
        'Word (.docx)': len(glob.glob(os.path.join(directorio, '*PROFESIONAL*.docx'))),
        'Excel Profesional': len(glob.glob(os.path.join(directorio, '*PROFESIONAL*.xlsx'))),
        'Excel Avanzado': len(glob.glob(os.path.join(directorio, '*AVANZADO*.xlsx'))),
        'Excel Premium': len(glob.glob(os.path.join(directorio, '*PREMIUM*.xlsx'))),
        'PowerPoint': len(glob.glob(os.path.join(directorio, '*ULTRA_PREMIUM*.pptx'))),
        'PDF': len(glob.glob(os.path.join(directorio, '*ULTRA_PREMIUM*.pdf'))),
        'HTML Interactivo': len(glob.glob(os.path.join(directorio, '*INTERACTIVO*.html'))),
        'Análisis PNG': len(glob.glob(os.path.join(directorio, '*ESTADISTICO*.png'))),
        'Predicciones PNG': len(glob.glob(os.path.join(directorio, '*PREDICCIONES*.png'))),
        'Plantillas': len(glob.glob(os.path.join(directorio, 'plantillas/*.docx'))),
    }
    
    total_archivos = sum(formatos.values())
    
    # Calcular tamaños
    todos_archivos = []
    for patron in ['*.docx', '*.xlsx', '*.pptx', '*.pdf', '*.html', '*.png']:
        todos_archivos.extend(glob.glob(os.path.join(directorio, patron)))
    
    # Excluir comprimidos y temporales
    todos_archivos = [f for f in todos_archivos if not any(x in f for x in ['.zip', '~', 'temp', 'plantillas'])]
    tamaño_total = sum(os.path.getsize(f) for f in todos_archivos if os.path.exists(f))
    
    # Generar reporte
    reporte = {
        'fecha': datetime.now().isoformat(),
        'duracion_total_segundos': duracion_total,
        'duracion_total_formato': f"{int(duracion_total//60)}m {int(duracion_total%60)}s",
        'total_scripts': len(resultados),
        'scripts_exitosos': sum(1 for r in resultados if r.get('exito', False)),
        'scripts_fallidos': sum(1 for r in resultados if not r.get('exito', False)),
        'total_archivos_generados': total_archivos,
        'tamaño_total_mb': tamaño_total / 1024 / 1024,
        'formatos': formatos,
        'resultados_scripts': resultados
    }
    
    # Guardar JSON
    archivo_json = os.path.join(directorio, 'REPORTE_FINAL_COMPLETO.json')
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    # Guardar texto
    archivo_txt = os.path.join(directorio, 'REPORTE_FINAL_COMPLETO.txt')
    with open(archivo_txt, 'w', encoding='utf-8') as f:
        f.write("╔" + "="*68 + "╗\n")
        f.write("║" + " "*20 + "REPORTE FINAL COMPLETO" + " "*25 + "║\n")
        f.write("║" + " "*15 + "Sistema de Conversión Premium 2.0" + " "*18 + "║\n")
        f.write("╚" + "="*68 + "╝\n\n")
        f.write(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"⏱️  Duración Total: {reporte['duracion_total_formato']}\n\n")
        f.write("="*70 + "\n")
        f.write("RESUMEN DE EJECUCIÓN\n")
        f.write("="*70 + "\n\n")
        f.write(f"Total Scripts Ejecutados: {reporte['total_scripts']}\n")
        f.write(f"✅ Exitosos: {reporte['scripts_exitosos']}\n")
        f.write(f"❌ Fallidos: {reporte['scripts_fallidos']}\n\n")
        f.write("="*70 + "\n")
        f.write("ARCHIVOS GENERADOS\n")
        f.write("="*70 + "\n\n")
        
        for formato, cantidad in formatos.items():
            if cantidad > 0:
                f.write(f"  {formato:30s} : {cantidad:3d} archivos\n")
        
        f.write(f"\n  {'TOTAL':30s} : {total_archivos:3d} archivos\n")
        f.write(f"  {'Tamaño Total':30s} : {tamaño_total/1024/1024:.2f} MB\n\n")
        f.write("="*70 + "\n")
        f.write("DETALLE DE SCRIPTS\n")
        f.write("="*70 + "\n\n")
        
        for resultado in resultados:
            estado = "✅" if resultado.get('exito', False) else "❌"
            duracion = f"{resultado.get('duracion', 0):.1f}s" if 'duracion' in resultado else "N/A"
            f.write(f"{estado} {resultado['descripcion']:40s} ({duracion})\n")
            if not resultado.get('exito', False) and 'error' in resultado:
                f.write(f"   Error: {resultado['error'][:100]}\n")
            f.write("\n")
    
    print(f"\n📄 Reporte final guardado:")
    print(f"   • {archivo_txt}")
    print(f"   • {archivo_json}")
    
    return reporte

def main():
    """Función principal"""
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    
    print("🚀 INICIANDO GENERACIÓN COMPLETA DE DOCUMENTOS\n")
    print("Este proceso ejecutará TODOS los scripts de conversión.\n")
    print("Puede tardar varios minutos...\n")
    
    # Ejecutar todos los scripts
    resultados, duracion_total = ejecutar_todos_los_scripts()
    
    # Generar reporte final
    print("\n" + "="*70)
    print("📊 GENERANDO REPORTE FINAL")
    print("="*70)
    reporte = generar_reporte_final(directorio, resultados, duracion_total)
    
    # Resumen final
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*25 + "RESUMEN FINAL" + " "*25 + "║")
    print("╠" + "="*68 + "╣")
    print(f"║  Duración Total:        {reporte['duracion_total_formato']:>20s}" + " "*25 + "║")
    print(f"║  Scripts Ejecutados:    {reporte['total_scripts']:>20d}" + " "*25 + "║")
    print(f"║  Scripts Exitosos:     {reporte['scripts_exitosos']:>20d}" + " "*25 + "║")
    print(f"║  Scripts Fallidos:     {reporte['scripts_fallidos']:>20d}" + " "*25 + "║")
    print(f"║  Archivos Generados:   {reporte['total_archivos_generados']:>20d}" + " "*25 + "║")
    print(f"║  Tamaño Total:         {reporte['tamaño_total_mb']:>19.2f} MB" + " "*25 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\n✅ GENERACIÓN COMPLETA FINALIZADA!")
    print(f"📊 Se generaron {reporte['total_archivos_generados']} documentos en múltiples formatos")
    print(f"📁 Revisa los reportes para más detalles")

if __name__ == "__main__":
    main()



