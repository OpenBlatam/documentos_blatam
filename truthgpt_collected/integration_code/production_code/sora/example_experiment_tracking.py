#!/usr/bin/env python3
"""
Ejemplo de Experiment Tracking con Sora
=========================================

Demuestra cómo usar el experiment tracking integrado con wandb/mlflow.
"""

import torch
import time
from pathlib import Path

from sora import (
    TextToVideoConfig,
    TextToVideoModule,
    ImageToVideoConfig,
    ImageToVideoModule,
    SoraExperimentTracker,
    track_video_generation,
    save_video_opencv,
    benchmark_video_generation,
)


def example_text_to_video_tracking():
    """Ejemplo de tracking para text-to-video."""
    print("=" * 70)
    print("📊 Ejemplo: Experiment Tracking - Text-to-Video")
    print("=" * 70)
    
    config = TextToVideoConfig(
        hidden_dim=256,
        video_length=8,
        resolution=(128, 128),
        fps=24,
        diffusion_steps=10
    )
    
    model = TextToVideoModule(config)
    model.eval()
    
    prompts = [
        "A beautiful sunset over the ocean",
        "A cat playing piano",
        "A futuristic city"
    ]
    
    with SoraExperimentTracker(
        project="sora-text2video",
        experiment_name="test-run-1",
        use_wandb=True,
        use_mlflow=False,
        config=config.to_dict()
    ) as tracker:
        for i, prompt in enumerate(prompts, 1):
            print(f"\n🎨 Generando video {i}/3: '{prompt}'")
            
            start_time = time.time()
            
            with torch.no_grad():
                video, metadata = model.generate_from_text(
                    prompt,
                    num_inference_steps=5,
                    seed=42 + i
                )
            
            generation_time = time.time() - start_time
            
            # Guardar video
            video_path = f"output_tracked_{i}.mp4"
            save_video_opencv(video, video_path, fps=config.fps)
            
            # Loggear en tracker
            tracker.log_text_to_video(
                prompt=prompt,
                video=video,
                metadata=metadata,
                generation_time=generation_time,
                config=config,
                video_path=video_path
            )
            
            print(f"  ✅ Video generado y trackeado")
            print(f"     - Tiempo: {generation_time:.2f}s")
            print(f"     - Shape: {video.shape}")
    
    print("\n✨ Experimento completado y loggeado en wandb!")


def example_image_to_video_tracking():
    """Ejemplo de tracking para image-to-video."""
    print("\n" + "=" * 70)
    print("📊 Ejemplo: Experiment Tracking - Image-to-Video")
    print("=" * 70)
    
    config = ImageToVideoConfig(
        hidden_dim=256,
        video_length=8,
        resolution=(128, 128),
        motion_strength=0.5
    )
    
    model = ImageToVideoModule(config)
    model.eval()
    
    # Crear imagen dummy
    dummy_image = torch.randn(1, 3, 128, 128)
    
    motion_strengths = [0.3, 0.5, 0.7]
    
    with SoraExperimentTracker(
        project="sora-image2video",
        experiment_name="motion-strength-test",
        use_wandb=True,
        config=config.to_dict()
    ) as tracker:
        for strength in motion_strengths:
            print(f"\n🎨 Animando con motion_strength={strength}")
            
            start_time = time.time()
            
            with torch.no_grad():
                video, metadata = model.animate_image(
                    dummy_image,
                    num_inference_steps=5,
                    motion_strength=strength,
                    seed=100
                )
            
            generation_time = time.time() - start_time
            
            # Loggear
            tracker.log_image_to_video(
                image_path=None,
                video=video,
                metadata=metadata,
                generation_time=generation_time,
                config=config
            )
            
            print(f"  ✅ Video animado y trackeado")
    
    print("\n✨ Experimento completado!")


def example_benchmark_tracking():
    """Ejemplo de tracking para benchmarks."""
    print("\n" + "=" * 70)
    print("📊 Ejemplo: Experiment Tracking - Benchmark")
    print("=" * 70)
    
    config = TextToVideoConfig(
        hidden_dim=256,
        video_length=8,
        resolution=(128, 128)
    )
    
    model = TextToVideoModule(config)
    model.eval()
    
    with SoraExperimentTracker(
        project="sora-benchmarks",
        experiment_name="performance-test",
        use_wandb=True,
        config=config.to_dict()
    ) as tracker:
        print("⏱️  Ejecutando benchmark...")
        
        results = benchmark_video_generation(
            model,
            input_shape=(1, 8, 3, 128, 128),
            num_runs=5
        )
        
        # Loggear resultados
        tracker.log_benchmark(results, model_config=config.to_dict())
        
        print(f"  ✅ Benchmark completado:")
        print(f"     - Mean Time: {results['mean_time_ms']:.2f} ms")
        print(f"     - FPS: {results['fps']:.2f}")
    
    print("\n✨ Benchmark loggeado en wandb!")


def example_model_info_tracking():
    """Ejemplo de tracking de información del modelo."""
    print("\n" + "=" * 70)
    print("📊 Ejemplo: Experiment Tracking - Model Info")
    print("=" * 70)
    
    configs = [
        TextToVideoConfig(hidden_dim=128, video_length=4),
        TextToVideoConfig(hidden_dim=256, video_length=8),
        TextToVideoConfig(hidden_dim=512, video_length=16),
    ]
    
    with SoraExperimentTracker(
        project="sora-model-comparison",
        experiment_name="model-sizes",
        use_wandb=True
    ) as tracker:
        for config in configs:
            model = TextToVideoModule(config)
            info = model.get_model_info()
            
            print(f"\n📊 Modelo: hidden_dim={config.hidden_dim}, frames={config.video_length}")
            print(f"  - Parámetros: {info['total_parameters']:,}")
            
            tracker.log_model_info(
                model_info=info,
                model_config=config.to_dict()
            )
    
    print("\n✨ Comparación de modelos loggeada!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Ejemplos de Experiment Tracking - Módulo Sora")
    print("=" * 70)
    
    # Ejemplo 1: Text-to-Video tracking
    example_text_to_video_tracking()
    
    # Ejemplo 2: Image-to-Video tracking
    example_image_to_video_tracking()
    
    # Ejemplo 3: Benchmark tracking
    example_benchmark_tracking()
    
    # Ejemplo 4: Model info tracking
    example_model_info_tracking()
    
    print("\n" + "=" * 70)
    print("✨ Todos los ejemplos de tracking completados!")
    print("=" * 70)
    print("\n💡 Tip: Visita wandb.ai para ver los resultados de tus experimentos\n")


