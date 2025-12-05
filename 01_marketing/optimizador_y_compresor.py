#!/usr/bin/env python3
"""
Optimizador y Compresor Avanzado - Optimiza y comprime documentos generados
para reducir tamaño manteniendo calidad, y genera reportes de optimización.
"""

import os
import glob
from datetime import datetime
import zipfile
from pathlib import Path

def optimizar_imagenes_en_excel(archivo_excel):
    """Optimiza imágenes en archivos Excel"""
    try:
        import openpyxl
        from PIL import Image
        import io
        
        wb = openpyxl.load_workbook(archivo_excel)
        optimizado = False
        
        for sheet in wb.worksheets:
            if hasattr(sheet, '_images'):
                for img in sheet._images:
                    # Comprimir imagen si es muy grande
                    if hasattr(img, '_data'):
                        try:
                            pil_img = Image.open(io.BytesIO(img._data()))
                            # Reducir calidad si es necesario
                            if pil_img.size[0] > 2000 or pil_img.size[1] > 2000:
                                # Redimensionar manteniendo aspecto
                                ratio = min(2000/pil_img.size[0], 2000/pil_img.size[1])
                                new_size = (int(pil_img.size[0]*ratio), int(pil_img.size[1]*ratio))
                                pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                                
                                # Guardar comprimido
                                buffer = io.BytesIO()
                                pil_img.save(buffer, format='PNG', optimize=True)
                                img._data = buffer.getvalue()
                                optimizado = True
                        except:
                            pass
        
        if optimizado:
            wb.save(archivo_excel.replace('.xlsx', '_optimizado.xlsx'))
            return True
    except Exception as e:
        print(f"⚠️  Error optimizando {archivo_excel}: {e}")
    return False

def comprimir_documentos(directorio, formato='zip'):
    """Comprime documentos por tipo"""
    print("📦 Comprimiendo documentos...")
    
    tipos = {
        'Word': '*.docx',
        'Excel': '*.xlsx',
        'PowerPoint': '*.pptx',
        'PDF': '*.pdf',
        'HTML': '*.html',
    }
    
    comprimidos = []
    
    for tipo, patron in tipos.items():
        archivos = glob.glob(os.path.join(directorio, patron))
        if archivos:
            nombre_zip = os.path.join(directorio, f'{tipo}_COMPLETO_{datetime.now().strftime("%Y%m%d")}.zip')
            
            with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for archivo in archivos:
                    # Excluir ya comprimidos
                    if not archivo.endswith('.zip'):
                        zipf.write(archivo, os.path.basename(archivo))
            
            tamaño_original = sum(os.path.getsize(f) for f in archivos)
            tamaño_comprimido = os.path.getsize(nombre_zip)
            ratio = (1 - tamaño_comprimido/tamaño_original) * 100
            
            comprimidos.append({
                'tipo': tipo,
                'archivo': nombre_zip,
                'archivos': len(archivos),
                'tamaño_original': tamaño_original,
                'tamaño_comprimido': tamaño_comprimido,
                'compresion': f"{ratio:.1f}%"
            })
            
            print(f"  ✓ {tipo}: {len(archivos)} archivos → {nombre_zip} ({ratio:.1f}% compresión)")
    
    return comprimidos

def generar_reporte_optimizacion(directorio, comprimidos):
    """Genera reporte de optimización"""
    reporte = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    REPORTE DE OPTIMIZACIÓN Y COMPRESIÓN                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
📁 Directorio: {directorio}

📦 ARCHIVOS COMPRIMIDOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    total_original = 0
    total_comprimido = 0
    
    for comp in comprimidos:
        reporte += f"""
  {comp['tipo']}:
    • Archivos: {comp['archivos']}
    • Tamaño original: {comp['tamaño_original']/1024/1024:.2f} MB
    • Tamaño comprimido: {comp['tamaño_comprimido']/1024/1024:.2f} MB
    • Compresión: {comp['compresion']}
    • Archivo: {os.path.basename(comp['archivo'])}
"""
        total_original += comp['tamaño_original']
        total_comprimido += comp['tamaño_comprimido']
    
    ratio_total = (1 - total_comprimido/total_original) * 100 if total_original > 0 else 0
    
    reporte += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOTAL:
    • Tamaño original: {total_original/1024/1024:.2f} MB
    • Tamaño comprimido: {total_comprimido/1024/1024:.2f} MB
    • Compresión total: {ratio_total:.1f}%
    • Espacio ahorrado: {(total_original-total_comprimido)/1024/1024:.2f} MB

╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    archivo_reporte = os.path.join(directorio, 'REPORTE_OPTIMIZACION.txt')
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print(f"\n📄 Reporte guardado: {archivo_reporte}")
    print(reporte)

def main():
    """Función principal"""
    directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
    
    print("⚡ Iniciando optimización y compresión...\n")
    
    # Comprimir documentos
    comprimidos = comprimir_documentos(directorio)
    
    # Generar reporte
    if comprimidos:
        generar_reporte_optimizacion(directorio, comprimidos)
    
    print("\n✅ Optimización completada!")

if __name__ == "__main__":
    main()








