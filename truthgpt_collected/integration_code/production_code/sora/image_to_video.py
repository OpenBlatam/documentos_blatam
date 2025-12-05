#!/usr/bin/env python3
"""
Image-to-Video - Animación de Imágenes Estáticas
==================================================

Implementación de animación de imágenes estáticas en videos,
similar a las capacidades de Sora 2.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple
import torch.nn.functional as F

from .sora_base import VideoGenerationConfig, VideoGenerationModule
from core.error_handling import safe_execute
from core.utils import setup_logger

try:
    from pydantic import Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = setup_logger(__name__)


class ImageToVideoConfig(VideoGenerationConfig):
    """
    Configuración para animación de imágenes con validación mejorada.
    
    Attributes:
        image_encoder_dim: Dimensión del encoder de imagen (default: 512)
        motion_strength: Fuerza del movimiento (0.0 a 1.0) (default: 0.5)
        use_vae: Si usar VAE para encoding de imagen (default: True)
        encoder_layers: Número de capas en encoder (default: 3)
    """
    if hasattr(VideoGenerationConfig, 'model_config'):  # Pydantic disponible
        image_encoder_dim: int = Field(default=512, ge=128, le=1024, description="Dimensión encoder imagen")
        motion_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Fuerza movimiento")
        use_vae: bool = Field(default=True, description="Usar VAE")
        encoder_layers: int = Field(default=3, ge=1, le=8, description="Capas encoder")
    else:
        image_encoder_dim: int = 512
        motion_strength: float = 0.5
        use_vae: bool = True
        encoder_layers: int = 3


class ImageEncoder(nn.Module):
    """Encoder de imagen simplificado."""
    
    def __init__(self, config: ImageToVideoConfig):
        super().__init__()
        self.config = config
        
        # Encoder CNN
        self.encoder = nn.Sequential(
            # Downsample 1
            nn.Conv2d(3, 64, 3, padding=1),
            nn.GroupNorm(8, 64),
            nn.GELU(),
            nn.Conv2d(64, 64, 3, padding=1, stride=2),
            
            # Downsample 2
            nn.GroupNorm(8, 64),
            nn.GELU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.GroupNorm(8, 128),
            nn.GELU(),
            nn.Conv2d(128, 128, 3, padding=1, stride=2),
            
            # Downsample 3
            nn.GroupNorm(8, 128),
            nn.GELU(),
            nn.Conv2d(128, 256, 3, padding=1),
            nn.GroupNorm(8, 256),
            nn.GELU(),
            nn.Conv2d(256, config.image_encoder_dim, 3, padding=1, stride=2),
        )
        
        # Proyección a hidden_dim
        self.proj = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(config.image_encoder_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
    def forward(self, image: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            image: [batch, 3, height, width] - Imagen RGB
        Returns:
            features: [batch, hidden_dim] - Features globales
            spatial_features: [batch, channels, H, W] - Features espaciales
        """
        # Encoder
        spatial_features = self.encoder(image)  # [batch, image_encoder_dim, H/8, W/8]
        
        # Features globales
        features = self.proj(spatial_features)  # [batch, hidden_dim]
        
        return features, spatial_features


