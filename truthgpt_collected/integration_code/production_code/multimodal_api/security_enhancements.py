#!/usr/bin/env python3
"""
Mejoras de Seguridad para la API Multimodal.

Funcionalidades avanzadas de seguridad.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import secrets
import hmac

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SecurityManager:
    """Gestor de seguridad."""
    
    def __init__(self):
        """Inicializa el gestor de seguridad."""
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.max_failed_attempts = 5
        self.block_duration_seconds = 3600  # 1 hora
    
    def check_rate_limit_security(
        self,
        identifier: str,
        max_attempts: int = 5,
        window_seconds: int = 300
    ) -> bool:
        """
        Verifica rate limit de seguridad.
        
        Args:
            identifier: Identificador (IP, user_id, etc.)
            max_attempts: Máximo de intentos
            window_seconds: Ventana de tiempo
        
        Returns:
            True si está permitido
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Limpiar intentos antiguos
        if identifier in self.failed_attempts:
            self.failed_attempts[identifier] = [
                attempt for attempt in self.failed_attempts[identifier]
                if attempt > cutoff
            ]
        
        # Verificar si está bloqueado
        if identifier in self.blocked_ips:
            block_until = self.blocked_ips[identifier]
            if now < block_until:
                return False
            else:
                # Desbloquear
                del self.blocked_ips[identifier]
        
        # Verificar intentos fallidos
        if identifier in self.failed_attempts:
            attempts = len(self.failed_attempts[identifier])
            if attempts >= max_attempts:
                # Bloquear
                self.blocked_ips[identifier] = now + timedelta(seconds=self.block_duration_seconds)
                logger.warning(f"IP bloqueada: {identifier}")
                return False
        
        return True
    
    def record_failed_attempt(self, identifier: str):
        """
        Registra un intento fallido.
        
        Args:
            identifier: Identificador
        """
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(datetime.now())
        logger.warning(f"Intento fallido registrado para: {identifier}")
    
    def record_successful_attempt(self, identifier: str):
        """
        Registra un intento exitoso (limpia intentos fallidos).
        
        Args:
            identifier: Identificador
        """
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Genera un token seguro.
        
        Args:
            length: Longitud del token
        
        Returns:
            Token seguro
        """
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """
        Hashea una contraseña de forma segura.
        
        Args:
            password: Contraseña
            salt: Salt (opcional)
        
        Returns:
            (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Usar PBKDF2 o similar en producción
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        password_hash = hash_obj.hex()
        
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """
        Verifica una contraseña.
        
        Args:
            password: Contraseña a verificar
            password_hash: Hash almacenado
            salt: Salt
        
        Returns:
            True si coincide
        """
        computed_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)
    
    def generate_csrf_token(self) -> str:
        """
        Genera un token CSRF.
        
        Returns:
            Token CSRF
        """
        return secrets.token_urlsafe(32)
    
    def validate_input(self, input_data: str, max_length: int = 10000) -> bool:
        """
        Valida input básico.
        
        Args:
            input_data: Datos a validar
            max_length: Longitud máxima
        
        Returns:
            True si es válido
        """
        if not input_data:
            return False
        
        if len(input_data) > max_length:
            return False
        
        # Verificar caracteres peligrosos básicos
        dangerous_patterns = ['<script', 'javascript:', 'onerror=']
        input_lower = input_data.lower()
        for pattern in dangerous_patterns:
            if pattern in input_lower:
                return False
        
        return True
    
    def get_security_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de seguridad.
        
        Returns:
            Estadísticas
        """
        return {
            "blocked_ips": len(self.blocked_ips),
            "failed_attempts": sum(len(attempts) for attempts in self.failed_attempts.values()),
            "unique_identifiers": len(self.failed_attempts)
        }


