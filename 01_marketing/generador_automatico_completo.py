#!/usr/bin/env python3
"""
Generador Automático Completo - Sistema de conversión masiva con:
- Detección automática de archivos Markdown
- Conversión a todos los formatos disponibles
- Generación de reportes de conversión
- Plantillas personalizables
- Optimización automática
"""

import os
import glob
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys

def encontrar_archivos_markdown_importantes(directorio, max_archivos=20):
    """Encuentra los archivos Markdown más importantes"""
    
    # Archivos prioritarios (si existen)
    archivos_prioritarios = [
        'SISTEMAS_PROMPTS_CONSOLIDADO.md',
        'PRESUPUESTO_PRICING.md',
        'DASHBOARD_METRICAS.md',
        'ANALISIS_COMPETITIVO.md',
        'REPORTES_EJECUTIVOS.md',
        'PROMPT_INDICE_MAESTRO_TECNICO.md',
        'PROMPT_TEMPLATE_CREACION_DOCUMENTACION.md',
        'PROMPTS_SISTEMAS_COMPLETOS.md',
    ]
    
    encontrados = []
    
    # Buscar archivos prioritarios primero
    for archivo in archivos_prioritarios:
        ruta = os.path.join(directorio, archivo)
        if os.path.exists(ruta):
            encontrados.append(archivo)
    
    # Si no hay suficientes, buscar otros archivos importantes
    if len(encontrados) < max_archivos:
        patrones = [
            '*GUIA*.md',
            '*SISTEMA*.md',
            '*ANALISIS*.md',
            '*DASHBOARD*.md',
            '*REPORTE*.md',
        ]
        
        for patron in patrones:
            archivos = glob.glob(os.path.join(directorio, patron))
            for archivo in archivos[:5]:  # Máximo 5 por patrón
                nombre = os.path.basename(archivo)
                if nombre not in encontrados and len(encontrados) < max_archivos:
                    encontrados.append(nombre)
    
    return encontrados[:max_archivos]

def ejecutar_script(script_path, descripcion):
    """Ejecuta un script de conversión"""
    print(f"\n{'='*70}")
    print(f"🔄 {descripcion}")
    print(f"{'='*70}")
    
    try:
        resultado = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(script_path),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo
        )
        
        if resultado.returncode == 0:
            print(f"✅ {descripcion} - Completado")
            return True, resultado.stdout
        else:
            print(f"⚠️  {descripcion} - Errores encontrados")
            print(resultado.stderr[:500])  # Primeros 500 caracteres del error
            return False, resultado.stderr
    except subprocess.TimeoutExpired:
        print(f"⏱️  {descripcion} - Tiempo agotado")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ {descripcion} - Error: {e}")
        return False, str(e)

