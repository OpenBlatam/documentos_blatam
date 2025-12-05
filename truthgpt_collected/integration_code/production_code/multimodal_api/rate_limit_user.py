#!/usr/bin/env python3
"""
Rate Limiting por Usuario/API Key.

Permite límites personalizados por usuario o API key.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class UserRateLimit:
    """Límite de rate por usuario."""
    user_id: str
    max_requests: int
    window_seconds: int
    current_requests: int = 0
    window_start: datetime = None
    
    def __post_init__(self):
        if self.window_start is None:
            self.window_start = datetime.now()
    
    def reset_if_needed(self):
        """Resetea la ventana si es necesario."""
        elapsed = (datetime.now() - self.window_start).total_seconds()
        if elapsed >= self.window_seconds:
            self.current_requests = 0
            self.window_start = datetime.now()
    
    def can_make_request(self) -> bool:
        """
        Verifica si puede hacer un request.
        
        Returns:
            True si puede hacer request
        """
        self.reset_if_needed()
        return self.current_requests < self.max_requests
    
    def record_request(self):
        """Registra un request."""
        self.reset_if_needed()
        self.current_requests += 1


class UserRateLimiter:
    """Rate limiter por usuario."""
    
    def __init__(self, default_limit: int = 100, default_window: int = 60):
        """
        Inicializa el rate limiter por usuario.
        
        Args:
            default_limit: Límite por defecto
            default_window: Ventana por defecto (segundos)
        """
        self.default_limit = default_limit
        self.default_window = default_window
        self.user_limits: Dict[str, UserRateLimit] = {}
        self.custom_limits: Dict[str, Dict[str, int]] = {}
    
    def set_user_limit(
        self,
        user_id: str,
        max_requests: int,
        window_seconds: int
    ):
        """
        Establece límite personalizado para un usuario.
        
        Args:
            user_id: ID de usuario
            max_requests: Máximo de requests
            window_seconds: Ventana en segundos
        """
        self.custom_limits[user_id] = {
            "max_requests": max_requests,
            "window_seconds": window_seconds
        }
        logger.info(
            f"Límite personalizado para usuario {user_id}: {max_requests}/{window_seconds}s"
        )
    
    def get_user_limit(self, user_id: str) -> UserRateLimit:
        """
        Obtiene límite de usuario (crea si no existe).
        
        Args:
            user_id: ID de usuario
        
        Returns:
            Límite de usuario
        """
        if user_id not in self.user_limits:
            # Usar límite personalizado si existe
            if user_id in self.custom_limits:
                custom = self.custom_limits[user_id]
                limit = UserRateLimit(
                    user_id=user_id,
                    max_requests=custom["max_requests"],
                    window_seconds=custom["window_seconds"]
                )
            else:
                limit = UserRateLimit(
                    user_id=user_id,
                    max_requests=self.default_limit,
                    window_seconds=self.default_window
                )
            
            self.user_limits[user_id] = limit
        
        return self.user_limits[user_id]
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica rate limit para un usuario.
        
        Args:
            user_id: ID de usuario
        
        Returns:
            (permitido, información)
        """
        limit = self.get_user_limit(user_id)
        
        allowed = limit.can_make_request()
        
        info = {
            "user_id": user_id,
            "limit": limit.max_requests,
            "remaining": max(0, limit.max_requests - limit.current_requests),
            "window_seconds": limit.window_seconds,
            "reset_at": (limit.window_start + timedelta(seconds=limit.window_seconds)).isoformat()
        }
        
        if allowed:
            limit.record_request()
            info["remaining"] = max(0, limit.max_requests - limit.current_requests)
        
        return allowed, info
    
    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas de un usuario.
        
        Args:
            user_id: ID de usuario
        
        Returns:
            Estadísticas o None
        """
        if user_id not in self.user_limits:
            return None
        
        limit = self.user_limits[user_id]
        limit.reset_if_needed()
        
        return {
            "user_id": user_id,
            "limit": limit.max_requests,
            "current": limit.current_requests,
            "remaining": max(0, limit.max_requests - limit.current_requests),
            "window_seconds": limit.window_seconds,
            "window_start": limit.window_start.isoformat(),
            "reset_at": (limit.window_start + timedelta(seconds=limit.window_seconds)).isoformat()
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de todos los usuarios.
        
        Returns:
            Estadísticas
        """
        stats = {}
        for user_id in self.user_limits:
            stats[user_id] = self.get_user_stats(user_id)
        
        return {
            "total_users": len(self.user_limits),
            "users": stats,
            "default_limit": self.default_limit,
            "default_window": self.default_window
        }
    
    def reset_user(self, user_id: str):
        """
        Resetea límite de un usuario.
        
        Args:
            user_id: ID de usuario
        """
        if user_id in self.user_limits:
            limit = self.user_limits[user_id]
            limit.current_requests = 0
            limit.window_start = datetime.now()
            logger.info(f"Límite reseteado para usuario {user_id}")
    
    def clear_user(self, user_id: str):
        """
        Elimina límite de un usuario.
        
        Args:
            user_id: ID de usuario
        """
        if user_id in self.user_limits:
            del self.user_limits[user_id]
            logger.info(f"Límite eliminado para usuario {user_id}")

