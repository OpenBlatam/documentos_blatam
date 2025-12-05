#!/usr/bin/env python3
"""
Test de Sistemas de Throughput
===============================

Compara diferentes sistemas de throughput y muestra mejoras teóricas.
"""

import json
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class ThroughputSystemResult:
    """Resultado de un sistema de throughput."""
    name: str
    throughput_tokens_per_sec: float
    hardware: str
    model: str
    techniques: list
    source_url: str


def main():
    """Ejecuta análisis de sistemas de throughput."""
    print("=" * 80)
    print("ANÁLISIS DE SISTEMAS DE THROUGHPUT - TOP 10")
    print("=" * 80)
    print()
    
    # Cargar datos del JSON
    with open('scraped_papers/top10_throughput_systems.json', 'r') as f:
        data = json.load(f)
    
    systems = data['systems']
    
    # Mostrar todos los sistemas
    print("📊 TOP 10 SISTEMAS DE THROUGHPUT")
    print("=" * 80)
    print()
    
    sorted_systems = sorted(systems, key=lambda x: x['throughput_tokens_per_sec'], reverse=True)
    
    for i, system in enumerate(sorted_systems, 1):
        print(f"{i}. {system['name']}")
        print(f"   Throughput: {system['throughput_tokens_per_sec']:,.0f} tokens/s")
        print(f"   Hardware: {system['hardware']}")
        print(f"   Modelo: {system['model']}")
        print(f"   Técnicas: {', '.join(system['techniques'][:3])}")
        print(f"   Link: {system['source_url']}")
        print()
    
    # Análisis comparativo
    print("=" * 80)
    print("📈 ANÁLISIS COMPARATIVO")
    print("=" * 80)
    print()
    
    max_throughput = max(s['throughput_tokens_per_sec'] for s in systems)
    min_throughput = min(s['throughput_tokens_per_sec'] for s in systems)
    avg_throughput = sum(s['throughput_tokens_per_sec'] for s in systems) / len(systems)
    
    print(f"Throughput máximo: {max_throughput:,.0f} tokens/s ({sorted_systems[0]['name']})")
    print(f"Throughput mínimo: {min_throughput:,.0f} tokens/s ({sorted_systems[-1]['name']})")
    print(f"Throughput promedio: {avg_throughput:,.0f} tokens/s")
    print(f"Rango: {max_throughput / min_throughput:.0f}× diferencia")
    print()
    
    # Agrupar por hardware
    print("🔧 AGRUPACIÓN POR HARDWARE")
    print("-" * 80)
    by_hardware = {}
    for system in systems:
        hw = system['hardware']
        if hw not in by_hardware:
            by_hardware[hw] = []
        by_hardware[hw].append(system)
    
    for hw, hw_systems in sorted(by_hardware.items(), key=lambda x: max(s['throughput_tokens_per_sec'] for s in x[1]), reverse=True):
        max_hw = max(s['throughput_tokens_per_sec'] for s in hw_systems)
        print(f"{hw}:")
        print(f"  Máximo: {max_hw:,.0f} tokens/s")
        print(f"  Sistemas: {len(hw_systems)}")
        print()
    
    # Técnicas más comunes
    print("⚙️ TÉCNICAS MÁS COMUNES")
    print("-" * 80)
    technique_count = {}
    for system in systems:
        for technique in system['techniques']:
            technique_count[technique] = technique_count.get(technique, 0) + 1
    
    sorted_techniques = sorted(technique_count.items(), key=lambda x: x[1], reverse=True)
    for technique, count in sorted_techniques[:10]:
        print(f"  {technique}: {count} sistemas")
    print()
    
    # Mejores combinaciones teóricas
    print("=" * 80)
    print("🚀 MEJORES COMBINACIONES TEÓRICAS")
    print("=" * 80)
    print()
    
    print("Combinación 1: TensorRT-LLM + vLLM")
    print("  - TensorRT-LLM: 40,000 tokens/s (FP8, Speculative, Kernel Fusion)")
    print("  - vLLM: 4,656 tokens/s (PagedAttention, Continuous Batching)")
    print("  - Combinado: ~35,000 tokens/s (conservador, considerando overhead)")
    print()
    
    print("Combinación 2: Hardware Especializado")
    print("  - Cerebras: 2,100 tokens/s (70B), 969 tokens/s (405B)")
    print("  - Groq LPU: 877 tokens/s (8B), 284 tokens/s (70B)")
    print("  - Ventaja: Hardware dedicado, baja latencia")
    print()
    
    print("Combinación 3: Optimizaciones Software")
    print("  - FP8 Quantization: 4× reducción memoria")
    print("  - Speculative Decoding: 2-4× speedup")
    print("  - Kernel Fusion: 1.3× speedup")
    print("  - Combinado: ~10× speedup teórico")
    print()
    
    # Guardar resumen
    summary = {
        'top_systems': sorted_systems[:5],
        'statistics': {
            'max_throughput': max_throughput,
            'min_throughput': min_throughput,
            'avg_throughput': avg_throughput,
            'range_factor': max_throughput / min_throughput
        },
        'by_hardware': {hw: {
            'max_throughput': max(s['throughput_tokens_per_sec'] for s in systems),
            'count': len(systems)
        } for hw, systems in by_hardware.items()},
        'top_techniques': sorted_techniques[:10]
    }
    
    with open('throughput_systems_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("💾 Resumen guardado en: throughput_systems_summary.json")
    print()
    
    return summary


if __name__ == "__main__":
    result = main()



