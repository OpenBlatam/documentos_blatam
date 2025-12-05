#!/usr/bin/env python3
"""
Sistema de Caché Avanzado para Redundancy
==========================================

Implementación de caché LRU optimizado para matrices de similitud.
"""

import torch
import hashlib
import time
from typing import Dict, Optional, Any, Tuple
from collections import OrderedDict
from dataclasses import dataclass

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class CacheEntry:
    """Entrada del caché."""
    similarity_matrix: torch.Tensor
    timestamp: float
    access_count: int = 0
    size_bytes: int = 0


class LRUSimilarityCache:
    """
    Caché LRU para matrices de similitud.
    
    Características:
    - Evicción LRU automática
    - Límite de tamaño y memoria
    - Estadísticas de hit/miss
    - Thread-safe (básico)
    """
    
    def __init__(
        self,
        max_size: int = 100,
        max_memory_mb: float = 500.0
    ):
        """
        Args:
            max_size: Número máximo de entradas
            max_memory_mb: Memoria máxima en MB
        
        Raises:
            ValueError: Si max_size o max_memory_mb son inválidos
        """
        if max_size <= 0:
            raise ValueError(f"max_size debe ser > 0, recibido: {max_size}")
        if max_memory_mb <= 0:
            raise ValueError(f"max_memory_mb debe ser > 0, recibido: {max_memory_mb}")
        
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
    
    def _calculate_size(self, tensor: torch.Tensor) -> int:
        """Calcula tamaño aproximado del tensor en bytes."""
        return tensor.numel() * tensor.element_size()
    
    def _generate_key(
        self,
        embeddings: torch.Tensor,
        method: str
    ) -> str:
        """Genera clave única para embeddings y método."""
        def _gen():
            embeddings_bytes = embeddings.cpu().numpy().tobytes()
            hash_obj = hashlib.sha256(embeddings_bytes)
            hash_obj.update(method.encode())
            return hash_obj.hexdigest()
        
        result, _ = safe_execute(_gen, default_value=str(time.time()), log_errors=False)
        return result
    
    def get(
        self,
        embeddings: torch.Tensor,
        method: str
    ) -> Optional[torch.Tensor]:
        """
        Obtiene matriz de similitud del caché.
        
        Args:
            embeddings: Embeddings de entrada
            method: Método de similitud
        
        Returns:
            Matriz de similitud o None si no está en caché
        
        Raises:
            ValueError: Si embeddings es None o method está vacío
            TypeError: Si embeddings no es un tensor
        """
        if embeddings is None:
            raise ValueError("embeddings no puede ser None")
        if not isinstance(embeddings, torch.Tensor):
            raise TypeError(f"embeddings debe ser torch.Tensor, recibido: {type(embeddings)}")
        if not method or not isinstance(method, str):
            raise ValueError(f"method debe ser una cadena no vacía, recibido: {method}")
        key = self._generate_key(embeddings, method)
        
        if key in self.cache:
            entry = self.cache[key]
            entry.access_count += 1
            entry.timestamp = time.time()
            
            self.cache.move_to_end(key)
            self.hits += 1
            
            return entry.similarity_matrix.clone()
        
        self.misses += 1
        return None
    
    def set(
        self,
        embeddings: torch.Tensor,
        method: str,
        similarity_matrix: torch.Tensor
    ) -> bool:
        """
        Almacena matriz de similitud en caché.
        
        Args:
            embeddings: Embeddings de entrada
            method: Método de similitud
            similarity_matrix: Matriz de similitud a cachear
        
        Returns:
            True si se almacenó exitosamente
        
        Raises:
            ValueError: Si algún parámetro es None o inválido
            TypeError: Si los tensores no son del tipo correcto
        """
        if embeddings is None:
            raise ValueError("embeddings no puede ser None")
        if similarity_matrix is None:
            raise ValueError("similarity_matrix no puede ser None")
        if not isinstance(embeddings, torch.Tensor):
            raise TypeError(f"embeddings debe ser torch.Tensor, recibido: {type(embeddings)}")
        if not isinstance(similarity_matrix, torch.Tensor):
            raise TypeError(f"similarity_matrix debe ser torch.Tensor, recibido: {type(similarity_matrix)}")
        if not method or not isinstance(method, str):
            raise ValueError(f"method debe ser una cadena no vacía, recibido: {method}")
        key = self._generate_key(embeddings, method)
        size = self._calculate_size(similarity_matrix)
        
        if size > self.max_memory_bytes:
            return False
        
        while (len(self.cache) >= self.max_size or 
               (self.current_memory + size) > self.max_memory_bytes):
            if not self.cache:
                break
            self._evict_lru()
        
        entry = CacheEntry(
            similarity_matrix=similarity_matrix.clone(),
            timestamp=time.time(),
            access_count=1,
            size_bytes=size
        )
        
        if key in self.cache:
            old_entry = self.cache.pop(key)
            self.current_memory -= old_entry.size_bytes
        
        self.cache[key] = entry
        self.current_memory += size
        
        return True
    
    def _evict_lru(self):
        """Elimina la entrada menos recientemente usada."""
        if self.cache:
            key, entry = self.cache.popitem(last=False)
            self.current_memory -= entry.size_bytes
    
    def clear(self):
        """Limpia todo el caché."""
        self.cache.clear()
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'memory_mb': self.current_memory / (1024 * 1024),
            'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }


