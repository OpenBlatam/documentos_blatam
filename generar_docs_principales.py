#!/usr/bin/env python3
"""
Script para generar documentos premium (PDF, Word, Excel) con gráficas
de los documentos MÁS IMPORTANTES del proyecto.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from generar_docs_premium import DocumentConverter
from pathlib import Path


def main():
    """Genera documentos de los archivos más importantes."""
    base_dir = Path(".")
    output_dir = "docs_premium_principales"
    
    converter = DocumentConverter(output_dir)
    
    # Lista específica de documentos más importantes
    important_files = [
        "airflow_automation_prompt.md",
        "truthgpt_collected/integration_code/production_code/ARCHITECTURE_IMPROVEMENTS.md",
        "truthgpt_collected/integration_code/production_code/REFACTORING_PLAN.md",
        "truthgpt_collected/integration_code/production_code/README.md",
        "truthgpt_collected/integration_code/production_code/ARCHITECTURE.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_ARQUITECTURA_COMPLETAS.md",
        "truthgpt_collected/integration_code/production_code/MEJORAS_ADICIONALES_RECOMENDADAS.md",
        "truthgpt_collected/integration_code/production_code/RESUMEN_FINAL_MEJORAS.md",
        "ARCHITECTURE.md",
        "README.md",
        "CHANGELOG.md",
        "BEST_PRACTICES.md",
        "04_business_strategy/Other/Plans/master_plan_final.md",
        "06_documentation/Master_documents/00_documentacion_maestra_index.md",
        "06_documentation/resumen_final_completo.md",
        "06_documentation/Other/Summaries/final_executive_summary.md",
        "04_business_strategy/Strategic_plans/00_indice_maestro_estrategia_suprema.md",
        "05_technology/Other/sistema_completo_definitivo.md",
        "05_technology/Other/final_master_ecosystem_summary.md",
        "06_strategy/Business_strategies/strategy_master_index.md"
    ]
    
    print("🔍 Procesando documentos principales...\n")
    print("="*60)
    
    processed = 0
    for file_path in important_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"\n📄 Procesando: {file_path}")
            doc_info = {
                "path": full_path,
                "name": full_path.stem,
                "priority": 1
            }
            try:
                converter.convert_document(doc_info)
                processed += 1
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        else:
            print(f"⚠️  No encontrado: {file_path}")
    
    print("\n" + "="*60)
    print(f"\n✨ Procesados {processed} documentos principales")
    print(f"📁 Archivos guardados en: {Path(output_dir).absolute()}")


if __name__ == "__main__":
    main()



