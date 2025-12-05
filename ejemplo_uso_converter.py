#!/usr/bin/env python3
"""
Ejemplo de uso del Sistema Avanzado de Conversión de Documentos
=================================================================

Este script demuestra cómo usar el convertidor avanzado para
crear documentos en múltiples formatos.
"""

from document_converter_advanced import DocumentConverterAdvanced
from pathlib import Path
import sys

def ejemplo_basico():
    """Ejemplo básico de conversión"""
    print("="*70)
    print("EJEMPLO 1: Conversión Básica")
    print("="*70)
    
    # Crear convertidor
    converter = DocumentConverterAdvanced(output_dir="ejemplos_salida")
    
    # Archivo de ejemplo (puedes cambiar esto)
    input_file = "A1_ADZ.md"  # Ajusta según tus archivos
    
    if not Path(input_file).exists():
        print(f"⚠️  Archivo no encontrado: {input_file}")
        print("   Crea un archivo .md o ajusta la ruta")
        return
    
    # Convertir a PDF
    print(f"\n📄 Convirtiendo {input_file} a PDF...")
    pdf_file = converter.convert_to_pdf(input_file)
    if pdf_file:
        print(f"✅ PDF creado: {pdf_file}")
    else:
        print("❌ Error creando PDF")
    
    # Convertir a Word
    print(f"\n📝 Convirtiendo {input_file} a Word...")
    word_file = converter.convert_to_word(input_file, style="professional")
    if word_file:
        print(f"✅ Word creado: {word_file}")
    else:
        print("❌ Error creando Word")
    
    # Convertir a Excel
    print(f"\n📊 Convirtiendo {input_file} a Excel...")
    excel_file = converter.convert_to_excel(input_file, style="professional")
    if excel_file:
        print(f"✅ Excel creado: {excel_file}")
    else:
        print("❌ Error creando Excel")


def ejemplo_multiple_formatos():
    """Ejemplo de conversión a múltiples formatos"""
    print("\n" + "="*70)
    print("EJEMPLO 2: Conversión a Múltiples Formatos")
    print("="*70)
    
    converter = DocumentConverterAdvanced(output_dir="ejemplos_salida")
    
    input_file = "A1_ADZ.md"
    
    if not Path(input_file).exists():
        print(f"⚠️  Archivo no encontrado: {input_file}")
        return
    
    print(f"\n🔄 Convirtiendo {input_file} a todos los formatos...")
    results = converter.convert_all_formats(
        input_file,
        formats=['pdf', 'word', 'excel'],
        word={'style': 'professional'},
        excel={'style': 'premium'}
    )
    
    print("\n📋 Resultados:")
    for formato, archivo in results.items():
        if archivo:
            print(f"  ✅ {formato.upper()}: {archivo}")
        else:
            print(f"  ❌ {formato.upper()}: Error")


def ejemplo_deteccion_librerias():
    """Ejemplo de detección de librerías"""
    print("\n" + "="*70)
    print("EJEMPLO 3: Detección de Librerías")
    print("="*70)
    
    converter = DocumentConverterAdvanced()
    
    print("\n📚 Librerías disponibles:")
    print("-" * 70)
    
    # PDF
    print("\n📄 Librerías PDF:")
    pdf_libs = ['reportlab', 'fpdf', 'weasyprint', 'pdfkit', 'pypdf', 
                'PyMuPDF', 'xhtml2pdf', 'docx2pdf']
    for lib in pdf_libs:
        status = "✅" if converter.available_libraries.get(lib) else "❌"
        print(f"  {status} {lib}")
    
    # Word
    print("\n📝 Librerías Word:")
    word_libs = ['python-docx', 'mammoth']
    for lib in word_libs:
        status = "✅" if converter.available_libraries.get(lib) else "❌"
        print(f"  {status} {lib}")
    
    # Excel
    print("\n📊 Librerías Excel:")
    excel_libs = ['openpyxl', 'xlsxwriter', 'pandas', 'xlrd', 'xlwt']
    for lib in excel_libs:
        status = "✅" if converter.available_libraries.get(lib) else "❌"
        print(f"  {status} {lib}")
    
    # Utilidades
    print("\n🛠️  Librerías Utilidades:")
    util_libs = ['markdown', 'Pillow', 'matplotlib']
    for lib in util_libs:
        status = "✅" if converter.available_libraries.get(lib) else "❌"
        print(f"  {status} {lib}")


def ejemplo_estilos():
    """Ejemplo de diferentes estilos"""
    print("\n" + "="*70)
    print("EJEMPLO 4: Diferentes Estilos")
    print("="*70)
    
    converter = DocumentConverterAdvanced(output_dir="ejemplos_salida")
    
    input_file = "A1_ADZ.md"
    
    if not Path(input_file).exists():
        print(f"⚠️  Archivo no encontrado: {input_file}")
        return
    
    estilos = ['simple', 'professional', 'premium']
    
    for estilo in estilos:
        print(f"\n🎨 Creando Word con estilo: {estilo}")
        word_file = converter.convert_to_word(
            input_file,
            output_file=f"ejemplos_salida/documento_{estilo}.docx",
            style=estilo
        )
        if word_file:
            print(f"  ✅ Creado: {word_file}")
        else:
            print(f"  ❌ Error")


def ejemplo_masivo():
    """Ejemplo de conversión masiva"""
    print("\n" + "="*70)
    print("EJEMPLO 5: Conversión Masiva")
    print("="*70)
    
    converter = DocumentConverterAdvanced(output_dir="ejemplos_salida")
    
    # Buscar todos los archivos .md en el directorio actual
    archivos_md = list(Path(".").glob("*.md"))
    
    if not archivos_md:
        print("⚠️  No se encontraron archivos .md en el directorio actual")
        return
    
    print(f"\n📁 Encontrados {len(archivos_md)} archivos .md")
    print("🔄 Convirtiendo a PDF...")
    
    for archivo in archivos_md[:5]:  # Limitar a 5 para el ejemplo
        print(f"\n  📄 Procesando: {archivo.name}")
        pdf_file = converter.convert_to_pdf(str(archivo))
        if pdf_file:
            print(f"    ✅ PDF: {pdf_file}")
        else:
            print(f"    ❌ Error")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("SISTEMA AVANZADO DE CONVERSIÓN DE DOCUMENTOS")
    print("Ejemplos de Uso")
    print("="*70)
    
    # Verificar librerías disponibles
    ejemplo_deteccion_librerias()
    
    # Ejemplos de conversión
    try:
        ejemplo_basico()
        ejemplo_multiple_formatos()
        ejemplo_estilos()
        # ejemplo_masivo()  # Descomentar si quieres probar conversión masiva
    except Exception as e:
        print(f"\n❌ Error en los ejemplos: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ Ejemplos completados")
    print("="*70)
    print("\n💡 Tip: Instala más librerías para mejores resultados:")
    print("   pip install -r requirements_document_converter.txt")


if __name__ == "__main__":
    main()

