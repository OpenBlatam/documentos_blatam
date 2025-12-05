#!/usr/bin/env python3
"""
Ejemplos de Uso - Best Techniques Papers
==========================================

Ejemplos completos de cómo usar los módulos de mejores técnicas.
"""

import torch
from best import (
    Paper2506_10848v2Config,
    Paper2506_10848v2_BestTechniques,
    Paper2510_04871v1Config,
    Paper2510_04871v1_BestTechniques,
    TruthGPT_Paper2506_10848v2_Integration,
    TruthGPT_Paper2510_04871v1_Integration,
    AdaptiveLayerNorm,
    GatedAttention,
    EnsembleAttention
)


def example_basic_usage():
    """Ejemplo básico de uso."""
    print("=" * 60)
    print("Ejemplo 1: Uso Básico")
    print("=" * 60)
    
    config = Paper2506_10848v2Config(hidden_dim=512, num_heads=8)
    model = Paper2506_10848v2_BestTechniques(config)
    
    x = torch.randn(2, 32, 512)
    output = model(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print("✅ Uso básico completado\n")


def example_with_attention_mask():
    """Ejemplo con attention mask."""
    print("=" * 60)
    print("Ejemplo 2: Con Attention Mask")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    x = torch.randn(2, 32, 512)
    attention_mask = torch.ones(2, 32, dtype=torch.bool)
    attention_mask[0, 20:] = False
    
    output = model(x, attention_mask=attention_mask)
    print(f"Output shape: {output.shape}")
    print("✅ Attention mask aplicado correctamente\n")


def example_ensemble_attention():
    """Ejemplo de ensemble attention."""
    print("=" * 60)
    print("Ejemplo 3: Ensemble Attention")
    print("=" * 60)
    
    config = Paper2510_04871v1Config(
        hidden_dim=512,
        num_heads=8,
        num_ensemble_heads=4
    )
    model = Paper2510_04871v1_BestTechniques(config)
    
    x = torch.randn(2, 32, 512)
    output = model(x)
    
    metrics = model.get_metrics()
    print(f"Output shape: {output.shape}")
    print(f"Ensemble diversity: {metrics.get('ensemble_diversity', 0):.4f}")
    print("✅ Ensemble attention funcionando\n")


def example_gradient_checkpointing():
    """Ejemplo de gradient checkpointing."""
    print("=" * 60)
    print("Ejemplo 4: Gradient Checkpointing")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    model.train()
    model.enable_gradient_checkpointing(True)
    
    x = torch.randn(2, 32, 512, requires_grad=True)
    output = model(x)
    loss = output.mean()
    loss.backward()
    
    print(f"Output shape: {output.shape}")
    print(f"Gradient computed: {x.grad is not None}")
    print("✅ Gradient checkpointing funcionando\n")


def example_serialization():
    """Ejemplo de serialización."""
    print("=" * 60)
    print("Ejemplo 5: Serialización")
    print("=" * 60)
    
    import tempfile
    import os
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    x = torch.randn(2, 32, 512)
    original_output = model(x)
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as f:
            temp_path = f.name
        
        model.save_state_dict(temp_path)
        loaded_model = Paper2506_10848v2_BestTechniques.load_state_dict(temp_path)
        loaded_output = loaded_model(x)
        
        print(f"Original output shape: {original_output.shape}")
        print(f"Loaded output shape: {loaded_output.shape}")
        print(f"Outputs match: {torch.allclose(original_output, loaded_output, atol=1e-6)}")
        print("✅ Serialización funcionando\n")
    except Exception as e:
        print(f"⚠️ Serialización test skipped: {e}\n")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def example_benchmarking():
    """Ejemplo de benchmarking."""
    print("=" * 60)
    print("Ejemplo 6: Benchmarking")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    result = model.benchmark(
        batch_size=4,
        seq_len=128,
        num_runs=10
    )
    
    print(f"Average time: {result['avg_time']:.4f}s")
    print(f"Min time: {result['min_time']:.4f}s")
    print(f"Max time: {result['max_time']:.4f}s")
    print(f"Throughput: {result['throughput']:.2f} tokens/s")
    if result.get('memory_used_mb'):
        print(f"Memory used: {result['memory_used_mb']:.2f} MB")
    print("✅ Benchmarking completado\n")


def example_optimization():
    """Ejemplo de optimización."""
    print("=" * 60)
    print("Ejemplo 7: Optimización")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    model.optimize_for_inference()
    info = model.get_model_info()
    
    print(f"Total parameters: {info['total_parameters']:,}")
    print(f"Trainable parameters: {info['trainable_parameters']:,}")
    print("✅ Modelo optimizado para inferencia\n")


def example_integration():
    """Ejemplo de integración con TruthGPT."""
    print("=" * 60)
    print("Ejemplo 8: Integración con TruthGPT")
    print("=" * 60)
    
    import torch.nn as nn
    
    base_model = nn.Sequential(
        nn.Linear(512, 512),
        nn.ReLU(),
        nn.Linear(512, 512)
    )
    
    config = Paper2506_10848v2Config()
    enhanced_model = TruthGPT_Paper2506_10848v2_Integration(
        base_model,
        config
    )
    
    x = torch.randn(2, 32, 512)
    output = enhanced_model(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print("✅ Integración funcionando\n")


def example_individual_components():
    """Ejemplo de componentes individuales."""
    print("=" * 60)
    print("Ejemplo 9: Componentes Individuales")
    print("=" * 60)
    
    x = torch.randn(2, 32, 512)
    
    norm = AdaptiveLayerNorm(hidden_dim=512)
    norm_output = norm(x)
    print(f"AdaptiveLayerNorm output: {norm_output.shape}")
    
    attn = GatedAttention(hidden_dim=512, num_heads=8)
    attn_output = attn(x)
    print(f"GatedAttention output: {attn_output.shape}")
    
    ensemble = EnsembleAttention(hidden_dim=512, num_heads=8, num_ensemble=4)
    ensemble_output = ensemble(x)
    print(f"EnsembleAttention output: {ensemble_output.shape}")
    
    print("✅ Componentes individuales funcionando\n")


def example_mixed_precision():
    """Ejemplo de mixed precision."""
    print("=" * 60)
    print("Ejemplo 10: Mixed Precision")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    model.eval()
    
    x = torch.randn(2, 32, 512)
    
    output_fp32 = model(x, use_autocast=False)
    output_fp16 = model(x, use_autocast=True)
    
    print(f"FP32 output shape: {output_fp32.shape}")
    print(f"FP16 output shape: {output_fp16.shape}")
    print(f"Outputs similar: {torch.allclose(output_fp32, output_fp16.float(), atol=1e-2)}")
    print("✅ Mixed precision funcionando\n")


def example_memory_estimation():
    """Ejemplo de estimación de memoria."""
    print("=" * 60)
    print("Ejemplo 11: Estimación de Memoria")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    mem_fp32 = model.estimate_memory_usage(batch_size=4, seq_len=128, dtype=torch.float32)
    mem_fp16 = model.estimate_memory_usage(batch_size=4, seq_len=128, dtype=torch.float16)
    
    print(f"FP32 estimated memory: {mem_fp32['total_estimated_mb']:.2f} MB")
    print(f"FP16 estimated memory: {mem_fp16['total_estimated_mb']:.2f} MB")
    print(f"Memory savings: {(1 - mem_fp16['total_estimated_mb'] / mem_fp32['total_estimated_mb']) * 100:.1f}%")
    print("✅ Estimación de memoria funcionando\n")


def example_layer_analysis():
    """Ejemplo de análisis de capas."""
    print("=" * 60)
    print("Ejemplo 12: Análisis de Capas")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    analysis = model.analyze_layers()
    print(f"Total layers: {analysis['total_layers']}")
    print(f"Layer types: {list(analysis['layer_types'].keys())}")
    print(f"Top 3 layers by parameters:")
    sorted_layers = sorted(analysis['layers'], key=lambda x: x['parameters'], reverse=True)[:3]
    for layer in sorted_layers:
        print(f"  {layer['name']}: {layer['parameters']:,} params ({layer['memory_mb']:.2f} MB)")
    print("✅ Análisis de capas funcionando\n")


def example_dtype_conversion():
    """Ejemplo de conversión de dtype."""
    print("=" * 60)
    print("Ejemplo 13: Conversión de Dtype")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    original_dtype = next(model.parameters()).dtype
    print(f"Original dtype: {original_dtype}")
    
    model.convert_dtype(torch.float16)
    new_dtype = next(model.parameters()).dtype
    print(f"New dtype: {new_dtype}")
    print("✅ Conversión de dtype funcionando\n")


def example_paper_comparison():
    """Ejemplo de comparación entre papers."""
    print("=" * 60)
    print("Ejemplo 14: Comparación entre Papers")
    print("=" * 60)
    
    from best import PaperComparator
    
    comparator = PaperComparator()
    comparison = comparator.full_comparison(batch_size=2, seq_len=64, num_runs=5)
    
    print(f"Paper 2506 parameters: {comparison.paper_2506['architecture']['total_parameters']:,}")
    print(f"Paper 2510 parameters: {comparison.paper_2510['architecture']['total_parameters']:,}")
    print(f"Faster model: {comparison.differences['performance']['faster']}")
    print(f"More efficient: {comparison.differences['memory']['more_efficient']}")
    print("✅ Comparación entre papers funcionando\n")


def example_gradient_analysis():
    """Ejemplo de análisis de gradientes."""
    print("=" * 60)
    print("Ejemplo 15: Análisis de Gradientes")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    model.train()
    
    x = torch.randn(2, 32, 512, requires_grad=True)
    output = model(x)
    loss = output.mean()
    loss.backward()
    
    grad_norm = model.get_gradient_norm()
    grad_analysis = model.analyze_gradients()
    
    print(f"Gradient norm: {grad_norm:.4f}")
    print(f"Has gradients: {grad_analysis['has_gradients']}")
    print(f"Mean norm: {grad_analysis['mean_norm']:.4f}")
    print(f"Parameters with gradients: {grad_analysis['param_count']}")
    
    clipped_norm = model.clip_gradients(max_norm=1.0)
    print(f"After clipping: {clipped_norm:.4f}")
    print("✅ Análisis de gradientes funcionando\n")


def example_export():
    """Ejemplo de exportación."""
    print("=" * 60)
    print("Ejemplo 16: Exportación de Modelos")
    print("=" * 60)
    
    import tempfile
    import os
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    temp_dir = tempfile.mkdtemp()
    onnx_path = os.path.join(temp_dir, 'model.onnx')
    ts_path = os.path.join(temp_dir, 'model.pt')
    
    try:
        onnx_success = model.export_to_onnx(onnx_path, input_shape=(1, 32, 512))
        ts_success = model.export_to_torchscript(ts_path, input_shape=(1, 32, 512))
        
        print(f"ONNX export: {'✅ Success' if onnx_success else '❌ Failed'}")
        print(f"TorchScript export: {'✅ Success' if ts_success else '❌ Failed'}")
        print("✅ Exportación funcionando\n")
    except Exception as e:
        print(f"⚠️ Export test skipped: {e}\n")
    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def example_training_setup():
    """Ejemplo de setup de entrenamiento."""
    print("=" * 60)
    print("Ejemplo 17: Setup de Entrenamiento")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    optimizer = model.setup_optimizer(learning_rate=1e-4, optimizer_type='adamw')
    scheduler = model.setup_scheduler(optimizer, scheduler_type='cosine', max_steps=1000)
    
    print(f"Optimizer: {type(optimizer).__name__}")
    print(f"Scheduler: {type(scheduler).__name__ if scheduler else 'None'}")
    print(f"Learning rate: {optimizer.param_groups[0]['lr']}")
    
    model.freeze_parameters(freeze=False)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {trainable:,}")
    
    model.freeze_parameters(freeze=True)
    trainable_after = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"After freezing: {trainable_after:,}")
    print("✅ Setup de entrenamiento funcionando\n")


def example_health_check():
    """Ejemplo de health check."""
    print("=" * 60)
    print("Ejemplo 18: Health Check")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    health = model.health_check()
    print(f"Status: {health['status']}")
    print(f"Has parameters: {health['checks'].get('has_parameters', False)}")
    print(f"Parameters valid: {health['checks'].get('parameters_valid', False)}")
    print(f"Config valid: {health['checks'].get('config_valid', False)}")
    
    validation = model.validate_model()
    print(f"Model valid: {validation['valid']}")
    print(f"Issues: {len(validation['issues'])}")
    print(f"Warnings: {len(validation['warnings'])}")
    print("✅ Health check funcionando\n")


def example_comprehensive_report():
    """Ejemplo de reporte completo."""
    print("=" * 60)
    print("Ejemplo 19: Reporte Completo")
    print("=" * 60)
    
    config = Paper2506_10848v2Config()
    model = Paper2506_10848v2_BestTechniques(config)
    
    report = model.generate_comprehensive_report(
        include_benchmark=False,
        include_memory_estimation=True
    )
    
    print(f"Model: {report['model_name']}")
    print(f"Status: {report['health']['status']}")
    print(f"Parameters: {report['model_info']['total_parameters']:,}")
    print(f"Size: {report['model_info']['total_size_mb']:.2f} MB")
    print(f"Layers: {report['layer_analysis']['total_layers']}")
    print(f"Memory (FP32): {report['memory_estimation']['total_estimated_mb']:.2f} MB")
    print("✅ Reporte completo generado\n")


def example_sora_integration():
    """Ejemplo de integración con Sora."""
    print("=" * 60)
    print("Ejemplo 20: Integración con Sora")
    print("=" * 60)
    
    try:
        from sora import VideoGenerationConfig, VideoGenerationModule
        
        sora_config = VideoGenerationConfig(
            hidden_dim=512,
            video_length=16,
            resolution=(256, 256),
            fps=24
        )
        
        sora_model = VideoGenerationModule(sora_config)
        
        config = Paper2506_10848v2Config(hidden_dim=512)
        best_model = Paper2506_10848v2_BestTechniques(config)
        
        latent = torch.randn(2, 16, 512, 256, 256)
        
        video, metadata = sora_model(latent)
        print(f"Sora video shape: {video.shape}")
        print(f"Sora metadata: {metadata.get('num_frames')} frames")
        
        enhanced_features = best_model(video.view(2, -1, 512))
        print(f"Enhanced features shape: {enhanced_features.shape}")
        print("✅ Integración Sora + Best Techniques funcionando\n")
    except ImportError:
        print("⚠️ Módulo sora no disponible, saltando ejemplo\n")


def example_sora_with_best_attention():
    """Ejemplo de Sora con Gated Attention de Best."""
    print("=" * 60)
    print("Ejemplo 21: Sora con Gated Attention")
    print("=" * 60)
    
    try:
        from sora import VideoGenerationConfig, VideoGenerationModule
        
        sora_config = VideoGenerationConfig(hidden_dim=512, video_length=8)
        sora_model = VideoGenerationModule(sora_config)
        
        gated_attn = GatedAttention(hidden_dim=512, num_heads=8)
        
        latent = torch.randn(1, 8, 512, 128, 128)
        video, _ = sora_model(latent)
        
        batch, frames, channels, height, width = video.shape
        video_flat = video.view(batch * frames, height * width, channels)
        
        enhanced = gated_attn(video_flat)
        print(f"Original video shape: {video.shape}")
        print(f"Enhanced with GatedAttention: {enhanced.shape}")
        print("✅ Sora + Gated Attention funcionando\n")
    except ImportError:
        print("⚠️ Módulo sora no disponible, saltando ejemplo\n")


def example_sora_with_adaptive_norm():
    """Ejemplo de Sora con Adaptive LayerNorm."""
    print("=" * 60)
    print("Ejemplo 22: Sora con Adaptive LayerNorm")
    print("=" * 60)
    
    try:
        from sora import VideoGenerationConfig, VideoGenerationModule
        
        sora_config = VideoGenerationConfig(hidden_dim=512, video_length=8)
        sora_model = VideoGenerationModule(sora_config)
        
        adaptive_norm = AdaptiveLayerNorm(hidden_dim=512)
        
        latent = torch.randn(1, 8, 512, 128, 128)
        video, _ = sora_model(latent)
        
        batch, frames, channels, height, width = video.shape
        video_flat = video.view(batch * frames, height * width, channels)
        
        normalized = adaptive_norm(video_flat)
        print(f"Original video shape: {video.shape}")
        print(f"Normalized with AdaptiveLayerNorm: {normalized.shape}")
        print("✅ Sora + Adaptive LayerNorm funcionando\n")
    except ImportError:
        print("⚠️ Módulo sora no disponible, saltando ejemplo\n")


def example_sora_integrated():
    """Ejemplo de Sora Integrated con Best Techniques."""
    print("=" * 60)
    print("Ejemplo 23: Sora Integrated")
    print("=" * 60)
    
    try:
        from sora import (
            VideoGenerationConfig,
            create_sora_integrated,
            SoraAnalytics,
            SoraOptimizer
        )
        
        config = VideoGenerationConfig(
            hidden_dim=512,
            video_length=16,
            resolution=(256, 256)
        )
        
        sora = create_sora_integrated(config)
        
        latent = torch.randn(2, 16, 512, 256, 256)
        video, metadata = sora(latent)
        
        print(f"Video generado: {video.shape}")
        print(f"Metadata: {metadata.get('num_frames')} frames")
        
        if SoraAnalytics:
            analytics = SoraAnalytics(sora)
            quality = analytics.analyze_generation_quality(video, metadata)
            print(f"Quality score: {quality.get('overall_quality', 0):.4f}")
        
        if SoraOptimizer:
            optimizer = SoraOptimizer(sora)
            result = optimizer.optimize_for_inference()
            print(f"Optimization: {result.get('optimized', False)}")
        
        print("✅ Sora Integrated funcionando\n")
    except ImportError:
        print("⚠️ Módulo sora no disponible, saltando ejemplo\n")


def example_sora_ensemble_attention():
    """Ejemplo de Sora con Ensemble Attention."""
    print("=" * 60)
    print("Ejemplo 24: Sora con Ensemble Attention")
    print("=" * 60)
    
    try:
        from sora import VideoGenerationConfig, VideoGenerationModule
        
        sora_config = VideoGenerationConfig(hidden_dim=512, video_length=8)
        sora_model = VideoGenerationModule(sora_config)
        
        ensemble_attn = EnsembleAttention(
            hidden_dim=512,
            num_heads=8,
            num_ensemble=4
        )
        
        latent = torch.randn(1, 8, 512, 128, 128)
        video, _ = sora_model(latent)
        
        batch, frames, channels, height, width = video.shape
        video_flat = video.view(batch * frames, height * width, channels)
        
        ensemble_output = ensemble_attn(video_flat)
        metrics = ensemble_attn.get_metrics()
        
        print(f"Original video shape: {video.shape}")
        print(f"Ensemble output shape: {ensemble_output.shape}")
        print(f"Ensemble diversity: {metrics.get('ensemble_diversity', 0):.4f}")
        print("✅ Sora + Ensemble Attention funcionando\n")
    except ImportError:
        print("⚠️ Módulo sora no disponible, saltando ejemplo\n")


def example_sora_optimization_pipeline():
    """Ejemplo de pipeline de optimización Sora + Best."""
    print("=" * 60)
    print("Ejemplo 25: Pipeline de Optimización")
    print("=" * 60)
    
    try:
        from sora import VideoGenerationConfig, VideoGenerationModule
        
        sora_config = VideoGenerationConfig(
            hidden_dim=512,
            video_length=16,
            resolution=(256, 256),
            use_mixed_precision=True
        )
        sora_model = VideoGenerationModule(sora_config)
        
        config = Paper2506_10848v2Config(hidden_dim=512)
        best_model = Paper2506_10848v2_BestTechniques(config)
        
        best_model.optimize_for_inference()
        sora_model.eval()
        
        latent = torch.randn(2, 16, 512, 256, 256)
        
        with torch.no_grad():
            video, sora_metadata = sora_model(latent)
            batch, frames, channels, height, width = video.shape
            video_features = video.view(batch, frames * height * width, channels)
            enhanced = best_model(video_features)
        
        print(f"Video generado: {video.shape}")
        print(f"Features mejoradas: {enhanced.shape}")
        print(f"Sora FPS: {sora_metadata.get('fps', 0)}")
        
        best_info = best_model.get_model_info()
        print(f"Best model params: {best_info['total_parameters']:,}")
        print("✅ Pipeline de optimización funcionando\n")
    except ImportError:
        print("⚠️ Módulo sora no disponible, saltando ejemplo\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Ejemplos de Uso - Best Techniques Papers")
    print("=" * 60 + "\n")
    
    example_basic_usage()
    example_with_attention_mask()
    example_ensemble_attention()
    example_gradient_checkpointing()
    example_serialization()
    example_benchmarking()
    example_optimization()
    example_integration()
    example_individual_components()
    example_mixed_precision()
    example_memory_estimation()
    example_layer_analysis()
    example_dtype_conversion()
    example_paper_comparison()
    example_gradient_analysis()
    example_export()
    example_training_setup()
    example_health_check()
    example_comprehensive_report()
    
    print("\n" + "=" * 60)
    print("Ejemplos de Integración con Sora")
    print("=" * 60 + "\n")
    
    example_sora_integration()
    example_sora_with_best_attention()
    example_sora_with_adaptive_norm()
    example_sora_integrated()
    example_sora_ensemble_attention()
    example_sora_optimization_pipeline()
    
    print("=" * 60)
    print("Todos los ejemplos completados exitosamente! ✅")
    print("=" * 60)

