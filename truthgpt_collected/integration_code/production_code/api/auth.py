#!/usr/bin/env python3
"""
Optional Authentication
=======================

Optional API key authentication that can be enabled via feature flags.
"""

import os
from typing import Optional, Set
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.utils import setup_logger

logger = setup_logger(__name__)

security = HTTPBearer(auto_error=False)


class OptionalAuth:
    """Optional authentication manager."""
    
    def __init__(self, enabled: bool = False):
        """
        Initialize optional auth.
        
        Args:
            enabled: Whether auth is enabled
        """
        self.enabled = enabled
        self.api_keys = self._load_api_keys()
        logger.info(f"Optional auth initialized: enabled={enabled}, keys_count={len(self.api_keys)}")
    
    def _load_api_keys(self) -> Set[str]:
        """
        Load API keys from environment or config.
        
        Returns:
            Set of API keys loaded from environment variables or config file
        
        Note:
            Checks multiple sources:
            1. API_KEYS environment variable (comma-separated)
            2. API_KEY environment variable (single key)
            3. Config file (api.api_keys list)
        """
        keys = set()
        
        # Load from environment variable (comma-separated)
        env_keys = os.getenv("API_KEYS", "")
        if env_keys:
            keys.update(k.strip() for k in env_keys.split(",") if k.strip())
        
        # Load from single API_KEY env var
        single_key = os.getenv("API_KEY")
        if single_key:
            keys.add(single_key.strip())
        
        # Load from config file if available
        try:
            from core.config_manager import get_config_manager
            config_manager = get_config_manager()
            config = config_manager.get_config("api")
            if config and isinstance(config, dict):
                api_keys = config.get("api_keys", [])
                if isinstance(api_keys, list):
                    keys.update(str(k).strip() for k in api_keys if k)
        except Exception as e:
            logger.debug(f"Could not load API keys from config: {e}")
        
        return keys
    
    def verify_api_key(self, api_key: Optional[str]) -> bool:
        """
        Verify API key.
        
        Args:
            api_key: API key to verify
        
        Returns:
            True if valid or auth disabled
        """
        if not self.enabled:
            return True
        
        if not api_key:
            return False
        
        return api_key in self.api_keys
    
    def require_auth(self, request: Request) -> Optional[str]:
        """
        Require authentication if enabled.
        
        Args:
            request: FastAPI request
        
        Returns:
            API key if valid or None if auth disabled
        
        Raises:
            HTTPException if auth required but invalid
        """
        if not self.enabled:
            return None
        
        # Try to get API key from header
        auth_header = request.headers.get("Authorization", "")
        api_key = None
        
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "").strip()
        elif auth_header.startswith("ApiKey "):
            api_key = auth_header.replace("ApiKey ", "").strip()
        else:
            # Try X-API-Key header
            api_key = request.headers.get("X-API-Key", "").strip()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not self.verify_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return api_key


# Global auth instance
_auth_instance: Optional[OptionalAuth] = None


def get_auth(enabled: bool = False) -> OptionalAuth:
    """Get or create auth instance."""
    global _auth_instance
    if _auth_instance is None:
        # Check if enabled via env var
        enabled = enabled or os.getenv("API_AUTH_ENABLED", "false").lower() == "true"
        _auth_instance = OptionalAuth(enabled)
    return _auth_instance


def verify_api_key_optional(
    request: Request,
    auth_enabled: bool = False
) -> Optional[str]:
    """
    Dependency for optional API key verification.
    
    Args:
        request: FastAPI request
        auth_enabled: Whether auth is enabled for this endpoint
    
    Returns:
        API key if valid or None if auth disabled
    
    Raises:
        HTTPException if auth required but invalid
    """
    auth = get_auth(auth_enabled)
    return auth.require_auth(request)


def create_auth_dependency(auth_enabled: bool = False):
    """
    Create a FastAPI dependency for optional authentication.
    
    Args:
        auth_enabled: Whether auth is enabled for this endpoint
    
    Returns:
        FastAPI dependency function
    """
    async def auth_dependency(request: Request) -> Optional[str]:
        return verify_api_key_optional(request, auth_enabled)
    
    return auth_dependency

