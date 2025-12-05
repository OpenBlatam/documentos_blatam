#!/usr/bin/env python3
"""
Ejemplo de Uso del Sistema de Análisis y Visualización
=======================================================

Este script demuestra cómo usar las nuevas utilidades de análisis,
visualización y optimización de rendimiento.
"""

import torch
from pathlib import Path

from core import (
    ModuleAnalyzer,
    analyze_forward_pass,
    compute_flops,
    generate_module_report,
    generate_comparison_report,
    visualize_architecture,
    PerformanceMonitor,
    optimize_for_inference,
    compile_module,
    profile_memory
)


def example_module_analysis():
    """Ejemplo: Análisis completo de un módulo."""
    print("=" * 60)
    print("EJEMPLO 1: Análisis de Módulo")
    print("=" * 60)
    
    # Importar un módulo de ejemplo
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        analyzer = ModuleAnalyzer()
        analysis = analyzer.analyze_module(module)
        
        print(f"\n📊 Análisis de {analysis.module_name}:")
        print(f"  - Total parámetros: {analysis.total_parameters:,}")
        print(f"  - Parámetros entrenables: {analysis.trainable_parameters:,}")
        print(f"  - Memoria total: {analysis.memory_total_mb:.2f} MB")
        print(f"  - Número de capas: {analysis.layer_count}")
        print(f"  - Tipos de capas: {analysis.architecture_summary['layer_types']}")
        
        # Encontrar cuellos de botella
        bottlenecks = analyzer.find_bottlenecks(module)
        if bottlenecks:
            print(f"\n⚠️ Cuellos de botella encontrados:")
            for bottleneck in bottlenecks[:5]:
                print(f"  - {bottleneck.name}: {bottleneck.parameters:,} params")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_forward_analysis():
    """Ejemplo: Análisis de forward pass."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Análisis de Forward Pass")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        hidden_states = torch.randn(2, 128, 512)
        
        forward_analysis = analyze_forward_pass(module, hidden_states)
        
        print(f"\n📊 Análisis de Forward Pass:")
        print(f"  - Input shape: {forward_analysis['input_shape']}")
        print(f"  - Output shape: {forward_analysis['output_shape']}")
        print(f"  - Número de activaciones: {forward_analysis['num_activations']}")
        
        # Mostrar algunas activaciones
        activations = forward_analysis['activations']
        print(f"\n📈 Primeras activaciones:")
        for i, (name, info) in enumerate(list(activations.items())[:3]):
            print(f"  - {name}:")
            print(f"      Shape: {info['shape']}")
            print(f"      Mean: {info['mean']:.4f}, Std: {info['std']:.4f}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_flops_computation():
    """Ejemplo: Cálculo de FLOPs."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Cálculo de FLOPs")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        flops = compute_flops(module, input_shape=(1, 128, 512))
        
        print(f"\n📊 FLOPs:")
        print(f"  - FLOPs: {flops.get('flops_formatted', 'N/A')}")
        print(f"  - Parámetros: {flops.get('parameters_formatted', 'N/A')}")
        if 'flops_per_parameter' in flops:
            print(f"  - FLOPs por parámetro: {flops['flops_per_parameter']:.2f}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_report_generation():
    """Ejemplo: Generación de reportes."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Generación de Reportes")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        # Generar reporte individual
        report_path = Path('module_report.md')
        report = generate_module_report(module, report_path, format='markdown')
        print(f"\n✓ Reporte generado: {report_path}")
        print(f"  Tamaño: {len(report)} caracteres")
        
        # Visualizar arquitectura
        arch_path = Path('architecture.txt')
        arch = visualize_architecture(module, arch_path)
        print(f"\n✓ Arquitectura guardada: {arch_path}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_performance_monitoring():
    """Ejemplo: Monitoreo de rendimiento."""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Monitoreo de Rendimiento")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        hidden_states = torch.randn(2, 128, 512)
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        with monitor.measure('forward'):
            output, _ = module(hidden_states)
        
        with monitor.measure('forward_with_cache'):
            output, _ = module.forward_with_cache(hidden_states)
        
        monitor.stop()
        
        summary = monitor.get_summary()
        print(f"\n📊 Resumen de Rendimiento:")
        print(f"  - Total operaciones: {summary['total_operations']}")
        for op_name, op_stats in summary['operations'].items():
            print(f"\n  {op_name}:")
            print(f"    - Count: {op_stats['count']}")
            print(f"    - Avg time: {op_stats['avg_time']*1000:.2f} ms")
            print(f"    - Min time: {op_stats['min_time']*1000:.2f} ms")
            print(f"    - Max time: {op_stats['max_time']*1000:.2f} ms")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_optimization():
    """Ejemplo: Optimización de módulos."""
    print("\n" + "=" * 60)
    print("EJEMPLO 6: Optimización de Módulos")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        hidden_states = torch.randn(2, 128, 512)
        
        print("\n📊 Optimización para inferencia:")
        optimize_for_inference(module)
        print("  ✓ Módulo optimizado")
        
        print("\n📊 Compilación:")
        compiled = compile_module(module, mode='default')
        print("  ✓ Módulo compilado")
        
        if torch.cuda.is_available():
            print("\n📊 Perfilado de memoria:")
            memory_info = profile_memory(module, hidden_states, device='cuda')
            if memory_info.get('available'):
                print(f"  - Memoria inicial: {memory_info['initial_mb']:.2f} MB")
                print(f"  - Memoria pico: {memory_info['peak_mb']:.2f} MB")
                print(f"  - Memoria usada: {memory_info['used_mb']:.2f} MB")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


if __name__ == "__main__":
    print("\n🚀 EJEMPLOS DE ANÁLISIS Y VISUALIZACIÓN\n")
    
    try:
        example_module_analysis()
    except Exception as e:
        print(f"Error en ejemplo 1: {e}")
    
    try:
        example_forward_analysis()
    except Exception as e:
        print(f"Error en ejemplo 2: {e}")
    
    try:
        example_flops_computation()
    except Exception as e:
        print(f"Error en ejemplo 3: {e}")
    
    try:
        example_report_generation()
    except Exception as e:
        print(f"Error en ejemplo 4: {e}")
    
    try:
        example_performance_monitoring()
    except Exception as e:
        print(f"Error en ejemplo 5: {e}")
    
    try:
        example_optimization()
    except Exception as e:
        print(f"Error en ejemplo 6: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados")
    print("=" * 60)