class OptimizedRedundancyProcessor:
    """
    Procesador optimizado de redundancia con caché y optimizaciones.
    """
    
    def __init__(
        self,
        similarity_cache: Optional[LRUSimilarityCache] = None,
        use_batch_optimization: bool = True,
        chunk_size: int = 1000
    ):
        """
        Args:
            similarity_cache: Caché de similitudes (opcional)
            use_batch_optimization: Si usar optimizaciones de batch
            chunk_size: Tamaño de chunk para procesamiento
        
        Raises:
            ValueError: Si chunk_size es inválido
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size debe ser > 0, recibido: {chunk_size}")
        
        self.similarity_cache = similarity_cache
        self.use_batch_optimization = use_batch_optimization
        self.chunk_size = chunk_size
    
    def process_large_batch(
        self,
        items: torch.Tensor,
        suppressor,
        threshold: float
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa un batch grande de forma optimizada.
        
        Args:
            items: Items a procesar [batch_size, seq_len, hidden_dim]
            suppressor: Supresor de redundancia
            threshold: Umbral de similitud
        
        Returns:
            Items únicos y estadísticas
        
        Raises:
            ValueError: Si items o suppressor son None, o threshold es inválido
            TypeError: Si items no es un tensor
        """
        if items is None:
            raise ValueError("items no puede ser None")
        if suppressor is None:
            raise ValueError("suppressor no puede ser None")
        if not isinstance(items, torch.Tensor):
            raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold debe estar en [0.0, 1.0], recibido: {threshold}")
        batch_size = items.size(0)
        
        if batch_size <= self.chunk_size:
            return suppressor.process_bulk(items)
        
        unique_items_list = []
        total_reduced = 0
        total_processed = 0
        
        for i in range(0, batch_size, self.chunk_size):
            chunk = items[i:i + self.chunk_size]
            chunk_unique, chunk_stats = suppressor.process_bulk(chunk)
            
            unique_items_list.append(chunk_unique)
            total_reduced += chunk_stats.get('original_size', 0) - chunk_stats.get('reduced_size', 0)
            total_processed += chunk_stats.get('original_size', 0)
        
        unique_items = torch.cat(unique_items_list, dim=0)
        
        stats = {
            'original_size': batch_size,
            'reduced_size': unique_items.size(0),
            'reduction_rate': (batch_size - unique_items.size(0)) / batch_size if batch_size > 0 else 0.0,
            'chunks_processed': (batch_size + self.chunk_size - 1) // self.chunk_size,
            'total_reduced': total_reduced,
            'total_processed': total_processed
        }
        
        return unique_items, stats

