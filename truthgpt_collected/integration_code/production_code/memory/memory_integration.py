#!/usr/bin/env python3
"""
Integración Avanzada de Memory con Otros Módulos
=================================================

Funciones y clases para integrar el módulo de memoria con otros sistemas.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)

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


class MemoryWithBestTechniques:
    """
    Memory integrado con Best Techniques para mejor rendimiento.
    
    Mejoras:
    - Gated Attention para mejor procesamiento de embeddings
    - Adaptive LayerNorm para normalización adaptativa
    - Ensemble Attention para diversidad (opcional)
    - Mejor calidad en almacenamiento y recuperación
    """
    
    def __init__(
        self,
        base_memory: Any,
        best_config: Optional[Any] = None,
        best_paper_type: str = "2506_10848v2",
        enable_gated_attention: bool = True,
        enable_adaptive_norm: bool = True,
        enable_ensemble: bool = False
    ):
        """
        Args:
            base_memory: Sistema de memoria base
            best_config: Configuración de Best Techniques (opcional)
            best_paper_type: Tipo de paper ("2506_10848v2" o "2510_04871v1")
            enable_gated_attention: Habilitar Gated Attention
            enable_adaptive_norm: Habilitar Adaptive LayerNorm
            enable_ensemble: Habilitar Ensemble Attention
        
        Raises:
            ValueError: Si base_memory es None
        """
        if base_memory is None:
            raise ValueError("base_memory no puede ser None")
        
        self.base_memory = base_memory
        self.enable_best = (enable_gated_attention or enable_adaptive_norm or enable_ensemble) and BEST_AVAILABLE
        
        if self.enable_best:
            if best_config is None:
                memory_dim = getattr(base_memory.config, 'memory_dim', getattr(base_memory.config, 'hidden_dim', 512))
                if best_paper_type == "2506_10848v2" and PAPER_2506_10848_AVAILABLE:
                    best_config = Paper2506_10848v2Config(hidden_dim=memory_dim)
                    self.best_model = Paper2506_10848v2_BestTechniques(best_config)
                elif best_paper_type == "2510_04871v1" and PAPER_2510_04871_AVAILABLE:
                    best_config = Paper2510_04871v1Config(hidden_dim=memory_dim)
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
            
            memory_dim = getattr(base_memory.config, 'memory_dim', getattr(base_memory.config, 'hidden_dim', 512))
            num_heads = getattr(base_memory.config, 'num_heads', 8)
            
            if self.enable_gated_attention:
                self.gated_attention = GatedAttention(
                    hidden_dim=memory_dim,
                    num_heads=num_heads
                )
            
            if self.enable_adaptive_norm:
                self.adaptive_norm = AdaptiveLayerNorm(hidden_dim=memory_dim)
            
            if self.enable_ensemble:
                self.ensemble_attention = EnsembleAttention(
                    hidden_dim=memory_dim,
                    num_heads=num_heads,
                    num_ensemble=4
                )
            
            logger.info(
                "Memory con Best Techniques habilitado",
                gated_attention=self.enable_gated_attention,
                adaptive_norm=self.enable_adaptive_norm,
                ensemble=self.enable_ensemble
            )
        else:
            self.best_model = None
            self.gated_attention = None
            self.adaptive_norm = None
            self.ensemble_attention = None
            logger.info("Memory sin Best Techniques (módulo no disponible)")
    
    def store_episode(self, episode: torch.Tensor, metadata: Optional[Dict] = None, **kwargs):
        """
        Almacena episodio con Best Techniques integradas.
        
        Args:
            episode: Tensor de episodio [hidden_dim] o [batch, hidden_dim]
            metadata: Metadata del episodio
            **kwargs: Argumentos adicionales
        """
        if episode.dim() == 1:
            episode = episode.unsqueeze(0)
        
        if self.enable_best and (self.enable_adaptive_norm or self.enable_gated_attention or self.enable_ensemble):
            if self.enable_adaptive_norm and self.adaptive_norm:
                episode = self.adaptive_norm(episode)
            
            if self.enable_gated_attention and self.gated_attention:
                episode = self.gated_attention(episode)
            elif self.enable_ensemble and self.ensemble_attention:
                episode = self.ensemble_attention(episode)
        
        if episode.dim() == 2 and episode.size(0) == 1:
            episode = episode.squeeze(0)
        
        return self.base_memory.store_episode(episode, metadata, **kwargs)
    
    def retrieve_episodes(self, query: torch.Tensor, k: int = 10, **kwargs) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Recupera episodios con Best Techniques integradas.
        
        Args:
            query: Tensor de query [hidden_dim] o [batch, hidden_dim]
            k: Número de episodios a recuperar
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (retrieved_episodes, weights)
        """
        if query.dim() == 1:
            query = query.unsqueeze(0)
        
        if self.enable_best and (self.enable_adaptive_norm or self.enable_gated_attention or self.enable_ensemble):
            if self.enable_adaptive_norm and self.adaptive_norm:
                query = self.adaptive_norm(query)
            
            if self.enable_gated_attention and self.gated_attention:
                query = self.gated_attention(query)
            elif self.enable_ensemble and self.ensemble_attention:
                query = self.ensemble_attention(query)
        
        retrieved, weights = self.base_memory.retrieve_episodes(query, k, **kwargs)
        
        if self.enable_best and self.best_model and retrieved.size(0) > 0:
            enhanced = self.best_model(retrieved)
            retrieved = enhanced
        
        if query.dim() == 2 and query.size(0) == 1:
            query = query.squeeze(0)
        
        return retrieved, weights
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con Best Techniques integradas.
        
        Args:
            hidden_states: Tensor [batch, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        if hasattr(self.base_memory, 'forward'):
            return self.base_memory.forward(hidden_states, **kwargs)
        else:
            retrieved, weights = self.retrieve_episodes(hidden_states, k=10, **kwargs)
            metadata = {
                'best_techniques_enabled': self.enable_best,
                'gated_attention': self.enable_gated_attention,
                'adaptive_norm': self.enable_adaptive_norm,
                'ensemble': self.enable_ensemble
            }
            return retrieved, metadata


def create_memory_with_best_techniques(
    memory_config: Any,
    best_config: Optional[Any] = None,
    best_paper_type: str = "2506_10848v2",
    memory_paper_type: str = "2506_15841v2",
    enable_gated_attention: bool = True,
    enable_adaptive_norm: bool = True,
    enable_ensemble: bool = False
) -> Optional[MemoryWithBestTechniques]:
    """
    Factory function para crear Memory con Best Techniques.
    
    Args:
        memory_config: Configuración de memoria
        best_config: Configuración de Best Techniques (opcional)
        best_paper_type: Tipo de paper Best ("2506_10848v2" o "2510_04871v1")
        memory_paper_type: Tipo de paper Memory ("2506_15841v2" o "2509_04439v1")
        enable_gated_attention: Habilitar Gated Attention
        enable_adaptive_norm: Habilitar Adaptive LayerNorm
        enable_ensemble: Habilitar Ensemble Attention
    
    Returns:
        Instancia de MemoryWithBestTechniques o None si hay error
    """
    try:
        from memory import create_memory_system
        
        config_dict = memory_config.__dict__ if hasattr(memory_config, '__dict__') else memory_config
        
        base_memory = create_memory_system(
            memory_paper_type,
            **config_dict
        )
        
        if base_memory is None:
            logger.error("No se pudo crear el sistema de memoria base")
            return None
        
        return MemoryWithBestTechniques(
            base_memory,
            best_config,
            best_paper_type,
            enable_gated_attention,
            enable_adaptive_norm,
            enable_ensemble
        )
    except Exception as e:
        logger.error(f"Error creando Memory con Best Techniques: {e}", exc_info=True)
        return None


