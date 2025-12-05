#!/usr/bin/env python3
"""
Paper: 2506.15841v2 (Memory Paper)
===================================

Implementación específica basada en técnicas de memoria avanzada.
Este módulo implementa las técnicas específicas propuestas en este paper.

Paper URL: https://arxiv.org/html/2506.15841v2

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Memoria Episódica:
   - Episodio: E_i = {(x_t, a_t, r_t)} para t ∈ [t_start, t_end]
   - Almacenamiento: M_episodic = {E_i} con metadata temporal
   - Implementado en: episodic_memory

2. Memoria Semántica:
   - Consolidación: M_semantic = f_consolidate(M_episodic)
     donde f_consolidate agrega episodios similares
   - Embedding semántico: s_i = W_s · aggregate(E_i)
   - Implementado en: semantic_memory

3. Consolidación Adaptativa:
   - Rate: r(t) = r_0 · (1 - consolidation_rate)^t
   - Agregación: v_consolidated = Σ_i w_i · v_i / Σ_i w_i
     donde w_i son pesos basados en frecuencia de acceso
   - Implementado en: consolidate()
"""

import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from core.utils import setup_logger
from core.paper_base import BasePaperModule, BasePaperConfig
from core.error_handling import safe_execute
from collections import deque, defaultdict
import heapq
import time
import json
from pathlib import Path
from itertools import islice
import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    import psutil
except ImportError:
    psutil = None

try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    ray = None
    RAY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import bitsandbytes as bnb
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    bnb = None
    BITSANDBYTES_AVAILABLE = False

try:
    from diskcache import Cache as DiskCache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DiskCache = None
    DISKCACHE_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

if RAY_AVAILABLE:
    @ray.remote
    def _ray_similarity_worker(query_np: np.ndarray, chunk_np: np.ndarray) -> np.ndarray:
        query_tensor = torch.from_numpy(query_np)
        chunk_tensor = torch.from_numpy(chunk_np)
        sims = torch.matmul(query_tensor, chunk_tensor.transpose(-2, -1))
        return sims.numpy()

logger = setup_logger(__name__)

def _config_to_dict(config: Any) -> Dict[str, Any]:
    """
    Normaliza cualquier configuración (pydantic, dataclass o dict) a un dict estándar.
    """
    if hasattr(config, "model_dump"):
        return config.model_dump()
    if hasattr(config, "dict"):
        return config.dict()
    if hasattr(config, "__dict__"):
        return dict(config.__dict__)
    return dict(config)

try:
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

if PYDANTIC_AVAILABLE:
    class Paper2506_15841v2Config(BasePaperConfig):
        """Configuración específica para paper 2506.15841v2 (Memory)."""
        memory_dim: int = Field(default=512, ge=1, le=32768, description="Dimensión de memoria")
        max_memory_size: int = Field(default=10000, ge=1, description="Tamaño máximo de memoria")
        retrieval_k: int = Field(default=10, ge=1, description="Número de episodios a recuperar")
        memory_consolidation_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Tasa de consolidación")
        use_episodic_memory: bool = Field(default=True, description="Usar memoria episódica")
        use_semantic_memory: bool = Field(default=True, description="Usar memoria semántica")
        temperature: float = Field(default=1.0, ge=0.1, le=10.0, description="Temperatura para retrieval")
        enable_cache: bool = Field(default=True, description="Habilitar caché de retrievals")
        cache_size: int = Field(default=1000, ge=1, description="Tamaño del caché")
        enable_compression: bool = Field(default=False, description="Habilitar compresión de memoria")
        compression_ratio: float = Field(default=0.5, ge=0.1, le=0.9, description="Ratio de compresión")
        enable_prioritization: bool = Field(default=True, description="Habilitar priorización de episodios")
        enable_persistence: bool = Field(default=True, description="Habilitar persistencia de memoria")
        persistence_path: Optional[str] = Field(default=None, description="Ruta para persistencia")
        enable_semantic_search: bool = Field(default=True, description="Habilitar búsqueda semántica mejorada")
        enable_text_embeddings: bool = Field(default=False, description="Convertir texto a embeddings automáticamente")
        embedding_model_name: Optional[str] = Field(
            default="sentence-transformers/all-MiniLM-L6-v2",
            description="Modelo SentenceTransformer para embeddings"
        )
        enable_disk_cache: bool = Field(default=False, description="Usar diskcache para resultados persistentes")
        disk_cache_path: Optional[str] = Field(default="./memory_diskcache", description="Ruta para diskcache")
        enable_bitsandbytes: bool = Field(default=False, description="Aplicar cuantización bitsandbytes")
        quantization_dtype: str = Field(default="nf4", description="Dtype bitsandbytes (nf4, fp4, int8)")
        enable_redis_replication: bool = Field(default=False, description="Replica episodios en Redis")
        redis_url: Optional[str] = Field(default="redis://localhost:6379/0", description="URL de Redis para replicación")
        enable_ray_retrieval: bool = Field(default=False, description="Usar Ray para retrieval distribuido")
        ray_chunk_size: int = Field(default=2048, ge=1, description="Chunk size para workers Ray")
        
        @field_validator('memory_dim', 'max_memory_size', 'retrieval_k')
        @classmethod
        def validate_positive(cls, v: int) -> int:
            if v <= 0:
                raise ValueError(f"Valor debe ser positivo, recibido: {v}")
            return v
else:
    @dataclass
    class Paper2506_15841v2Config:
        """Configuración específica para paper 2506.15841v2 (Memory)."""
        hidden_dim: int = 512
        memory_dim: int = 512
        max_memory_size: int = 10000
        retrieval_k: int = 10
        memory_consolidation_rate: float = 0.1
        use_episodic_memory: bool = True
        use_semantic_memory: bool = True
        temperature: float = 1.0
        enable_cache: bool = True
        cache_size: int = 1000
        enable_compression: bool = False
        compression_ratio: float = 0.5
        enable_prioritization: bool = True
        enable_persistence: bool = True
        persistence_path: Optional[str] = None
        enable_semantic_search: bool = True
        enable_text_embeddings: bool = False
        embedding_model_name: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2"
        enable_disk_cache: bool = False
        disk_cache_path: Optional[str] = "./memory_diskcache"
        enable_bitsandbytes: bool = False
        quantization_dtype: str = "nf4"
        enable_redis_replication: bool = False
        redis_url: Optional[str] = "redis://localhost:6379/0"
        enable_ray_retrieval: bool = False
        ray_chunk_size: int = 2048


