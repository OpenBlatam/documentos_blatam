#!/usr/bin/env python3
"""
Ejemplos Avanzados de Uso de las Nuevas Funcionalidades
========================================================

Este script demuestra el uso de:
- Profiling
- Monitoreo
- Manejo de errores mejorado
"""

import torch
import time
from core import (
    get_registry,
    Profiler,
    profile_module,
    MetricsCollector,
    create_default_health_checks,
    retry,
    RetryStrategy,
    safe_execute,
    ErrorHandler
)
from research.paper_malto import MALTOModule, MALTOConfig


def example_profiling():
    """Ejemplo de profiling."""
    print("=" * 60)
    print("EJEMPLO 1: Profiling")
    print("=" * 60)
    
    config = MALTOConfig(hidden_dim=512)
    module = MALTOModule(config)
    hidden_states = torch.randn(2, 10, 512)
    
    # Profiling de módulo completo
    print("\n📊 Profiling de módulo completo:")
    results = profile_module(module, hidden_states, num_runs=5)
    
    print(f"  - Módulo: {results['module_name']}")
    print(f"  - Total tiempo: {results['summary']['total_time']:.4f}s")
    print(f"  - Tiempo promedio por llamada: {results['summary']['avg_time_per_call']:.4f}s")
    
    print("\n  Top funciones:")
    for func in results['summary']['top_functions'][:3]:
        print(f"    - {func['name']}: {func['total_time']:.4f}s ({func['calls']} calls)")
    
    # Profiling manual
    print("\n🔍 Profiling manual:")
    profiler = Profiler()
    profiler.start()
    
    @profiler.profile
    def expensive_operation(x):
        return x * 2
    
    for _ in range(10):
        expensive_operation(torch.randn(100, 100))
    
    with profiler.profile_context('batch_processing'):
        time.sleep(0.01)
    
    profiler.stop()
    
    summary = profiler.get_summary()
    print(f"  - Total funciones: {summary['total_functions']}")
    print(f"  - Total tiempo: {summary['total_time']:.4f}s")


def example_monitoring():
    """Ejemplo de monitoreo."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Monitoreo")
    print("=" * 60)
    
    # Metrics Collector
    print("\n📈 Metrics Collector:")
    collector = MetricsCollector()
    
    config = MALTOConfig(hidden_dim=512)
    module = MALTOModule(config)
    hidden_states = torch.randn(2, 10, 512)
    
    # Simular varias ejecuciones
    for i in range(5):
        start = time.time()
        output, metadata = module(hidden_states)
        elapsed = time.time() - start
        
        collector.record('forward_time', elapsed, tags={'batch': str(i)})
        collector.increment('requests_total')
        collector.set_gauge('memory_usage', 512.0 + i * 10)
    
    # Obtener métricas
    summary = collector.get_summary()
    print(f"  - Total métricas: {summary['total_metrics']}")
    print(f"  - Contadores: {summary['counters']}")
    print(f"  - Gauges: {summary['gauges']}")
    
    # Health Monitor
    print("\n🏥 Health Monitor:")
    monitor = create_default_health_checks()
    
    health = monitor.get_overall_health(module)
    print(f"  - Estado general: {health.status}")
    print(f"  - Mensaje: {health.message}")
    print(f"  - Detalles: {health.details}")


def example_error_handling():
    """Ejemplo de manejo de errores."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Manejo de Errores")
    print("=" * 60)
    
    # Retry con exponential backoff
    print("\n🔄 Retry con exponential backoff:")
    
    attempt_count = 0
    
    @retry(
        max_attempts=3,
        delay=0.1,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=(ValueError,)
    )
    def risky_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Intento {attempt_count} falló")
        return "Éxito"
    
    try:
        result = risky_operation()
        print(f"  - Resultado: {result}")
        print(f"  - Intentos: {attempt_count}")
    except Exception as e:
        print(f"  - Error final: {e}")
    
    # Safe execute
    print("\n🛡️ Safe execute:")
    
    def may_fail(x):
        if x < 0:
            raise ValueError("x debe ser positivo")
        return x * 2
    
    result, error = safe_execute(may_fail, default_value=0, x=-5)
    print(f"  - Resultado: {result}")
    print(f"  - Error: {error}")
    
    result, error = safe_execute(may_fail, default_value=0, x=5)
    print(f"  - Resultado: {result}")
    print(f"  - Error: {error}")
    
    # Error Handler
    print("\n🔧 Error Handler:")
    
    handler = ErrorHandler()
    
    def handle_value_error(exc, context):
        print(f"    Manejando ValueError: {exc}")
        return "valor por defecto"
    
    def handle_generic(exc, context):
        print(f"    Manejando error genérico: {exc}")
        return None
    
    handler.register_handler(ValueError, handle_value_error)
    handler.set_default_handler(handle_generic)
    
    result = handler.handle(ValueError("test error"), context={'module': 'test'})
    print(f"  - Resultado del handler: {result}")


def example_integrated():
    """Ejemplo integrado de todas las funcionalidades."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Uso Integrado")
    print("=" * 60)
    
    # Configurar
    collector = MetricsCollector()
    monitor = create_default_health_checks()
    profiler = Profiler()
    
    # Cargar módulo
    registry = get_registry()
    module = registry.load_paper('malto')
    
    if not module:
        print("  ⚠️ No se pudo cargar el módulo")
        return
    
    # Health check
    health = monitor.get_overall_health(module)
    print(f"\n🏥 Health Check: {health.status}")
    
    # Profiling
    profiler.start()
    hidden_states = torch.randn(2, 10, 512)
    
    # Ejecutar con monitoreo
    for i in range(3):
        with profiler.profile_context('forward'):
            start = time.time()
            output, metadata = module(hidden_states)
            elapsed = time.time() - start
            
            collector.record('forward_time', elapsed)
            collector.increment('requests_total')
    
    profiler.stop()
    
    # Resultados
    print("\n📊 Resultados:")
    print(f"  - Métricas: {collector.get_summary()['total_metrics']} métricas")
    print(f"  - Profiling: {len(profiler.get_results())} funciones perfiladas")
    
    top_func = profiler.get_results('total_time')[0] if profiler.get_results() else None
    if top_func:
        print(f"  - Función más costosa: {top_func.function_name} ({top_func.total_time:.4f}s)")


if __name__ == "__main__":
    print("\n🚀 EJEMPLOS AVANZADOS DE USO\n")
    
    try:
        example_profiling()
    except Exception as e:
        print(f"Error en ejemplo profiling: {e}")
    
    try:
        example_monitoring()
    except Exception as e:
        print(f"Error en ejemplo monitoring: {e}")
    
    try:
        example_error_handling()
    except Exception as e:
        print(f"Error en ejemplo error handling: {e}")
    
    try:
        example_integrated()
    except Exception as e:
        print(f"Error en ejemplo integrado: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados")
    print("=" * 60)


