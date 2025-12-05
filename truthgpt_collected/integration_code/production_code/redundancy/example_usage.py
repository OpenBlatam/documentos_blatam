#!/usr/bin/env python3
"""
Ejemplos de Uso del Módulo de Redundancia
==========================================

Ejemplos prácticos de cómo usar los sistemas de supresión de redundancia.
"""

import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from redundancy import (
    create_redundancy_suppressor,
    Paper2510_00071Config,
    Paper2510_00071_RedundancySuppressor,
    compute_similarity_batch,
    find_duplicate_items,
    batch_deduplicate,
    calculate_reduction_stats,
    compare_redundancy_methods,
    optimize_threshold,
    RedundancyAnalytics,
    RedundancyOptimizer,
    RedundancyExporter
)


def example_1_basic_usage():
    """Ejemplo 1: Uso básico del supresor de redundancia."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Uso Básico")
    print("="*60)
    
    config = Paper2510_00071Config(
        similarity_threshold=0.85,
        redundancy_detection_method="cosine",
        bulk_processing_batch_size=1000
    )
    
    suppressor = Paper2510_00071_RedundancySuppressor(config)
    
    batch_size, seq_len, hidden_dim = 20, 32, 512
    items = torch.randn(batch_size, seq_len, hidden_dim)
    
    unique_items, stats = suppressor.process_bulk(items)
    
    print(f"Items originales: {batch_size}")
    print(f"Items únicos: {unique_items.size(0)}")
    print(f"Reducción: {stats['reduction_rate']:.2%}")
    print(f"Clusters: {stats['num_clusters']}")
    print(f"Tamaño promedio de cluster: {stats['avg_cluster_size']:.2f}")


def example_2_factory_function():
    """Ejemplo 2: Usando la función factory."""
    print("\n" + "="*60)
    print("EJEMPLO 2: Función Factory")
    print("="*60)
    
    suppressor = create_redundancy_suppressor(
        "2510_00071",
        similarity_threshold=0.8,
        redundancy_detection_method="cosine",
        use_hierarchical_clustering=True
    )
    
    if suppressor:
        items = torch.randn(15, 32, 512)
        unique_items, stats = suppressor.process_bulk(items)
        
        print(f"✅ Supresor creado exitosamente")
        print(f"Reducción: {stats['reduction_rate']:.2%}")
    else:
        print("❌ Error creando supresor")


def example_3_utility_functions():
    """Ejemplo 3: Usando funciones de utilidad."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Funciones de Utilidad")
    print("="*60)
    
    items = torch.randn(10, 32, 512)
    
    duplicates = find_duplicate_items(items, threshold=0.85, method="cosine")
    print(f"Duplicados encontrados: {len(duplicates)}")
    for idx1, idx2, sim in duplicates[:5]:
        print(f"  Items {idx1} y {idx2}: similitud {sim:.3f}")
    
    unique_items, stats = batch_deduplicate(items, threshold=0.85)
    print(f"\nDeduplicación:")
    print(f"  Original: {stats['original_size']}")
    print(f"  Único: {stats['unique_size']}")
    print(f"  Reducción: {stats['reduction_rate']:.2%}")


def example_4_method_comparison():
    """Ejemplo 4: Comparación de métodos."""
    print("\n" + "="*60)
    print("EJEMPLO 4: Comparación de Métodos")
    print("="*60)
    
    items = torch.randn(20, 32, 512)
    
    results = compare_redundancy_methods(items, threshold=0.85)
    
    for method, result in results.items():
        if 'error' not in result:
            print(f"\n{method.upper()}:")
            print(f"  Reducción: {result['stats']['reduction_rate']:.2%}")
            print(f"  Tiempo: {result['processing_time']:.4f}s")
            print(f"  Items únicos: {result['unique_size']}")


def example_5_threshold_optimization():
    """Ejemplo 5: Optimización de threshold."""
    print("\n" + "="*60)
    print("EJEMPLO 5: Optimización de Threshold")
    print("="*60)
    
    items = torch.randn(30, 32, 512)
    
    result = optimize_threshold(
        items,
        method="cosine",
        target_reduction_rate=0.3,
        threshold_range=(0.7, 0.95),
        num_samples=15
    )
    
    if 'optimal_threshold' in result:
        print(f"Threshold óptimo: {result['optimal_threshold']:.3f}")
        print(f"Tasa de reducción lograda: {result['achieved_reduction_rate']:.2%}")
        print(f"Tasa objetivo: {result['target_reduction_rate']:.2%}")
        print(f"Error: {result['error']:.4f}")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")


