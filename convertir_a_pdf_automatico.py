#!/usr/bin/env python3
"""
Script para convertir A1_ADZ.docx a PDF usando diferentes métodos
"""

import subprocess
import os
import sys

def convertir_con_libreoffice(docx_path, pdf_path):
    """Intenta convertir usando LibreOffice"""
    try:
        # Buscar LibreOffice en diferentes ubicaciones
        libreoffice_paths = [
            'libreoffice',
            '/Applications/LibreOffice.app/Contents/MacOS/soffice',
            '/usr/local/bin/libreoffice'
        ]
        
        for lo_path in libreoffice_paths:
            try:
                result = subprocess.run(
                    [lo_path, '--headless', '--convert-to', 'pdf', 
                     '--outdir', os.path.dirname(pdf_path) or '.',
                     docx_path],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    # LibreOffice crea el PDF con el mismo nombre base
                    base_name = os.path.splitext(os.path.basename(docx_path))[0]
                    temp_pdf = os.path.join(os.path.dirname(pdf_path) or '.', f'{base_name}.pdf')
                    if os.path.exists(temp_pdf):
                        os.rename(temp_pdf, pdf_path)
                        return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return False
    except Exception as e:
        print(f"Error con LibreOffice: {e}")
        return False

def convertir_con_textutil(docx_path, pdf_path):
    """Intenta convertir usando textutil (limitado en macOS)"""
    try:
        # textutil no convierte directamente a PDF, pero podemos intentar
        # convertir a RTF primero y luego a PDF
        print("⚠️  textutil no soporta conversión directa a PDF")
        return False
    except Exception as e:
        print(f"Error con textutil: {e}")
        return False

def abrir_con_word(docx_path):
    """Abre el archivo en Word para conversión manual"""
    try:
        subprocess.run(['open', '-a', 'Microsoft Word', docx_path])
        return True
    except Exception as e:
        print(f"Error abriendo Word: {e}")
        return False

def main():
    docx_file = 'A1_ADZ_limpio.docx'
    pdf_file = 'A1_ADZ.pdf'
    
    if not os.path.exists(docx_file):
        print(f"❌ Error: No se encontró {docx_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("CONVERTIR A PDF - A1_ADZ")
    print("=" * 60)
    print()
    
    # Método 1: LibreOffice
    print("📄 Intentando convertir con LibreOffice...")
    if convertir_con_libreoffice(docx_file, pdf_file):
        print(f"✅ PDF creado exitosamente: {pdf_file}")
        return
    
    # Método 2: textutil (no funciona directamente)
    print("📄 Intentando con textutil...")
    if convertir_con_textutil(docx_file, pdf_file):
        print(f"✅ PDF creado exitosamente: {pdf_file}")
        return
    
    # Si ningún método automático funciona, dar instrucciones
    print()
    print("⚠️  No se pudo convertir automáticamente a PDF")
    print()
    print("=" * 60)
    print("INSTRUCCIONES PARA CREAR PDF MANUALMENTE")
    print("=" * 60)
    print()
    print("OPCIÓN 1 - Microsoft Word (Recomendado):")
    print("   1. Abra el archivo en Word:")
    print(f"      open -a 'Microsoft Word' {docx_file}")
    print("   2. Vaya a: Archivo > Guardar como")
    print("   3. Seleccione formato: PDF")
    print("   4. Guarde como: A1_ADZ.pdf")
    print()
    print("OPCIÓN 2 - Páginas (macOS):")
    print("   1. Abra el archivo en Páginas")
    print("   2. Vaya a: Archivo > Exportar a > PDF")
    print("   3. Guarde como: A1_ADZ.pdf")
    print()
    print("OPCIÓN 3 - Instalar docx2pdf:")
    print("   pip install docx2pdf")
    print("   python3 -c \"from docx2pdf import convert; convert('A1_ADZ_limpio.docx', 'A1_ADZ.pdf')\"")
    print()
    print("OPCIÓN 4 - Instalar LibreOffice:")
    print("   brew install --cask libreoffice")
    print("   libreoffice --headless --convert-to pdf A1_ADZ_limpio.docx")
    print()
    
    # Intentar abrir Word automáticamente
    respuesta = input("¿Desea abrir el archivo en Microsoft Word ahora? (s/n): ")
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        if abrir_con_word(docx_file):
            print("✅ Archivo abierto en Word. Siga las instrucciones para guardar como PDF.")
        else:
            print("⚠️  No se pudo abrir Word. Por favor, ábralo manualmente.")

if __name__ == "__main__":
    main()







