#!/usr/bin/env python3
"""
Sistema de Autenticación para la API Multimodal.

Autenticación básica con API keys y JWT.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from fastapi import HTTPException, status, Security
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class APIKeyManager:
    """Gestor de API keys."""
    
    def __init__(self):
        """Inicializa el gestor de API keys."""
        # En producción, esto debería estar en una base de datos
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.key_to_user: Dict[str, str] = {}
    
    def create_api_key(
        self,
        user_id: str,
        name: str = "default",
        rate_limit: int = 100
    ) -> str:
        """
        Crea una nueva API key.
        
        Args:
            user_id: ID del usuario
            name: Nombre de la key
            rate_limit: Límite de rate limiting
        
        Returns:
            API key generada
        """
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            "user_id": user_id,
            "name": name,
            "rate_limit": rate_limit,
            "created_at": datetime.now(),
            "last_used": None
        }
        
        self.key_to_user[key_hash] = user_id
        
        logger.info(f"API key creada para usuario: {user_id}")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Valida una API key.
        
        Args:
            api_key: API key a validar
        
        Returns:
            Información del usuario o None
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash not in self.api_keys:
            return None
        
        key_info = self.api_keys[key_hash]
        key_info["last_used"] = datetime.now()
        
        return {
            "user_id": key_info["user_id"],
            "name": key_info["name"],
            "rate_limit": key_info["rate_limit"]
        }
    
    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoca una API key.
        
        Args:
            api_key: API key a revocar
        
        Returns:
            True si se revocó correctamente
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            user_id = self.api_keys[key_hash]["user_id"]
            del self.api_keys[key_hash]
            if key_hash in self.key_to_user:
                del self.key_to_user[key_hash]
            logger.info(f"API key revocada para usuario: {user_id}")
            return True
        
        return False


class JWTAuth:
    """Autenticación con JWT."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Inicializa autenticación JWT.
        
        Args:
            secret_key: Clave secreta para firmar tokens
            algorithm: Algoritmo de firma
        """
        if not JWT_AVAILABLE:
            raise ImportError("PyJWT no está instalado. Instala con: pip install PyJWT")
        
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un token JWT.
        
        Args:
            user_id: ID del usuario
            expires_delta: Tiempo de expiración
        
        Returns:
            Token JWT
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Valida un token JWT.
        
        Args:
            token: Token a validar
        
        Returns:
            Payload del token o None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return None


# Instancia global
api_key_manager = APIKeyManager()

# Security scheme para FastAPI
if FASTAPI_AVAILABLE:
    security = HTTPBearer(auto_error=False)
    
    async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
    ) -> Dict[str, Any]:
        """
        Obtiene el usuario actual desde el token.
        
        Args:
            credentials: Credenciales del request
        
        Returns:
            Información del usuario
        
        Raises:
            HTTPException: Si no está autenticado
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se proporcionaron credenciales",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Intentar validar como API key primero
        user_info = api_key_manager.validate_api_key(credentials.credentials)
        if user_info:
            return user_info
        
        # Intentar validar como JWT
        # jwt_auth = JWTAuth(secret_key="your-secret-key")  # Debería venir de config
        # user_info = jwt_auth.validate_token(credentials.credentials)
        # if user_info:
        #     return user_info
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )


