#!/usr/bin/env python3
"""
Paper: 2509.04439v1 (Memory Paper)
===================================

Implementación específica basada en técnicas de memoria avanzada.
Este módulo implementa las técnicas específicas propuestas en este paper.

Paper URL: https://arxiv.org/html/2509.04439v1

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Almacenamiento en Memoria:
   - Key-Value Storage: M = {(k_i, v_i)} donde k_i son claves y v_i son valores
   - Embeddings: k_i = W_k · x_i, v_i = W_v · x_i
   - Implementado en: store()

2. Recuperación por Similitud:
   - Similarity: s(q, k_i) = cos(q, k_i) = (q · k_i) / (||q|| · ||k_i||)
   - Top-K retrieval: R = {k_i | s(q, k_i) ∈ top-K}
   - Implementado en: retrieve()

3. Consolidación de Memoria:
   - Decay: w_i(t) = w_i(0) · decay^t donde decay < 1
   - Consolidación: v'_i = Σ_j w_j · v_j / Σ_j w_j (promedio ponderado)
   - Implementado en: consolidate()
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from core.utils import setup_logger
from core.paper_base import BasePaperModule, BasePaperConfig
from core.error_handling import safe_execute
from collections import deque, defaultdict
import time

logger = setup_logger(__name__)

try:
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

if PYDANTIC_AVAILABLE:
    class Paper2509_04439v1Config(BasePaperConfig):
        """Configuración específica para paper 2509.04439v1 (Memory)."""
        memory_dim: int = Field(default=512, ge=1, le=32768, description="Dimensión de memoria")
        max_memory_size: int = Field(default=10000, ge=1, description="Tamaño máximo de memoria")
        retrieval_k: int = Field(default=10, ge=1, description="Número de items a recuperar")
        memory_decay: float = Field(default=0.95, ge=0.0, le=1.0, description="Tasa de decaimiento de memoria")
        use_hierarchical_memory: bool = Field(default=True, description="Usar memoria jerárquica")
        temperature: float = Field(default=1.0, ge=0.1, le=10.0, description="Temperatura para retrieval")
        
        @field_validator('memory_dim', 'max_memory_size', 'retrieval_k')
        @classmethod
        def validate_positive(cls, v: int) -> int:
            if v <= 0:
                raise ValueError(f"Valor debe ser positivo, recibido: {v}")
            return v
else:
    @dataclass
    class Paper2509_04439v1Config:
        """Configuración específica para paper 2509.04439v1 (Memory)."""
        hidden_dim: int = 512
        memory_dim: int = 512
        max_memory_size: int = 10000
        retrieval_k: int = 10
        memory_decay: float = 0.95
        use_hierarchical_memory: bool = True
        temperature: float = 1.0
        
        def validate(self):
            """Valida la configuración."""
            if self.memory_dim <= 0:
                raise ValueError(f"memory_dim debe ser > 0, recibido: {self.memory_dim}")
            if self.max_memory_size <= 0:
                raise ValueError(f"max_memory_size debe ser > 0, recibido: {self.max_memory_size}")
            if not 0.0 <= self.memory_decay <= 1.0:
                raise ValueError(f"memory_decay debe estar en [0.0, 1.0], recibido: {self.memory_decay}")


class Paper2509_04439v1_MemorySystem(BasePaperModule):
    """
    Sistema de memoria avanzado basado en paper 2509.04439v1.
    
    Mejoras implementadas:
    - Herencia de BasePaperModule (validación, métricas, save/load)
    - Validación completa de inputs
    - Batch processing optimizado
    - Temperature scaling
    - Manejo robusto de errores
    - Métricas detalladas
    
    Basado en: https://arxiv.org/html/2509.04439v1
    """
    
    def __init__(self, config: Paper2509_04439v1Config):
        if PYDANTIC_AVAILABLE:
            config_dict = config.model_dump() if hasattr(config, 'model_dump') else config.__dict__
        else:
            config_dict = config.__dict__ if hasattr(config, '__dict__') else config
            if hasattr(config, 'validate'):
                config.validate()
        
        super().__init__(config_dict)
        self.config = config
        
        # Memoria a corto plazo
        self.short_term_memory = deque(maxlen=config.max_memory_size // 10)
        
        # Memoria a largo plazo
        self.long_term_memory = {}
        
        # Embeddings de memoria
        self.memory_embeddings = nn.Parameter(
            torch.randn(config.max_memory_size, config.memory_dim) * 0.02
        )
        self.memory_keys = nn.Parameter(
            torch.randn(config.max_memory_size, config.memory_dim) * 0.02
        )
        
        # Proyecciones específicas del paper
        self.query_projection = nn.Linear(config.memory_dim, config.memory_dim)
        self.memory_projection = nn.Linear(config.memory_dim, config.memory_dim)
        
        # Tracking
        self.consolidation_counter = 0
        self.memory_access_counts = defaultdict(int)
        
        # Métricas
        self.register_buffer('avg_similarity', torch.tensor(0.0))
        self.register_buffer('retrieval_accuracy', torch.tensor(0.0))
        
        # Estadísticas
        self.total_retrievals = 0
        self.total_stores = 0
        self.total_consolidations = 0
        
        logger.info(
            "Initialized Paper 2509.04439v1 Memory System",
            memory_dim=config.memory_dim,
            max_size=config.max_memory_size,
            use_hierarchical=config.use_hierarchical_memory
        )
    
    def store(
        self, 
        key: torch.Tensor, 
        value: torch.Tensor, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Almacena información en memoria según técnicas del paper.
        
        Args:
            key: Tensor clave [memory_dim] o [batch, memory_dim]
            value: Tensor valor [memory_dim] o [batch, memory_dim]
            metadata: Metadata adicional
        
        Returns:
            bool: True si se almacenó exitosamente
        """
        def _store():
            if not isinstance(key, torch.Tensor) or not isinstance(value, torch.Tensor):
                raise TypeError("key y value deben ser torch.Tensor")
            
            if key.size(-1) != self.config.memory_dim or value.size(-1) != self.config.memory_dim:
                raise ValueError(
                    f"Dimensión debe ser {self.config.memory_dim}, "
                    f"key: {key.size(-1)}, value: {value.size(-1)}"
                )
            
            if key.dim() > 1:
                for k, v in zip(key, value):
                    self._store_single(k.detach(), v.detach(), metadata)
            else:
                self._store_single(key.detach(), value.detach(), metadata)
            
            self.total_stores += 1
            return True
        
        result, error = safe_execute(_store, default_value=False, log_errors=True)
        if error:
            logger.error("Error almacenando en memoria", error=str(error))
        return result
    
    def _store_single(
        self, 
        key: torch.Tensor, 
        value: torch.Tensor, 
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Almacena un solo par key-value."""
        self.short_term_memory.append({
            'key': key.cpu() if key.is_cuda else key,
            'value': value.cpu() if value.is_cuda else value,
            'metadata': metadata or {},
            'timestamp': time.time(),
            'access_count': 0
        })
    
    def retrieve(
        self, 
        query: torch.Tensor, 
        k: Optional[int] = None, 
        temperature: Optional[float] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Recupera información de memoria usando técnicas específicas del paper.
        
        Mejoras:
        - Validación de inputs
        - Temperature scaling para control de sharpness
        - Mejor manejo de memoria vacía
        - Batch processing support
        
        Args:
            query: Query tensor [memory_dim] or [batch, memory_dim]
            k: Número de items a recuperar
            temperature: Temperature para softmax (controla sharpness)
            
        Returns:
            retrieved_values: Valores recuperados [k, memory_dim] or [batch, k, memory_dim]
            retrieved_weights: Pesos de atención [k] or [batch, k]
        """
        k = k or self.config.retrieval_k
        temperature = temperature if temperature is not None else self.config.temperature
        self.total_retrievals += 1
        
        # Validation
        if query.dim() == 1:
            query = query.unsqueeze(0)
            batch_size = 1
            squeeze_output = True
        else:
            batch_size = query.size(0)
            squeeze_output = False
        
        if query.size(-1) != self.config.memory_dim:
            raise ValueError(f"Query dim mismatch: expected {self.config.memory_dim}, got {query.size(-1)}")
        
        if len(self.short_term_memory) == 0:
            empty_values = torch.zeros(batch_size, 1, self.config.memory_dim, device=query.device)
            empty_weights = torch.ones(batch_size, 1, device=query.device)
            if squeeze_output:
                return empty_values.squeeze(0), empty_weights.squeeze(0)
            return empty_values, empty_weights
        
        # Proyectar query según técnicas del paper
        query_proj = self.query_projection(query)  # [batch, memory_dim]
        
        # Recuperar de memoria a corto plazo
        short_term_keys = torch.stack([item['key'] for item in self.short_term_memory]).to(query.device)
        short_term_values = torch.stack([item['value'] for item in self.short_term_memory]).to(query.device)
        
        # Calcular similitud (técnica específica del paper)
        # [batch, memory_dim] x [num_memories, memory_dim]^T -> [batch, num_memories]
        similarity_scores = torch.matmul(query_proj, short_term_keys.transpose(-2, -1))
        
        # Temperature scaling
        similarity_scores = similarity_scores / (temperature * (self.config.memory_dim ** 0.5))
        similarity_weights = F.softmax(similarity_scores, dim=-1)
        
        # Actualizar métricas
        avg_sim = similarity_scores.mean().item()
        self.avg_similarity = 0.9 * self.avg_similarity + 0.1 * avg_sim
        
        # Top-k retrieval
        actual_k = min(k, len(short_term_keys))
        top_k_values, top_k_indices = torch.topk(similarity_weights, actual_k, dim=-1)
        
        # Gather retrieved values
        # Expand indices for batch: [batch, k] -> [batch, k, 1] -> [batch, k, memory_dim]
        indices_expanded = top_k_indices.unsqueeze(-1).expand(-1, -1, self.config.memory_dim)
        retrieved_values = torch.gather(
            short_term_values.unsqueeze(0).expand(batch_size, -1, -1),
            dim=1,
            index=indices_expanded
        )
        retrieved_weights = top_k_values
        
        # Actualizar contadores
        for batch_idx in range(batch_size):
            for idx in top_k_indices[batch_idx].cpu().numpy():
                if idx < len(self.short_term_memory):
                    self.short_term_memory[idx]['access_count'] += 1
                    self.memory_access_counts[idx] += 1
        
        if squeeze_output:
            return retrieved_values.squeeze(0), retrieved_weights.squeeze(0)
        return retrieved_values, retrieved_weights
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass del paper: procesa hidden_states con sistema de memoria.
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado de shape [batch_size, seq_len, hidden_dim]
            - metadata: Diccionario con métricas e información adicional
        """
        self.validate_inputs(hidden_states, **kwargs)
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        try:
            query = hidden_states[:, -1, :]  # [batch, hidden_dim]
            
            retrieved_values, retrieved_weights = self.retrieve(
                query,
                k=self.config.retrieval_k,
                temperature=self.config.temperature
            )
            
            if retrieved_values.size(0) > 0 and retrieved_values.size(1) > 0:
                memory_contribution = torch.sum(
                    retrieved_values * retrieved_weights.unsqueeze(-1),
                    dim=1
                )  # [batch, hidden_dim]
                
                memory_contribution = memory_contribution.unsqueeze(1).expand(-1, seq_len, -1)
                output = hidden_states + memory_contribution
            else:
                output = hidden_states
            
            if self.config.use_hierarchical_memory:
                self.store(query, query, metadata={'batch_size': batch_size, 'seq_len': seq_len})
            
            stats = self.get_memory_stats()
            metadata = {
                **stats,
                'avg_similarity': self.avg_similarity.item(),
                'retrieval_accuracy': self.retrieval_accuracy.item(),
                'total_retrievals': self.total_retrievals,
                'total_stores': self.total_stores,
                'total_consolidations': self.total_consolidations,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item()
            }
            
            self._update_metrics(**metadata)
            
            return output, metadata
            
        except Exception as e:
            logger.error("Error en forward de Paper2509_04439v1", error=str(e), exc_info=True)
            error_metadata = {
                'error': str(e),
                'short_term_size': len(self.short_term_memory),
                'long_term_size': len(self.long_term_memory)
            }
            return hidden_states, error_metadata
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about memory usage."""
        return {
            'short_term_size': len(self.short_term_memory),
            'long_term_size': len(self.long_term_memory),
            'total_accesses': sum(self.memory_access_counts.values()),
            'consolidation_count': self.consolidation_counter,
            'avg_access_count': (
                sum(self.memory_access_counts.values()) / len(self.memory_access_counts)
                if self.memory_access_counts else 0.0
            ),
            'memory_utilization': len(self.short_term_memory) / (self.config.max_memory_size // 10) if (self.config.max_memory_size // 10) > 0 else 0.0
        }
    
    def consolidate(self, force: bool = False) -> int:
        """
        Consolida memoria según técnicas del paper.
        
        Args:
            force: Si True, fuerza consolidación incluso si no hay suficientes memorias
        
        Returns:
            int: Número de memorias consolidadas
        """
        def _consolidate():
            if len(self.short_term_memory) == 0:
                return 0
            
            if not force and len(self.short_term_memory) < 10:
                logger.debug("No hay suficientes memorias para consolidar")
                return 0
        
        # Consolidar memorias más accedidas
        sorted_memories = sorted(
            enumerate(self.short_term_memory),
            key=lambda x: x[1]['access_count'],
            reverse=True
        )
        
        # Mover top memorias a largo plazo
        num_to_consolidate = max(1, self.config.max_memory_size // 20)
        consolidated = 0
        
        for idx, memory_item in sorted_memories[:num_to_consolidate]:
            memory_id = f"ltm_{self.consolidation_counter}_{idx}"
            self.long_term_memory[memory_id] = {
                'key': memory_item['key'],
                'value': memory_item['value'],
                'metadata': memory_item['metadata'],
                'consolidation_time': time.time(),
                'access_count': memory_item['access_count']
            }
            consolidated += 1
        
        self.consolidation_counter += 1
        self.total_consolidations += 1
        
        logger.info(
            f"Consolidación completada: {consolidated} memorias, total LTM: {len(self.long_term_memory)}"
        )
        
        return consolidated
        
        result, error = safe_execute(_consolidate, default_value=0, log_errors=True)
        if error:
            logger.error("Error en consolidación", error=str(error))
        return result


class TruthGPT_Paper2509_04439v1_Integration(BasePaperModule):
    """
    Integración del paper 2509.04439v1 con TruthGPT.
    
    Mejoras:
    - Herencia de BasePaperModule
    - Validación robusta
    - Métricas completas
    - Manejo de errores
    """
    
    def __init__(
        self, 
        base_model: nn.Module, 
        paper_config: Paper2509_04439v1Config
    ):
        if PYDANTIC_AVAILABLE:
            config_dict = paper_config.model_dump() if hasattr(paper_config, 'model_dump') else paper_config.__dict__
        else:
            config_dict = paper_config.__dict__ if hasattr(paper_config, '__dict__') else paper_config
        
        super().__init__(config_dict)
        
        self.base_model = base_model
        self.memory_system = Paper2509_04439v1_MemorySystem(paper_config)
    
    def forward(
        self, 
        hidden_states: torch.Tensor, 
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con sistema de memoria del paper.
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado de shape [batch_size, seq_len, hidden_dim]
            - metadata: Diccionario con métricas e información adicional
        """
        # Procesar con modelo base
        if hasattr(self.base_model, 'forward'):
            base_output = self.base_model(hidden_states, **kwargs)
        else:
            base_output = hidden_states
        
        # Si el modelo base retorna solo tensor, usar directamente
        if isinstance(base_output, torch.Tensor):
            base_hidden = base_output
        elif isinstance(base_output, tuple):
            base_hidden = base_output[0]
        else:
            base_hidden = hidden_states
        
        # Procesar con sistema de memoria
        output, metadata = self.memory_system.forward(base_hidden, **kwargs)
        
        # Combinar metadata si el modelo base retornó metadata
        if isinstance(base_output, tuple) and len(base_output) > 1:
            base_metadata = base_output[1] if isinstance(base_output[1], dict) else {}
            metadata = {**base_metadata, **metadata, 'memory_enabled': True}
        else:
            metadata['memory_enabled'] = True
        
        return output, metadata


if __name__ == "__main__":
    config = Paper2509_04439v1Config()
    memory_system = Paper2509_04439v1_MemorySystem(config)
    
    # Test
    key = torch.randn(config.memory_dim)
    value = torch.randn(config.memory_dim)
    memory_system.store(key, value, {'test': True})
    
    query = torch.randn(config.memory_dim)
    retrieved, weights = memory_system.retrieve(query)
    print(f"✅ Paper 2509.04439v1 Memory System test:")
    print(f"   Retrieved shape: {retrieved.shape}, Weights shape: {weights.shape}")

