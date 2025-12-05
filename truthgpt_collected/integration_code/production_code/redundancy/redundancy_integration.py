#!/usr/bin/env python3
"""
Integración Avanzada de Redundancy con Otros Módulos
=====================================================

Funciones y clases para integrar el módulo de redundancia con otros sistemas.
"""

from typing import Dict, List, Tuple, Optional, Any, Callable
import torch
import time
from pathlib import Path

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class RedundancyMemoryIntegration:
    """
    Integración entre Redundancy y Memory modules.
    
    Permite usar redundancia para optimizar la memoria episódica.
    """
    
    def __init__(
        self,
        redundancy_suppressor: Any,
        memory_system: Optional[Any] = None
    ):
        """
        Args:
            redundancy_suppressor: Instancia del supresor de redundancia
            memory_system: Sistema de memoria (opcional)
        
        Raises:
            ValueError: Si redundancy_suppressor es None
        """
        if redundancy_suppressor is None:
            raise ValueError("redundancy_suppressor no puede ser None")
        
        self.redundancy_suppressor = redundancy_suppressor
        self.memory_system = memory_system
        self.integration_stats = {
            'memory_optimizations': 0,
            'redundancy_applied': 0,
            'total_saved': 0
        }
    
    def optimize_memory_episodes(
        self,
        episodes: torch.Tensor,
        threshold: float = 0.85
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Optimiza episodios de memoria eliminando redundancias.
        
        Args:
            episodes: Episodios de memoria [num_episodes, seq_len, hidden_dim]
            threshold: Umbral de similitud
        
        Returns:
            Episodios optimizados y estadísticas
        
        Raises:
            ValueError: Si episodes es None o threshold no es válido
            TypeError: Si episodes no es un tensor
        """
        if episodes is None:
            raise ValueError("episodes no puede ser None")
        if not isinstance(episodes, torch.Tensor):
            raise TypeError(f"episodes debe ser torch.Tensor, recibido: {type(episodes)}")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold debe estar en [0.0, 1.0], recibido: {threshold}")
        def _optimize():
            if episodes.size(0) == 0:
                return episodes, {'reduction_rate': 0.0, 'original_size': 0}
            
            unique_episodes, stats = self.redundancy_suppressor.process_bulk(episodes)
            
            self.integration_stats['memory_optimizations'] += 1
            self.integration_stats['redundancy_applied'] += 1
            self.integration_stats['total_saved'] += episodes.size(0) - unique_episodes.size(0)
            
            return unique_episodes, stats
        
        result, error = safe_execute(
            _optimize,
            default_value=(episodes, {'reduction_rate': 0.0, 'error': str(error)}),
            log_errors=True
        )
        
        return result
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de integración."""
        return {
            **self.integration_stats,
            'redundancy_metrics': self.redundancy_suppressor.get_metrics() if hasattr(self.redundancy_suppressor, 'get_metrics') else {}
        }


class RedundancyPipelineIntegration:
    """
    Integración de redundancia en pipelines de procesamiento.
    """
    
    def __init__(
        self,
        redundancy_suppressor: Any,
        preprocess_fn: Optional[Callable] = None,
        postprocess_fn: Optional[Callable] = None
    ):
        """
        Args:
            redundancy_suppressor: Supresor de redundancia
            preprocess_fn: Función de preprocesamiento
            postprocess_fn: Función de postprocesamiento
        
        Raises:
            ValueError: Si redundancy_suppressor es None
        """
        if redundancy_suppressor is None:
            raise ValueError("redundancy_suppressor no puede ser None")
        
        self.redundancy_suppressor = redundancy_suppressor
        self.preprocess_fn = preprocess_fn
        self.postprocess_fn = postprocess_fn
    
    def process_pipeline(
        self,
        data: torch.Tensor,
        apply_redundancy: bool = True
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa datos a través del pipeline con redundancia.
        
        Args:
            data: Datos a procesar
            apply_redundancy: Si aplicar supresión de redundancia
        
        Returns:
            Datos procesados y metadata
        
        Raises:
            ValueError: Si data es None
            TypeError: Si data no es un tensor
        """
        if data is None:
            raise ValueError("data no puede ser None")
        if not isinstance(data, torch.Tensor):
            raise TypeError(f"data debe ser torch.Tensor, recibido: {type(data)}")
        metadata = {'pipeline_steps': []}
        output = data
        
        if self.preprocess_fn:
            output = self.preprocess_fn(output)
            metadata['pipeline_steps'].append('preprocess')
        
        if apply_redundancy:
            unique_output, redundancy_stats = self.redundancy_suppressor.process_bulk(output)
            output = unique_output
            metadata['redundancy_stats'] = redundancy_stats
            metadata['pipeline_steps'].append('redundancy')
        
        if self.postprocess_fn:
            output = self.postprocess_fn(output)
            metadata['pipeline_steps'].append('postprocess')
        
        return output, metadata


class RedundancyStreamingProcessor:
    """
    Procesador de redundancia para streaming de datos.
    """
    
    def __init__(
        self,
        redundancy_suppressor: Any,
        buffer_size: int = 100,
        flush_interval: float = 5.0
    ):
        """
        Args:
            redundancy_suppressor: Supresor de redundancia
            buffer_size: Tamaño del buffer
            flush_interval: Intervalo de flush en segundos
        
        Raises:
            ValueError: Si redundancy_suppressor es None o parámetros inválidos
        """
        if redundancy_suppressor is None:
            raise ValueError("redundancy_suppressor no puede ser None")
        if buffer_size <= 0:
            raise ValueError(f"buffer_size debe ser > 0, recibido: {buffer_size}")
        if flush_interval <= 0:
            raise ValueError(f"flush_interval debe ser > 0, recibido: {flush_interval}")
        
        self.redundancy_suppressor = redundancy_suppressor
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer: List[torch.Tensor] = []
        self.last_flush = time.time()
        self.processed_count = 0
    
    def add_item(self, item: torch.Tensor) -> Optional[torch.Tensor]:
        """
        Agrega un item al buffer y procesa si es necesario.
        
        Args:
            item: Item a agregar
        
        Returns:
            Item único si el buffer se procesó, None en caso contrario
        
        Raises:
            ValueError: Si item es None
            TypeError: Si item no es un tensor
        """
        if item is None:
            raise ValueError("item no puede ser None")
        if not isinstance(item, torch.Tensor):
            raise TypeError(f"item debe ser torch.Tensor, recibido: {type(item)}")
        
        self.buffer.append(item)
        
        should_flush = (
            len(self.buffer) >= self.buffer_size or
            (time.time() - self.last_flush) >= self.flush_interval
        )
        
        if should_flush:
            return self.flush()
        
        return None
    
    def flush(self) -> Optional[torch.Tensor]:
        """
        Procesa el buffer y lo limpia.
        
        Returns:
            Items únicos procesados
        """
        if not self.buffer:
            return None
        
        def _process():
            batch = torch.stack(self.buffer)
            unique_items, stats = self.redundancy_suppressor.process_bulk(batch)
            self.processed_count += len(self.buffer)
            return unique_items
        
        result, error = safe_execute(
            _process,
            default_value=None,
            log_errors=True
        )
        
        self.buffer.clear()
        self.last_flush = time.time()
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del procesador de streaming."""
        return {
            'buffer_size': len(self.buffer),
            'processed_count': self.processed_count,
            'time_since_flush': time.time() - self.last_flush
        }


def create_integrated_redundancy_system(
    redundancy_config: Optional[Any] = None,
    memory_config: Optional[Any] = None,
    enable_memory: bool = True
) -> Dict[str, Any]:
    """
    Crea un sistema integrado de redundancia y memoria.
    
    Args:
        redundancy_config: Configuración de redundancia
        memory_config: Configuración de memoria
        enable_memory: Si habilitar integración con memoria
    
    Returns:
        Diccionario con los sistemas creados
    """
    from redundancy import create_redundancy_suppressor
    
    systems = {}
    
    def _create():
        redundancy_suppressor = create_redundancy_suppressor(
            "2510_00071",
            **(redundancy_config.__dict__ if redundancy_config else {})
        )
        systems['redundancy'] = redundancy_suppressor
        
        if enable_memory:
            try:
                from memory import create_memory_system
                memory_system = create_memory_system(
                    "2506_15841v2",
                    **(memory_config.__dict__ if memory_config else {})
                )
                systems['memory'] = memory_system
                systems['integration'] = RedundancyMemoryIntegration(
                    redundancy_suppressor,
                    memory_system
                )
            except ImportError:
                logger.warning("Memory module no disponible, continuando sin integración")
        
        return systems
    
    result, error = safe_execute(_create, default_value={}, log_errors=True)
    return result


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


class RedundancyWithBestTechniques:
    """
    Redundancy integrado con Best Techniques para mejor rendimiento.
    
    Mejoras:
    - Gated Attention para mejor procesamiento de features
    - Adaptive LayerNorm para normalización adaptativa
    - Ensemble Attention para diversidad (opcional)
    - Mejor calidad en detección de redundancia
    """
    
    def __init__(
        self,
        base_suppressor: Any,
        best_config: Optional[Any] = None,
        best_paper_type: str = "2506_10848v2",
        enable_gated_attention: bool = True,
        enable_adaptive_norm: bool = True,
        enable_ensemble: bool = False
    ):
        """
        Args:
            base_suppressor: Supresor de redundancia base
            best_config: Configuración de Best Techniques (opcional)
            best_paper_type: Tipo de paper ("2506_10848v2" o "2510_04871v1")
            enable_gated_attention: Habilitar Gated Attention
            enable_adaptive_norm: Habilitar Adaptive LayerNorm
            enable_ensemble: Habilitar Ensemble Attention
        
        Raises:
            ValueError: Si base_suppressor es None
        """
        if base_suppressor is None:
            raise ValueError("base_suppressor no puede ser None")
        
        self.base_suppressor = base_suppressor
        self.enable_best = (enable_gated_attention or enable_adaptive_norm or enable_ensemble) and BEST_AVAILABLE
        
        if self.enable_best:
            if best_config is None:
                hidden_dim = getattr(base_suppressor.config, 'hidden_dim', 512)
                if best_paper_type == "2506_10848v2" and PAPER_2506_10848_AVAILABLE:
                    best_config = Paper2506_10848v2Config(hidden_dim=hidden_dim)
                    self.best_model = Paper2506_10848v2_BestTechniques(best_config)
                elif best_paper_type == "2510_04871v1" and PAPER_2510_04871_AVAILABLE:
                    best_config = Paper2510_04871v1Config(hidden_dim=hidden_dim)
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
            
            hidden_dim = getattr(base_suppressor.config, 'hidden_dim', 512)
            num_heads = getattr(base_suppressor.config, 'num_heads', 8)
            
            if self.enable_gated_attention:
                self.gated_attention = GatedAttention(
                    hidden_dim=hidden_dim,
                    num_heads=num_heads
                )
            
            if self.enable_adaptive_norm:
                self.adaptive_norm = AdaptiveLayerNorm(hidden_dim=hidden_dim)
            
            if self.enable_ensemble:
                self.ensemble_attention = EnsembleAttention(
                    hidden_dim=hidden_dim,
                    num_heads=num_heads,
                    num_ensemble=4
                )
            
            logger.info(
                "Redundancy con Best Techniques habilitado",
                gated_attention=self.enable_gated_attention,
                adaptive_norm=self.enable_adaptive_norm,
                ensemble=self.enable_ensemble
            )
        else:
            self.best_model = None
            self.gated_attention = None
            self.adaptive_norm = None
            self.ensemble_attention = None
            logger.info("Redundancy sin Best Techniques (módulo no disponible)")
    
    def process_bulk(self, items: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa items con Best Techniques integradas.
        
        Args:
            items: Tensor [batch, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (unique_items, metadata)
        """
        if items.dim() != 3:
            raise ValueError(f"items debe ser 3D [batch, seq_len, hidden_dim], recibido: {items.shape}")
        
        if self.enable_best and (self.enable_adaptive_norm or self.enable_gated_attention or self.enable_ensemble):
            batch_size, seq_len, hidden_dim = items.shape
            
            if self.enable_adaptive_norm and self.adaptive_norm:
                items = self.adaptive_norm(items)
            
            if self.enable_gated_attention and self.gated_attention:
                items = self.gated_attention(items)
            elif self.enable_ensemble and self.ensemble_attention:
                items = self.ensemble_attention(items)
        
        unique_items, base_metadata = self.base_suppressor.process_bulk(items, **kwargs)
        
        if self.enable_best and self.best_model:
            enhanced = self.best_model(unique_items)
            unique_items = enhanced
            
            base_metadata['best_techniques_enabled'] = True
            base_metadata['gated_attention'] = self.enable_gated_attention
            base_metadata['adaptive_norm'] = self.enable_adaptive_norm
            base_metadata['ensemble'] = self.enable_ensemble
        
        return unique_items, base_metadata
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con Best Techniques integradas.
        
        Args:
            hidden_states: Tensor [batch, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        return self.process_bulk(hidden_states, **kwargs)


def create_redundancy_with_best_techniques(
    redundancy_config: Any,
    best_config: Optional[Any] = None,
    best_paper_type: str = "2506_10848v2",
    enable_gated_attention: bool = True,
    enable_adaptive_norm: bool = True,
    enable_ensemble: bool = False
) -> Optional[RedundancyWithBestTechniques]:
    """
    Factory function para crear Redundancy con Best Techniques.
    
    Args:
        redundancy_config: Configuración de redundancia
        best_config: Configuración de Best Techniques (opcional)
        best_paper_type: Tipo de paper ("2506_10848v2" o "2510_04871v1")
        enable_gated_attention: Habilitar Gated Attention
        enable_adaptive_norm: Habilitar Adaptive LayerNorm
        enable_ensemble: Habilitar Ensemble Attention
    
    Returns:
        Instancia de RedundancyWithBestTechniques o None si hay error
    """
    try:
        from redundancy import create_redundancy_suppressor
        
        base_suppressor = create_redundancy_suppressor(
            "2510_00071",
            **(redundancy_config.__dict__ if hasattr(redundancy_config, '__dict__') else redundancy_config)
        )
        
        if base_suppressor is None:
            logger.error("No se pudo crear el supresor de redundancia base")
            return None
        
        return RedundancyWithBestTechniques(
            base_suppressor,
            best_config,
            best_paper_type,
            enable_gated_attention,
            enable_adaptive_norm,
            enable_ensemble
        )
    except Exception as e:
        logger.error(f"Error creando Redundancy con Best Techniques: {e}", exc_info=True)
        return None

