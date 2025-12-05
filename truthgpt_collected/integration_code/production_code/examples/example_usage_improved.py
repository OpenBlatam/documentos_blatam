#!/usr/bin/env python3
"""
Ejemplo de Uso de las Mejoras Implementadas
============================================

Este script demuestra cómo usar las nuevas funcionalidades:
- Registry system
- Benchmarking
- Testing
- Cache system
"""

import torch
from core import (
    get_registry,
    BenchmarkRunner,
    compare_results,
    run_tests
)
from research.paper_malto import MALTOModule, MALTOConfig


def example_registry():
    """Ejemplo de uso del registry."""
    print("=" * 60)
    print("EJEMPLO 1: Registry System")
    print("=" * 60)
    
    registry = get_registry()
    
    # Listar papers
    print("\n📚 Papers disponibles:")
    papers = registry.list_papers(category='research')
    for paper in papers[:5]:
        print(f"  - {paper.paper_id} ({paper.category})")
    
    # Buscar papers
    print("\n🔍 Buscando papers con 'reasoning':")
    results = registry.search_papers(query='reasoning')
    for paper in results[:3]:
        print(f"  - {paper.paper_id}")
    
    # Cargar paper
    print("\n📦 Cargando paper 'malto':")
    module = registry.load_paper('malto')
    if module:
        print(f"  ✓ Módulo cargado: {module.__class__.__name__}")
    
    # Estadísticas
    print("\n📊 Estadísticas del registry:")
    stats = registry.get_statistics()
    print(f"  - Total papers: {stats['total_papers']}")
    print(f"  - Papers cargados: {stats['loaded_papers']}")
    print(f"  - Cache hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"  - Tiempo promedio de carga: {stats['avg_load_time']:.3f}s")


def example_benchmarking():
    """Ejemplo de benchmarking."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Benchmarking")
    print("=" * 60)
    
    # Crear módulo
    config = MALTOConfig(hidden_dim=512)
    module = MALTOModule(config)
    
    # Benchmark
    runner = BenchmarkRunner(device='cpu', num_runs=5)
    result = runner.benchmark(module, batch_size=2, seq_len=64)
    
    print(f"\n📈 Resultados del benchmark:")
    print(f"  - Módulo: {result.module_name}")
    print(f"  - Forward time: {result.forward_time*1000:.2f} ms")
    print(f"  - Throughput: {result.throughput:.2f} tokens/s" if result.throughput else "  - Throughput: N/A")
    print(f"  - Latency: {result.latency:.2f} ms")
    print(f"  - Std dev: {result.metadata.get('std_forward', 0)*1000:.2f} ms")


def example_testing():
    """Ejemplo de testing."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Testing")
    print("=" * 60)
    
    # Crear módulo
    config = MALTOConfig(hidden_dim=512)
    module = MALTOModule(config)
    
    # Ejecutar tests
    summary = run_tests(module, device='cpu')
    
    print(f"\n✅ Resumen de tests:")
    print(f"  - Total tests: {summary['total_tests']}")
    print(f"  - Pasados: {summary['passed']}")
    print(f"  - Fallidos: {summary['failed']}")
    print(f"  - Pass rate: {summary['pass_rate']:.2%}")
    
    print(f"\n📋 Detalles:")
    for result in summary['results']:
        status = "✓" if result['passed'] else "✗"
        print(f"  {status} {result['test']}")
        if result['error']:
            print(f"      Error: {result['error']}")


def example_cache():
    """Ejemplo de sistema de cache."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Cache System")
    print("=" * 60)
    
    # Crear módulo
    config = MALTOConfig(hidden_dim=512)
    module = MALTOModule(config)
    module.eval()
    
    # Habilitar cache
    module.enable_cache(enable=True, max_size=5)
    
    # Crear input
    hidden_states = torch.randn(2, 10, 512)
    
    # Primera llamada (sin cache)
    import time
    start = time.time()
    output1, _ = module.forward_with_cache(hidden_states)
    time1 = time.time() - start
    
    # Segunda llamada (con cache)
    start = time.time()
    output2, _ = module.forward_with_cache(hidden_states)
    time2 = time.time() - start
    
    print(f"\n⚡ Comparación de tiempos:")
    print(f"  - Primera llamada: {time1*1000:.3f} ms")
    print(f"  - Segunda llamada (cache): {time2*1000:.3f} ms")
    print(f"  - Speedup: {time1/time2:.2f}x")
    
    # Estadísticas de cache
    cache_stats = module.get_cache_stats()
    print(f"\n📊 Estadísticas de cache:")
    print(f"  - Cache habilitado: {cache_stats['cache_enabled']}")
    print(f"  - Tamaño actual: {cache_stats['cache_size']}")
    print(f"  - Tamaño máximo: {cache_stats['max_cache_size']}")


def example_gradient_checkpointing():
    """Ejemplo de gradient checkpointing."""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Gradient Checkpointing")
    print("=" * 60)
    
    # Crear módulo
    config = MALTOConfig(hidden_dim=512)
    module = MALTOModule(config)
    module.train()
    
    # Habilitar gradient checkpointing
    module.enable_gradient_checkpointing(enable=True)
    
    # Forward y backward
    hidden_states = torch.randn(2, 10, 512, requires_grad=True)
    output, _ = module(hidden_states)
    loss = output.mean()
    loss.backward()
    
    print(f"\n💾 Gradient checkpointing habilitado")
    print(f"  - Output shape: {output.shape}")
    print(f"  - Gradiente calculado: {hidden_states.grad is not None}")


if __name__ == "__main__":
    print("\n🚀 EJEMPLOS DE USO DE MEJORAS IMPLEMENTADAS\n")
    
    try:
        example_registry()
    except Exception as e:
        print(f"Error en ejemplo registry: {e}")
    
    try:
        example_benchmarking()
    except Exception as e:
        print(f"Error en ejemplo benchmarking: {e}")
    
    try:
        example_testing()
    except Exception as e:
        print(f"Error en ejemplo testing: {e}")
    
    try:
        example_cache()
    except Exception as e:
        print(f"Error en ejemplo cache: {e}")
    
    try:
        example_gradient_checkpointing()
    except Exception as e:
        print(f"Error en ejemplo gradient checkpointing: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados")
    print("=" * 60)