def generar_reporte_conversion(directorio, resultados):
    """Genera un reporte de conversión en JSON y texto"""
    
    reporte = {
        'fecha': datetime.now().isoformat(),
        'directorio': directorio,
        'total_archivos_procesados': len(resultados),
        'exitosos': sum(1 for r in resultados if r['exito']),
        'fallidos': sum(1 for r in resultados if not r['exito']),
        'resultados': resultados
    }
    
    # Guardar JSON
    archivo_json = os.path.join(directorio, 'REPORTE_CONVERSION.json')
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    # Guardar texto
    archivo_txt = os.path.join(directorio, 'REPORTE_CONVERSION.txt')
    with open(archivo_txt, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("REPORTE DE CONVERSIÓN AUTOMÁTICA\n")
        f.write("="*70 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Directorio: {directorio}\n\n")
        f.write(f"Total archivos procesados: {reporte['total_archivos_procesados']}\n")
        f.write(f"Exitosos: {reporte['exitosos']}\n")
        f.write(f"Fallidos: {reporte['fallidos']}\n\n")
        f.write("-"*70 + "\n")
        f.write("DETALLE DE RESULTADOS\n")
        f.write("-"*70 + "\n\n")
        
        for resultado in resultados:
            estado = "✅" if resultado['exito'] else "❌"
            f.write(f"{estado} {resultado['script']}\n")
            f.write(f"   Archivo: {resultado.get('archivo', 'N/A')}\n")
            if resultado.get('mensaje'):
                f.write(f"   Mensaje: {resultado['mensaje'][:200]}\n")
            f.write("\n")
    
    print(f"\n📄 Reporte guardado: {archivo_txt}")
    print(f"📄 Reporte JSON: {archivo_json}")
    
    return reporte

def main():
    """Función principal de generación automática"""
    
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "GENERADOR AUTOMÁTICO COMPLETO" + " "*20 + "║")
    print("║" + " "*15 + "Sistema de Conversión Masiva Premium" + " "*15 + "║")
    print("╚" + "="*68 + "╝")
    print(f"\n📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📁 Directorio: {directorio}\n")
    
    # Encontrar archivos importantes
    print("🔍 Buscando archivos Markdown importantes...")
    archivos = encontrar_archivos_markdown_importantes(directorio, max_archivos=10)
    print(f"✓ Encontrados {len(archivos)} archivos importantes\n")
    
    # Scripts disponibles
    scripts = [
        ('convertir_md_a_documentos_profesionales.py', 'Conversión Profesional'),
        ('convertir_todos_archivos_avanzado.py', 'Conversión Avanzada'),
        ('convertir_mejorado_premium.py', 'Conversión Premium'),
        ('convertir_completo_ultra_premium.py', 'Conversión Ultra Premium'),
        ('convertir_html_interactivo.py', 'Dashboards HTML Interactivos'),
        ('mejoras_avanzadas_analisis.py', 'Análisis Estadístico Avanzado'),
    ]
    
    resultados = []
    
    # Ejecutar cada script
    for script, descripcion in scripts:
        script_path = os.path.join(directorio, script)
        if os.path.exists(script_path):
            exito, mensaje = ejecutar_script(script_path, descripcion)
            resultados.append({
                'script': script,
                'descripcion': descripcion,
                'exito': exito,
                'mensaje': mensaje[:500] if mensaje else None,
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f"⚠️  Script no encontrado: {script}")
            resultados.append({
                'script': script,
                'descripcion': descripcion,
                'exito': False,
                'mensaje': 'Script no encontrado',
                'timestamp': datetime.now().isoformat()
            })
    
    # Generar reporte
    print("\n" + "="*70)
    print("📊 GENERANDO REPORTE DE CONVERSIÓN")
    print("="*70)
    reporte = generar_reporte_conversion(directorio, resultados)
    
    # Resumen final
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*25 + "RESUMEN FINAL" + " "*25 + "║")
    print("╠" + "="*68 + "╣")
    print(f"║  Total procesados: {reporte['total_archivos_procesados']:3d} scripts" + " "*35 + "║")
    print(f"║  Exitosos:         {reporte['exitosos']:3d} scripts" + " "*38 + "║")
    print(f"║  Fallidos:        {reporte['fallidos']:3d} scripts" + " "*38 + "║")
    print("╚" + "="*68 + "╝")
    
    # Contar archivos generados
    formatos = {
        'Word': len(glob.glob(os.path.join(directorio, '*PROFESIONAL*.docx'))),
        'Excel Profesional': len(glob.glob(os.path.join(directorio, '*PROFESIONAL*.xlsx'))),
        'Excel Avanzado': len(glob.glob(os.path.join(directorio, '*AVANZADO*.xlsx'))),
        'Excel Premium': len(glob.glob(os.path.join(directorio, '*PREMIUM*.xlsx'))),
        'PowerPoint': len(glob.glob(os.path.join(directorio, '*ULTRA_PREMIUM*.pptx'))),
        'PDF': len(glob.glob(os.path.join(directorio, '*ULTRA_PREMIUM*.pdf'))),
        'HTML': len(glob.glob(os.path.join(directorio, '*INTERACTIVO*.html'))),
    }
    
    total_archivos = sum(formatos.values())
    
    print("\n📁 ARCHIVOS GENERADOS:")
    print("-"*70)
    for formato, cantidad in formatos.items():
        if cantidad > 0:
            print(f"  {formato:25s} : {cantidad:3d} archivos")
    print("-"*70)
    print(f"  {'TOTAL':25s} : {total_archivos:3d} archivos")
    print("="*70)
    
    print("\n✅ Proceso de generación automática completado!")
    print(f"📊 Se generaron {total_archivos} documentos en múltiples formatos")

if __name__ == "__main__":
    main()








