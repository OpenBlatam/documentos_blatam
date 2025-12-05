#!/usr/bin/env python3
"""
Integración de Sora con otros módulos
======================================

Integra el módulo Sora con memory y redundancy para mejor rendimiento.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import torch.nn as nn

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)

# Importar módulos opcionales
try:
    from memory import Paper2506_15841v2_MemorySystem, Paper2506_15841v2Config
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from redundancy import Paper2510_00071_RedundancySuppressor, Paper2510_00071Config
    REDUNDANCY_AVAILABLE = True
except ImportError:
    REDUNDANCY_AVAILABLE = False

try:
    from best import (
        Paper2506_10848v2_BestTechniques,
        Paper2506_10848v2Config,
        Paper2510_04871v1_BestTechniques,
        Paper2510_04871v1Config,
        GatedAttention,
        AdaptiveLayerNorm,
        EnsembleAttention
    )
    try:
        from best import PAPER_2506_10848_AVAILABLE, PAPER_2510_04871_AVAILABLE
    except ImportError:
        PAPER_2506_10848_AVAILABLE = Paper2506_10848v2_BestTechniques is not None
        PAPER_2510_04871_AVAILABLE = Paper2510_04871v1_BestTechniques is not None
    BEST_AVAILABLE = True
except ImportError:
    BEST_AVAILABLE = False
    PAPER_2506_10848_AVAILABLE = False
    PAPER_2510_04871_AVAILABLE = False
    Paper2506_10848v2_BestTechniques = None
    Paper2506_10848v2Config = None
    Paper2510_04871v1_BestTechniques = None
    Paper2510_04871v1Config = None
    GatedAttention = None
    AdaptiveLayerNorm = None
    EnsembleAttention = None

from .sora_base import VideoGenerationModule, VideoGenerationConfig


class SoraWithMemory(VideoGenerationModule):
    """
    Sora integrado con sistema de memoria para mejor contexto.
    
    Mejoras:
    - Memoria episódica para recordar generaciones previas
    - Mejor coherencia temporal
    - Contexto persistente entre generaciones
    """
    
    def __init__(
        self,
        base_config: VideoGenerationConfig,
        memory_config: Optional[Any] = None,
        enable_memory: bool = True
    ):
        super().__init__(base_config)
        
        self.enable_memory = enable_memory and MEMORY_AVAILABLE
        
        if self.enable_memory:
            if memory_config is None:
                memory_config = Paper2506_15841v2Config(
                    memory_dim=base_config.hidden_dim,
                    max_memory_size=1000,
                    enable_cache=True
                )
            self.memory_system = Paper2506_15841v2_MemorySystem(memory_config)
            logger.info("Sora con memoria habilitada")
        else:
            self.memory_system = None
            logger.info("Sora sin memoria (módulo no disponible)")
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con memoria integrada.
        
        Args:
            hidden_states: Tensor de video [batch, frames, height, width, channels]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        # Procesar con modelo base
        base_output, base_metadata = super().forward(hidden_states, **kwargs)
        
        # Aplicar memoria si está habilitada
        if self.enable_memory and self.memory_system:
            # Extraer features para memoria
            batch_size, frames, height, width, channels = base_output.shape
            # Usar último frame como query
            last_frame = base_output[:, -1, :, :, :].mean(dim=(1, 2))  # [batch, channels]
            
            # Almacenar en memoria
            self.memory_system.store_episode(
                last_frame,
                metadata={
                    'frames': frames,
                    'resolution': (height, width),
                    'timestamp': kwargs.get('timestamp')
                }
            )
            
            # Recuperar contexto de memoria
            retrieved, weights = self.memory_system.retrieve_episodes(last_frame, k=5)
            
            if retrieved.size(0) > 0 and retrieved.size(1) > 0:
                # Integrar memoria en output
                memory_contribution = (retrieved * weights.unsqueeze(-1)).sum(dim=1)
                # Expandir a toda la secuencia
                memory_contribution = memory_contribution.unsqueeze(1).unsqueeze(1).unsqueeze(1)
                memory_contribution = memory_contribution.expand(-1, frames, height, width, -1)
                
                # Combinar con output (solo en canales compatibles)
                if memory_contribution.size(-1) == channels:
                    base_output = base_output + memory_contribution * 0.1  # Peso pequeño
            
            # Actualizar metadata
            base_metadata['memory_used'] = True
            base_metadata['memory_episodes'] = len(self.memory_system.episodic_memory) if self.memory_system else 0
        
        return base_output, base_metadata


class SoraWithRedundancySuppression(VideoGenerationModule):
    """
    Sora con supresión de redundancia para mejor eficiencia.
    
    Mejoras:
    - Elimina frames redundantes antes de procesar
    - Reduce carga computacional
    - Mantiene calidad visual
    """
    
    def __init__(
        self,
        base_config: VideoGenerationConfig,
        redundancy_config: Optional[Any] = None,
        enable_redundancy: bool = True
    ):
        super().__init__(base_config)
        
        self.enable_redundancy = enable_redundancy and REDUNDANCY_AVAILABLE
        
        if self.enable_redundancy:
            if redundancy_config is None:
                redundancy_config = Paper2510_00071Config(
                    similarity_threshold=0.9,
                    enable_caching=True
                )
            self.redundancy_suppressor = Paper2510_00071_RedundancySuppressor(redundancy_config)
            logger.info("Sora con supresión de redundancia habilitada")
        else:
            self.redundancy_suppressor = None
            logger.info("Sora sin supresión de redundancia (módulo no disponible)")
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con supresión de redundancia.
        
        Args:
            hidden_states: Tensor de video [batch, frames, height, width, channels]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        # Aplicar supresión de redundancia si está habilitada
        if self.enable_redundancy and self.redundancy_suppressor:
            # Convertir a formato [batch, frames, features] para redundancy
            batch_size, frames, height, width, channels = hidden_states.shape
            # Aplanar espacialmente
            flattened = hidden_states.view(batch_size, frames, height * width * channels)
            
            # Aplicar supresión de redundancia
            unique_frames, redundancy_stats = self.redundancy_suppressor.process_bulk(flattened)
            
            # Reshape de vuelta
            unique_frames = unique_frames.view(-1, frames, height, width, channels)
            
            # Procesar con modelo base
            base_output, base_metadata = super().forward(unique_frames, **kwargs)
            
            # Actualizar metadata
            base_metadata['redundancy_suppressed'] = True
            base_metadata['redundancy_stats'] = redundancy_stats
        else:
            # Procesar normalmente
            base_output, base_metadata = super().forward(hidden_states, **kwargs)
        
        return base_output, base_metadata


class SoraIntegrated(VideoGenerationModule):
    """
    Sora completamente integrado con memoria y redundancia.
    
    Mejoras:
    - Memoria para contexto persistente
    - Supresión de redundancia para eficiencia
    - Mejor calidad y rendimiento
    """
    
    def __init__(
        self,
        base_config: VideoGenerationConfig,
        memory_config: Optional[Any] = None,
        redundancy_config: Optional[Any] = None,
        enable_memory: bool = True,
        enable_redundancy: bool = True
    ):
        super().__init__(base_config)
        
        # Memoria
        self.enable_memory = enable_memory and MEMORY_AVAILABLE
        if self.enable_memory:
            if memory_config is None:
                memory_config = Paper2506_15841v2Config(
                    memory_dim=base_config.hidden_dim,
                    max_memory_size=1000,
                    enable_cache=True
                )
            self.memory_system = Paper2506_15841v2_MemorySystem(memory_config)
        
        # Redundancia
        self.enable_redundancy = enable_redundancy and REDUNDANCY_AVAILABLE
        if self.enable_redundancy:
            if redundancy_config is None:
                redundancy_config = Paper2510_00071Config(
                    similarity_threshold=0.9,
                    enable_caching=True
                )
            self.redundancy_suppressor = Paper2510_00071_RedundancySuppressor(redundancy_config)
        
        logger.info(
            "Sora integrado inicializado",
            memory=self.enable_memory,
            redundancy=self.enable_redundancy
        )
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con todas las integraciones.
        
        Args:
            hidden_states: Tensor de video
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        # 1. Supresión de redundancia (si está habilitada)
        if self.enable_redundancy and self.redundancy_suppressor:
            batch_size, frames, height, width, channels = hidden_states.shape
            flattened = hidden_states.view(batch_size, frames, height * width * channels)
            unique_frames, redundancy_stats = self.redundancy_suppressor.process_bulk(flattened)
            hidden_states = unique_frames.view(-1, frames, height, width, channels)
        
        # 2. Procesar con modelo base
        base_output, base_metadata = super().forward(hidden_states, **kwargs)
        
        # 3. Aplicar memoria (si está habilitada)
        if self.enable_memory and self.memory_system:
            batch_size, frames, height, width, channels = base_output.shape
            last_frame = base_output[:, -1, :, :, :].mean(dim=(1, 2))
            
            # Almacenar
            self.memory_system.store_episode(
                last_frame,
                metadata={'frames': frames, 'resolution': (height, width)}
            )
            
            # Recuperar
            retrieved, weights = self.memory_system.retrieve_episodes(last_frame, k=5)
            
            if retrieved.size(0) > 0 and retrieved.size(1) > 0:
                memory_contribution = (retrieved * weights.unsqueeze(-1)).sum(dim=1)
                memory_contribution = memory_contribution.unsqueeze(1).unsqueeze(1).unsqueeze(1)
                memory_contribution = memory_contribution.expand(-1, frames, height, width, -1)
                
                if memory_contribution.size(-1) == channels:
                    base_output = base_output + memory_contribution * 0.1
        
        # 4. Metadata completa
        metadata = {
            **base_metadata,
            'memory_enabled': self.enable_memory,
            'redundancy_enabled': self.enable_redundancy
        }
        
        if self.enable_memory and self.memory_system:
            metadata['memory_episodes'] = len(self.memory_system.episodic_memory)
        
        if self.enable_redundancy and self.redundancy_suppressor:
            metadata['redundancy_stats'] = redundancy_stats if 'redundancy_stats' in locals() else {}
        
        return base_output, metadata


class SoraWithBestTechniques(VideoGenerationModule):
    """
    Sora integrado con Best Techniques para mejor rendimiento.
    
    Mejoras:
    - Gated Attention para mejor atención en video
    - Adaptive LayerNorm para normalización adaptativa
    - Ensemble Attention para diversidad de atención
    - Mejor calidad y estabilidad en generación
    """
    
    def __init__(
        self,
        base_config: VideoGenerationConfig,
        best_config: Optional[Any] = None,
        best_paper_type: str = "2506_10848v2",
        enable_gated_attention: bool = True,
        enable_adaptive_norm: bool = True,
        enable_ensemble: bool = False
    ):
        super().__init__(base_config)
        
        self.enable_best = enable_gated_attention or enable_adaptive_norm or enable_ensemble
        self.enable_best = self.enable_best and BEST_AVAILABLE
        
        if self.enable_best:
            if best_config is None:
                if best_paper_type == "2506_10848v2" and PAPER_2506_10848_AVAILABLE:
                    best_config = Paper2506_10848v2Config(hidden_dim=base_config.hidden_dim)
                    self.best_model = Paper2506_10848v2_BestTechniques(best_config)
                elif best_paper_type == "2510_04871v1" and PAPER_2510_04871_AVAILABLE:
                    best_config = Paper2510_04871v1Config(hidden_dim=base_config.hidden_dim)
                    self.best_model = Paper2510_04871v1_BestTechniques(best_config)
                else:
                    self.best_model = None
            else:
                if best_paper_type == "2506_10848v2" and PAPER_2506_10848_AVAILABLE:
                    self.best_model = Paper2506_10848v2_BestTechniques(best_config)
                elif best_paper_type == "2510_04871v1" and PAPER_2510_04871_AVAILABLE:
                    self.best_model = Paper2510_04871v1_BestTechniques(best_config)
                else:
                    self.best_model = None
            
            self.enable_gated_attention = enable_gated_attention and GatedAttention is not None
            self.enable_adaptive_norm = enable_adaptive_norm and AdaptiveLayerNorm is not None
            self.enable_ensemble = enable_ensemble and EnsembleAttention is not None
            
            num_heads = getattr(base_config, 'num_heads', 8)
            
            if self.enable_gated_attention:
                self.gated_attention = GatedAttention(
                    hidden_dim=base_config.hidden_dim,
                    num_heads=num_heads
                )
            
            if self.enable_adaptive_norm:
                self.adaptive_norm = AdaptiveLayerNorm(hidden_dim=base_config.hidden_dim)
            
            if self.enable_ensemble:
                self.ensemble_attention = EnsembleAttention(
                    hidden_dim=base_config.hidden_dim,
                    num_heads=num_heads,
                    num_ensemble=4
                )
            
            logger.info(
                "Sora con Best Techniques habilitado",
                gated_attention=self.enable_gated_attention,
                adaptive_norm=self.enable_adaptive_norm,
                ensemble=self.enable_ensemble
            )
        else:
            self.best_model = None
            self.gated_attention = None
            self.adaptive_norm = None
            self.ensemble_attention = None
            logger.info("Sora sin Best Techniques (módulo no disponible)")
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con Best Techniques integradas.
        
        Args:
            hidden_states: Tensor de video [batch, frames, channels, height, width]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        if hidden_states.dim() == 5:
            batch_size, frames, channels, height, width = hidden_states.shape
        else:
            raise ValueError(f"hidden_states debe ser 5D [batch, frames, C, H, W], recibido: {hidden_states.shape}")
        
        if self.enable_best and (self.enable_adaptive_norm or self.enable_gated_attention or self.enable_ensemble):
            latent_reshaped = hidden_states.permute(0, 1, 3, 4, 2).contiguous()
            latent_flat = latent_reshaped.view(batch_size * frames, height * width, channels)
            
            if self.enable_adaptive_norm and self.adaptive_norm:
                latent_flat = self.adaptive_norm(latent_flat)
            
            if self.enable_gated_attention and self.gated_attention:
                latent_flat = self.gated_attention(latent_flat)
            elif self.enable_ensemble and self.ensemble_attention:
                latent_flat = self.ensemble_attention(latent_flat)
            
            hidden_states = latent_flat.view(batch_size, frames, height, width, channels)
            hidden_states = hidden_states.permute(0, 1, 4, 2, 3).contiguous()
        
        base_output, base_metadata = super().forward(hidden_states, **kwargs)
        
        if self.enable_best and self.best_model:
            batch_size, frames, out_channels, out_height, out_width = base_output.shape
            output_reshaped = base_output.permute(0, 1, 3, 4, 2).contiguous()
            output_flat = output_reshaped.view(batch_size * frames, out_height * out_width, out_channels)
            
            enhanced = self.best_model(output_flat)
            
            base_output = enhanced.view(batch_size, frames, out_height, out_width, out_channels)
            base_output = base_output.permute(0, 1, 4, 2, 3).contiguous()
            
            base_metadata['best_techniques_enabled'] = True
            base_metadata['gated_attention'] = self.enable_gated_attention
            base_metadata['adaptive_norm'] = self.enable_adaptive_norm
            base_metadata['ensemble'] = self.enable_ensemble
        
        return base_output, base_metadata


def create_sora_with_memory(
    config: VideoGenerationConfig,
    memory_config: Optional[Any] = None
) -> SoraWithMemory:
    """
    Factory function para crear Sora con memoria.
    
    Args:
        config: Configuración de video
        memory_config: Configuración de memoria (opcional)
    
    Returns:
        Instancia de SoraWithMemory
    """
    return SoraWithMemory(config, memory_config)


def create_sora_with_redundancy(
    config: VideoGenerationConfig,
    redundancy_config: Optional[Any] = None
) -> SoraWithRedundancySuppression:
    """
    Factory function para crear Sora con supresión de redundancia.
    
    Args:
        config: Configuración de video
        redundancy_config: Configuración de redundancia (opcional)
    
    Returns:
        Instancia de SoraWithRedundancySuppression
    """
    return SoraWithRedundancySuppression(config, redundancy_config)


def create_sora_integrated(
    config: VideoGenerationConfig,
    memory_config: Optional[Any] = None,
    redundancy_config: Optional[Any] = None
) -> SoraIntegrated:
    """
    Factory function para crear Sora completamente integrado.
    
    Args:
        config: Configuración de video
        memory_config: Configuración de memoria (opcional)
        redundancy_config: Configuración de redundancia (opcional)
    
    Returns:
        Instancia de SoraIntegrated
    """
    return SoraIntegrated(config, memory_config, redundancy_config)


def create_sora_with_best_techniques(
    config: VideoGenerationConfig,
    best_config: Optional[Any] = None,
    best_paper_type: str = "2506_10848v2",
    enable_gated_attention: bool = True,
    enable_adaptive_norm: bool = True,
    enable_ensemble: bool = False
) -> SoraWithBestTechniques:
    """
    Factory function para crear Sora con Best Techniques.
    
    Args:
        config: Configuración de video
        best_config: Configuración de Best Techniques (opcional)
        best_paper_type: Tipo de paper ("2506_10848v2" o "2510_04871v1")
        enable_gated_attention: Habilitar Gated Attention
        enable_adaptive_norm: Habilitar Adaptive LayerNorm
        enable_ensemble: Habilitar Ensemble Attention
    
    Returns:
        Instancia de SoraWithBestTechniques
    """
    return SoraWithBestTechniques(
        config,
        best_config,
        best_paper_type,
        enable_gated_attention,
        enable_adaptive_norm,
        enable_ensemble
    )

