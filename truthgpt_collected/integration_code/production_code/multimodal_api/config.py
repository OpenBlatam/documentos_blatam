#!/usr/bin/env python3
"""
Configuración para la API Multimodal.

Maneja configuración desde variables de entorno y archivos.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import os
from pathlib import Path

try:
    from pydantic import BaseSettings
    PYDANTIC_AVAILABLE = True
except ImportError:
    try:
        from pydantic_settings import BaseSettings
        PYDANTIC_AVAILABLE = True
    except ImportError:
        PYDANTIC_AVAILABLE = False


@dataclass
class APIConfig:
    """Configuración de la API."""
    
    # Servidor
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Rate Limiting
    rate_limit_max_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_strategy: str = "sliding_window"
    
    # Cache
    cache_backend: str = "memory"  # "memory" o "redis"
    cache_redis_url: Optional[str] = None
    cache_default_ttl: int = 3600
    cache_max_size: int = 10000
    
    # Task Queue
    queue_max_workers: int = 4
    
    # Autenticación
    auth_enabled: bool = False
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    
    # Generadores
    video_generator_enabled: bool = True
    image_generator_enabled: bool = True
    audio_generator_enabled: bool = True
    
    # Storage
    storage_path: str = "./storage"
    storage_url_prefix: str = "/storage"
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """
        Crea configuración desde variables de entorno.
        
        Returns:
            Configuración
        """
        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            reload=os.getenv("API_RELOAD", "false").lower() == "true",
            
            rate_limit_max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
            rate_limit_strategy=os.getenv("RATE_LIMIT_STRATEGY", "sliding_window"),
            
            cache_backend=os.getenv("CACHE_BACKEND", "memory"),
            cache_redis_url=os.getenv("CACHE_REDIS_URL"),
            cache_default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
            cache_max_size=int(os.getenv("CACHE_MAX_SIZE", "10000")),
            
            queue_max_workers=int(os.getenv("QUEUE_MAX_WORKERS", "4")),
            
            auth_enabled=os.getenv("AUTH_ENABLED", "false").lower() == "true",
            jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            
            video_generator_enabled=os.getenv("VIDEO_GENERATOR_ENABLED", "true").lower() == "true",
            image_generator_enabled=os.getenv("IMAGE_GENERATOR_ENABLED", "true").lower() == "true",
            audio_generator_enabled=os.getenv("AUDIO_GENERATOR_ENABLED", "true").lower() == "true",
            
            storage_path=os.getenv("STORAGE_PATH", "./storage"),
            storage_url_prefix=os.getenv("STORAGE_URL_PREFIX", "/storage"),
            
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_") and not callable(v)
        }


# Configuración global
config = APIConfig.from_env()


