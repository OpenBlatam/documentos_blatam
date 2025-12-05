#!/usr/bin/env python3
"""
Extractor de Top 10 Sistemas de Throughput para LLMs
======================================================

Extrae información de los sistemas con mayor throughput reportado
y genera JSON con toda la información técnica.
"""

import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ThroughputSystem:
    """Información de un sistema de throughput."""
    name: str
    throughput_tokens_per_sec: float
    model: str
    hardware: str
    setup: str
    source: str
    source_url: str
    techniques: List[str]
    notes: str
    benchmark_type: str  # "output_tokens", "total_tokens", "tps_per_user"
    year: int


def extract_throughput_systems() -> List[ThroughputSystem]:
    """Extrae información de los sistemas de throughput."""
    
    systems = [
        ThroughputSystem(
            name="TensorRT-LLM (Llama 4 on B200)",
            throughput_tokens_per_sec=40000.0,
            model="Llama-4",
            hardware="NVIDIA B200 (Blackwell)",
            setup="TensorRT-LLM optimizations + speculative decoding",
            source="NVIDIA / TensorRT-LLM GitHub",
            source_url="https://github.com/NVIDIA/TensorRT-LLM",
            techniques=[
                "TensorRT-LLM optimizations",
                "Speculative decoding",
                "FP8 quantization",
                "Kernel fusion",
                "Blackwell architecture"
            ],
            notes="NVIDIA publica cifras de >40k tokens/s para Llama-4 en una B200 (Blackwell) con sus optimizaciones y speculative decoding",
            benchmark_type="output_tokens",
            year=2025
        ),
        ThroughputSystem(
            name="Cerebrium/TensorRT (H100)",
            throughput_tokens_per_sec=19000.0,
            model="Llama-family (small)",
            hardware="NVIDIA H100",
            setup="FP8 + optimizations + batching + speculative",
            source="Cerebrium/TensorRT tutorials",
            source_url="https://www.cerebrium.ai",
            techniques=[
                "FP8 quantization",
                "Speculative decoding",
                "Batching optimizations",
                "TensorRT optimizations"
            ],
            notes="Ejemplo práctico reproducido: ~19k tokens/s en H100 y ~4.5k tokens/s en A100. Requiere batching y optimizaciones (FP8, speculative)",
            benchmark_type="output_tokens",
            year=2024
        ),
        ThroughputSystem(
            name="DGX B200 Blackwell (Llama 4 Maverick)",
            throughput_tokens_per_sec=1038.0,
            model="Llama-4 Maverick",
            hardware="DGX B200 Blackwell",
            setup="TensorRT + optimizations",
            source="Nvidia/DGX B200 showbenchmarks",
            source_url="https://www.tomshardware.com",
            techniques=[
                "TensorRT optimizations",
                "Blackwell architecture",
                "Multi-user serving",
                "Low-latency optimizations"
            ],
            notes="Reportó ~1,038 TPS/user en showbenchmarks. Métrica 'TPS/user' - útil para servicios con baja latencia por usuario",
            benchmark_type="tps_per_user",
            year=2025
        ),
        ThroughputSystem(
            name="vLLM Benchmarking Suite",
            throughput_tokens_per_sec=4656.0,
            model="Multi-model",
            hardware="Various GPUs",
            setup="vLLM serving stack",
            source="vLLM Documentation",
            source_url="https://docs.vllm.ai",
            techniques=[
                "PagedAttention",
                "Continuous batching",
                "KV cache optimization",
                "Multi-model serving"
            ],
            notes="vLLM benchmarking suite muestra ejemplos de ~4.6k total tokens/s. Varía por modelo y configuración (total tokens vs output tokens)",
            benchmark_type="total_tokens",
            year=2024
        ),
        ThroughputSystem(
            name="DeepSeek-R1 (Qwen-7B)",
            throughput_tokens_per_sec=3362.7,
            model="DeepSeek-R1-Distill-Qwen-7B",
            hardware="Specific hardware configuration",
            setup="Optimized inference stack",
            source="DatabaseMart / DeepSeek benchmark",
            source_url="https://www.databasemart.com",
            techniques=[
                "Model distillation",
                "Inference optimizations",
                "Hardware-specific optimizations"
            ],
            notes="Benchmark publicado: DeepSeek-R1-Distill-Qwen-7B = 3,362.71 tokens/s. Excelente para modelos medianos muy optimizados",
            benchmark_type="output_tokens",
            year=2025
        ),
        ThroughputSystem(
            name="Cerebras Inference (Llama-3.1-70B)",
            throughput_tokens_per_sec=2100.0,
            model="Llama-3.1-70B",
            hardware="Cerebras specialized hardware",
            setup="Cerebras inference appliance",
            source="Cerebras reports",
            source_url="https://www.cerebras.net",
            techniques=[
                "Specialized hardware (Wafer-Scale Engine)",
                "Custom inference stack",
                "Hardware-software co-design"
            ],
            notes="Cerebras reportó ~2,100 tok/s para Llama-70B en su sistema. Plataformas especializadas muestran throughput alto para modelos grandes",
            benchmark_type="output_tokens",
            year=2024
        ),
        ThroughputSystem(
            name="Cerebras (Llama 3.1 405B)",
            throughput_tokens_per_sec=969.0,
            model="Llama-3.1-405B",
            hardware="Cerebras specialized hardware",
            setup="Cerebras inference appliance",
            source="Cerebras reports",
            source_url="https://www.cerebras.net",
            techniques=[
                "Specialized hardware (Wafer-Scale Engine)",
                "Custom inference stack",
                "Very large model optimization"
            ],
            notes="Cerebras indicó ~969 tokens/s para Llama-405B. Muestra la ventaja de HW especializado frente a GPU general, con TTFT muy bajo y contextos largos",
            benchmark_type="output_tokens",
            year=2024
        ),
        ThroughputSystem(
            name="Groq (Llama-3: 8B / 70B)",
            throughput_tokens_per_sec=877.0,  # 8B model
            model="Llama-3 (8B: 877 tok/s, 70B: 284 tok/s)",
            hardware="Groq LPU (Language Processing Unit)",
            setup="Groq inference platform",
            source="Groq benchmarks (external reports)",
            source_url="https://www.groq.com",
            techniques=[
                "LPU (Language Processing Unit)",
                "Custom hardware architecture",
                "Low-latency inference"
            ],
            notes="Reportes independientes: ~877 tok/s en Llama-3 8B y ~284 tok/s en Llama-3 70B en la plataforma Groq LPU. Útil cuando comparas LPUs vs GPUs",
            benchmark_type="output_tokens",
            year=2024
        ),
        ThroughputSystem(
            name="SwiftSpec (Llama3-70B, 8 GPUs Hopper)",
            throughput_tokens_per_sec=348.0,
            model="Llama3-70B",
            hardware="8x NVIDIA Hopper GPUs",
            setup="SwiftSpec pipeline + speculative decoding",
            source="SwiftSpec paper (2025)",
            source_url="https://arxiv.org/abs/2025",
            techniques=[
                "Asynchronous pipeline",
                "Speculative decoding",
                "Multi-GPU optimization",
                "SwiftSpec framework"
            ],
            notes="Paper SwiftSpec (2025) reporta ~348 output tokens/s para Llama3-70B usando 8 GPUs Nvidia Hopper con pipeline asincrónico y speculative decoding",
            benchmark_type="output_tokens",
            year=2025
        ),
        ThroughputSystem(
            name="OPT-66B (Decoding Speculative Decoding)",
            throughput_tokens_per_sec=15.0,
            model="OPT-66B",
            hardware="Reproducible research setup",
            setup="Speculative decoding baseline",
            source="Academic paper (Decoding Speculative Decoding)",
            source_url="https://arxiv.org",
            techniques=[
                "Speculative decoding",
                "Baseline implementation",
                "Reproducible research setup"
            ],
            notes="Papers académicos reportan números modestos en setups reproducibles (~15 tok/s para OPT-66B). Muestra la gran variabilidad según hardware y configuración",
            benchmark_type="output_tokens",
            year=2024
        )
    ]
    
    return systems