def example_6_analytics():
    """Ejemplo 6: Sistema de analytics."""
    print("\n" + "="*60)
    print("EJEMPLO 6: Analytics")
    print("="*60)
    
    analytics = RedundancyAnalytics()
    config = Paper2510_00071Config(similarity_threshold=0.85)
    suppressor = Paper2510_00071_RedundancySuppressor(config)
    
    import time
    
    for i in range(5):
        items = torch.randn(15, 32, 512)
        
        start_time = time.time()
        unique_items, stats = suppressor.process_bulk(items)
        processing_time = time.time() - start_time
        
        analytics.record_batch(
            items.size(0),
            unique_items.size(0),
            processing_time,
            method="cosine"
        )
    
    summary = analytics.get_summary()
    print(f"Total procesado: {summary['metrics']['total_processed']}")
    print(f"Total reducido: {summary['metrics']['total_reduced']}")
    print(f"Tasa promedio de reducción: {summary['metrics']['avg_reduction_rate']:.2%}")
    print(f"Eficiencia: {summary['metrics']['efficiency']:.2f}%")
    print(f"Batches procesados: {summary['total_batches']}")


def example_7_optimizer():
    """Ejemplo 7: Optimizador de parámetros."""
    print("\n" + "="*60)
    print("EJEMPLO 7: Optimizador")
    print("="*60)
    
    config = Paper2510_00071Config(similarity_threshold=0.85)
    suppressor = Paper2510_00071_RedundancySuppressor(config)
    optimizer = RedundancyOptimizer(suppressor)
    
    sample_items = torch.randn(25, 32, 512)
    
    result = optimizer.optimize_threshold(
        sample_items,
        target_reduction_rate=0.3,
        threshold_range=(0.7, 0.95)
    )
    
    if 'optimal_threshold' in result:
        print(f"Threshold optimizado: {result['optimal_threshold']:.3f}")
        print(f"Nuevo threshold del supresor: {suppressor.similarity_threshold:.3f}")


def example_8_export():
    """Ejemplo 8: Exportación de datos."""
    print("\n" + "="*60)
    print("EJEMPLO 8: Exportación")
    print("="*60)
    
    config = Paper2510_00071Config(similarity_threshold=0.85)
    suppressor = Paper2510_00071_RedundancySuppressor(config)
    
    items = torch.randn(20, 32, 512)
    unique_items, stats = suppressor.process_bulk(items)
    
    metrics = suppressor.get_metrics()
    
    export_data = {
        'stats': stats,
        'metrics': metrics,
        'config': {
            'similarity_threshold': config.similarity_threshold,
            'detection_method': config.redundancy_detection_method
        }
    }
    
    output_path = "/tmp/redundancy_report.json"
    success = RedundancyExporter.export_to_json(export_data, output_path)
    
    if success:
        print(f"✅ Reporte exportado a {output_path}")
    else:
        print("❌ Error exportando reporte")


def example_9_monitoring():
    """Ejemplo 9: Monitoreo y observabilidad."""
    print("\n" + "="*60)
    print("EJEMPLO 9: Monitoreo")
    print("="*60)
    
    try:
        from redundancy import create_redundancy_monitor, RedundancyMonitor
        
        config = Paper2510_00071Config(similarity_threshold=0.85)
        suppressor = Paper2510_00071_RedundancySuppressor(config)
        
        monitor = create_redundancy_monitor(suppressor, enable_monitoring=True)
        
        if monitor:
            items = torch.randn(20, 32, 512)
            unique_items, stats = suppressor.process_bulk(items)
            
            monitor.record_processing(
                original_size=stats['original_size'],
                reduced_size=stats['reduced_size'],
                processing_time=0.5,
                success=True
            )
            
            health = monitor.get_health_check()
            if health:
                print(f"✅ Health Status: {health.status}")
                print(f"   Message: {health.message}")
            
            summary = monitor.get_metrics_summary()
            print(f"✅ Métricas: {summary.get('processed_count', 0)} procesados")
        else:
            print("⚠️ Monitoreo no disponible")
    except ImportError:
        print("⚠️ Módulo de monitoreo no disponible")


