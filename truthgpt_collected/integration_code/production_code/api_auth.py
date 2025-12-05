#!/usr/bin/env python3
"""
Sistema de Autenticación para API
==================================

⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.

The current API uses `api.auth` (OptionalAuth) which provides simpler, optional authentication.
This module (api_auth.py) provides a more complex APIKeyManager with permissions and rate limiting.

If you need the functionality from this module, consider:
1. Using `api.auth` for simple optional authentication
2. Using `api.rate_limiting` for rate limiting
3. Implementing custom permission logic if needed

This file is kept for backward compatibility only.
All new code should use `api.auth` instead.

Autenticación y autorización para la API REST.
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "api_auth (root) is deprecated. Use 'api.auth' for optional authentication instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, List, Any, Callable
import secrets
from datetime import datetime, timedelta

from core.utils import setup_logger

logger = setup_logger(__name__)

# Constants
DEFAULT_API_KEY_LENGTH = 32
DEFAULT_RATE_LIMIT = 100
DEFAULT_ADMIN_RATE_LIMIT = 1000
RATE_LIMIT_WINDOW_HOURS = 1
DEFAULT_PERMISSIONS = ['read', 'write', 'admin']
READ_PERMISSION = 'read'
ADMIN_PERMISSION = 'admin'

# Security
security = HTTPBearer()


class APIKeyManager:
    """Gestor de API keys."""
    
    def __init__(self):
        """Inicializa gestor."""
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.default_key = self.generate_api_key()
        self.api_keys[self.default_key] = {
            'name': 'default',
            'created': datetime.now(),
            'permissions': DEFAULT_PERMISSIONS.copy(),
            'rate_limit': DEFAULT_ADMIN_RATE_LIMIT
        }
        logger.info("APIKeyManager inicializado")
    
    def generate_api_key(self) -> str:
        """Genera una nueva API key."""
        return secrets.token_urlsafe(DEFAULT_API_KEY_LENGTH)
    
    def create_api_key(
        self, 
        name: str, 
        permissions: Optional[List[str]] = None, 
        rate_limit: int = DEFAULT_RATE_LIMIT
    ) -> str:
        """
        Crea una nueva API key.
        
        Args:
            name: Nombre de la key
            permissions: Lista de permisos
            rate_limit: Límite de requests por hora
        
        Returns:
            API key generada
        
        Raises:
            ValueError: Si name está vacío o rate_limit es inválido
        """
        if not name or not name.strip():
            raise ValueError("API key name cannot be empty")
        if rate_limit <= 0:
            raise ValueError(f"rate_limit must be > 0, got {rate_limit}")
        
        key = self.generate_api_key()
        self.api_keys[key] = {
            'name': name.strip(),
            'created': datetime.now(),
            'permissions': permissions or [READ_PERMISSION],
            'rate_limit': rate_limit
        }
        logger.info(f"API key creada: {name}")
        return key
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Valida una API key.
        
        Args:
            api_key: API key a validar
        
        Returns:
            True si es válida
        """
        return api_key in self.api_keys
    
    def get_permissions(self, api_key: str) -> List[str]:
        """
        Obtiene permisos de una API key.
        
        Args:
            api_key: API key
        
        Returns:
            Lista de permisos
        """
        if api_key in self.api_keys:
            return self.api_keys[api_key].get('permissions', [])
        return []
    
    def has_permission(self, api_key: str, permission: str) -> bool:
        """
        Verifica si una API key tiene un permiso.
        
        Args:
            api_key: API key
            permission: Permiso a verificar
        
        Returns:
            True si tiene el permiso
        """
        if not api_key or not permission:
            return False
        
        permissions = self.get_permissions(api_key)
        return permission in permissions or ADMIN_PERMISSION in permissions


# Instancia global
_api_key_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    """Obtiene instancia del gestor de API keys."""
    return _api_key_manager


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verifica API key desde header.
    
    Args:
        credentials: Credenciales HTTP
    
    Returns:
        API key validada
    
    Raises:
        HTTPException si la key no es válida
    """
    api_key = credentials.credentials
    manager = get_api_key_manager()
    
    if not manager.validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key


def require_permission(permission: str) -> Callable:
    """
    Decorador para requerir permiso.
    
    Args:
        permission: Permiso requerido
    
    Returns:
        Dependency function
    
    Raises:
        ValueError: Si permission está vacío
    """
    if not permission or not permission.strip():
        raise ValueError("Permission cannot be empty")
    
    def check_permission(api_key: str = Depends(verify_api_key)) -> str:
        manager = get_api_key_manager()
        if not manager.has_permission(api_key, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return api_key
    
    return check_permission


class RateLimiter:
    """Rate limiter por API key."""
    
    def __init__(self):
        """Inicializa rate limiter."""
        self.requests: Dict[str, List[datetime]] = {}
        logger.info("RateLimiter inicializado")
    
    def check_rate_limit(self, api_key: str, limit: int = DEFAULT_RATE_LIMIT) -> bool:
        """
        Verifica rate limit.
        
        Args:
            api_key: API key
            limit: Límite de requests por hora
        
        Returns:
            True si está dentro del límite
        
        Raises:
            ValueError: Si api_key está vacío o limit es inválido
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        if limit <= 0:
            raise ValueError(f"limit must be > 0, got {limit}")
        
        now = datetime.now()
        hour_ago = now - timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
        
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # Limpiar requests antiguos
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > hour_ago
        ]
        
        # Verificar límite
        if len(self.requests[api_key]) >= limit:
            return False
        
        # Registrar request
        self.requests[api_key].append(now)
        return True
    
    def get_remaining(self, api_key: str, limit: int = DEFAULT_RATE_LIMIT) -> int:
        """
        Obtiene requests restantes.
        
        Args:
            api_key: API key
            limit: Límite total
        
        Returns:
            Requests restantes
        
        Raises:
            ValueError: Si api_key está vacío o limit es inválido
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        if limit <= 0:
            raise ValueError(f"limit must be > 0, got {limit}")
        
        now = datetime.now()
        hour_ago = now - timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
        
        if api_key not in self.requests:
            return limit
        
        recent = [
            req_time for req_time in self.requests[api_key]
            if req_time > hour_ago
        ]
        
        return max(0, limit - len(recent))


# Instancia global
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Obtiene instancia del rate limiter."""
    return _rate_limiter


def check_rate_limit(api_key: str = Depends(verify_api_key)) -> str:
    """
    Dependency para verificar rate limit.
    
    Args:
        api_key: API key
    
    Returns:
        API key si está dentro del límite
    
    Raises:
        HTTPException si excede el límite
    """
    manager = get_api_key_manager()
    limit = manager.api_keys.get(api_key, {}).get('rate_limit', DEFAULT_RATE_LIMIT)
    limiter = get_rate_limiter()
    
    if not limiter.check_rate_limit(api_key, limit):
        remaining = limiter.get_remaining(api_key, limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limit}/hour. Remaining: {remaining}",
            headers={
                "X-RateLimit-Limit": str(limit), 
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": str(3600)  # Retry after 1 hour
            }
        )
    
    return api_key