class ImageToVideoModule(VideoGenerationModule):
    """
    Módulo de animación de imágenes estáticas.
    
    Anima imágenes estáticas en videos usando:
    - Encoder de imagen para extraer features
    - Generación de movimiento basada en features
    - Proceso de difusión para alta calidad
    """
    
    def __init__(self, config: ImageToVideoConfig):
        super().__init__(config)
        self.config: ImageToVideoConfig = config
        
        # Image encoder
        self.image_encoder = ImageEncoder(config)
        
        # Motion generator
        self.motion_generator = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
        # Proyección de condición
        self.condition_proj = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
    def encode_image(self, image: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Codifica imagen a features.
        
        Args:
            image: [batch, 3, height, width] - Imagen RGB
        Returns:
            global_features: [batch, hidden_dim] - Features globales
            spatial_features: [batch, channels, H, W] - Features espaciales
        """
        return self.image_encoder(image)
    
    def forward(
        self,
        image: torch.Tensor,
        timestep: Optional[torch.Tensor] = None,
        use_cache: bool = False
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Anima imagen estática en video.
        
        Args:
            image: [batch, 3, height, width] - Imagen estática
            timestep: [batch] - Timestep para difusión (opcional)
            use_cache: Si usar cache LRU
            
        Returns:
            video: [batch, frames, channels, height, width] - Video animado
            metadata: Diccionario con métricas
        """
        try:
            # Validar inputs
            if image.dim() != 4:
                raise ValueError(f"image debe ser 4D [batch, 3, H, W], recibido: {image.shape}")
            
            batch_size = image.shape[0]
            frames = self.config.video_length
            height, width = self.config.resolution
            
            # Codificar imagen
            global_features, spatial_features = self.encode_image(image)
            
            # Generar movimiento
            motion_features = self.motion_generator(global_features)
            
            # Proyectar condición
            condition = self.condition_proj(global_features)
            
            # Expandir spatial features a todos los frames con variación temporal
            # [batch, channels, H, W] -> [batch, frames, channels, H, W]
            latent_height, latent_width = spatial_features.shape[2], spatial_features.shape[3]
            
            # Crear latente inicial basado en imagen
            base_latent = spatial_features.unsqueeze(1).expand(-1, frames, -1, -1, -1)
            
            # Agregar variación temporal
            motion_noise = torch.randn(
                batch_size, frames, self.config.hidden_dim,
                latent_height, latent_width,
                device=image.device,
                dtype=image.dtype
            ) * self.config.motion_strength
            
            # Combinar imagen base con movimiento
            latent = base_latent + motion_noise
            
            # Llamar al forward base
            video, metadata = super().forward(
                latent=latent,
                condition=condition,
                timestep=timestep,
                use_cache=use_cache
            )
            
            # Agregar metadata específica
            metadata.update({
                'image_shape': list(image.shape),
                'motion_strength': self.config.motion_strength,
                'image_features_norm': global_features.norm().item(),
            })
            
            return video, metadata
            
        except Exception as e:
            logger.error("Error en forward de ImageToVideoModule", error=str(e), exc_info=True)
            batch_size = image.shape[0] if image.dim() >= 1 else 1
            empty_video = torch.zeros(
                batch_size, self.config.video_length, self.config.channels,
                *self.config.resolution,
                device=image.device
            )
            return empty_video, {'error': str(e)}
    
    def animate_image(
        self,
        image: torch.Tensor,
        num_inference_steps: Optional[int] = None,
        motion_strength: Optional[float] = None,
        seed: Optional[int] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Anima imagen estática en video.
        
        Args:
            image: [batch, 3, height, width] - Imagen estática
            num_inference_steps: Número de pasos de inferencia
            motion_strength: Fuerza del movimiento (sobrescribe config)
            seed: Semilla para reproducibilidad
            
        Returns:
            video: Video animado
            metadata: Información adicional
        """
        def _animate():
            if seed is not None:
                torch.manual_seed(seed)
            
            device = image.device if hasattr(image, 'device') else next(self.parameters()).device if list(self.parameters()) else torch.device('cpu')
            
            # Actualizar motion_strength si se proporciona
            if motion_strength is not None:
                self.config.motion_strength = motion_strength
            
            # Proceso de difusión simplificado
            steps = num_inference_steps or self.config.diffusion_steps
            
            # Denoising loop
            with torch.no_grad():
                for step in range(steps):
                    timestep = torch.tensor([step], device=device)
                    video, metadata = self.forward(image, timestep=timestep)
            
            metadata.update({
                'inference_steps': steps,
                'motion_strength': self.config.motion_strength,
                'seed': seed,
            })
            
            return video, metadata
        
        result, error = safe_execute(
            _animate,
            default_value=(
                torch.zeros(image.shape[0] if image.dim() >= 1 else 1, self.config.video_length, self.config.channels, *self.config.resolution, device=image.device),
                {'error': 'Animation failed'}
            ),
            log_errors=True
        )
        
        if error:
            logger.error("Error animando imagen", error=str(error))
        
        return result

