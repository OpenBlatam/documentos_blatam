#!/usr/bin/env python3
"""
Script para convertir MÁS documentos importantes a PDF, Word y Excel
con gráficas profesionales.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from generar_docs_importantes_pdf_word_excel import DocumentConverter
from pathlib import Path


def main():
    """Convierte más documentos importantes."""
    base_dir = Path("/Users/adan/Documents/documentos_blatam")
    output_dir = "docs_premium_adicionales"
    
    converter = DocumentConverter(output_dir)
    
    # Lista expandida de documentos adicionales importantes
    additional_files = [
        # Documentos de mejoras y resúmenes
        "RESUMEN_FUNCIONALIDADES_AVANZADAS.md",
        "MEJORAS_FINALES.md",
        "MEJORAS_IMPLEMENTADAS.md",
        "RESUMEN_MEJORAS_COMPLETAS.md",
        "CHANGELOG.md",
        
        # Documentos de producción adicionales
        "truthgpt_collected/integration_code/production_code/MEJORAS_FINALES_CONSOLIDADO.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_FINALES_COMPLETAS.md",
        "truthgpt_collected/integration_code/production_code/CODE_QUALITY_IMPROVEMENTS.md",
        "truthgpt_collected/integration_code/production_code/ROUTES_IMPROVEMENTS.md",
        "truthgpt_collected/integration_code/production_code/SERVICES_IMPROVEMENTS.md",
        "truthgpt_collected/integration_code/production_code/APPLICATION_FACTORY_IMPROVEMENTS.md",
        "truthgpt_collected/integration_code/production_code/API_UTILITIES_IMPROVEMENTS.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_RUTAS_API.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_DECORADORES_UTILIDADES.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_UTILIDADES_ADICIONALES.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_ULTIMAS_UTILIDADES.md",
        "truthgpt_collected/integration_code/production_code/CHANGELOG_MEJORAS.md",
        "truthgpt_collected/integration_code/production_code/CHECKLIST_VERIFICACION.md",
        "truthgpt_collected/integration_code/production_code/GUIA_USO_UTILIDADES.md",
        "truthgpt_collected/integration_code/production_code/INDICE_DOCUMENTACION_COMPLETO.md",
        "truthgpt_collected/integration_code/production_code/RESUMEN_FINAL_COMPLETO.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_APLICADAS.md",
        
        # Documentos de fases
        "truthgpt_collected/integration_code/production_code/PHASE1_COMPLETE.md",
        "truthgpt_collected/integration_code/production_code/PHASE2_COMPLETE.md",
        "truthgpt_collected/integration_code/production_code/PHASE3_COMPLETE.md",
        "truthgpt_collected/integration_code/production_code/PHASE4_COMPLETE.md",
        "truthgpt_collected/integration_code/production_code/PHASE5_COMPLETE.md",
        
        # Documentos de documentación
        "truthgpt_collected/integration_code/production_code/docs/README.md",
        "truthgpt_collected/integration_code/production_code/docs/LIBRERIAS_IMPLEMENTADAS.md",
        "truthgpt_collected/integration_code/production_code/docs/architecture/layers.md",
        
        # Otros documentos importantes
        "truthgpt_collected/integration_code/production_code/MEJORAS_MODULOS_V2.md",
        "truthgpt_collected/integration_code/production_code/CODE_CLEANUP_SUMMARY.md",
        "truthgpt_collected/integration_code/production_code/CLEANUP_SUMMARY.md",
        "truthgpt_collected/integration_code/production_code/redundancy/RESUMEN_FINAL_COMPLETO.md",
        "truthgpt_collected/integration_code/production_code/redundancy/README.md",
        "truthgpt_collected/integration_code/production_code/sora/README.md",
        "truthgpt_collected/integration_code/production_code/sora/CHANGELOG.md",
        "truthgpt_collected/integration_code/production_code/multimodal_api/CHANGELOG.md",
        "truthgpt_collected/integration_code/production_code/multimodal_api/DEPLOYMENT.md",
        "truthgpt_collected/integration_code/production_code/best/README.md",
        "truthgpt_collected/integration_code/production_code/best/CHANGELOG.md",
    ]
    
    print("=" * 70)
    print("📚 CONVERSIÓN DE DOCUMENTOS ADICIONALES")
    print("=" * 70)
    print()
    
    processed = 0
    not_found = 0
    
    for file_path in additional_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"\n📄 Procesando: {file_path}")
            try:
                result = converter.convert(str(full_path))
                if result:
                    processed += 1
                    print(f"✅ Completado: {Path(file_path).stem}")
                else:
                    print(f"⚠️  Error en conversión: {file_path}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        else:
            not_found += 1
            if not_found <= 5:  # Solo mostrar los primeros 5 no encontrados
                print(f"⚠️  No encontrado: {file_path}")
    
    print("\n" + "=" * 70)
    print(f"✨ Procesados {processed} documentos adicionales")
    if not_found > 0:
        print(f"⚠️  {not_found} archivos no encontrados")
    print(f"📁 Archivos guardados en: {Path(output_dir).absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    main()

