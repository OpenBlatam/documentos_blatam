#!/usr/bin/env python3
"""
Test Comparativo: TruthGPT Base vs TruthGPT + Ultimate Long Context
===================================================================

Compara el rendimiento de TruthGPT base vs TruthGPT con Ultimate Long Context
para identificar cuándo y cómo mejora.
"""

import torch
import time
import json
from typing import Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from truthgpt_optimization_core_integration import (
    TruthGPTOptimizationCore,
    TruthGPTOptimizationCoreConfig
)

from truthgpt_ultimate_long_context_integration import (
    TruthGPTUltimateCore,
    TruthGPTUltimateConfig,
    create_truthgpt_ultimate
)


def test_model_performance(
    model,
    context_lengths: List[int] = [512, 1024, 2048, 4096, 8192, 16384],
    batch_size: int = 2,
    vocab_size: int = 50257,
    num_runs: int = 3
) -> Dict[str, Any]:
    """Prueba el rendimiento del modelo en diferentes longitudes de contexto."""
    
    results = {
        'context_lengths': [],
        'forward_times': [],
        'memory_usage': [],
        'success': [],
        'errors': []
    }
    
    model.eval()
    
    for ctx_len in context_lengths:
        print(f"  Testing context length: {ctx_len:,} tokens")
        
        try:
            # Crear input
            input_ids = torch.randint(0, vocab_size, (batch_size, ctx_len))
            
            # Medir tiempo
            times = []
            for _ in range(num_runs):
                start = time.time()
                with torch.no_grad():
                    if isinstance(model, TruthGPTUltimateCore):
                        logits, metadata = model.model(input_ids)
                    else:
                        logits, metadata = model.model(input_ids)
                elapsed = (time.time() - start) * 1000  # ms
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            
            # Memoria aproximada
            memory_mb = (input_ids.numel() * 4) / (1024 * 1024)  # FP32
            
            results['context_lengths'].append(ctx_len)
            results['forward_times'].append(avg_time)
            results['memory_usage'].append(memory_mb)
            results['success'].append(True)
            results['errors'].append(None)
            
            print(f"    ✅ Success: {avg_time:.2f}ms, {memory_mb:.2f}MB")
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:100]}")
            results['context_lengths'].append(ctx_len)
            results['forward_times'].append(None)
            results['memory_usage'].append(None)
            results['success'].append(False)
            results['errors'].append(str(e))
    
    return results


def compare_models():
    """Compara TruthGPT base vs TruthGPT + Ultimate."""
    
    print("="*80)
    print("COMPARACIÓN: TruthGPT Base vs TruthGPT + Ultimate Long Context")
    print("="*80)
    
    # Configuración base
    base_config = TruthGPTOptimizationCoreConfig(
        hidden_size=768,
        num_hidden_layers=6,  # Reducido para tests rápidos
        num_attention_heads=12,
        max_position_embeddings=2048,
        vocab_size=50257
    )
    
    ultimate_config = TruthGPTUltimateConfig(
        hidden_size=768,
        num_hidden_layers=6,
        num_attention_heads=12,
        max_position_embeddings=2048,
        vocab_size=50257,
        enable_ultimate_long_context=True,
        ultimate_context_preset="best_quality",
        ultimate_context_length=131072
    )
    
    all_results = {}
    
    # 1. TruthGPT Base
    print("\n" + "="*80)
    print("TEST 1: TruthGPT Base")
    print("="*80)
    
    try:
        base_core = TruthGPTOptimizationCore(base_config)
        base_results = test_model_performance(
            base_core,
            context_lengths=[512, 1024, 2048, 4096]
        )
        all_results['truthgpt_base'] = base_results
    except Exception as e:
        print(f"❌ Error initializing TruthGPT Base: {e}")
        all_results['truthgpt_base'] = {'error': str(e)}
    
    # 2. TruthGPT + Ultimate (Best Quality)
    print("\n" + "="*80)
    print("TEST 2: TruthGPT + Ultimate Long Context (Best Quality)")
    print("="*80)
    
    try:
        ultimate_core = TruthGPTUltimateCore(ultimate_config)
        ultimate_results = test_model_performance(
            ultimate_core,
            context_lengths=[512, 1024, 2048, 4096, 8192, 16384]
        )
        all_results['truthgpt_ultimate'] = ultimate_results
    except Exception as e:
        print(f"❌ Error initializing TruthGPT Ultimate: {e}")
        all_results['truthgpt_ultimate'] = {'error': str(e)}
    
    # 3. TruthGPT + Ultimate (Training Free)
    print("\n" + "="*80)
    print("TEST 3: TruthGPT + Ultimate Long Context (Training Free)")
    print("="*80)
    
    try:
        training_free_config = TruthGPTUltimateConfig(
            hidden_size=768,
            num_hidden_layers=6,
            num_attention_heads=12,
            max_position_embeddings=2048,
            vocab_size=50257,
            enable_ultimate_long_context=True,
            ultimate_context_preset="training_free",
            ultimate_context_length=131072
        )
        tf_core = TruthGPTUltimateCore(training_free_config)
        tf_results = test_model_performance(
            tf_core,
            context_lengths=[512, 1024, 2048, 4096, 8192]
        )
        all_results['truthgpt_ultimate_tf'] = tf_results
    except Exception as e:
        print(f"❌ Error initializing TruthGPT Ultimate (TF): {e}")
        all_results['truthgpt_ultimate_tf'] = {'error': str(e)}
    
    # Análisis comparativo
    print("\n" + "="*80)
    print("ANÁLISIS COMPARATIVO")
    print("="*80)
    
    if 'truthgpt_base' in all_results and 'truthgpt_ultimate' in all_results:
        base = all_results['truthgpt_base']
        ultimate = all_results['truthgpt_ultimate']
        
        if 'forward_times' in base and 'forward_times' in ultimate:
            print("\n📊 Rendimiento por Contexto:")
            print("-" * 80)
            print(f"{'Contexto':<12} {'Base (ms)':<15} {'Ultimate (ms)':<18} {'Mejora':<15} {'Estado'}")
            print("-" * 80)
            
            # Comparar contextos comunes
            base_times = dict(zip(base['context_lengths'], base['forward_times']))
            ultimate_times = dict(zip(ultimate['context_lengths'], ultimate['forward_times']))
            
            for ctx_len in sorted(set(base['context_lengths']) & set(ultimate['context_lengths'])):
                base_time = base_times.get(ctx_len)
                ultimate_time = ultimate_times.get(ctx_len)
                
                if base_time and ultimate_time:
                    improvement = ((base_time - ultimate_time) / base_time) * 100
                    status = "✅ Mejora" if improvement > 0 else "⚠️ Más lento"
                    print(f"{ctx_len:<12,} {base_time:<15.2f} {ultimate_time:<18.2f} {improvement:>6.1f}% {status}")
            
            # Contextos extendidos solo en Ultimate
            print("\n📈 Contextos Extendidos (solo Ultimate):")
            print("-" * 80)
            for ctx_len in ultimate['context_lengths']:
                if ctx_len not in base['context_lengths']:
                    ultimate_time = ultimate_times.get(ctx_len)
                    if ultimate_time:
                        print(f"  {ctx_len:,} tokens: {ultimate_time:.2f}ms ✅")
    
    # Guardar resultados
    output_file = 'truthgpt_ultimate_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    return all_results


