#!/usr/bin/env python3
"""
Script mejorado para generar documentos premium individuales (PDF, Word, Excel)
para cada documento importante con gráficas de alta calidad.
"""

import sys
sys.path.insert(0, '.')

from generar_documentos_premium import (
    DocumentProcessor, PDFGenerator, WordGenerator, ExcelGenerator,
    PDF_AVAILABLE, WORD_AVAILABLE, EXCEL_AVAILABLE,
    BASE_DIR, OUTPUT_DIR, IMPORTANT_DOCS
)
import re
from pathlib import Path

def process_individual_document(doc_path: Path):
    """Procesa un documento individual y genera PDF, Word y Excel"""
    doc_name = doc_path.stem
    safe_name = re.sub(r'[^\w\-_]', '_', doc_name)
    
    print(f"  📄 Procesando: {doc_name}")
    
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analizar documento
        processor = DocumentProcessor()
        processor.analyze_document(content)
        
        # Extraer título
        title = doc_name.replace('_', ' ').replace('-', ' ').title()
        first_line = content.split('\n')[0].strip()
        if first_line.startswith('#'):
            title = first_line.lstrip('#').strip()
            # Limpiar emojis del título
            title = re.sub(r'[^\x00-\x7F]+', '', title).strip()
        
        # Generar gráficas
        charts = processor.generate_statistics_charts()
        
        # Generar PDF individual
        if PDF_AVAILABLE:
            try:
                pdf_path = OUTPUT_DIR / f"{safe_name}.pdf"
                pdf_gen = PDFGenerator(pdf_path)
                pdf_gen.generate(title, content, processor.stats, charts)
                print(f"    ✅ PDF: {safe_name}.pdf")
            except Exception as e:
                print(f"    ⚠️  Error PDF: {e}")
        
        # Generar Word individual
        if WORD_AVAILABLE:
            try:
                word_path = OUTPUT_DIR / f"{safe_name}.docx"
                word_gen = WordGenerator(word_path)
                word_gen.generate(title, content, processor.stats, charts)
                print(f"    ✅ Word: {safe_name}.docx")
            except Exception as e:
                print(f"    ⚠️  Error Word: {e}")
        
        # Generar Excel individual
        if EXCEL_AVAILABLE:
            try:
                excel_path = OUTPUT_DIR / f"{safe_name}.xlsx"
                excel_gen = ExcelGenerator(excel_path)
                excel_gen.generate(title, content, processor.stats, charts)
                print(f"    ✅ Excel: {safe_name}.xlsx")
            except Exception as e:
                print(f"    ⚠️  Error Excel: {e}")
                
    except Exception as e:
        print(f"  ❌ Error procesando {doc_name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal - genera documentos individuales para cada archivo"""
    print("🚀 Generando documentos premium individuales...")
    print(f"📁 Directorio de salida: {OUTPUT_DIR}\n")
    
    processed_count = 0
    error_count = 0
    
    for doc_path_str in IMPORTANT_DOCS:
        full_path = BASE_DIR / doc_path_str
        if full_path.exists():
            print(f"📖 {doc_path_str}")
            process_individual_document(full_path)
            processed_count += 1
            print()
        else:
            print(f"⚠️  No encontrado: {doc_path_str}\n")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Proceso completado!")
    print(f"📊 Documentos procesados: {processed_count}")
    print(f"⚠️  Documentos no encontrados: {error_count}")
    print(f"📁 Archivos generados en: {OUTPUT_DIR}")
    print(f"{'='*60}")
    
    # Resumen de archivos generados
    pdfs = list(OUTPUT_DIR.glob("*.pdf"))
    words = list(OUTPUT_DIR.glob("*.docx"))
    excels = list(OUTPUT_DIR.glob("*.xlsx"))
    
    print(f"\n📄 Total de archivos generados:")
    print(f"   PDFs: {len(pdfs)}")
    print(f"   Words: {len(words)}")
    print(f"   Excels: {len(excels)}")
    print(f"   Total: {len(pdfs) + len(words) + len(excels)} archivos")


if __name__ == "__main__":
    main()



