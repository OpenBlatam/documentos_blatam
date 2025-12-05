#!/usr/bin/env python3
"""
Text-to-Video - Generación de Video desde Texto
================================================

Implementación de generación de video desde descripciones de texto,
similar a Sora 2.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple
import math

from .sora_base import VideoGenerationConfig, VideoGenerationModule
from core.error_handling import safe_execute
from core.utils import setup_logger

try:
    from pydantic import Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = setup_logger(__name__)


class TextToVideoConfig(VideoGenerationConfig):
    """
    Configuración para generación de video desde texto con validación mejorada.
    
    Attributes:
        text_encoder_dim: Dimensión del encoder de texto (default: 768)
        text_encoder_layers: Número de capas del encoder (default: 6)
        max_text_length: Longitud máxima del texto (default: 128)
        use_clip: Si usar CLIP para encoding de texto (default: True)
        text_dropout: Dropout en encoder de texto (default: 0.1)
    """
    if hasattr(VideoGenerationConfig, 'model_config'):  # Pydantic disponible
        text_encoder_dim: int = Field(default=768, ge=128, le=2048, description="Dimensión encoder texto")
        text_encoder_layers: int = Field(default=6, ge=1, le=24, description="Capas encoder")
        max_text_length: int = Field(default=128, ge=1, le=512, description="Longitud máxima texto")
        use_clip: bool = Field(default=True, description="Usar CLIP")
        text_dropout: float = Field(default=0.1, ge=0.0, le=1.0, description="Dropout texto")
    else:
        text_encoder_dim: int = 768
        text_encoder_layers: int = 6
        max_text_length: int = 128
        use_clip: bool = True
        text_dropout: float = 0.1


class TextEncoder(nn.Module):
    """Encoder de texto simplificado."""
    
    def __init__(self, config: TextToVideoConfig):
        super().__init__()
        self.config = config
        
        # Embedding de tokens
        self.token_embedding = nn.Embedding(
            config.max_text_length,
            config.text_encoder_dim
        )
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.text_encoder_dim,
            nhead=8,
            dim_feedforward=config.text_encoder_dim * 4,
            dropout=config.text_dropout,
            batch_first=True,
            activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=config.text_encoder_layers
        )
        
        # Proyección a hidden_dim
        self.proj = nn.Sequential(
            nn.Linear(config.text_encoder_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
    def forward(self, text_tokens: torch.Tensor) -> torch.Tensor:
        """
        Args:
            text_tokens: [batch, seq_len] - Tokens de texto
        Returns:
            [batch, hidden_dim] - Embedding de texto
        """
        # Embedding
        x = self.token_embedding(text_tokens)
        
        # Transformer
        x = self.transformer(x)
        
        # Pooling (promedio)
        x = x.mean(dim=1)
        
        # Proyección
        x = self.proj(x)
        
        return x


class TextToVideoModule(VideoGenerationModule):
    """
    Módulo de generación de video desde texto.
    
    Genera videos desde descripciones de texto usando:
    - Encoder de texto para procesar prompts
    - Arquitectura base de generación de video
    - Proceso de difusión para alta calidad
    """
    
    def __init__(self, config: TextToVideoConfig):
        super().__init__(config)
        self.config: TextToVideoConfig = config
        
        # Text encoder
        self.text_encoder = TextEncoder(config)
        
        # Proyección de condición
        self.condition_proj = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim)
        )
        
    def encode_text(self, text_tokens: torch.Tensor) -> torch.Tensor:
        """
        Codifica texto a embedding.
        
        Args:
            text_tokens: [batch, seq_len] - Tokens de texto
        Returns:
            [batch, hidden_dim] - Embedding de texto
        """
        return self.text_encoder(text_tokens)
    
    def forward(
        self,
        text_tokens: torch.Tensor,
        timestep: Optional[torch.Tensor] = None,
        use_cache: bool = False
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Genera video desde tokens de texto.
        
        Args:
            text_tokens: [batch, seq_len] - Tokens de texto
            timestep: [batch] - Timestep para difusión (opcional)
            use_cache: Si usar cache LRU
            
        Returns:
            video: [batch, frames, channels, height, width] - Video generado
            metadata: Diccionario con métricas
        """
        try:
            # Validar inputs
            if text_tokens.dim() != 2:
                raise ValueError(f"text_tokens debe ser 2D, recibido: {text_tokens.shape}")
            
            batch_size = text_tokens.shape[0]
            frames = self.config.video_length
            height, width = self.config.resolution
            
            # Codificar texto
            text_embedding = self.encode_text(text_tokens)  # [batch, hidden_dim]
            
            # Proyectar condición
            condition = self.condition_proj(text_embedding)  # [batch, hidden_dim]
            
            # Crear latente inicial (ruido aleatorio)
            latent = torch.randn(
                batch_size, frames, self.config.hidden_dim,
                height // 8, width // 8,  # Latent space más pequeño
                device=text_tokens.device,
                dtype=text_tokens.dtype
            )
            
            # Llamar al forward base
            video, metadata = super().forward(
                latent=latent,
                condition=condition,
                timestep=timestep,
                use_cache=use_cache
            )
            
            # Agregar metadata específica
            metadata.update({
                'text_length': text_tokens.shape[1],
                'text_embedding_norm': text_embedding.norm().item(),
            })
            
            return video, metadata
            
        except Exception as e:
            logger.error("Error en forward de TextToVideoModule", error=str(e), exc_info=True)
            batch_size = text_tokens.shape[0] if text_tokens.dim() >= 1 else 1
            empty_video = torch.zeros(
                batch_size, self.config.video_length, self.config.channels,
                *self.config.resolution,
                device=text_tokens.device
            )
            return empty_video, {'error': str(e)}
    
    def generate_from_text(
        self,
        text_prompt: str,
        num_inference_steps: Optional[int] = None,
        seed: Optional[int] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Genera video desde texto directamente.
        
        Args:
            text_prompt: Descripción del video a generar
            num_inference_steps: Número de pasos de inferencia
            seed: Semilla para reproducibilidad
            
        Returns:
            video: Video generado
            metadata: Información adicional
        """
        def _generate():
            if seed is not None:
                torch.manual_seed(seed)
            
            device = next(self.parameters()).device if list(self.parameters()) else torch.device('cpu')
            
            # Tokenizar texto (simplificado - en producción usar tokenizer real)
            # Por ahora, crear tokens dummy basados en longitud del texto
            text_length = min(len(text_prompt.split()), self.config.max_text_length)
            text_tokens = torch.randint(
                0, self.config.max_text_length,
                (1, text_length),
                device=device
            )
            
            # Proceso de difusión simplificado
            steps = num_inference_steps or self.config.diffusion_steps
            
            # Denoising loop
            with torch.no_grad():
                for step in range(steps):
                    timestep = torch.tensor([step], device=device)
                    video, metadata = self.forward(text_tokens, timestep=timestep)
            
            metadata.update({
                'prompt': text_prompt,
                'inference_steps': steps,
                'seed': seed,
            })
            
            return video, metadata
        
        result, error = safe_execute(
            _generate,
            default_value=(
                torch.zeros(1, self.config.video_length, self.config.channels, *self.config.resolution),
                {'error': 'Generation failed'}
            ),
            log_errors=True
        )
        
        if error:
            logger.error("Error generando video desde texto", error=str(error))
        
        return result