def analyze_when_improves(results: Dict[str, Any]):
    """Analiza cuándo Ultimate mejora sobre TruthGPT base."""
    
    print("\n" + "="*80)
    print("ANÁLISIS: ¿CUÁNDO MEJORA ULTIMATE?")
    print("="*80)
    
    if 'truthgpt_base' not in results or 'truthgpt_ultimate' not in results:
        print("⚠️ No hay datos suficientes para comparar")
        return
    
    base = results['truthgpt_base']
    ultimate = results['truthgpt_ultimate']
    
    if 'error' in base or 'error' in ultimate:
        print("⚠️ Hay errores en los resultados")
        return
    
    base_times = dict(zip(base['context_lengths'], base['forward_times']))
    ultimate_times = dict(zip(ultimate['context_lengths'], ultimate['forward_times']))
    
    print("\n🎯 CONCLUSIONES:")
    print("-" * 80)
    
    # 1. Contextos donde mejora
    improvements = []
    for ctx_len in sorted(set(base['context_lengths']) & set(ultimate['context_lengths'])):
        base_time = base_times.get(ctx_len)
        ultimate_time = ultimate_times.get(ctx_len)
        
        if base_time and ultimate_time:
            improvement = ((base_time - ultimate_time) / base_time) * 100
            if improvement > 0:
                improvements.append((ctx_len, improvement))
    
    if improvements:
        print("\n✅ MEJORA EN:")
        for ctx_len, imp in improvements:
            print(f"  • {ctx_len:,} tokens: {imp:.1f}% más rápido")
    else:
        print("\n⚠️ No hay mejoras significativas en velocidad")
    
    # 2. Contextos extendidos
    extended = [ctx for ctx in ultimate['context_lengths'] if ctx not in base['context_lengths']]
    if extended:
        print(f"\n🚀 CONTEXTOS EXTENDIDOS:")
        print(f"  • TruthGPT Base: máximo {max(base['context_lengths']):,} tokens")
        print(f"  • TruthGPT Ultimate: hasta {max(ultimate['context_lengths']):,} tokens")
        print(f"  • Extensión: {max(ultimate['context_lengths']) / max(base['context_lengths']):.1f}x")
    
    # 3. Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    print("-" * 80)
    print("Usa TruthGPT + Ultimate cuando:")
    print("  ✅ Necesitas contexto > 2K tokens")
    print("  ✅ Tareas requieren dependencias largas")
    print("  ✅ Necesitas compresión semántica")
    print("  ✅ Quieres optimización con rewards")
    print("\nUsa TruthGPT Base cuando:")
    print("  ✅ Contexto < 2K tokens")
    print("  ✅ Necesitas máxima velocidad")
    print("  ✅ No necesitas extensiones de contexto")


if __name__ == "__main__":
    results = compare_models()
    analyze_when_improves(results)
    
    print("\n" + "="*80)
    print("✅ Comparación completada!")
    print("="*80)