def example_10_config_profiles():
    """Ejemplo 10: Perfiles de configuración."""
    print("\n" + "="*60)
    print("EJEMPLO 10: Perfiles de Configuración")
    print("="*60)
    
    try:
        from redundancy import (
            PerformanceProfile,
            RedundancyConfigProfile,
            RedundancyConfigManager,
            create_config_from_profile,
            get_recommended_profile
        )
        
        print("📋 Perfiles disponibles:")
        profiles = RedundancyConfigProfile.list_profiles()
        for profile in profiles:
            print(f"   - {profile}")
        
        print("\n🔧 Crear configuración desde perfil:")
        speed_config = create_config_from_profile(PerformanceProfile.SPEED)
        print(f"   Speed profile threshold: {speed_config['similarity_threshold']}")
        
        print("\n🎯 Recomendación de perfil:")
        recommended = get_recommended_profile("speed", data_size=10000)
        print(f"   Perfil recomendado: {recommended.value}")
        
        print("\n⚙️ Gestor de configuración:")
        config_manager = RedundancyConfigManager()
        config_manager.load_profile(PerformanceProfile.QUALITY)
        current = config_manager.get_config()
        print(f"   Threshold actual: {current['similarity_threshold']}")
        
        config_manager.update_config({'similarity_threshold': 0.90})
        updated = config_manager.get_config()
        print(f"   Threshold actualizado: {updated['similarity_threshold']}")
        
        print("✅ Perfiles de configuración funcionando")
    except ImportError:
        print("⚠️ Módulo de configuración no disponible")


def example_11_debugging():
    """Ejemplo 11: Utilidades de debugging."""
    print("\n" + "="*60)
    print("EJEMPLO 11: Debugging")
    print("="*60)
    
    try:
        from redundancy import RedundancyDebugger, create_redundancy_debugger
        
        debugger = create_redundancy_debugger(enabled=True)
        
        print("🔍 Debugging habilitado")
        
        def test_operation():
            import time
            time.sleep(0.1)
            return "result"
        
        result = debugger.time_operation("test_operation", test_operation)
        print(f"   Resultado: {result}")
        
        stats = debugger.get_operation_stats()
        print(f"   Operaciones registradas: {stats['total_operations']}")
        print(f"   Errores: {stats['total_errors']}")
        
        recent = debugger.get_recent_operations(5)
        print(f"   Operaciones recientes: {len(recent)}")
        
        print("✅ Debugging funcionando")
    except ImportError:
        print("⚠️ Módulo de debugging no disponible")


def example_12_alerts():
    """Ejemplo 12: Sistema de alertas."""
    print("\n" + "="*60)
    print("EJEMPLO 12: Sistema de Alertas")
    print("="*60)
    
    try:
        from redundancy import (
            RedundancyAlertSystem,
            AlertLevel,
            create_redundancy_alert_system
        )
        
        alert_system = create_redundancy_alert_system()
        
        print("🚨 Sistema de alertas inicializado")
        
        context = {
            'error_rate': 0.15,
            'reduction_rate': 0.03,
            'processing_time': 6.0,
            'cache_hit_rate': 0.25
        }
        
        alerts = alert_system.check_alerts(context)
        print(f"   Alertas generadas: {len(alerts)}")
        
        for alert in alerts:
            print(f"   - [{alert.level.value}] {alert.message}")
        
        summary = alert_system.get_alert_summary()
        print(f"   Total alertas: {summary['total_alerts']}")
        print(f"   Alertas activas: {summary['active_alerts']}")
        
        print("✅ Sistema de alertas funcionando")
    except ImportError:
        print("⚠️ Módulo de alertas no disponible")


if __name__ == "__main__":
    print("Ejemplos de Uso del Módulo de Redundancia")
    print("=" * 60)
    
    try:
        example_1_basic_usage()
        example_2_factory_function()
        example_3_utility_functions()
        example_4_method_comparison()
        example_5_threshold_optimization()
        example_6_analytics()
        example_7_optimizer()
        example_8_export()
        example_9_monitoring()
        example_10_config_profiles()
        example_11_debugging()
        example_12_alerts()
        
        print("\n" + "="*60)
        print("✅ Todos los ejemplos completados")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {e}")
        import traceback
        traceback.print_exc()

