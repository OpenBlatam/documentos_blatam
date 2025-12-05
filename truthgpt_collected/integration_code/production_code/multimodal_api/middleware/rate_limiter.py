#!/usr/bin/env python3
"""
Rate Limiter Inteligente para la API Multimodal.

Implementa rate limiting con múltiples estrategias:
- Fixed Window
- Sliding Window
- Token Bucket
- Priorización por tipo de tarea
"""

from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import time
import threading

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Estrategias de rate limiting."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Configuración de rate limiting."""
    max_requests: int = 100
    window_seconds: int = 60
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_size: int = 10  # Para token bucket
    priority_multiplier: Dict[int, float] = None  # Multiplicador por prioridad
    
    def __post_init__(self):
        if self.priority_multiplier is None:
            # Prioridad alta (1-3) tiene más límite
            self.priority_multiplier = {
                1: 2.0,  # 2x más requests
                2: 1.5,
                3: 1.2,
                4: 1.0,
                5: 1.0,
                6: 0.8,
                7: 0.6,
                8: 0.4,
                9: 0.2,
                10: 0.1
            }


@dataclass
class RateLimitResult:
    """Resultado de verificación de rate limit."""
    allowed: bool
    remaining_requests: int
    reset_after_seconds: int
    retry_after_seconds: Optional[int] = None
    limit_exceeded: bool = False


class RateLimiter:
    """Rate limiter inteligente con múltiples estrategias."""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Inicializa el rate limiter.
        
        Args:
            config: Configuración de rate limiting
        """
        self.config = config or RateLimitConfig()
        self.limits: Dict[str, deque] = {}  # Para sliding window
        self.token_buckets: Dict[str, Dict[str, float]] = {}  # Para token bucket
        self.fixed_windows: Dict[str, Tuple[int, float]] = {}  # Para fixed window
        self.lock = threading.Lock()
        
    def check_rate_limit(
        self,
        identifier: str,
        priority: int = 5,
        custom_limit: Optional[int] = None
    ) -> RateLimitResult:
        """
        Verifica si un request está permitido.
        
        Args:
            identifier: Identificador único (IP, user_id, etc.)
            priority: Prioridad de la tarea (1-10)
            custom_limit: Límite personalizado (opcional)
        
        Returns:
            Resultado de verificación
        """
        with self.lock:
            # Calcular límite efectivo basado en prioridad
            multiplier = self.config.priority_multiplier.get(priority, 1.0)
            max_requests = int((custom_limit or self.config.max_requests) * multiplier)
            
            if self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
                return self._check_fixed_window(identifier, max_requests)
            elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return self._check_sliding_window(identifier, max_requests)
            elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return self._check_token_bucket(identifier, max_requests)
            else:
                return self._check_sliding_window(identifier, max_requests)
    
    def _check_fixed_window(
        self,
        identifier: str,
        max_requests: int
    ) -> RateLimitResult:
        """Verifica rate limit usando fixed window."""
        now = time.time()
        window_start = int(now / self.config.window_seconds) * self.config.window_seconds
        
        if identifier not in self.fixed_windows:
            self.fixed_windows[identifier] = (0, window_start)
        
        count, window = self.fixed_windows[identifier]
        
        # Si estamos en una nueva ventana, resetear
        if window < window_start:
            count = 0
            window = window_start
        
        if count >= max_requests:
            reset_after = int(self.config.window_seconds - (now - window))
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_after_seconds=reset_after,
                retry_after_seconds=reset_after,
                limit_exceeded=True
            )
        
        # Incrementar contador
        self.fixed_windows[identifier] = (count + 1, window)
        
        return RateLimitResult(
            allowed=True,
            remaining_requests=max_requests - count - 1,
            reset_after_seconds=int(self.config.window_seconds - (now - window))
        )
    
    def _check_sliding_window(
        self,
        identifier: str,
        max_requests: int
    ) -> RateLimitResult:
        """Verifica rate limit usando sliding window."""
        now = time.time()
        cutoff = now - self.config.window_seconds
        
        if identifier not in self.limits:
            self.limits[identifier] = deque()
        
        # Limpiar timestamps antiguos
        while self.limits[identifier] and self.limits[identifier][0] < cutoff:
            self.limits[identifier].popleft()
        
        if len(self.limits[identifier]) >= max_requests:
            oldest = self.limits[identifier][0]
            retry_after = int(cutoff + self.config.window_seconds - now + 1)
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_after_seconds=int(self.config.window_seconds - (now - oldest)),
                retry_after_seconds=max(1, retry_after),
                limit_exceeded=True
            )
        
        # Agregar timestamp actual
        self.limits[identifier].append(now)
        
        return RateLimitResult(
            allowed=True,
            remaining_requests=max_requests - len(self.limits[identifier]),
            reset_after_seconds=self.config.window_seconds
        )
    
    def _check_token_bucket(
        self,
        identifier: str,
        max_requests: int
    ) -> RateLimitResult:
        """Verifica rate limit usando token bucket."""
        now = time.time()
        
        if identifier not in self.token_buckets:
            self.token_buckets[identifier] = {
                "tokens": float(max_requests),
                "last_update": now,
                "capacity": float(max_requests)
            }
        
        bucket = self.token_buckets[identifier]
        
        # Calcular tokens a agregar
        elapsed = now - bucket["last_update"]
        tokens_to_add = elapsed * (max_requests / self.config.window_seconds)
        bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now
        
        if bucket["tokens"] < 1.0:
            # No hay tokens disponibles
            tokens_needed = 1.0 - bucket["tokens"]
            retry_after = int(tokens_needed / (max_requests / self.config.window_seconds))
            return RateLimitResult(
                allowed=False,
                remaining_requests=int(bucket["tokens"]),
                reset_after_seconds=self.config.window_seconds,
                retry_after_seconds=max(1, retry_after),
                limit_exceeded=True
            )
        
        # Consumir un token
        bucket["tokens"] -= 1.0
        
        return RateLimitResult(
            allowed=True,
            remaining_requests=int(bucket["tokens"]),
            reset_after_seconds=self.config.window_seconds
        )
    
    def get_stats(self, identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de rate limiting.
        
        Args:
            identifier: Identificador específico (opcional)
        
        Returns:
            Estadísticas
        """
        with self.lock:
            if identifier:
                return {
                    "identifier": identifier,
                    "strategy": self.config.strategy.value,
                    "current_requests": len(self.limits.get(identifier, [])),
                    "max_requests": self.config.max_requests,
                    "window_seconds": self.config.window_seconds
                }
            else:
                return {
                    "total_identifiers": len(self.limits),
                    "strategy": self.config.strategy.value,
                    "max_requests": self.config.max_requests,
                    "window_seconds": self.config.window_seconds
                }
    
    def reset(self, identifier: Optional[str] = None):
        """
        Resetea el rate limiter para un identificador o todos.
        
        Args:
            identifier: Identificador específico (opcional)
        """
        with self.lock:
            if identifier:
                self.limits.pop(identifier, None)
                self.token_buckets.pop(identifier, None)
                self.fixed_windows.pop(identifier, None)
            else:
                self.limits.clear()
                self.token_buckets.clear()
                self.fixed_windows.clear()


