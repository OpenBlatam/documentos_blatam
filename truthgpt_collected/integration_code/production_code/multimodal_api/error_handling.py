#!/usr/bin/env python3
"""
Manejo Avanzado de Errores para la API Multimodal.

Sistema robusto de manejo de errores con categorización y recovery.
"""

from typing import Dict, Any, Optional, Type
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import traceback

try:
    from fastapi import HTTPException, status
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categorías de errores."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    PROCESSING = "processing"
    STORAGE = "storage"
    NETWORK = "network"
    INTERNAL = "internal"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class APIError:
    """Error estructurado de la API."""
    category: ErrorCategory
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retryable: bool = False
    status_code: int = 500
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "error": {
                "category": self.category.value,
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "retryable": self.retryable,
                "timestamp": self.timestamp.isoformat()
            }
        }


class ErrorHandler:
    """Manejador de errores centralizado."""
    
    def __init__(self):
        """Inicializa el manejador de errores."""
        self.error_counts: Dict[str, int] = {}
        self.error_history: list = []
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> APIError:
        """
        Maneja un error y lo convierte en APIError.
        
        Args:
            error: Excepción
            context: Contexto adicional
        
        Returns:
            APIError estructurado
        """
        context = context or {}
        
        # Categorizar error
        category, code, message, status_code, retryable = self._categorize_error(
            error
        )
        
        api_error = APIError(
            category=category,
            code=code,
            message=message,
            details={
                "exception_type": type(error).__name__,
                "context": context,
                "traceback": traceback.format_exc() if logger.level <= 10 else None
            },
            retryable=retryable,
            status_code=status_code
        )
        
        # Registrar error
        self._record_error(api_error)
        
        return api_error
    
    def _categorize_error(
        self,
        error: Exception
    ) -> tuple:
        """
        Categoriza un error.
        
        Args:
            error: Excepción
        
        Returns:
            (category, code, message, status_code, retryable)
        """
        error_type = type(error)
        error_str = str(error).lower()
        
        # Validación
        if "validation" in error_str or "invalid" in error_str:
            return (
                ErrorCategory.VALIDATION,
                "VALIDATION_ERROR",
                str(error),
                400,
                False
            )
        
        # Autenticación
        if "auth" in error_str or "unauthorized" in error_str:
            return (
                ErrorCategory.AUTHENTICATION,
                "AUTH_ERROR",
                "Error de autenticación",
                401,
                False
            )
        
        # Rate limit
        if "rate limit" in error_str or "too many" in error_str:
            return (
                ErrorCategory.RATE_LIMIT,
                "RATE_LIMIT_EXCEEDED",
                "Rate limit excedido",
                429,
                True
            )
        
        # Not found
        if "not found" in error_str or "404" in error_str:
            return (
                ErrorCategory.NOT_FOUND,
                "NOT_FOUND",
                "Recurso no encontrado",
                404,
                False
            )
        
        # Network
        if any(net in error_str for net in ["connection", "timeout", "network"]):
            return (
                ErrorCategory.NETWORK,
                "NETWORK_ERROR",
                "Error de red",
                503,
                True
            )
        
        # Storage
        if any(storage in error_str for storage in ["storage", "file", "disk"]):
            return (
                ErrorCategory.STORAGE,
                "STORAGE_ERROR",
                "Error de almacenamiento",
                500,
                True
            )
        
        # Default: Internal
        return (
            ErrorCategory.INTERNAL,
            "INTERNAL_ERROR",
            "Error interno del servidor",
            500,
            False
        )
    
    def _record_error(self, api_error: APIError):
        """
        Registra un error.
        
        Args:
            api_error: Error a registrar
        """
        key = f"{api_error.category.value}:{api_error.code}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        self.error_history.append({
            "error": api_error.to_dict()["error"],
            "recorded_at": datetime.now().isoformat()
        })
        
        # Mantener solo últimos 1000 errores
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
        
        logger.error(
            f"Error {api_error.code}",
            category=api_error.category.value,
            retryable=api_error.retryable
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de errores.
        
        Returns:
            Estadísticas
        """
        total_errors = sum(self.error_counts.values())
        
        by_category = {}
        for key, count in self.error_counts.items():
            category = key.split(":")[0]
            by_category[category] = by_category.get(category, 0) + count
        
        return {
            "total_errors": total_errors,
            "by_category": by_category,
            "by_code": dict(self.error_counts),
            "recent_errors": self.error_history[-10:] if self.error_history else []
        }
    
    def create_http_exception(self, api_error: APIError) -> HTTPException:
        """
        Crea una HTTPException desde APIError.
        
        Args:
            api_error: Error estructurado
        
        Returns:
            HTTPException
        """
        if not FASTAPI_AVAILABLE:
            raise api_error
        
        return HTTPException(
            status_code=api_error.status_code,
            detail=api_error.to_dict()
        )


# Instancia global
error_handler = ErrorHandler()


