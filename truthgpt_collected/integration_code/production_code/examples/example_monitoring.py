#!/usr/bin/env python3
"""
Ejemplo de Uso del Sistema de Monitoreo
========================================

Demuestra cómo usar el sistema de monitoreo y métricas.
"""

import time
import torch
from monitoring_system import (
    SystemMonitor,
    MetricsCollector,
    HealthMonitor,
    MetricType,
    get_system_monitor
)


def example_metrics_collection():
    """Ejemplo de recolección de métricas."""
    print("=" * 60)
    print("Ejemplo 1: Recolección de Métricas")
    print("=" * 60)
    
    collector = MetricsCollector()
    
    # Contadores
    collector.increment("requests.total")
    collector.increment("requests.total", 5)
    collector.increment("requests.success")
    
    # Gauges
    collector.set_gauge("memory.usage", 0.75)
    collector.set_gauge("cpu.usage", 0.45)
    
    # Histogramas
    for i in range(10):
        collector.record_histogram("response.time", 0.1 + i * 0.05)
    
    # Timers
    start = time.time()
    time.sleep(0.1)
    collector.record_timer("operation.duration", time.time() - start)
    
    # Obtener resumen
    summary = collector.get_metric_summary("requests.total")
    print(f"Requests total: {summary}")
    
    all_metrics = collector.get_all_metrics()
    print(f"Total métricas: {all_metrics['total_metrics']}")


def example_health_checks():
    """Ejemplo de health checks."""
    print("\n" + "=" * 60)
    print("Ejemplo 2: Health Checks")
    print("=" * 60)
    
    monitor = get_system_monitor()
    
    # Ejecutar health checks
    health = monitor.health_monitor.check_all()
    
    for module, check in health.items():
        print(f"{module}: {check.status} - {check.message}")
    
    # Salud general
    overall = monitor.health_monitor.get_overall_health()
    print(f"\nSalud general: {overall['status']}")
    print(f"Salud: {overall['health_percentage']:.1f}%")


def example_system_status():
    """Ejemplo de estado del sistema."""
    print("\n" + "=" * 60)
    print("Ejemplo 3: Estado del Sistema")
    print("=" * 60)
    
    monitor = get_system_monitor()
    
    # Registrar algunas métricas
    monitor.metrics_collector.increment("operations.total")
    monitor.metrics_collector.set_gauge("system.load", 0.6)
    
    # Obtener estado completo
    status = monitor.get_system_status()
    
    print(f"Timestamp: {status['timestamp']}")
    print(f"Health: {status['health']['status']}")
    print(f"Total métricas: {status['metrics']['total_metrics']}")


def example_export():
    """Ejemplo de exportación."""
    print("\n" + "=" * 60)
    print("Ejemplo 4: Exportación")
    print("=" * 60)
    
    monitor = get_system_monitor()
    
    # Registrar métricas
    for i in range(5):
        monitor.metrics_collector.increment("test.counter")
        monitor.metrics_collector.set_gauge("test.gauge", i * 0.1)
    
    # Exportar métricas
    monitor.metrics_collector.export_metrics("metrics_export.json")
    print("Métricas exportadas")
    
    # Exportar reporte
    monitor.export_report("system_report.json")
    print("Reporte exportado")


def example_visualization():
    """Ejemplo de visualización."""
    print("\n" + "=" * 60)
    print("Ejemplo 5: Visualización")
    print("=" * 60)
    
    monitor = get_system_monitor()
    
    # Registrar métricas para visualizar
    for i in range(10):
        monitor.metrics_collector.increment(f"module{i}.requests")
        monitor.metrics_collector.set_gauge(f"module{i}.usage", i * 0.1)
    
    # Visualizar
    try:
        monitor.visualize_metrics("metrics_visualization.png")
        print("Visualización guardada")
    except Exception as e:
        print(f"Visualización no disponible: {e}")


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("Ejemplos del Sistema de Monitoreo")
    print("=" * 60 + "\n")
    
    try:
        example_metrics_collection()
        example_health_checks()
        example_system_status()
        example_export()
        example_visualization()
        
        print("\n" + "=" * 60)
        print("✅ Todos los ejemplos completados!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

