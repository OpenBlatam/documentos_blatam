#!/usr/bin/env python3
"""
Sistema de Caching Optimizado para la API Multimodal.

Implementa caching inteligente con:
- TTL configurable
- Invalidación por patrón
- Estadísticas de hit/miss
- Soporte para múltiples backends (memoria, Redis)
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import time
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuración de cache."""
    default_ttl: int = 3600  # 1 hora por defecto
    max_size: int = 10000  # Máximo de entradas en memoria
    backend: str = "memory"  # "memory" o "redis"
    redis_url: Optional[str] = None
    key_prefix: str = "multimodal_api:"


class CacheManager:
    """Gestor de cache optimizado."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Inicializa el cache manager.
        
        Args:
            config: Configuración de cache
        """
        self.config = config or CacheConfig()
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_client = None
        self.lock = threading.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
        
        if self.config.backend == "redis" and REDIS_AVAILABLE:
            try:
                redis_url = self.config.redis_url or "redis://localhost:6379/0"
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Conectado a Redis para cache")
            except Exception as e:
                logger.warning(f"No se pudo conectar a Redis: {e}. Usando cache en memoria")
                self.config.backend = "memory"
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Genera una clave de cache única.
        
        Args:
            prefix: Prefijo de la clave
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        
        Returns:
            Clave de cache
        """
        key_parts = [prefix]
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}={v}")
        
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        return f"{self.config.key_prefix}{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache.
        
        Args:
            key: Clave de cache
        
        Returns:
            Valor cacheado o None
        """
        if self.config.backend == "redis" and self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    self.stats["hits"] += 1
                    return json.loads(cached)
                else:
                    self.stats["misses"] += 1
                    return None
            except Exception as e:
                logger.error(f"Error obteniendo de Redis: {e}")
                self.stats["misses"] += 1
                return None
        
        # Cache en memoria
        with self.lock:
            if key not in self.memory_cache:
                self.stats["misses"] += 1
                return None
            
            entry = self.memory_cache[key]
            
            # Verificar expiración
            if time.time() > entry["expires_at"]:
                del self.memory_cache[key]
                self.stats["misses"] += 1
                return None
            
            self.stats["hits"] += 1
            entry["hits"] = entry.get("hits", 0) + 1
            return entry["value"]
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Almacena un valor en el cache.
        
        Args:
            key: Clave de cache
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos (opcional)
        
        Returns:
            True si se almacenó correctamente
        """
        ttl = ttl or self.config.default_ttl
        expires_at = time.time() + ttl
        
        if self.config.backend == "redis" and self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                self.stats["sets"] += 1
                return True
            except Exception as e:
                logger.error(f"Error almacenando en Redis: {e}")
                return False
        
        # Cache en memoria
        with self.lock:
            # Limpiar si excede tamaño máximo
            if len(self.memory_cache) >= self.config.max_size:
                # Eliminar entrada más antigua
                oldest_key = min(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k].get("created_at", 0)
                )
                del self.memory_cache[oldest_key]
            
            self.memory_cache[key] = {
                "value": value,
                "created_at": time.time(),
                "expires_at": expires_at,
                "hits": 0
            }
            self.stats["sets"] += 1
            return True
    
    def delete(self, key: str) -> bool:
        """
        Elimina una entrada del cache.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            True si se eliminó correctamente
        """
        if self.config.backend == "redis" and self.redis_client:
            try:
                deleted = self.redis_client.delete(key)
                if deleted:
                    self.stats["deletes"] += 1
                return bool(deleted)
            except Exception as e:
                logger.error(f"Error eliminando de Redis: {e}")
                return False
        
        with self.lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
                self.stats["deletes"] += 1
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida todas las claves que coincidan con un patrón.
        
        Args:
            pattern: Patrón a buscar
        
        Returns:
            Número de claves eliminadas
        """
        count = 0
        
        if self.config.backend == "redis" and self.redis_client:
            try:
                keys = self.redis_client.keys(f"{self.config.key_prefix}{pattern}*")
                if keys:
                    count = self.redis_client.delete(*keys)
                    self.stats["deletes"] += count
            except Exception as e:
                logger.error(f"Error invalidando patrón en Redis: {e}")
        else:
            with self.lock:
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if pattern in k
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    count += 1
                self.stats["deletes"] += count
        
        return count
    
    def clear(self):
        """Limpia todo el cache."""
        if self.config.backend == "redis" and self.redis_client:
            try:
                pattern = f"{self.config.key_prefix}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Error limpiando Redis: {e}")
        else:
            with self.lock:
                self.memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Estadísticas
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0.0
        
        stats = {
            "backend": self.config.backend,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total
        }
        
        if self.config.backend == "memory":
            with self.lock:
                stats["size"] = len(self.memory_cache)
                stats["max_size"] = self.config.max_size
        
        return stats


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    cache_manager: Optional[CacheManager] = None
) -> Callable:
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        ttl: Tiempo de vida del cache en segundos
        key_prefix: Prefijo para la clave de cache
        cache_manager: Instancia de CacheManager (opcional)
    
    Returns:
        Decorador
    """
    manager = cache_manager or CacheManager()
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            cache_key = manager._generate_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # Intentar obtener del cache
            cached_value = manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


