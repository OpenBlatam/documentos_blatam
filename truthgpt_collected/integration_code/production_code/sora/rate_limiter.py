#!/usr/bin/env python3
"""
Rate Limiter - Control de Tasa para API
=========================================

Sistema de rate limiting para la API de Sora.
"""

import time
from typing import Dict, Optional, Any
from collections import defaultdict, deque
from threading import Lock
from datetime import datetime, timedelta


class RateLimiter:
    """
    Rate limiter simple usando token bucket algorithm.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        """
        Inicializa el rate limiter.
        
        Args:
            requests_per_minute: Requests permitidas por minuto
            requests_per_hour: Requests permitidas por hora
            requests_per_day: Requests permitidas por día
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        self.minute_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.hour_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.day_requests: Dict[str, deque] = defaultdict(lambda: deque())
        
        self.lock = Lock()
    
    def is_allowed(self, client_id: str = "default") -> tuple[bool, Optional[str]]:
        """
        Verifica si un request está permitido.
        
        Args:
            client_id: ID del cliente
        
        Returns:
            (allowed, error_message)
        """
        with self.lock:
            now = time.time()
            
            # Limpiar requests antiguos
            self._cleanup_old_requests(client_id, now)
            
            # Verificar límites
            minute_count = len(self.minute_requests[client_id])
            hour_count = len(self.hour_requests[client_id])
            day_count = len(self.day_requests[client_id])
            
            if minute_count >= self.requests_per_minute:
                return False, f"Rate limit exceeded: {minute_count}/{self.requests_per_minute} requests per minute"
            
            if hour_count >= self.requests_per_hour:
                return False, f"Rate limit exceeded: {hour_count}/{self.requests_per_hour} requests per hour"
            
            if day_count >= self.requests_per_day:
                return False, f"Rate limit exceeded: {day_count}/{self.requests_per_day} requests per day"
            
            # Registrar request
            self.minute_requests[client_id].append(now)
            self.hour_requests[client_id].append(now)
            self.day_requests[client_id].append(now)
            
            return True, None
    
    def _cleanup_old_requests(self, client_id: str, now: float):
        """Limpia requests antiguos."""
        # Limpiar requests de más de 1 minuto
        while (self.minute_requests[client_id] and 
               now - self.minute_requests[client_id][0] > 60):
            self.minute_requests[client_id].popleft()
        
        # Limpiar requests de más de 1 hora
        while (self.hour_requests[client_id] and 
               now - self.hour_requests[client_id][0] > 3600):
            self.hour_requests[client_id].popleft()
        
        # Limpiar requests de más de 1 día
        while (self.day_requests[client_id] and 
               now - self.day_requests[client_id][0] > 86400):
            self.day_requests[client_id].popleft()
    
    def get_remaining(self, client_id: str = "default") -> Dict[str, int]:
        """
        Obtiene requests restantes.
        
        Args:
            client_id: ID del cliente
        
        Returns:
            Diccionario con requests restantes
        """
        with self.lock:
            now = time.time()
            self._cleanup_old_requests(client_id, now)
            
            return {
                'minute': max(0, self.requests_per_minute - len(self.minute_requests[client_id])),
                'hour': max(0, self.requests_per_hour - len(self.hour_requests[client_id])),
                'day': max(0, self.requests_per_day - len(self.day_requests[client_id])),
            }


class APIMetrics:
    """Métricas para la API."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_generation_time = 0.0
        self.total_videos_generated = 0
        self.lock = Lock()
    
    def record_request(self, generation_time: float = 0.0, success: bool = True):
        """Registra un request."""
        with self.lock:
            self.request_count += 1
            if not success:
                self.error_count += 1
            if success:
                self.total_generation_time += generation_time
                self.total_videos_generated += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas."""
        with self.lock:
            avg_time = (self.total_generation_time / self.total_videos_generated 
                       if self.total_videos_generated > 0 else 0.0)
            
            return {
                'total_requests': self.request_count,
                'total_errors': self.error_count,
                'total_success': self.total_videos_generated,
                'success_rate': (self.total_videos_generated / self.request_count 
                               if self.request_count > 0 else 0.0),
                'average_generation_time': avg_time,
            }
    
    def reset(self):
        """Resetea las métricas."""
        with self.lock:
            self.request_count = 0
            self.error_count = 0
            self.total_generation_time = 0.0
            self.total_videos_generated = 0