def generate_json_output(systems: List[ThroughputSystem]) -> Dict[str, Any]:
    """Genera JSON con toda la información."""
    
    output = {
        'metadata': {
            'title': 'Top 10 Sistemas de Throughput para LLMs',
            'description': 'Sistemas con mayor throughput reportado (tokens por segundo)',
            'extraction_date': datetime.now().isoformat(),
            'total_systems': len(systems),
            'notes': [
                'No son comparables directamente sin normalizar: distinto hardware, modelo, modo (output vs total tokens)',
                'Speculative decoding + FP8/quant tiende a dar los saltos más grandes de throughput',
                'HW especializado (Cerebras, Groq, Blackwell) suele superar a GPUs generales',
                'Papers académicos reportan speedups relativos (× sobre baseline) en vez de tokens/s absolutos'
            ]
        },
        'systems': [asdict(system) for system in systems],
        'summary': {
            'max_throughput': max(s.throughput_tokens_per_sec for s in systems),
            'min_throughput': min(s.throughput_tokens_per_sec for s in systems),
            'avg_throughput': sum(s.throughput_tokens_per_sec for s in systems) / len(systems),
            'by_hardware': {},
            'by_model_size': {},
            'by_technique': {}
        }
    }
    
    # Agrupar por hardware
    by_hardware = {}
    for system in systems:
        hw = system.hardware
        if hw not in by_hardware:
            by_hardware[hw] = []
        by_hardware[hw].append({
            'name': system.name,
            'throughput': system.throughput_tokens_per_sec,
            'model': system.model
        })
    output['summary']['by_hardware'] = by_hardware
    
    # Agrupar por técnicas
    all_techniques = {}
    for system in systems:
        for technique in system.techniques:
            if technique not in all_techniques:
                all_techniques[technique] = []
            all_techniques[technique].append({
                'name': system.name,
                'throughput': system.throughput_tokens_per_sec
            })
    output['summary']['by_technique'] = all_techniques
    
    return output


def main():
    """Función principal."""
    print("=" * 80)
    print("EXTRACTOR DE TOP 10 SISTEMAS DE THROUGHPUT")
    print("=" * 80)
    print()
    
    # Extraer sistemas
    systems = extract_throughput_systems()
    
    print(f"✅ Extraídos {len(systems)} sistemas de throughput")
    print()
    
    # Generar JSON
    json_output = generate_json_output(systems)
    
    # Guardar JSON
    output_file = 'scraped_papers/top10_throughput_systems.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    
    print(f"💾 JSON guardado en: {output_file}")
    print()
    
    # Mostrar resumen
    print("📊 RESUMEN")
    print("=" * 80)
    print(f"Throughput máximo: {json_output['summary']['max_throughput']:,.0f} tokens/s")
    print(f"Throughput mínimo: {json_output['summary']['min_throughput']:,.0f} tokens/s")
    print(f"Throughput promedio: {json_output['summary']['avg_throughput']:,.0f} tokens/s")
    print()
    
    print("Top 3 sistemas:")
    sorted_systems = sorted(systems, key=lambda x: x.throughput_tokens_per_sec, reverse=True)
    for i, system in enumerate(sorted_systems[:3], 1):
        print(f"  {i}. {system.name}: {system.throughput_tokens_per_sec:,.0f} tokens/s")
    print()
    
    return json_output


if __name__ == "__main__":
    result = main()



