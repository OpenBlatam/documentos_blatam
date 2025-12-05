#!/usr/bin/env python3
"""
Test para Ultimate Long Context Model
=====================================

Prueba el modelo integrado con diferentes configuraciones y casos de uso.
"""

import torch
import time
import json
from typing import Dict, Any
import sys
import os


def convert_to_json_serializable(obj):
    """Convierte objetos a formato JSON serializable."""
    if isinstance(obj, torch.Tensor):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, bool, str, type(None))):
        return obj
    else:
        return str(obj)

# Añadir path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from papers.research.paper_ultimate_long_context import (
    UltimateLongContextModule,
    UltimateLongContextConfig,
    UltimateLongContextPresets
)


def test_model(
    config: UltimateLongContextConfig,
    context_lengths: list = [2048, 4096, 8192, 16384],
    batch_size: int = 2,
    hidden_dim: int = 768
) -> Dict[str, Any]:
    """Prueba el modelo con diferentes longitudes de contexto."""
    
    print(f"\n{'='*80}")
    print(f"Testing Ultimate Long Context Model")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  - Semantic Compression: {config.use_semantic_compression}")
    print(f"  - AdaGroPE: {config.use_adagrope}")
    print(f"  - LongRoPE: {config.use_longrope}")
    print(f"  - CEPE: {config.use_cepe}")
    print(f"  - LongReward: {config.use_longreward}")
    print(f"  - Extended Context: {config.extended_context_length:,} tokens")
    print(f"{'='*80}\n")
    
    # Inicializar modelo
    try:
        model = UltimateLongContextModule(config)
        model.eval()
    except Exception as e:
        print(f"❌ Error initializing model: {e}")
        return {'error': str(e)}
    
    results = {
        'config': {
            'use_semantic_compression': config.use_semantic_compression,
            'use_adagrope': config.use_adagrope,
            'use_longrope': config.use_longrope,
            'use_cepe': config.use_cepe,
            'use_longreward': config.use_longreward,
            'extended_context_length': config.extended_context_length
        },
        'tests': []
    }
    
    for ctx_len in context_lengths:
        if ctx_len > config.extended_context_length:
            print(f"⏭️  Skipping {ctx_len} (exceeds extended_context_length)")
            continue
        
        print(f"Testing context length: {ctx_len:,} tokens")
        
        try:
            # Crear input
            hidden_states = torch.randn(batch_size, ctx_len, hidden_dim)
            position_ids = torch.arange(ctx_len).unsqueeze(0).repeat(batch_size, 1)
            
            # Forward pass
            start_time = time.time()
            with torch.no_grad():
                output, metadata = model(hidden_states, position_ids=position_ids)
            elapsed_time = (time.time() - start_time) * 1000  # ms
            
            # Memoria (aproximada)
            memory_mb = (hidden_states.numel() * 4) / (1024 * 1024)  # FP32
            
            # Verificar output
            assert output.shape[0] == batch_size, "Batch size mismatch"
            assert output.shape[2] == hidden_dim, "Hidden dim mismatch"
            
            print(f"  ✅ Success: {elapsed_time:.2f}ms, {memory_mb:.2f}MB")
            print(f"     Input: {hidden_states.shape} → Output: {output.shape}")
            
            # Mostrar metadata de etapas
            if 'stages' in metadata:
                print(f"     Stages used: {list(metadata['stages'].keys())}")
                for stage_name, stage_meta in metadata['stages'].items():
                    if 'compression_ratio' in stage_meta:
                        print(f"       {stage_name}: compression={stage_meta['compression_ratio']:.3f}")
            
            results['tests'].append({
                'context_length': ctx_len,
                'batch_size': batch_size,
                'hidden_dim': hidden_dim,
                'forward_time_ms': elapsed_time,
                'memory_mb': memory_mb,
                'input_shape': list(hidden_states.shape),
                'output_shape': list(output.shape),
                'metadata': convert_to_json_serializable(metadata),
                'success': True,
                'error': ''
            })
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results['tests'].append({
                'context_length': ctx_len,
                'success': False,
                'error': str(e)
            })
    
    # Métricas finales
    try:
        metrics = model.get_metrics()
        results['model_metrics'] = metrics
        print(f"\n📊 Model Metrics:")
        print(f"   Active modules: {metrics.get('active_modules', [])}")
        print(f"   Total stages: {metrics.get('total_stages', 0)}")
    except Exception as e:
        print(f"⚠️  Could not get metrics: {e}")
    
    return results


def main():
    """Ejecuta todas las pruebas."""
    
    all_results = {}
    
    # 1. Training-free configuration
    print("\n" + "="*80)
    print("TEST 1: Training-Free Configuration")
    print("="*80)
    config_tf = UltimateLongContextPresets.training_free()
    results_tf = test_model(config_tf, context_lengths=[2048, 4096, 8192])
    all_results['training_free'] = results_tf
    
    # 2. Fast inference configuration
    print("\n" + "="*80)
    print("TEST 2: Fast Inference Configuration")
    print("="*80)
    config_fast = UltimateLongContextPresets.fast_inference()
    results_fast = test_model(config_fast, context_lengths=[2048, 4096, 8192])
    all_results['fast_inference'] = results_fast
    
    # 3. Best quality configuration (solo si los módulos funcionan)
    print("\n" + "="*80)
    print("TEST 3: Best Quality Configuration")
    print("="*80)
    config_quality = UltimateLongContextPresets.best_quality()
    # Solo probar con contextos pequeños primero
    results_quality = test_model(config_quality, context_lengths=[2048, 4096])
    all_results['best_quality'] = results_quality
    
    # 4. Maximum extension (solo CEPE que funciona)
    print("\n" + "="*80)
    print("TEST 4: Maximum Extension (CEPE only)")
    print("="*80)
    config_max = UltimateLongContextConfig(
        hidden_dim=768,
        use_semantic_compression=False,
        use_adagrope=False,
        use_longrope=False,
        use_cepe=True,  # Solo CEPE que funciona
        use_longreward=False,
        extended_context_length=16384
    )
    results_max = test_model(config_max, context_lengths=[2048, 4096, 8192, 16384])
    all_results['maximum_extension'] = results_max
    
    # Guardar resultados
    output_file = 'ultimate_long_context_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ All tests completed!")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}\n")
    
    # Resumen
    print("SUMMARY:")
    print("-" * 80)
    for config_name, results in all_results.items():
        if 'tests' in results:
            successful = sum(1 for t in results['tests'] if t.get('success', False))
            total = len(results['tests'])
            print(f"{config_name}: {successful}/{total} tests passed")
    
    return all_results


if __name__ == '__main__':
    main()