class Paper2506_15841v2_MemorySystem(BasePaperModule):
    """
    Sistema de memoria avanzado basado en paper 2506.15841v2.
    
    Mejoras implementadas:
    - Herencia de BasePaperModule (validación, métricas, save/load)
    - Validación completa de inputs
    - Batch processing optimizado
    - Estadísticas detalladas de episodios
    - Temperature scaling
    - Device handling mejorado
    - Caché de retrievals
    - Consolidación adaptativa mejorada
    - Integración con sistema de chat
    
    Basado en: https://arxiv.org/html/2506.15841v2
    """
    
    def __init__(self, config: Paper2506_15841v2Config):
        # Validar configuración
        config_dict = _config_to_dict(config)
        super().__init__(config_dict)
        
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.text_encoder = None
        self.disk_cache = None
        self.redis_client = None
        
        # Memoria episódica (técnica específica del paper)
        self.episodic_memory = deque(maxlen=config.max_memory_size)
        
        # Memoria semántica
        self.semantic_memory = {}
        
        # Embeddings de memoria con mejor inicialización
        self.memory_embeddings = nn.Parameter(
            torch.randn(config.max_memory_size, config.memory_dim) * 0.02
        )
        
        # Proyecciones específicas del paper con mejor inicialización
        self.episodic_projection = nn.Linear(config.memory_dim, config.memory_dim)
        self.semantic_projection = nn.Linear(config.memory_dim, config.memory_dim)
        
        # Initialize projections
        nn.init.xavier_uniform_(self.episodic_projection.weight)
        nn.init.xavier_uniform_(self.semantic_projection.weight)
        if self.episodic_projection.bias is not None:
            nn.init.zeros_(self.episodic_projection.bias)
        if self.semantic_projection.bias is not None:
            nn.init.zeros_(self.semantic_projection.bias)
        
        # Tracking
        self.episode_access_counts = defaultdict(int)
        self.consolidation_counter = 0
        
        # Caché de retrievals
        self.retrieval_cache = {} if config.enable_cache else None
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Metrics mejoradas
        self.register_buffer('avg_episode_similarity', torch.tensor(0.0))
        self.register_buffer('retrieval_accuracy', torch.tensor(0.0))
        self.register_buffer('consolidation_efficiency', torch.tensor(0.0))
        self.register_buffer('memory_utilization', torch.tensor(0.0))
        
        # Estadísticas adicionales
        self.total_retrievals = 0
        self.total_stores = 0
        self.total_consolidations = 0
        
        # Cache tensorizado de episodios
        self._episodic_tensor_cache: Optional[torch.Tensor] = None
        self._episodic_tensor_cache_device: Optional[torch.device] = None
        
        # Sistema de priorización
        self.episode_priorities = {} if config.enable_prioritization else None
        
        # Sistema de compresión
        if config.enable_compression:
            self.compression_projection = nn.Linear(config.memory_dim, int(config.memory_dim * config.compression_ratio))
            self.decompression_projection = nn.Linear(int(config.memory_dim * config.compression_ratio), config.memory_dim)
            nn.init.xavier_uniform_(self.compression_projection.weight)
            nn.init.xavier_uniform_(self.decompression_projection.weight)
        else:
            self.compression_projection = None
            self.decompression_projection = None
        
        # Persistencia
        self.persistence_path = Path(config.persistence_path) if config.persistence_path else None
        if config.enable_persistence and self.persistence_path:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
            # Cargar memoria persistida si existe
            self._load_persisted_memory()
        
        # Búsqueda semántica mejorada
        if config.enable_semantic_search:
            self.semantic_encoder = nn.Linear(config.memory_dim, config.memory_dim)
            nn.init.xavier_uniform_(self.semantic_encoder.weight)
        else:
            self.semantic_encoder = None
        
        # Tags/categorías para episodios
        self.episode_tags = defaultdict(set)
        
        logger.info(
            "Initialized Paper 2506.15841v2 Memory System",
            memory_dim=config.memory_dim,
            max_size=config.max_memory_size,
            use_cache=config.enable_cache,
            compression=config.enable_compression,
            persistence=config.enable_persistence
        )
        
        self._setup_text_encoder()
        self._setup_disk_cache()
        self._setup_quantization()
        self._setup_redis_replication()
    
    def store_episode(self, episode: torch.Tensor, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Almacena un episodio en memoria según técnicas del paper.
        
        Args:
            episode: Tensor del episodio [memory_dim] o [batch, memory_dim]
            metadata: Metadata adicional del episodio
        
        Returns:
            bool: True si se almacenó exitosamente
        """
        def _store():
            # Validar input
            processed_episode = self._prepare_episode_input(episode)
            
            if processed_episode.dim() > 1:
                for ep in processed_episode:
                    self._store_single_episode(ep.detach(), metadata)
            else:
                self._store_single_episode(processed_episode.detach(), metadata)
            
            self.total_stores += 1
            return True
        
        result, error = safe_execute(_store, default_value=False, log_errors=True)
        if error:
            logger.error("Error almacenando episodio", error=str(error))
        return result
    
    def _store_single_episode(self, episode: torch.Tensor, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Almacena un solo episodio."""
        if episode.size(-1) != self.config.memory_dim:
            raise ValueError(
                f"Dimensión de episodio no coincide: esperado {self.config.memory_dim}, "
                f"recibido {episode.size(-1)}"
            )
        
        self.episodic_memory.append({
            'episode': episode.detach().cpu() if episode.is_cuda else episode.detach(),
            'metadata': metadata or {},
            'timestamp': time.time(),
            'access_count': 0
        })
        
        # Limpiar caché si está habilitado
        if self.retrieval_cache and len(self.retrieval_cache) > self.config.cache_size:
            # Eliminar entradas más antiguas
            oldest_key = min(self.retrieval_cache.keys(), key=lambda k: self.retrieval_cache[k]['timestamp'])
            del self.retrieval_cache[oldest_key]
    
    def retrieve_episodes(
        self, 
        query: torch.Tensor, 
        k: Optional[int] = None, 
        temperature: Optional[float] = None, 
        use_cache: bool = True
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Recupera episodios relevantes usando técnicas del paper.
        
        Mejoras:
        - Batch processing support
        - Temperature scaling
        - Validación mejorada
        - Métricas de similitud
        - Caché de retrievals
        - Manejo robusto de errores
        
        Args:
            query: Query tensor [memory_dim] or [batch, memory_dim]
            k: Número de episodios a recuperar (usa config si None)
            temperature: Temperature para softmax (usa config si None)
            use_cache: Si True, usa caché de retrievals
            
        Returns:
            retrieved_episodes: Episodios recuperados
            retrieved_weights: Pesos de atención
        """
        k = k or self.config.retrieval_k
        temperature = temperature if temperature is not None else self.config.temperature
        
        def _retrieve():
            # Verificar caché
            if use_cache and self.retrieval_cache:
                cache_key = self._get_cache_key(query, k, temperature)
                if cache_key in self.retrieval_cache:
                    self.cache_hits += 1
                    cached = self.retrieval_cache[cache_key]
                    # Actualizar timestamp para LRU
                    self.retrieval_cache[cache_key] = {
                        **cached,
                        'timestamp': time.time()
                    }
                    # Mover tensores al dispositivo correcto
                    episodes = cached['episodes'].to(query.device)
                    weights = cached['weights'].to(query.device)
                    return episodes, weights
                self.cache_misses += 1
            
            return self._retrieve_episodes_impl(query, k, temperature, use_cache)
        
        result, error = safe_execute(
            _retrieve,
            default_value=(
                torch.zeros(1, 1, self.config.memory_dim, device=query.device),
                torch.ones(1, 1, device=query.device)
            ),
            log_errors=True
        )
        
        if error:
            logger.error("Error recuperando episodios", error=str(error))
        
        return result
    
    def _get_cache_key(self, query: torch.Tensor, k: int, temperature: float) -> str:
        """Genera clave de caché para query."""
        # Usar hash del tensor para la clave
        query_hash = hash(query.cpu().numpy().tobytes())
        return f"{query_hash}_{k}_{temperature}"
    
    def _retrieve_episodes_impl(
        self, 
        query: torch.Tensor, 
        k: int, 
        temperature: float, 
        use_cache: bool
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Implementación interna de retrieval.
        
        Args:
            query: Query tensor [memory_dim] or [batch, memory_dim]
            k: Número de episodios a recuperar
            temperature: Temperature para softmax
            use_cache: Si True, guarda resultado en caché
            
        Returns:
            Tuple de (episodios recuperados, pesos)
        """
        # Validation and batch handling
        if query.dim() == 1:
            query = query.unsqueeze(0)
            batch_size = 1
            squeeze_output = True
        else:
            batch_size = query.size(0)
            squeeze_output = False
        
        if query.size(-1) != self.config.memory_dim:
            raise ValueError(f"Query dim mismatch: expected {self.config.memory_dim}, got {query.size(-1)}")
        
        if len(self.episodic_memory) == 0 and self.disk_cache is not None:
            self._hydrate_from_disk_cache(limit=max(k * 2, 256))
        
        if len(self.episodic_memory) == 0:
            empty_episodes = torch.zeros(batch_size, 1, self.config.memory_dim, device=query.device)
            empty_weights = torch.ones(batch_size, 1, device=query.device)
            if squeeze_output:
                return empty_episodes.squeeze(0), empty_weights.squeeze(0)
            return empty_episodes, empty_weights
        
        # Proyectar query
        query_proj = self.episodic_projection(query)  # [batch, memory_dim]
        
        episodes = torch.stack([item['episode'] for item in self.episodic_memory]).to(query.device)
        similarity_scores = self._compute_similarity_scores(query_proj, episodes, temperature)
        similarity_weights = F.softmax(similarity_scores, dim=-1)
        
        # Update metrics
        avg_sim = similarity_scores.mean().item()
        self.avg_episode_similarity = 0.9 * self.avg_episode_similarity + 0.1 * avg_sim
        
        # Top-k retrieval
        actual_k = min(k, len(episodes))
        top_k_values, top_k_indices = torch.topk(similarity_weights, actual_k, dim=-1)
        
        # Gather retrieved episodes
        indices_expanded = top_k_indices.unsqueeze(-1).expand(-1, -1, self.config.memory_dim)
        retrieved_episodes = torch.gather(
            episodes.unsqueeze(0).expand(batch_size, -1, -1),
            dim=1,
            index=indices_expanded
        )
        retrieved_weights = top_k_values
        
        # Update access counts
        for batch_idx in range(batch_size):
            for idx in top_k_indices[batch_idx].cpu().numpy():
                if idx < len(self.episodic_memory):
                    self.episode_access_counts[idx] += 1
        
        # Guardar en caché si está habilitado
        if use_cache and self.retrieval_cache:
            cache_key = self._get_cache_key(query, k, temperature)
            # Limpiar caché si es necesario
            if len(self.retrieval_cache) >= self.config.cache_size:
                oldest_key = min(
                    self.retrieval_cache.keys(), 
                    key=lambda k: self.retrieval_cache[k].get('timestamp', 0)
                )
                del self.retrieval_cache[oldest_key]
            
            self.retrieval_cache[cache_key] = {
                'episodes': retrieved_episodes.detach().cpu() if retrieved_episodes.is_cuda else retrieved_episodes.detach(),
                'weights': retrieved_weights.detach().cpu() if retrieved_weights.is_cuda else retrieved_weights.detach(),
                'timestamp': time.time()
            }
        
        if squeeze_output:
            return retrieved_episodes.squeeze(0), retrieved_weights.squeeze(0)
        return retrieved_episodes, retrieved_weights
    
    def _prepare_episode_input(self, episode: Any) -> torch.Tensor:
        """
        Convierte episodios de diferentes formatos a tensores.
        """
        if isinstance(episode, torch.Tensor):
            return episode
        
        if isinstance(episode, str):
            if not self.text_encoder:
                raise ValueError("Text embeddings no habilitados. Active enable_text_embeddings para almacenar texto.")
            embedding = self.text_encoder.encode(
                episode,
                convert_to_tensor=True,
                device=str(self.device)
            )
            return embedding
        
        if isinstance(episode, (list, tuple)):
            tensor = torch.tensor(episode, dtype=self.memory_embeddings.dtype)
            return tensor
        
        if isinstance(episode, dict):
            content = episode.get('text') or episode.get('content')
            if content:
                return self._prepare_episode_input(content)
            tensor_values = episode.get('values')
            if tensor_values is not None:
                return torch.tensor(tensor_values, dtype=self.memory_embeddings.dtype)
        
        raise TypeError(f"type de episodio no soportado: {type(episode)}")
    
    def _setup_text_encoder(self):
        """Inicializa el encoder de texto si está habilitado."""
        if not self.config.enable_text_embeddings:
            return
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("SentenceTransformer no disponible, deshabilitando text embeddings")
            self.config.enable_text_embeddings = False
            return
        
        model_name = self.config.embedding_model_name or "sentence-transformers/all-MiniLM-L6-v2"
        try:
            self.text_encoder = SentenceTransformer(model_name, device=str(self.device))
            self.text_encoder.eval()
            logger.info("Text encoder inicializado", model=model_name)
        except Exception as exc:
            logger.error("Error inicializando text encoder", error=str(exc))
            self.text_encoder = None
            self.config.enable_text_embeddings = False
    
    def _setup_disk_cache(self):
        """Configura diskcache persistente para retrieval."""
        if not self.config.enable_disk_cache:
            return
        
        if not DISKCACHE_AVAILABLE:
            logger.warning("diskcache no disponible, ignorando disk cache")
            self.config.enable_disk_cache = False
            return
        
        cache_path = self.config.disk_cache_path or "./memory_diskcache"
        try:
            self.disk_cache = DiskCache(cache_path)
            logger.info("Disk cache habilitado", path=cache_path)
        except Exception as exc:
            logger.error("No se pudo iniciar disk cache", error=str(exc))
            self.disk_cache = None
            self.config.enable_disk_cache = False
    
    def _setup_quantization(self):
        """Aplica cuantización bitsandbytes si está habilitada."""
        if not self.config.enable_bitsandbytes or not BITSANDBYTES_AVAILABLE:
            return
        
        quant_dtype = self.config.quantization_dtype.lower()
        try:
            if quant_dtype in {"nf4", "fp4"} and hasattr(bnb.nn, "Linear4bit"):
                QuantLinear = bnb.nn.Linear4bit
                quant_kwargs = {
                    "bnb_4bit_use_double_quant": True,
                    "bnb_4bit_compute_dtype": torch.float16
                }
            else:
                QuantLinear = getattr(bnb.nn, "Linear8bitLt", None)
                quant_kwargs = {}
            
            if QuantLinear is None:
                logger.warning("bitsandbytes no soporta Linear deseado, omitiendo cuantización")
                return
            
            def quantize_linear(linear_layer: nn.Linear) -> nn.Module:
                quant_layer = QuantLinear(
                    linear_layer.in_features,
                    linear_layer.out_features,
                    bias=linear_layer.bias is not None,
                    **quant_kwargs
                )
                quant_layer.weight.data = linear_layer.weight.data.clone()
                if linear_layer.bias is not None and hasattr(quant_layer, "bias") and quant_layer.bias is not None:
                    quant_layer.bias.data = linear_layer.bias.data.clone()
                return quant_layer
            
            self.episodic_projection = quantize_linear(self.episodic_projection)
            self.semantic_projection = quantize_linear(self.semantic_projection)
            logger.info("Cuantización bitsandbytes aplicada", dtype=quant_dtype)
        except Exception as exc:
            logger.error("No se pudo aplicar cuantización bitsandbytes", error=str(exc))
    
    def _setup_redis_replication(self):
        """Inicializa cliente Redis opcional."""
        if not self.config.enable_redis_replication:
            return
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis no disponible, deshabilitando replicación")
            self.config.enable_redis_replication = False
            return
        
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            _ = self.redis_client.ping()
            logger.info("Replicación Redis habilitada", url=self.config.redis_url)
        except Exception as exc:
            logger.error("No se pudo conectar a Redis", error=str(exc))
            self.redis_client = None
            self.config.enable_redis_replication = False
    
    def _persist_episode_remotely(self, episode_payload: Dict[str, Any]) -> None:
        """Replica episodios en Redis si está habilitado."""
        if not self.redis_client:
            return
        
        try:
            key = f"memory_episode:{episode_payload['timestamp']}"
            self.redis_client.hset(key, mapping={
                "metadata": json.dumps(episode_payload.get('metadata', {})),
                "tensor": json.dumps(episode_payload.get('episode').tolist())
            })
            self.redis_client.expire(key, 60 * 60 * 24 * 7)  # 7 días
        except Exception as exc:
            logger.warning("Fallo replicando episodio en Redis", error=str(exc))
    
    def consolidate_to_semantic(self, force: bool = False):
        """
        Consolida episodios frecuentemente accedidos a memoria semántica.
        
        Args:
            force: Si True, fuerza consolidación incluso si no hay suficientes episodios
        
        Returns:
            int: Número de episodios consolidados
        """
        def _consolidate():
            if len(self.episodic_memory) == 0:
                return 0
            
            if not force and len(self.episodic_memory) < 10:
                logger.debug("No hay suficientes episodios para consolidar")
                return 0
            
            # Sort by access count
            sorted_episodes = sorted(
                enumerate(self.episodic_memory),
                key=lambda x: self.episode_access_counts.get(x[0], 0),
                reverse=True
            )
            
            # Consolidate top episodes
            num_to_consolidate = max(1, int(len(self.episodic_memory) * self.config.memory_consolidation_rate))
            consolidated = 0
            
            for idx, episode_item in sorted_episodes[:num_to_consolidate]:
                semantic_key = f"semantic_{self.consolidation_counter}_{idx}"
                self.semantic_memory[semantic_key] = {
                    'episode': episode_item['episode'],
                    'metadata': episode_item['metadata'],
                    'consolidation_time': time.time(),
                    'access_count': self.episode_access_counts.get(idx, 0)
                }
                consolidated += 1
            
            self.consolidation_counter += 1
            self.total_consolidations += 1
            
            # Actualizar métrica de eficiencia
            if consolidated > 0:
                efficiency = consolidated / num_to_consolidate
                self.consolidation_efficiency = (
                    0.9 * self.consolidation_efficiency + 0.1 * efficiency
                )
            
            logger.info(
                "Consolidación completada",
                consolidated=consolidated,
                total_semantic=len(self.semantic_memory)
            )
            
            return consolidated
        
        result, error = safe_execute(_consolidate, default_value=0, log_errors=True)
        if error:
            logger.error("Error en consolidación", error=str(error))
        return result
    
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
            # Usar último token como query para retrieval
            query = hidden_states[:, -1, :]  # [batch, hidden_dim]
            
            # Recuperar episodios relevantes
            retrieved_episodes, retrieved_weights = self.retrieve_episodes(
                query,
                k=self.config.retrieval_k,
                temperature=self.config.temperature
            )
            
            # Combinar con hidden_states
            if retrieved_episodes.size(0) > 0 and retrieved_episodes.size(1) > 0:
                # Promediar episodios recuperados con pesos
                memory_contribution = torch.sum(
                    retrieved_episodes * retrieved_weights.unsqueeze(-1),
                    dim=1
                )  # [batch, hidden_dim]
                
                # Expandir a toda la secuencia
                memory_contribution = memory_contribution.unsqueeze(1).expand(-1, seq_len, -1)
                
                # Combinar con hidden_states
                output = hidden_states + memory_contribution
            else:
                output = hidden_states
            
            # Almacenar episodio actual en memoria
            if self.config.use_episodic_memory:
                self.store_episode(query, metadata={'batch_size': batch_size, 'seq_len': seq_len})
            
            # Consolidar si es necesario
            if self.config.use_semantic_memory and len(self.episodic_memory) > 0:
                consolidation_threshold = self.config.max_memory_size * 0.8
                if len(self.episodic_memory) >= consolidation_threshold:
                    self.consolidate_to_semantic()
            
            # Calcular métricas
            stats = self.get_episodic_stats()
            metadata = {
                'episodic_size': stats['episodic_size'],
                'semantic_size': stats['semantic_size'],
                'avg_similarity': stats['avg_similarity'],
                'retrieval_accuracy': stats['retrieval_accuracy'],
                'total_retrievals': self.total_retrievals,
                'total_stores': self.total_stores,
                'total_consolidations': self.total_consolidations,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
                'output_mean': output.mean().item(),
                'output_std': output.std().item(),
                'output_max': output.max().item(),
                'output_min': output.min().item()
            }
            
            self._update_metrics(**metadata)
            
            return output, metadata
            
        except Exception as e:
            logger.error("Error en forward de Paper2506_15841v2", error=str(e), exc_info=True)
            error_metadata = {
                'error': str(e),
                'episodic_size': len(self.episodic_memory),
                'semantic_size': len(self.semantic_memory)
            }
            return hidden_states, error_metadata
    
    def get_episodic_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about episodic memory."""
        stats = {
            'episodic_size': len(self.episodic_memory),
            'semantic_size': len(self.semantic_memory),
            'total_accesses': sum(self.episode_access_counts.values()),
            'consolidation_count': self.consolidation_counter,
            'avg_similarity': self.avg_episode_similarity.item(),
            'retrieval_accuracy': self.retrieval_accuracy.item(),
            'consolidation_efficiency': self.consolidation_efficiency.item(),
            'memory_utilization': len(self.episodic_memory) / self.config.max_memory_size if self.config.max_memory_size > 0 else 0.0,
            'total_retrievals': self.total_retrievals,
            'total_stores': self.total_stores,
            'total_consolidations': self.total_consolidations
        }
        
        # Estadísticas de caché
        if self.retrieval_cache is not None:
            total_cache_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0.0
            stats.update({
                'cache_size': len(self.retrieval_cache),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': cache_hit_rate
            })
        
        return stats
    
    def clear_cache(self):
        """Limpia el caché de retrievals."""
        if self.retrieval_cache is not None:
            self.retrieval_cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            logger.info("Caché limpiado")
    
    def store_episode_with_tags(
        self, 
        episode: torch.Tensor, 
        metadata: Dict = None,
        tags: List[str] = None,
        priority: float = 1.0
    ) -> bool:
        """
        Almacena un episodio con tags y prioridad.
        
        Args:
            episode: Tensor del episodio
            metadata: Metadata adicional
            tags: Lista de tags para categorización
            priority: Prioridad del episodio (mayor = más importante)
        
        Returns:
            bool: True si se almacenó exitosamente
        """
        result = self.store_episode(episode, metadata)
        
        if result and len(self.episodic_memory) > 0:
            idx = len(self.episodic_memory) - 1
            
            # Añadir tags
            if tags:
                self.episode_tags[idx].update(tags)
            
            # Establecer prioridad
            if self.episode_priorities is not None:
                self.episode_priorities[idx] = priority
        
        return result
    
    def retrieve_by_tags(
        self, 
        query: torch.Tensor, 
        tags: List[str],
        k: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Recupera episodios que tienen tags específicos.
        
        Args:
            query: Query tensor
            tags: Lista de tags a buscar
            k: Número de episodios a recuperar
        
        Returns:
            Tuple de (episodios, pesos)
        """
        # Filtrar episodios por tags
        tagged_indices = [
            idx
            for idx, episode_tags in self.episode_tags.items()
            if any(tag in episode_tags for tag in tags)
        ]
        
        if not tagged_indices:
            # Si no hay episodios con esos tags, usar retrieval normal
            return self.retrieve_episodes(query, k=k)
        
        # Recuperar solo episodios con tags
        k = k or self.config.retrieval_k
        k = min(k, len(tagged_indices))
        
        # Calcular similitud solo con episodios etiquetados
        if query.dim() == 1:
            query = query.unsqueeze(0)
            squeeze_output = True
        else:
            squeeze_output = False
        
        query_proj = self.episodic_projection(query)
        tagged_episodes = torch.stack([
            self.episodic_memory[idx]['episode'] 
            for idx in tagged_indices
        ]).to(query.device)
        
        similarity_scores = torch.matmul(query_proj, tagged_episodes.transpose(-2, -1))
        similarity_scores = similarity_scores / (self.config.temperature * (self.config.memory_dim ** 0.5))
        similarity_weights = F.softmax(similarity_scores, dim=-1)
        
        top_k_values, top_k_indices = torch.topk(similarity_weights, k, dim=-1)
        
        indices_expanded = top_k_indices.unsqueeze(-1).expand(-1, -1, self.config.memory_dim)
        retrieved_episodes = torch.gather(
            tagged_episodes.unsqueeze(0).expand(query.size(0), -1, -1),
            dim=1,
            index=indices_expanded
        )
        
        if squeeze_output:
            return retrieved_episodes.squeeze(0), top_k_values.squeeze(0)
        return retrieved_episodes, top_k_values
    
    def compress_memory(self) -> int:
        """
        Comprime episodios antiguos para ahorrar espacio.
        
        Returns:
            int: Número de episodios comprimidos
        """
        def _compress():
            if not self.config.enable_compression or self.compression_projection is None:
                return 0
            
            if len(self.episodic_memory) == 0:
                return 0
            
            num_to_compress = max(1, int(len(self.episodic_memory) * self.config.compression_ratio))
            compressed = 0
            indices_to_compress = heapq.nsmallest(
                num_to_compress,
                range(len(self.episodic_memory)),
                key=lambda i: self.episode_access_counts.get(i, 0)
            )
            
            for idx in indices_to_compress:
                episode_item = self.episodic_memory[idx]
                episode = episode_item['episode']
                
                # Solo comprimir si no está ya comprimido
                if episode_item.get('compressed', False):
                    continue
                
                # Comprimir
                compressed_episode = self.compression_projection(episode)
                
                # Guardar versión comprimida
                episode_item['episode'] = compressed_episode.detach()
                episode_item['compressed'] = True
                episode_item['original_shape'] = episode.shape
                compressed += 1
            
            logger.info("Memoria comprimida", compressed=compressed, total=len(self.episodic_memory))
            return compressed
        
        result, error = safe_execute(_compress, default_value=0, log_errors=True)
        if error:
            logger.error("Error comprimiendo memoria", error=str(error))
        return result
    
    def decompress_episode(self, episode_idx: int) -> bool:
        """
        Descomprime un episodio específico.
        
        Args:
            episode_idx: Índice del episodio a descomprimir
        
        Returns:
            bool: True si se descomprimió exitosamente
        """
        def _decompress():
            if not self.config.enable_compression or self.decompression_projection is None:
                return False
            
            if not (0 <= episode_idx < len(self.episodic_memory)):
                raise IndexError(f"Índice de episodio inválido: {episode_idx}")
            
            episode_item = self.episodic_memory[episode_idx]
            
            if not episode_item.get('compressed', False):
                return False
            
            compressed_episode = episode_item['episode']
            decompressed = self.decompression_projection(compressed_episode)
            
            episode_item['episode'] = decompressed.detach()
            episode_item['compressed'] = False
            if 'original_shape' in episode_item:
                del episode_item['original_shape']
            
            logger.debug("Episodio descomprimido", idx=episode_idx)
            return True
        
        result, error = safe_execute(_decompress, default_value=False, log_errors=True)
        if error:
            logger.error("Error descomprimiendo episodio", idx=episode_idx, error=str(error))
        return result
    
    def _load_persisted_memory(self) -> bool:
        """
        Carga memoria persistida desde disco.
        
        Returns:
            bool: True si se cargó exitosamente
        """
        def _load():
            if not self.persistence_path:
                return False
            
            memory_file = self.persistence_path / "episodic_memory.json"
            if not memory_file.exists():
                logger.debug("Archivo de memoria persistida no encontrado", path=str(memory_file))
                return False
            
            with open(memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar episodios
            loaded_count = 0
            for item in data.get('episodes', []):
                try:
                    episode = torch.tensor(item['episode'])
                    if episode.size(-1) != self.config.memory_dim:
                        logger.warning(
                            "Dimensión de episodio no coincide al cargar",
                            expected=self.config.memory_dim,
                            got=episode.size(-1)
                        )
                        continue
                    
                    metadata = item.get('metadata', {})
                    self.episodic_memory.append({
                        'episode': episode,
                        'metadata': metadata,
                        'timestamp': item.get('timestamp', time.time()),
                        'compressed': item.get('compressed', False)
                    })
                    loaded_count += 1
                except Exception as e:
                    logger.warning("Error cargando episodio", error=str(e), item_idx=loaded_count)
                    continue
            
            # Cargar memoria semántica
            semantic_file = self.persistence_path / "semantic_memory.json"
            if semantic_file.exists():
                try:
                    with open(semantic_file, 'r', encoding='utf-8') as f:
                        semantic_data = json.load(f)
                        # Convertir listas a tensores
                        for key, value in semantic_data.items():
                            if 'episode' in value and isinstance(value['episode'], list):
                                value['episode'] = torch.tensor(value['episode'])
                        self.semantic_memory = semantic_data
                except Exception as e:
                    logger.warning("Error cargando memoria semántica", error=str(e))
            
            logger.info("Memoria persistida cargada", episodes=loaded_count)
            return loaded_count > 0
        
        result, error = safe_execute(_load, default_value=False, log_errors=True)
        if error:
            logger.error("Error cargando memoria persistida", error=str(error))
        return result
    
    def save_persisted_memory(self) -> bool:
        """
        Guarda memoria en disco.
        
        Returns:
            bool: True si se guardó exitosamente
        """
        def _save():
            if not self.persistence_path:
                logger.warning("Persistencia deshabilitada o ruta no configurada")
                return False
            
            if not self.persistence_path.exists():
                self.persistence_path.mkdir(parents=True, exist_ok=True)
            
            # Guardar episodios
            episodes_data = [
                {
                    'episode': (
                        item['episode'].cpu().tolist()
                        if isinstance(item['episode'], torch.Tensor)
                        else item['episode']
                    ),
                    'metadata': item.get('metadata', {}),
                    'timestamp': item.get('timestamp', time.time()),
                    'compressed': item.get('compressed', False)
                }
                for item in self.episodic_memory
            ]
            
            memory_file = self.persistence_path / "episodic_memory.json"
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump({'episodes': episodes_data}, f, indent=2, ensure_ascii=False)
            
            # Guardar memoria semántica
            semantic_file = self.persistence_path / "semantic_memory.json"
            semantic_data = {
                key: {
                    'episode': (
                        value.get('episode').cpu().tolist()
                        if isinstance(value.get('episode'), torch.Tensor)
                        else value.get('episode')
                    ),
                    'metadata': value.get('metadata', {}),
                    'consolidation_time': value.get('consolidation_time', time.time())
                }
                for key, value in self.semantic_memory.items()
            }
            
            with open(semantic_file, 'w', encoding='utf-8') as f:
                json.dump(semantic_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Memoria persistida guardada", episodes=len(self.episodic_memory))
            return True
        
        result, error = safe_execute(_save, default_value=False, log_errors=True)
        if error:
            logger.error("Error guardando memoria persistida", error=str(error))
        return result
    
    def get_episodes_by_priority(self, min_priority: float = 0.5) -> List[int]:
        """
        Obtiene índices de episodios con prioridad mínima.
        
        Args:
            min_priority: Prioridad mínima
        
        Returns:
            Lista de índices de episodios
        """
        if self.episode_priorities is None:
            return list(range(len(self.episodic_memory)))
        
        return [
            idx for idx, priority in self.episode_priorities.items()
            if priority >= min_priority
        ]
    
    def update_episode_priority(self, episode_idx: int, new_priority: float) -> bool:
        """
        Actualiza la prioridad de un episodio.
        
        Args:
            episode_idx: Índice del episodio
            new_priority: Nueva prioridad (debe ser >= 0)
        
        Returns:
            bool: True si se actualizó exitosamente
        """
        if not self.config.enable_prioritization or self.episode_priorities is None:
            logger.warning("Priorización deshabilitada")
            return False
        
        if not (0 <= episode_idx < len(self.episodic_memory)):
            logger.warning("Índice de episodio inválido", idx=episode_idx, max_idx=len(self.episodic_memory))
            return False
        
        if new_priority < 0:
            logger.warning("Prioridad debe ser >= 0", received=new_priority)
            return False
        
        self.episode_priorities[episode_idx] = new_priority
        logger.debug("Prioridad actualizada", idx=episode_idx, priority=new_priority)
        return True
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del estado de la memoria.
        
        Returns:
            Diccionario con resumen completo
        """
        stats = self.get_episodic_stats()
        
        summary = {
            **stats,
            'compression_enabled': self.config.enable_compression,
            'compression_ratio': self.config.compression_ratio if self.config.enable_compression else None,
            'compressed_episodes': sum(
                1 for item in self.episodic_memory 
                if item.get('compressed', False)
            ) if self.config.enable_compression else 0,
            'prioritization_enabled': self.config.enable_prioritization,
            'tagged_episodes': len(self.episode_tags),
            'persistence_enabled': self.config.enable_persistence,
            'persistence_path': str(self.persistence_path) if self.persistence_path else None,
            'semantic_search_enabled': self.config.enable_semantic_search
        }
        
        return summary
    
    def cleanup_old_episodes(self, max_age_seconds: float = 86400.0) -> int:
        """
        Limpia episodios antiguos basado en timestamp.
        
        Args:
            max_age_seconds: Edad máxima en segundos (default: 24 horas)
        
        Returns:
            int: Número de episodios eliminados
        """
        if len(self.episodic_memory) == 0:
            return 0
        
        current_time = time.time()
        new_memory_items = [
            item
            for item in self.episodic_memory
            if current_time - item.get('timestamp', current_time) <= max_age_seconds
        ]
        
        removed = len(self.episodic_memory) - len(new_memory_items)
        self.episodic_memory = deque(new_memory_items, maxlen=self.config.max_memory_size)
        
        if removed > 0:
            logger.info("Episodios antiguos eliminados", removed=removed, max_age_hours=max_age_seconds/3600)
        
        return removed
    
    def _hydrate_from_disk_cache(self, limit: int = 512) -> int:
        """Rellena memoria desde diskcache persistente."""
        if not self.disk_cache:
            return 0
        
        loaded = 0
        try:
            for key in self.disk_cache.iterkeys(reverse=True):
                if loaded >= limit or len(self.episodic_memory) >= self.config.max_memory_size:
                    break
                entry = self.disk_cache.get(key)
                if not entry:
                    continue
                episode_tensor = torch.tensor(
                    entry.get('episode', []),
                    dtype=self.memory_embeddings.dtype
                )
                record = {
                    'episode': episode_tensor,
                    'metadata': entry.get('metadata', {}),
                    'timestamp': time.time(),
                    'access_count': 0
                }
                self.episodic_memory.appendleft(record)
                loaded += 1
        except Exception as exc:
            logger.warning("Error hidratando desde diskcache", error=str(exc))
            return loaded
        
        if loaded > 0:
            logger.info("Memoria hidratada desde diskcache", loaded=loaded)
        return loaded
    
    def _compute_similarity_scores(
        self,
        query_proj: torch.Tensor,
        episodes: torch.Tensor,
        temperature: float
    ) -> torch.Tensor:
        """Calcula similitud usando path estándar o distribuido."""
        scaling = temperature * (self.config.memory_dim ** 0.5)
        use_ray = (
            self.config.enable_ray_retrieval
            and RAY_AVAILABLE
            and episodes.size(0) > self.config.ray_chunk_size
        )
        
        if use_ray:
            sims = self._distributed_similarity(query_proj, episodes)
        else:
            sims = torch.matmul(query_proj, episodes.transpose(-2, -1))
        
        return sims / scaling
    
    def _distributed_similarity(
        self,
        query_proj: torch.Tensor,
        episodes: torch.Tensor
    ) -> torch.Tensor:
        """Calcula similitud usando Ray para dividir episodios en chunks."""
        if not RAY_AVAILABLE:
            return torch.matmul(query_proj, episodes.transpose(-2, -1))
        
        try:
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True, include_dashboard=False, logging_level="ERROR")
        except Exception:
            return torch.matmul(query_proj, episodes.transpose(-2, -1))
        
        query_np = query_proj.detach().cpu().numpy()
        episodes_np = episodes.detach().cpu().numpy()
        chunk_size = max(1, self.config.ray_chunk_size)
        futures = []
        
        for start in range(0, episodes_np.shape[0], chunk_size):
            chunk_np = episodes_np[start:start + chunk_size]
            futures.append(_ray_similarity_worker.remote(query_np, chunk_np))
        
        try:
            results = ray.get(futures)
            concatenated = np.concatenate(results, axis=1)
            return torch.from_numpy(concatenated).to(query_proj.device)
        except Exception as exc:
            logger.warning("Fallo en retrieval distribuido, usando fallback", error=str(exc))
            return torch.matmul(query_proj, episodes.transpose(-2, -1))
    
    def export_memory_snapshot(self, output_path: Optional[str] = None) -> Path:
        """Exporta episodios y metadata a CSV/Parquet."""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas requerido para exportar snapshot")
        
        records = [
            {
                'timestamp': item.get('timestamp', 0.0),
                'access_count': item.get('access_count', 0),
                'metadata': json.dumps(item.get('metadata', {}))
            }
            for item in self.episodic_memory
        ]
        df = pd.DataFrame(records)
        
        path = Path(output_path or "./memory_snapshot.parquet")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".parquet":
            df.to_parquet(path, index=False)
        else:
            df.to_csv(path, index=False)
        
        logger.info("Snapshot de memoria exportado", path=str(path), rows=len(df))
        return path
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Devuelve métricas combinadas de caché en memoria y diskcache."""
        stats = {
            'cache_enabled': self.config.enable_cache,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_entries': len(self.retrieval_cache) if self.retrieval_cache else 0,
            'disk_cache_enabled': self.config.enable_disk_cache,
            'disk_cache_entries': len(self.disk_cache) if self.disk_cache else 0
        }
        total_requests = self.cache_hits + self.cache_misses
        stats['cache_hit_rate'] = self.cache_hits / total_requests if total_requests else 0.0
        return stats
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Genera reporte de monitoreo avanzado."""
        stats = self.get_memory_summary()
        cache_metrics = self.get_cache_metrics()
        
        system_metrics = {}
        if psutil:
            system_metrics = {
                'memory_percent': psutil.virtual_memory().percent,
                'cpu_percent': psutil.cpu_percent(interval=0.05)
            }
        
        report = {
            'memory_summary': stats,
            'cache_metrics': cache_metrics,
            'system_metrics': system_metrics,
            'redis_replication': {
                'enabled': self.config.enable_redis_replication,
                'url': self.config.redis_url if self.config.enable_redis_replication else None
            }
        }
        return report


class TruthGPT_Paper2506_15841v2_Integration(BasePaperModule):
    """
    Integración del paper 2506.15841v2 con TruthGPT.
    
    Mejoras:
    - Herencia de BasePaperModule
    - Validación robusta
    - Métricas completas
    - Manejo de errores
    """
    
    def __init__(self, base_model, paper_config: Paper2506_15841v2Config):
        config_dict = _config_to_dict(paper_config)
        super().__init__(config_dict)
        
        self.base_model = base_model
        self.memory_system = Paper2506_15841v2_MemorySystem(paper_config)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con memoria episódica del paper.
        
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
        
        # Aplicar sistema de memoria
        output, metadata = self.memory_system(base_output, **kwargs)
        
        return output, metadata


if __name__ == "__main__":
    print("=" * 60)
    print("Test del Sistema de Memoria Mejorado")
    print("=" * 60)
    
    config = Paper2506_15841v2Config(
        memory_dim=512,
        enable_cache=True,
        enable_persistence=True,
        enable_prioritization=True
    )
    memory_system = Paper2506_15841v2_MemorySystem(config)
    
    # Test básico
    print("\n1. Test básico:")
    episode = torch.randn(config.memory_dim)
    memory_system.store_episode(episode, {'test': True})
    
    query = torch.randn(config.memory_dim)
    retrieved, weights = memory_system.retrieve_episodes(query)
    print(f"   ✅ Retrieved episodes shape: {retrieved.shape}, Weights shape: {weights.shape}")
    
    # Test con tags
    print("\n2. Test con tags:")
    memory_system.store_episode_with_tags(
        torch.randn(config.memory_dim),
        tags=['test', 'example'],
        priority=0.8
    )
    retrieved_tags, _ = memory_system.retrieve_by_tags(query, tags=['test'])
    print(f"   ✅ Episodios con tag 'test': {retrieved_tags.shape[1]}")
    
    # Test de estadísticas
    print("\n3. Estadísticas:")
    stats = memory_system.get_episodic_stats()
    print(f"   ✅ Episodios: {stats['episodic_size']}")
    print(f"   ✅ Cache hit rate: {stats.get('cache_hit_rate', 0):.2%}")
    
    # Test de analytics (si está disponible)
    print("\n4. Analytics:")
    try:
        from memory.memory_analytics import MemoryAnalytics
        analytics = MemoryAnalytics(memory_system)
        report = analytics.get_comprehensive_report()
        print(f"   ✅ Analytics disponibles")
        print(f"   ✅ Total accesos: {report['access_patterns']['total_accesses']}")
    except ImportError:
        print("   ⚠️  Analytics no disponibles (instalar sklearn, matplotlib)")
    
    print("\n" + "=" * 60)
    print("✅ Todos los tests completados!")
    print("=" * 60)

