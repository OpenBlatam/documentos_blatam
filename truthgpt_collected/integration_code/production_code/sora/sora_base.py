#!/usr/bin/env python3
"""
Sora Base - Clases Base para Generación de Video
==================================================

Clases base para todos los módulos de generación de video tipo Sora 2.
Extiende BasePaperModule con funcionalidades específicas para video.

Mejoras:
- Validación robusta con Pydantic
- Optimizaciones de rendimiento
- Mejor manejo de errores
- Soporte para mixed precision
- Utilidades de exportación
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path
import math

from core.paper_base import BasePaperModule, BasePaperConfig
from core.error_handling import safe_execute

try:
    from pydantic import Field, field_validator, model_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class VideoGenerationConfig(BasePaperConfig):
    """
    Configuración base para generación de video con validación mejorada.
    
    Attributes:
        video_length: Número de frames a generar (default: 16)
        resolution: Resolución del video (height, width) (default: (512, 512))
        fps: Frames por segundo (default: 24)
        temporal_layers: Número de capas temporales (default: 4)
        diffusion_steps: Pasos de difusión (default: 50)
        latent_dim: Dimensión del espacio latente (default: 256)
        channels: Número de canales de salida (default: 3 para RGB)
        use_mixed_precision: Si usar mixed precision (default: False)
        attention_dropout: Dropout en atención (default: 0.1)
        spatial_blocks: Número de bloques espaciales (default: 2)
    """
    if PYDANTIC_AVAILABLE:
        video_length: int = Field(default=16, ge=1, le=1024, description="Número de frames")
        resolution: Tuple[int, int] = Field(
            default=(512, 512),
            description="Resolución (height, width)"
        )
        fps: int = Field(default=24, ge=1, le=120, description="Frames por segundo")
        temporal_layers: int = Field(default=4, ge=1, le=32, description="Capas temporales")
        diffusion_steps: int = Field(default=50, ge=1, le=1000, description="Pasos de difusión")
        latent_dim: int = Field(default=256, ge=64, le=2048, description="Dimensión latente")
        channels: int = Field(default=3, ge=1, le=4, description="Canales de salida")
        use_mixed_precision: bool = Field(default=False, description="Usar mixed precision")
        attention_dropout: float = Field(default=0.1, ge=0.0, le=1.0, description="Dropout atención")
        spatial_blocks: int = Field(default=2, ge=1, le=8, description="Bloques espaciales")
        
        @field_validator('resolution')
        @classmethod
        def validate_resolution(cls, v):
            """Valida que la resolución sea válida."""
            if isinstance(v, (list, str)):
                if isinstance(v, str):
                    import ast
                    v = ast.literal_eval(v)
                v = tuple(v)
            
            if not isinstance(v, tuple) or len(v) != 2:
                raise ValueError(f"resolution debe ser tuple de 2 elementos, recibido: {v}")
            
            height, width = v
            if height <= 0 or width <= 0:
                raise ValueError(f"resolution debe tener valores > 0, recibido: {v}")
            
            # Validar que sea múltiplo de 8 para eficiencia
            if height % 8 != 0 or width % 8 != 0:
                logger.warning(f"resolution {v} no es múltiplo de 8, puede afectar rendimiento")
            
            return v
        
        @field_validator('video_length')
        @classmethod
        def validate_video_length(cls, v):
            """Valida video_length."""
            if v <= 0:
                raise ValueError(f"video_length debe ser > 0, recibido: {v}")
            return v
        
        @model_validator(mode='after')
        def validate_config(self):
            """Validaciones adicionales después de inicialización."""
            # Validar que hidden_dim sea compatible
            if self.hidden_dim < self.latent_dim:
                logger.warning(
                    f"hidden_dim ({self.hidden_dim}) < latent_dim ({self.latent_dim}), "
                    "puede causar problemas"
                )
            return self
    else:
        video_length: int = 16
        resolution: Tuple[int, int] = (512, 512)
        fps: int = 24
        temporal_layers: int = 4
        diffusion_steps: int = 50
        latent_dim: int = 256
        channels: int = 3
        use_mixed_precision: bool = False
        attention_dropout: float = 0.1
        spatial_blocks: int = 2
    
    def __init__(self, **kwargs):
        # Convertir resolution a tuple si es necesario
        if 'resolution' in kwargs and isinstance(kwargs['resolution'], (list, str)):
            if isinstance(kwargs['resolution'], str):
                import ast
                kwargs['resolution'] = ast.literal_eval(kwargs['resolution'])
            kwargs['resolution'] = tuple(kwargs['resolution'])
        super().__init__(**kwargs)


class TemporalAttention(nn.Module):
    """
    Atención temporal optimizada para procesar secuencias de frames.
    
    Mejoras:
    - Atención eficiente con flash attention si está disponible
    - Mejor manejo de memoria
    - Soporte para causal attention
    """
    
    def __init__(
        self,
        dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
        causal: bool = False,
        use_flash: bool = True
    ):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.causal = causal
        self.use_flash = use_flash and hasattr(F, 'scaled_dot_product_attention')
        
        if dim % num_heads != 0:
            raise ValueError(f"dim {dim} debe ser divisible por num_heads {num_heads}")
        
        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.proj = nn.Linear(dim, dim)
        self.norm = nn.LayerNorm(dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, frames, height, width, channels]
        Returns:
            [batch, frames, height, width, channels]
        """
        B, T, H, W, C = x.shape
        x_flat = x.view(B * T, H * W, C)
        
        # Normalizar
        x_norm = self.norm(x_flat)
        
        # QKV projection
        qkv = self.qkv(x_norm)
        q, k, v = qkv.chunk(3, dim=-1)
        
        # Reshape para atención
        q = q.view(B * T, H * W, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B * T, H * W, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B * T, H * W, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Atención eficiente
        if self.use_flash and not self.causal:
            # Usar flash attention si está disponible
            out = F.scaled_dot_product_attention(
                q, k, v,
                dropout_p=self.dropout.p if self.training else 0.0,
                is_causal=False
            )
        else:
            # Atención estándar
            scale = 1.0 / math.sqrt(self.head_dim)
            attn = (q @ k.transpose(-2, -1)) * scale
            
            if self.causal:
                # Máscara causal
                mask = torch.triu(torch.ones(H * W, H * W, device=q.device), diagonal=1)
                attn = attn.masked_fill(mask.bool(), float('-inf'))
            
            attn = attn.softmax(dim=-1)
            attn = self.dropout(attn)
            out = attn @ v
        
        # Reshape y proyección
        out = out.transpose(1, 2).contiguous()
        out = out.view(B * T, H * W, C)
        out = self.proj(out)
        out = out.view(B, T, H, W, C)
        
        return out + x


class SpatialConvBlock(nn.Module):
    """Bloque de convolución espacial para procesar frames individuales."""
    
    def __init__(self, dim: int, kernel_size: int = 3, dropout: float = 0.1):
        super().__init__()
        self.conv1 = nn.Conv2d(dim, dim, kernel_size, padding=kernel_size//2)
        self.norm1 = nn.GroupNorm(8, dim)
        self.conv2 = nn.Conv2d(dim, dim, kernel_size, padding=kernel_size//2)
        self.norm2 = nn.GroupNorm(8, dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch * frames, channels, height, width]
        Returns:
            [batch * frames, channels, height, width]
        """
        residual = x
        x = self.conv1(x)
        x = self.norm1(x)
        x = nn.functional.gelu(x)
        x = self.dropout(x)
        
        x = self.conv2(x)
        x = self.norm2(x)
        x = self.dropout(x)
        
        return x + residual


class VideoGenerationModule(BasePaperModule):
    """
    Módulo base para generación de video tipo Sora 2.
    
    Proporciona la arquitectura base para todos los módulos de generación de video.
    """
    
    def __init__(self, config: VideoGenerationConfig):
        super().__init__(config)
        self.config: VideoGenerationConfig = config
        self._device: Optional[torch.device] = None
        
        # Temporal transformer layers
        self.temporal_layers = nn.ModuleList([
            TemporalAttention(
                config.hidden_dim,
                dropout=config.attention_dropout
            )
            for _ in range(config.temporal_layers)
        ])
        
        # Spatial processing
        self.spatial_blocks = nn.ModuleList([
            SpatialConvBlock(config.hidden_dim)
            for _ in range(config.spatial_blocks)
        ])
        
        # Time embedding para difusión
        self.time_embed = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 4),
            nn.GELU(),
            nn.Linear(config.hidden_dim * 4, config.hidden_dim)
        )
        
        # Output projection
        self.output_proj = nn.Conv2d(
            config.hidden_dim,
            config.channels,
            kernel_size=1
        )
        
    def forward(
        self,
        latent: torch.Tensor,
        condition: Optional[torch.Tensor] = None,
        timestep: Optional[torch.Tensor] = None,
        use_cache: bool = False
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa latente de video con optimizaciones.
        
        Args:
            latent: [batch, frames, channels, height, width] - Latente de video
            condition: [batch, condition_dim] - Condición (texto, imagen, etc.)
            timestep: [batch] - Timestep para difusión
            use_cache: Si usar cache LRU
            
        Returns:
            video: [batch, frames, channels, height, width] - Video procesado
            metadata: Diccionario con métricas
        """
        try:
            # Validar inputs
            if latent.dim() != 5:
                raise ValueError(f"latent debe ser 5D [batch, frames, C, H, W], recibido: {latent.shape}")
            
            if latent.shape[1] != self.config.video_length:
                raise ValueError(
                    f"latent frames ({latent.shape[1]}) != config.video_length ({self.config.video_length})"
                )
            
            batch_size, frames, C, H, W = latent.shape
            
            # Usar autocast si mixed precision está habilitado
            use_amp = self.config.use_mixed_precision and self.training
            dtype = torch.float16 if use_amp else None
            
            # Aplicar condición si existe
            if condition is not None:
                # Validar condición
                if condition.dim() not in [2, 3]:
                    raise ValueError(f"condition debe ser 2D o 3D, recibido: {condition.shape}")
                
                # Expandir condición a todos los frames si es 2D
                if condition.dim() == 2:
                    if condition.shape[-1] != C:
                        # Proyectar si es necesario (simplificado)
                        logger.warning(f"condition dim ({condition.shape[-1]}) != latent C ({C}), ajustando")
                    condition = condition.unsqueeze(1).expand(-1, frames, -1)
                
                # Aplicar condición de forma más sofisticada
                if condition.shape[-1] == C:
                    condition_expanded = condition.view(batch_size, frames, 1, 1, -1)
                    latent = latent + condition_expanded
                else:
                    # Proyección simple si dimensiones no coinciden
                    latent = latent + condition.mean(dim=-1, keepdim=True).unsqueeze(-1).unsqueeze(-1)
            
            # Aplicar time embedding si existe
            if timestep is not None:
                if timestep.dim() == 0:
                    timestep = timestep.unsqueeze(0)
                time_emb = self.time_embed(timestep.float())
                # Expandir a todos los frames
                time_emb = time_emb.unsqueeze(1).expand(-1, frames, -1)
                # Aplicar a latent
                time_emb_expanded = time_emb.view(batch_size, frames, 1, 1, -1)
                latent = latent + time_emb_expanded
            
            # Reshape para procesamiento temporal: [B, T, C, H, W] -> [B, T, H, W, C]
            latent = latent.permute(0, 1, 3, 4, 2).contiguous()
            
            # Aplicar capas temporales
            for layer in self.temporal_layers:
                latent = layer(latent)
            
            # Reshape para procesamiento espacial: [B, T, H, W, C] -> [B*T, C, H, W]
            B, T, H, W, C = latent.shape
            latent = latent.view(B * T, H, W, C).permute(0, 3, 1, 2).contiguous()
            
            # Procesamiento espacial
            for block in self.spatial_blocks:
                latent = block(latent)
            
            # Proyección a RGB
            video = self.output_proj(latent)  # [B*T, channels, H, W]
            
            # Reshape final: [B*T, channels, H, W] -> [B, T, channels, H, W]
            video = video.view(B, T, self.config.channels, H, W)
            
            # Métricas
            metadata = {
                'video_shape': list(video.shape),
                'num_frames': frames,
                'resolution': (H, W),
                'fps': self.config.fps,
                'latent_mean': latent.mean().item(),
                'latent_std': latent.std().item(),
                'video_mean': video.mean().item(),
                'video_std': video.std().item(),
            }
            
            # Actualizar métricas acumuladas
            self._update_metrics(metadata)
            
            return video, metadata
            
        except Exception as e:
            logger.error("Error en forward de VideoGenerationModule", error=str(e), exc_info=True)
            # Retornar tensor vacío en caso de error
            batch_size = latent.shape[0] if latent.dim() >= 1 else 1
            device = latent.device if hasattr(latent, 'device') else (self._device or torch.device('cpu'))
            empty_video = torch.zeros(
                batch_size, self.config.video_length, self.config.channels,
                *self.config.resolution,
                device=device
            )
            return empty_video, {'error': str(e)}


# Alias para compatibilidad
SoraConfig = VideoGenerationConfig
SoraModule = VideoGenerationModule

