#!/usr/bin/env python3
"""
Configuración para Paper 2506.15841v2
======================================

Módulo de configuración para el sistema de memoria.
"""

from typing import Optional
from dataclasses import dataclass

try:
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    from core.paper_base import BasePaperConfig
except ImportError:
    BasePaperConfig = None


def _config_to_dict(config) -> dict:
    """Normaliza cualquier configuración a un dict estándar."""
    if hasattr(config, "model_dump"):
        return config.model_dump()
    if hasattr(config, "dict"):
        return config.dict()
    if hasattr(config, "__dict__"):
        return dict(config.__dict__)
    return dict(config)


if PYDANTIC_AVAILABLE and BasePaperConfig:
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

