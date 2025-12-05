#!/usr/bin/env python3
"""
TruthGPT + Ultimate Long Context Integration
===========================================

Integra Ultimate Long Context Model con TruthGPT Optimization Core
para extender el contexto y mejorar el rendimiento en tareas largas.

ARQUITECTURA:
TruthGPT Base → Ultimate Long Context → TruthGPT Output

MEJORAS:
- Extensión de contexto de 1K → 131K tokens
- Encoding posicional dual (LongRoPE + AdaGroPE)
- Compresión semántica inteligente
- Optimización con rewards (LongReward)
- Compresión paralela (CEPE)
"""

import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging
import sys
import os

# Añadir path para imports
sys.path.insert(0, os.path.dirname(__file__))

from truthgpt_optimization_core_integration import (
    TruthGPTOptimizationCore,
    TruthGPTOptimizationCoreConfig,
    TruthGPTModel
)

from papers.research.paper_ultimate_long_context import (
    UltimateLongContextModule,
    UltimateLongContextConfig,
    UltimateLongContextPresets
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TruthGPTUltimateConfig(TruthGPTOptimizationCoreConfig):
    """Configuración extendida con Ultimate Long Context."""
    
    # Ultimate Long Context settings
    enable_ultimate_long_context: bool = True
    ultimate_context_preset: str = "best_quality"  # best_quality, training_free, fast_inference
    ultimate_context_length: int = 131072  # 131K tokens
    
    # Override max_position_embeddings cuando Ultimate está activo
    use_ultimate_position_encoding: bool = True
    
    # Configuración específica de Ultimate
    ultimate_config_overrides: Dict[str, Any] = field(default_factory=dict)


class TruthGPTUltimateModel(TruthGPTModel):
    """
    TruthGPT Model extendido con Ultimate Long Context.
    
    Reemplaza position_embeddings básicas con Ultimate Long Context
    para extender el contexto y mejorar el rendimiento.
    """
    
    def __init__(self, config: TruthGPTUltimateConfig):
        # Inicializar base sin position_embeddings si Ultimate está activo
        self.ultimate_config = config
        
        if config.enable_ultimate_long_context and config.use_ultimate_position_encoding:
            # Guardar max_position_embeddings original
            original_max_pos = config.max_position_embeddings
            # Temporalmente aumentar para inicialización
            config.max_position_embeddings = min(config.ultimate_context_length, 2048)
        
        # Inicializar modelo base
        super().__init__(config)
        
        # Reemplazar position_embeddings con Ultimate Long Context
        if config.enable_ultimate_long_context:
            # Obtener preset de Ultimate
            if config.ultimate_context_preset == "best_quality":
                ultimate_cfg = UltimateLongContextPresets.best_quality()
            elif config.ultimate_context_preset == "training_free":
                ultimate_cfg = UltimateLongContextPresets.training_free()
            elif config.ultimate_context_preset == "fast_inference":
                ultimate_cfg = UltimateLongContextPresets.fast_inference()
            else:
                ultimate_cfg = UltimateLongContextPresets.best_quality()
            
            # Ajustar hidden_dim
            ultimate_cfg.hidden_dim = config.hidden_size
            ultimate_cfg.base_context_length = original_max_pos
            ultimate_cfg.extended_context_length = config.ultimate_context_length
            
            # Aplicar overrides
            for key, value in config.ultimate_config_overrides.items():
                if hasattr(ultimate_cfg, key):
                    setattr(ultimate_cfg, key, value)
            
            # Crear módulo Ultimate Long Context
            self.ultimate_long_context = UltimateLongContextModule(ultimate_cfg)
            
            # Desactivar position_embeddings básicas (Ultimate las reemplaza)
            self.position_embeddings = None
            
            logger.info(
                f"Ultimate Long Context integrated: "
                f"{config.max_position_embeddings} → {config.ultimate_context_length:,} tokens"
            )
        else:
            self.ultimate_long_context = None
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con Ultimate Long Context.
        
        Pipeline:
        1. Token embeddings
        2. Ultimate Long Context (reemplaza position embeddings)
        3. TruthGPT blocks (distance-based attention)
        4. Layer norm + LM head
        """
        batch_size, seq_len = input_ids.shape
        
        # 1. Token embeddings
        token_embeds = self.token_embeddings(input_ids)  # [B, N, d]
        
        # 2. Position encoding con Ultimate Long Context
        if self.ultimate_long_context is not None:
            # Generar position_ids si no se proporcionan
            if position_ids is None:
                position_ids = torch.arange(seq_len, device=input_ids.device)
                position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
            
            # Aplicar Ultimate Long Context
            # Esto incluye: SemanticComp, LongRoPE, AdaGroPE, CEPE, LongReward
            hidden_states, ultimate_metadata = self.ultimate_long_context(
                token_embeds,
                position_ids=position_ids
            )
            
            # Guardar metadata para después (no pasarlo a blocks)
            self._last_ultimate_metadata = ultimate_metadata
        else:
            # Usar position embeddings básicas
            if position_ids is None:
                position_ids = torch.arange(seq_len, device=input_ids.device)
                position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
            
            pos_embeds = self.position_embeddings(position_ids)
            hidden_states = token_embeds + pos_embeds
        
        # 3. Apply dropout
        hidden_states = self.embedding_dropout(hidden_states)
        
        # 4. TruthGPT blocks (distance-based attention)
        attention_outputs = []
        for i, block in enumerate(self.blocks):
            hidden_states, attn_output = block(
                hidden_states,
                attention_mask=attention_mask,
                **kwargs
            )
            attention_outputs.append(attn_output)
        
        # 5. Final layer norm
        hidden_states = self.layer_norm(hidden_states)
        
        # 6. Language modeling head
        logits = self.lm_head(hidden_states)
        
        # Metadata combinada
        metadata = {
            'seq_len': seq_len,
            'num_blocks': len(self.blocks),
            'attention_outputs': attention_outputs
        }
        
        if self.ultimate_long_context is not None and hasattr(self, '_last_ultimate_metadata'):
            metadata['ultimate_long_context'] = self._last_ultimate_metadata
        
        return logits, metadata


class TruthGPTUltimateCore(TruthGPTOptimizationCore):
    """
    TruthGPT Optimization Core extendido con Ultimate Long Context.
    """
    
    def __init__(self, config: TruthGPTUltimateConfig):
        # Guardar config
        self.ultimate_config = config
        
        # Inicializar base con modelo extendido
        super().__init__(config)
        
        # Reemplazar modelo con versión Ultimate
        if config.enable_ultimate_long_context:
            self.model = TruthGPTUltimateModel(config)
            logger.info("TruthGPT Ultimate Core initialized with Ultimate Long Context")
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Obtiene todas las métricas incluyendo Ultimate Long Context."""
        base_metrics = super().get_all_metrics()
        
        # Añadir métricas de Ultimate Long Context
        if self.ultimate_config.enable_ultimate_long_context:
            if hasattr(self.model, 'ultimate_long_context'):
                ultimate_metrics = self.model.ultimate_long_context.get_metrics()
                base_metrics['ultimate_long_context'] = ultimate_metrics
        
        return base_metrics


def create_truthgpt_ultimate(
    preset: str = "best_quality",
    hidden_size: int = 768,
    num_layers: int = 12,
    num_heads: int = 12,
    max_context: int = 131072,
    **kwargs
) -> TruthGPTUltimateCore:
    """
    Factory function para crear TruthGPT Ultimate.
    
    Args:
        preset: "best_quality", "training_free", "fast_inference"
        hidden_size: Dimensión oculta
        num_layers: Número de capas
        num_heads: Número de heads de atención
        max_context: Contexto máximo en tokens
        **kwargs: Configuraciones adicionales
    
    Returns:
        TruthGPTUltimateCore instance
    """
    config = TruthGPTUltimateConfig(
        hidden_size=hidden_size,
        num_hidden_layers=num_layers,
        num_attention_heads=num_heads,
        max_position_embeddings=2048,  # Base context
        enable_ultimate_long_context=True,
        ultimate_context_preset=preset,
        ultimate_context_length=max_context,
        **kwargs
    )
    
    return TruthGPTUltimateCore(config)


if __name__ == "__main__":
    # Test básico
    print("Testing TruthGPT Ultimate Integration...")
    
    config = TruthGPTUltimateConfig(
        hidden_size=768,
        num_hidden_layers=6,  # Reducido para test rápido
        num_attention_heads=12,
        max_position_embeddings=2048,
        enable_ultimate_long_context=True,
        ultimate_context_preset="best_quality",
        ultimate_context_length=131072
    )
    
    core = TruthGPTUltimateCore(config)
    
    # Test forward
    batch_size, seq_len = 2, 4096
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))
    
    print(f"Input shape: {input_ids.shape}")
    
    with torch.no_grad():
        logits, metadata = core.model(input_ids)
    
    print(f"Output shape: {logits.shape}")
    print(f"✅ TruthGPT Ultimate Integration test passed!")

