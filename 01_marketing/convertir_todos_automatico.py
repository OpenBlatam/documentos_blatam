#!/usr/bin/env python3
"""
Script de automatización completa para convertir TODOS los archivos Markdown importantes
a todos los formatos disponibles (Word, Excel, PowerPoint, PDF) en una sola ejecución.
"""

import os
import glob
from datetime import datetime

def ejecutar_conversion_completa():
    """Ejecuta todas las conversiones disponibles"""
    
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    scripts = [
        ('convertir_md_a_documentos_profesionales.py', 'Profesional'),
        ('convertir_todos_archivos_avanzado.py', 'Avanzado'),
        ('convertir_mejorado_premium.py', 'Premium'),
        ('convertir_completo_ultra_premium.py', 'Ultra Premium'),
    ]
    
    print("=" * 70)
    print("🚀 CONVERSIÓN AUTOMÁTICA COMPLETA DE DOCUMENTOS")
    print("=" * 70)
    print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📁 Directorio: {directorio}")
    print("=" * 70)
    print()
    
    resultados = {}
    
    for script, version in scripts:
        script_path = os.path.join(directorio, script)
        if os.path.exists(script_path):
            print(f"\n▶️  Ejecutando: {version}")
            print("-" * 70)
            try:
                os.system(f"cd {directorio} && python3 {script} 2>&1 | grep -E '(✓|✅|⚠|Error)'")
                resultados[version] = "✅ Completado"
            except Exception as e:
                resultados[version] = f"❌ Error: {e}"
        else:
            resultados[version] = "⚠️  Script no encontrado"
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE CONVERSIÓN")
    print("=" * 70)
    for version, estado in resultados.items():
        print(f"  {version:20s} : {estado}")
    
    print("\n" + "=" * 70)
    print("✅ PROCESO COMPLETADO")
    print("=" * 70)
    
    # Contar archivos creados
    formatos = {
        'Word': glob.glob(os.path.join(directorio, '*PROFESIONAL*.docx')),
        'Excel Profesional': glob.glob(os.path.join(directorio, '*PROFESIONAL*.xlsx')),
        'Excel Avanzado': glob.glob(os.path.join(directorio, '*AVANZADO*.xlsx')),
        'Excel Premium': glob.glob(os.path.join(directorio, '*PREMIUM*.xlsx')),
        'PowerPoint': glob.glob(os.path.join(directorio, '*ULTRA_PREMIUM*.pptx')),
        'PDF': glob.glob(os.path.join(directorio, '*ULTRA_PREMIUM*.pdf')),
    }
    
    print("\n📁 ARCHIVOS CREADOS:")
    print("-" * 70)
    total = 0
    for formato, archivos in formatos.items():
        cantidad = len(archivos)
        total += cantidad
        if cantidad > 0:
            print(f"  {formato:25s} : {cantidad:3d} archivos")
    
    print("-" * 70)
    print(f"  {'TOTAL':25s} : {total:3d} archivos")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_conversion_completa()








