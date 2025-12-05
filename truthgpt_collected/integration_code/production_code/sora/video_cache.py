#!/usr/bin/env python3
"""
Video Cache - Sistema de Caché para Videos Generados
=====================================================

Sistema de caché inteligente para videos generados con:
- TTL configurable
- Invalidación automática
- Estadísticas de hit/miss
- Soporte para múltiples backends
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.utils import setup_logger

logger = setup_logger(__name__)


class VideoCache:
    """
    Sistema de caché para videos generados.
    
    Soporta:
    - Caché en memoria (LRU)
    - Caché en Redis (opcional)
    - TTL configurable
    - Estadísticas de uso
    """
    
    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600,
        cache_dir: Optional[Path] = None,
        use_redis: bool = False,
        redis_url: Optional[str] = None
    ):
        """
        Inicializa el caché de videos.
        
        Args:
            max_size: Tamaño máximo del caché en memoria
            ttl_seconds: Tiempo de vida en segundos
            cache_dir: Directorio para guardar videos en caché
            use_redis: Si usar Redis como backend
            redis_url: URL de Redis (si use_redis=True)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache_dir = cache_dir or Path("/tmp/sora_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_cache: OrderedDict = OrderedDict()
        self.cache_metadata: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        self.hits = 0
        self.misses = 0
        
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_client = None
        
        if self.use_redis:
            try:
                if redis_url:
                    self.redis_client = redis.from_url(redis_url)
                else:
                    self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.redis_client.ping()
                logger.info("Redis conectado para caché de videos")
            except Exception as e:
                logger.warning(f"Error conectando a Redis: {e}")
                self.use_redis = False
    
    def _generate_key(self, prompt: Optional[str] = None, config: Optional[Dict[str, Any]] = None, 
                     seed: Optional[int] = None, **kwargs) -> str:
        """
        Genera una clave única para el caché.
        
        Args:
            prompt: Prompt de texto (si aplica)
            config: Configuración del modelo
            seed: Semilla
            **kwargs: Otros parámetros
        
        Returns:
            Clave de caché
        """
        key_data = {
            'prompt': prompt,
            'config': config,
            'seed': seed,
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(
        self,
        prompt: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> Optional[Tuple[Path, Dict[str, Any]]]:
        """
        Obtiene un video del caché.
        
        Args:
            prompt: Prompt de texto
            config: Configuración
            seed: Semilla
            **kwargs: Otros parámetros
        
        Returns:
            (video_path, metadata) o None si no está en caché
        """
        cache_key = self._generate_key(prompt=prompt, config=config, seed=seed, **kwargs)
        
        with self.lock:
            # Intentar Redis primero
            if self.use_redis and self.redis_client:
                try:
                    cached_data = self.redis_client.get(f"sora:video:{cache_key}")
                    if cached_data:
                        data = json.loads(cached_data)
                        video_path = Path(data['video_path'])
                        if video_path.exists():
                            self.hits += 1
                            return video_path, data.get('metadata', {})
                except Exception as e:
                    logger.warning(f"Error obteniendo de Redis: {e}")
            
            # Intentar memoria
            if cache_key in self.memory_cache:
                metadata = self.cache_metadata.get(cache_key, {})
                timestamp = metadata.get('timestamp', 0)
                
                if time.time() - timestamp < self.ttl_seconds:
                    video_path = self.memory_cache[cache_key]
                    if video_path.exists():
                        self.memory_cache.move_to_end(cache_key)
                        self.hits += 1
                        return video_path, metadata.get('metadata', {})
                else:
                    # Expiró, eliminar
                    del self.memory_cache[cache_key]
                    if cache_key in self.cache_metadata:
                        del self.cache_metadata[cache_key]
            
            self.misses += 1
            return None
    
    def set(
        self,
        video_path: Path,
        metadata: Dict[str, Any],
        prompt: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        **kwargs
    ):
        """
        Guarda un video en el caché.
        
        Args:
            video_path: Path al video
            metadata: Metadata del video
            prompt: Prompt usado
            config: Configuración
            seed: Semilla
            **kwargs: Otros parámetros
        """
        cache_key = self._generate_key(prompt=prompt, config=config, seed=seed, **kwargs)
        
        with self.lock:
            # Guardar en memoria
            if len(self.memory_cache) >= self.max_size:
                # Eliminar el más antiguo (LRU)
                oldest_key = next(iter(self.memory_cache))
                del self.memory_cache[oldest_key]
                if oldest_key in self.cache_metadata:
                    del self.cache_metadata[oldest_key]
            
            self.memory_cache[cache_key] = video_path
            self.cache_metadata[cache_key] = {
                'timestamp': time.time(),
                'metadata': metadata
            }
            
            # Guardar en Redis si está disponible
            if self.use_redis and self.redis_client:
                try:
                    cache_data = {
                        'video_path': str(video_path),
                        'metadata': metadata,
                        'timestamp': time.time()
                    }
                    self.redis_client.setex(
                        f"sora:video:{cache_key}",
                        self.ttl_seconds,
                        json.dumps(cache_data)
                    )
                except Exception as e:
                    logger.warning(f"Error guardando en Redis: {e}")
    
    def clear(self):
        """Limpia el caché."""
        with self.lock:
            self.memory_cache.clear()
            self.cache_metadata.clear()
            self.hits = 0
            self.misses = 0
            
            if self.use_redis and self.redis_client:
                try:
                    keys = self.redis_client.keys("sora:video:*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Error limpiando Redis: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'total_requests': total_requests,
                'hit_rate': hit_rate,
                'cache_size': len(self.memory_cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'use_redis': self.use_redis
            }
    
    def cleanup_expired(self):
        """Limpia entradas expiradas del caché."""
        with self.lock:
            current_time = time.time()
            expired_keys = []
            
            for key, metadata in self.cache_metadata.items():
                timestamp = metadata.get('timestamp', 0)
                if current_time - timestamp >= self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.cache_metadata:
                    del self.cache_metadata[key]
            
            if expired_keys:
                logger.info(f"Limpiadas {len(expired_keys)} entradas expiradas del caché")


