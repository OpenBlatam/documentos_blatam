#!/usr/bin/env python3
"""
Presets - Configuraciones Predefinidas
========================================

Configuraciones predefinidas para diferentes casos de uso.
"""

from typing import Dict, Any, Optional
from enum import Enum

from sora import (
    TextToVideoConfig,
    ImageToVideoConfig,
    VideoToVideoConfig
)


class PresetType(Enum):
    """Tipos de presets."""
    FAST = "fast"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"
    ULTRA_QUALITY = "ultra_quality"
    LOW_RESOURCE = "low_resource"


class PresetManager:
    """
    Gestor de presets para configuraciones predefinidas.
    
    Proporciona configuraciones optimizadas para diferentes
    casos de uso y niveles de calidad.
    """
    
    @staticmethod
    def get_text_to_video_config(
        preset: PresetType = PresetType.BALANCED,
        resolution: Optional[tuple] = None,
        fps: Optional[int] = None
    ) -> TextToVideoConfig:
        """
        Obtiene configuración de text-to-video según preset.
        
        Args:
            preset: Tipo de preset
            resolution: Resolución personalizada (opcional)
            fps: FPS personalizado (opcional)
        
        Returns:
            Configuración de TextToVideo
        """
        presets = {
            PresetType.FAST: {
                'hidden_dim': 256,
                'video_length': 8,
                'resolution': (128, 128),
                'fps': 12,
                'diffusion_steps': 10
            },
            PresetType.BALANCED: {
                'hidden_dim': 512,
                'video_length': 16,
                'resolution': (256, 256),
                'fps': 24,
                'diffusion_steps': 20
            },
            PresetType.HIGH_QUALITY: {
                'hidden_dim': 768,
                'video_length': 24,
                'resolution': (512, 512),
                'fps': 30,
                'diffusion_steps': 50
            },
            PresetType.ULTRA_QUALITY: {
                'hidden_dim': 1024,
                'video_length': 32,
                'resolution': (768, 768),
                'fps': 30,
                'diffusion_steps': 100
            },
            PresetType.LOW_RESOURCE: {
                'hidden_dim': 128,
                'video_length': 4,
                'resolution': (64, 64),
                'fps': 8,
                'diffusion_steps': 5
            }
        }
        
        config_dict = presets.get(preset, presets[PresetType.BALANCED])
        
        if resolution:
            config_dict['resolution'] = resolution
        if fps:
            config_dict['fps'] = fps
        
        return TextToVideoConfig(**config_dict)
    
    @staticmethod
    def get_image_to_video_config(
        preset: PresetType = PresetType.BALANCED,
        resolution: Optional[tuple] = None,
        fps: Optional[int] = None,
        motion_strength: Optional[float] = None
    ) -> ImageToVideoConfig:
        """
        Obtiene configuración de image-to-video según preset.
        
        Args:
            preset: Tipo de preset
            resolution: Resolución personalizada
            fps: FPS personalizado
            motion_strength: Fuerza de movimiento
        
        Returns:
            Configuración de ImageToVideo
        """
        text_config = PresetManager.get_text_to_video_config(preset, resolution, fps)
        
        motion_strengths = {
            PresetType.FAST: 0.3,
            PresetType.BALANCED: 0.5,
            PresetType.HIGH_QUALITY: 0.7,
            PresetType.ULTRA_QUALITY: 0.8,
            PresetType.LOW_RESOURCE: 0.2
        }
        
        return ImageToVideoConfig(
            hidden_dim=text_config.hidden_dim,
            video_length=text_config.video_length,
            resolution=text_config.resolution,
            fps=text_config.fps,
            motion_strength=motion_strength or motion_strengths.get(preset, 0.5)
        )
    
    @staticmethod
    def get_video_to_video_config(
        preset: PresetType = PresetType.BALANCED
    ) -> VideoToVideoConfig:
        """
        Obtiene configuración de video-to-video según preset.
        
        Args:
            preset: Tipo de preset
        
        Returns:
            Configuración de VideoToVideo
        """
        style_strengths = {
            PresetType.FAST: 0.3,
            PresetType.BALANCED: 0.5,
            PresetType.HIGH_QUALITY: 0.7,
            PresetType.ULTRA_QUALITY: 0.9,
            PresetType.LOW_RESOURCE: 0.2
        }
        
        return VideoToVideoConfig(
            style_strength=style_strengths.get(preset, 0.5),
            temporal_consistency=0.8
        )
    
    @staticmethod
    def list_presets() -> Dict[str, Dict[str, Any]]:
        """
        Lista todos los presets disponibles.
        
        Returns:
            Diccionario con información de presets
        """
        return {
            'fast': {
                'description': 'Generación rápida, baja calidad',
                'use_case': 'Prototipado, pruebas rápidas',
                'estimated_time': '5-10 segundos',
                'resource_usage': 'Bajo'
            },
            'balanced': {
                'description': 'Balance entre calidad y velocidad',
                'use_case': 'Uso general, producción',
                'estimated_time': '20-30 segundos',
                'resource_usage': 'Medio'
            },
            'high_quality': {
                'description': 'Alta calidad, más tiempo',
                'use_case': 'Contenido profesional',
                'estimated_time': '60-90 segundos',
                'resource_usage': 'Alto'
            },
            'ultra_quality': {
                'description': 'Máxima calidad, mucho tiempo',
                'use_case': 'Contenido premium, final',
                'estimated_time': '3-5 minutos',
                'resource_usage': 'Muy alto'
            },
            'low_resource': {
                'description': 'Mínimos recursos, muy rápido',
                'use_case': 'Dispositivos limitados',
                'estimated_time': '2-5 segundos',
                'resource_usage': 'Muy bajo'
            }
        }


