#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de recolección de datos de modelos.
"""

from model_data import ModelDataManager, InfoConnector, ModelDataCollector
from core.paper_registry import get_registry

def example_basic_usage():
    """Ejemplo básico de uso."""
    print("=" * 60)
    print("Ejemplo 1: Uso Básico")
    print("=" * 60)
    
    # Inicializar gestor
    manager = ModelDataManager()
    
    # Obtener información del registry
    registry_info = manager.get_registry_info()
    print(f"\nTotal de papers disponibles: {registry_info.get('total_papers', 0)}")
    print(f"Categorías: {list(registry_info.get('categories', []))}")
    
    # Recolectar datos de algunos modelos
    print("\nRecolectando datos de modelos...")
    collected = manager.collect_from_registry(
        category='research',
        run_benchmarks=False,  # Desactivar benchmarks para ejemplo rápido
        limit=3
    )
    
    print(f"\nDatos recolectados de {len(collected)} modelos:")
    for data in collected:
        print(f"  - {data.model_name} ({data.paper_id})")
        print(f"    Parámetros: {data.parameters.get('total_parameters', 0):,}")
        print(f"    Forward count: {data.metrics.get('forward_count', 0)}")
    
    # Agregar datos
    aggregated = manager.aggregate_collected_data()
    print(f"\nDatos agregados:")
    print(f"  Total modelos: {aggregated.total_models}")
    print(f"  Categorías: {aggregated.categories}")
    
    # Exportar
    print("\nExportando datos...")
    exported = manager.export_all(format='json', include_aggregated=True)
    print(f"Archivos exportados: {list(exported.keys())}")


def example_info_connector():
    """Ejemplo de uso del InfoConnector."""
    print("\n" + "=" * 60)
    print("Ejemplo 2: Info Connector")
    print("=" * 60)
    
    connector = InfoConnector()
    
    # Obtener mejores papers
    print("\nTop 5 papers más usados:")
    best_papers = connector.get_best_papers(top_k=5, metric='load_count')
    for i, paper in enumerate(best_papers, 1):
        print(f"  {i}. {paper['paper_name']} ({paper['category']})")
        print(f"     Cargas: {paper['load_count']}")
    
    # Buscar papers
    print("\nBuscando papers con 'reasoning':")
    results = connector.search_papers(query='reasoning')
    print(f"Encontrados {len(results)} papers:")
    for paper in results[:5]:
        print(f"  - {paper['paper_name']} ({paper['category']})")
    
    # Resumen por categoría
    print("\nResumen por categoría:")
    summary = connector.get_category_summary()
    for category, stats in summary.items():
        print(f"  {category}:")
        print(f"    Count: {stats['count']}")
        print(f"    Total loads: {stats['total_loads']}")
        print(f"    Error rate: {stats['error_rate']:.2%}")


def example_data_collector():
    """Ejemplo de uso del DataCollector."""
    print("\n" + "=" * 60)
    print("Ejemplo 3: Data Collector")
    print("=" * 60)
    
    from research.paper_malto import MALTOModule, MALTOConfig
    
    # Crear modelo
    config = MALTOConfig(hidden_dim=512)
    model = MALTOModule(config)
    
    # Recolectar datos
    collector = ModelDataCollector(include_benchmarks=False)
    data = collector.collect_model_data(
        model,
        paper_id='malto',
        category='research',
        run_benchmarks=False
    )
    
    print(f"\nDatos recolectados de {data.model_name}:")
    print(f"  Paper ID: {data.paper_id}")
    print(f"  Categoría: {data.category}")
    print(f"  Total parámetros: {data.parameters.get('total_parameters', 0):,}")
    print(f"  Parámetros entrenables: {data.parameters.get('trainable_parameters', 0):,}")
    print(f"  Forward count: {data.metrics.get('forward_count', 0)}")
    print(f"  Device: {data.metadata.get('device', 'unknown')}")
    print(f"  Training mode: {data.metadata.get('training_mode', False)}")


def example_full_report():
    """Ejemplo de generación de reporte completo."""
    print("\n" + "=" * 60)
    print("Ejemplo 4: Reporte Completo")
    print("=" * 60)
    
    manager = ModelDataManager()
    
    print("\nGenerando reporte completo...")
    report = manager.get_full_report(
        category='research',
        run_benchmarks=False,  # Desactivar para ejemplo rápido
        export_format='markdown'
    )
    
    print(f"\nReporte generado:")
    print(f"  Modelos recolectados: {report['collected_models']}")
    print(f"  Timestamp: {report['timestamp']}")
    print(f"  Archivos exportados:")
    for key, path in report['exported_files'].items():
        print(f"    {key}: {path}")


if __name__ == '__main__':
    print("Ejemplos de uso del sistema de recolección de datos de modelos\n")
    
    try:
        # Ejemplo 1: Uso básico
        example_basic_usage()
        
        # Ejemplo 2: Info Connector
        example_info_connector()
        
        # Ejemplo 3: Data Collector
        example_data_collector()
        
        # Ejemplo 4: Reporte completo
        example_full_report()
        
        print("\n" + "=" * 60)
        print("Todos los ejemplos completados exitosamente!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError en ejemplo: {e}")
        import traceback
        traceback.print_exc()



