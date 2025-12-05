#!/usr/bin/env python3
"""
Ejemplos Avanzados del Módulo Sora
===================================

Ejemplos avanzados mostrando todas las capacidades del módulo Sora.
"""

import torch
from sora import (
    TextToVideoConfig,
    TextToVideoModule,
    ImageToVideoConfig,
    ImageToVideoModule,
    VideoToVideoConfig,
    VideoToVideoModule,
    DiffusionScheduler,
    SchedulerType,
    save_video_opencv,
    create_video_gif,
    normalize_video,
    resize_video
)


def example_text_to_video_advanced():
    """Ejemplo avanzado de text-to-video con diferentes configuraciones."""
    print("=" * 70)
    print("🎬 Ejemplo Avanzado: Text-to-Video")
    print("=" * 70)
    
    # Configuración de alta calidad
    config = TextToVideoConfig(
        hidden_dim=768,
        video_length=32,
        resolution=(512, 512),
        fps=30,
        temporal_layers=6,
        diffusion_steps=100,
        use_mixed_precision=True,
        text_encoder_layers=8,
        max_text_length=256
    )
    
    model = TextToVideoModule(config)
    model.eval()
    
    prompts = [
        "A cinematic shot of a futuristic city at sunset",
        "A cat playing piano in a jazz club",
        "Underwater scene with colorful coral reef"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n📝 Generando video {i}/3: '{prompt}'")
        
        with torch.no_grad():
            video, metadata = model.generate_from_text(
                prompt,
                num_inference_steps=20,
                seed=42 + i
            )
        
        print(f"  ✅ Video generado:")
        print(f"     - Shape: {video.shape}")
        print(f"     - Resolución: {metadata.get('resolution')}")
        print(f"     - Frames: {metadata.get('num_frames')}")
        print(f"     - FPS: {metadata.get('fps')}")
        
        # Guardar video
        output_path = f"output_text2video_{i}.mp4"
        try:
            save_video_opencv(video, output_path, fps=config.fps)
            print(f"     - Guardado en: {output_path}")
        except Exception as e:
            print(f"     - Error al guardar: {e}")


def example_image_to_video_advanced():
    """Ejemplo avanzado de image-to-video con diferentes motion strengths."""
    print("\n" + "=" * 70)
    print("🖼️  Ejemplo Avanzado: Image-to-Video")
    print("=" * 70)
    
    config = ImageToVideoConfig(
        hidden_dim=512,
        video_length=24,
        resolution=(256, 256),
        fps=24,
        motion_strength=0.5,
        encoder_layers=4
    )
    
    model = ImageToVideoModule(config)
    model.eval()
    
    # Crear imagen dummy
    dummy_image = torch.randn(1, 3, 256, 256)
    
    motion_strengths = [0.3, 0.5, 0.7, 0.9]
    
    for i, strength in enumerate(motion_strengths, 1):
        print(f"\n🎨 Animando con motion_strength={strength}")
        
        with torch.no_grad():
            video, metadata = model.animate_image(
                dummy_image,
                num_inference_steps=15,
                motion_strength=strength,
                seed=100 + i
            )
        
        print(f"  ✅ Video animado:")
        print(f"     - Shape: {video.shape}")
        print(f"     - Motion Strength: {metadata.get('motion_strength')}")
        
        # Crear GIF
        output_path = f"output_image2video_strength_{strength}.gif"
        try:
            create_video_gif(video, output_path, fps=config.fps)
            print(f"     - GIF guardado en: {output_path}")
        except Exception as e:
            print(f"     - Error al guardar: {e}")


def example_video_to_video():
    """Ejemplo de video-to-video transformation."""
    print("\n" + "=" * 70)
    print("🔄 Ejemplo: Video-to-Video Transformation")
    print("=" * 70)
    
    config = VideoToVideoConfig(
        hidden_dim=512,
        video_length=16,
        resolution=(256, 256),
        fps=24,
        style_strength=0.6,
        enhancement_mode="denoise",
        temporal_consistency=0.8
    )
    
    model = VideoToVideoModule(config)
    model.eval()
    
    # Crear video de entrada
    input_video = torch.randn(1, 16, 3, 256, 256)
    
    # Crear referencia de estilo
    style_reference = torch.randn(1, 3, 256, 256)
    
    print("\n🎨 Transformando video con estilo...")
    
    with torch.no_grad():
        video, metadata = model.transform_video(
            input_video,
            style_reference=style_reference,
            num_inference_steps=10,
            seed=200
        )
    
    print(f"  ✅ Video transformado:")
    print(f"     - Shape: {video.shape}")
    print(f"     - Style Strength: {metadata.get('style_strength')}")
    print(f"     - Enhancement Mode: {metadata.get('enhancement_mode')}")
    print(f"     - Temporal Consistency: {metadata.get('temporal_consistency')}")


def example_diffusion_schedulers():
    """Ejemplo de diferentes schedulers de difusión."""
    print("\n" + "=" * 70)
    print("⏱️  Ejemplo: Diffusion Schedulers")
    print("=" * 70)
    
    scheduler_types = [
        SchedulerType.LINEAR,
        SchedulerType.COSINE,
        SchedulerType.QUADRATIC,
        SchedulerType.SIGMOID
    ]
    
    for scheduler_type in scheduler_types:
        print(f"\n📊 Scheduler: {scheduler_type.value}")
        
        scheduler = DiffusionScheduler(
            num_train_timesteps=1000,
            scheduler_type=scheduler_type
        )
        
        # Obtener timesteps para inferencia
        timesteps = scheduler.set_timesteps(50)
        
        print(f"  - Timesteps shape: {timesteps.shape}")
        print(f"  - First timestep: {timesteps[0].item()}")
        print(f"  - Last timestep: {timesteps[-1].item()}")
        print(f"  - Betas range: [{scheduler.betas.min():.6f}, {scheduler.betas.max():.6f}]")


def example_video_processing():
    """Ejemplo de procesamiento de video."""
    print("\n" + "=" * 70)
    print("🛠️  Ejemplo: Video Processing")
    print("=" * 70)
    
    # Crear video dummy
    video = torch.randn(1, 16, 3, 256, 256)
    
    print(f"\n📹 Video original:")
    print(f"  - Shape: {video.shape}")
    print(f"  - Range: [{video.min():.2f}, {video.max():.2f}]")
    
    # Normalizar
    video_norm = normalize_video(video, method="tanh")
    print(f"\n✨ Video normalizado (tanh):")
    print(f"  - Range: [{video_norm.min():.2f}, {video_norm.max():.2f}]")
    
    # Redimensionar
    video_resized = resize_video(video, size=(128, 128))
    print(f"\n📐 Video redimensionado a (128, 128):")
    print(f"  - Shape: {video_resized.shape}")
    
    # Redimensionar a mayor
    video_upscaled = resize_video(video, size=(512, 512))
    print(f"\n📈 Video upscaled a (512, 512):")
    print(f"  - Shape: {video_upscaled.shape}")


def example_comparison_configs():
    """Compara diferentes configuraciones de modelos."""
    print("\n" + "=" * 70)
    print("📊 Comparación de Configuraciones")
    print("=" * 70)
    
    configs = [
        ("Básica", TextToVideoConfig(
            hidden_dim=256,
            video_length=8,
            resolution=(128, 128),
            temporal_layers=2
        )),
        ("Media", TextToVideoConfig(
            hidden_dim=512,
            video_length=16,
            resolution=(256, 256),
            temporal_layers=4
        )),
        ("Alta", TextToVideoConfig(
            hidden_dim=768,
            video_length=32,
            resolution=(512, 512),
            temporal_layers=6
        )),
        ("Premium", TextToVideoConfig(
            hidden_dim=1024,
            video_length=64,
            resolution=(1024, 1024),
            temporal_layers=8,
            use_mixed_precision=True
        ))
    ]
    
    for name, config in configs:
        model = TextToVideoModule(config)
        params = model.count_parameters()
        
        # Calcular memoria aproximada (simplificado)
        memory_mb = (params * 4) / (1024 ** 2)  # Asumiendo float32
        
        print(f"\n{name}:")
        print(f"  - Parámetros: {params:,}")
        print(f"  - Memoria aprox: {memory_mb:.1f} MB")
        print(f"  - Frames: {config.video_length}")
        print(f"  - Resolución: {config.resolution}")
        print(f"  - Hidden Dim: {config.hidden_dim}")
        print(f"  - Temporal Layers: {config.temporal_layers}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Ejemplos Avanzados - Módulo Sora")
    print("=" * 70)
    
    # Ejemplo 1: Text-to-Video avanzado
    example_text_to_video_advanced()
    
    # Ejemplo 2: Image-to-Video avanzado
    example_image_to_video_advanced()
    
    # Ejemplo 3: Video-to-Video
    example_video_to_video()
    
    # Ejemplo 4: Diffusion Schedulers
    example_diffusion_schedulers()
    
    # Ejemplo 5: Video Processing
    example_video_processing()
    
    # Ejemplo 6: Comparación de configuraciones
    example_comparison_configs()
    
    print("\n" + "=" * 70)
    print("✨ Todos los ejemplos avanzados completados!")
    print("=" * 70 + "\n")


