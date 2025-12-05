#!/usr/bin/env python3
"""
Ejemplo de uso del módulo Sora
===============================

Demuestra cómo usar los diferentes módulos de generación de video.
"""

import torch
from sora import (
    TextToVideoConfig,
    TextToVideoModule,
    ImageToVideoConfig,
    ImageToVideoModule
)


def example_text_to_video():
    """Ejemplo de generación de video desde texto."""
    print("=" * 60)
    print("🎬 Ejemplo: Text-to-Video")
    print("=" * 60)
    
    # Crear configuración
    config = TextToVideoConfig(
        hidden_dim=512,
        video_length=16,
        resolution=(256, 256),  # Resolución más pequeña para ejemplo
        fps=24,
        temporal_layers=2,  # Menos capas para ejemplo rápido
        diffusion_steps=10,  # Menos pasos para ejemplo rápido
        text_encoder_dim=768
    )
    
    print(f"\n📋 Configuración:")
    print(f"  - Frames: {config.video_length}")
    print(f"  - Resolución: {config.resolution}")
    print(f"  - FPS: {config.fps}")
    print(f"  - Capas temporales: {config.temporal_layers}")
    
    # Crear modelo
    model = TextToVideoModule(config)
    model.eval()
    
    print(f"\n✅ Modelo creado:")
    print(f"  - Parámetros totales: {model.count_parameters():,}")
    print(f"  - Device: {model.device}")
    print(f"  - Dtype: {model.dtype}")
    
    # Generar video desde texto
    prompts = [
        "A beautiful sunset over the ocean with waves crashing",
        "A cat playing with a ball of yarn",
        "A futuristic city with flying cars"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n🎨 Generando video {i}/3: '{prompt}'")
        
        with torch.no_grad():
            video, metadata = model.generate_from_text(
                prompt,
                num_inference_steps=5,
                seed=42 + i
            )
        
        print(f"  ✅ Video generado:")
        print(f"     - Shape: {video.shape}")
        print(f"     - Resolución: {metadata.get('resolution')}")
        print(f"     - Frames: {metadata.get('num_frames')}")
        print(f"     - Media: {metadata.get('video_mean', 0):.4f}")
        print(f"     - Std: {metadata.get('video_std', 0):.4f}")
    
    # Guardar modelo
    save_path = "text_to_video_model.pt"
    model.save_model(save_path)
    print(f"\n💾 Modelo guardado en: {save_path}")
    
    # Información del modelo
    info = model.get_model_info()
    print(f"\n📊 Información del modelo:")
    for key, value in info.items():
        if isinstance(value, (int, float)):
            if 'parameters' in key.lower():
                print(f"  - {key}: {value:,}")
            else:
                print(f"  - {key}: {value}")


def example_image_to_video():
    """Ejemplo de animación de imágenes."""
    print("\n" + "=" * 60)
    print("🖼️  Ejemplo: Image-to-Video")
    print("=" * 60)
    
    # Crear configuración
    config = ImageToVideoConfig(
        hidden_dim=512,
        video_length=16,
        resolution=(256, 256),
        fps=24,
        temporal_layers=2,
        motion_strength=0.5
    )
    
    print(f"\n📋 Configuración:")
    print(f"  - Frames: {config.video_length}")
    print(f"  - Resolución: {config.resolution}")
    print(f"  - FPS: {config.fps}")
    print(f"  - Motion Strength: {config.motion_strength}")
    
    # Crear modelo
    model = ImageToVideoModule(config)
    model.eval()
    
    print(f"\n✅ Modelo creado:")
    print(f"  - Parámetros totales: {model.count_parameters():,}")
    print(f"  - Device: {model.device}")
    
    # Crear imagen dummy (en producción, cargar imagen real)
    dummy_image = torch.randn(1, 3, 256, 256)
    
    print(f"\n🎨 Animando imagen...")
    
    with torch.no_grad():
        video, metadata = model.animate_image(
            dummy_image,
            num_inference_steps=5,
            motion_strength=0.7,
            seed=123
        )
    
    print(f"  ✅ Video animado:")
    print(f"     - Shape: {video.shape}")
    print(f"     - Resolución: {metadata.get('resolution')}")
    print(f"     - Frames: {metadata.get('num_frames')}")
    print(f"     - Motion Strength: {metadata.get('motion_strength')}")
    print(f"     - Media: {metadata.get('video_mean', 0):.4f}")
    
    # Guardar modelo
    save_path = "image_to_video_model.pt"
    model.save_model(save_path)
    print(f"\n💾 Modelo guardado en: {save_path}")


def example_comparison():
    """Compara diferentes configuraciones."""
    print("\n" + "=" * 60)
    print("📊 Comparación de Configuraciones")
    print("=" * 60)
    
    configs = [
        ("Pequeña", TextToVideoConfig(
            hidden_dim=256,
            video_length=8,
            resolution=(128, 128),
            temporal_layers=1
        )),
        ("Mediana", TextToVideoConfig(
            hidden_dim=512,
            video_length=16,
            resolution=(256, 256),
            temporal_layers=2
        )),
        ("Grande", TextToVideoConfig(
            hidden_dim=1024,
            video_length=32,
            resolution=(512, 512),
            temporal_layers=4
        ))
    ]
    
    for name, config in configs:
        model = TextToVideoModule(config)
        params = model.count_parameters()
        
        print(f"\n{name}:")
        print(f"  - Parámetros: {params:,}")
        print(f"  - Frames: {config.video_length}")
        print(f"  - Resolución: {config.resolution}")
        print(f"  - Hidden Dim: {config.hidden_dim}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎬 Ejemplos de Uso - Módulo Sora")
    print("=" * 60)
    
    # Ejemplo 1: Text-to-Video
    example_text_to_video()
    
    # Ejemplo 2: Image-to-Video
    example_image_to_video()
    
    # Ejemplo 3: Comparación
    example_comparison()
    
    print("\n" + "=" * 60)
    print("✨ Todos los ejemplos completados!")
    print("=" * 60 + "\n")


