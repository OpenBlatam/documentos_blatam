#!/usr/bin/env python3
"""
Sistema de Versionado de API.

Maneja múltiples versiones de la API con compatibilidad hacia atrás.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """Versiones de la API."""
    V1 = "v1"
    V2 = "v2"
    LATEST = "v2"


@dataclass
class VersionInfo:
    """Información de una versión."""
    version: str
    release_date: datetime
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None
    end_of_life: Optional[datetime] = None
    changelog: List[str] = None
    
    def __post_init__(self):
        if self.changelog is None:
            self.changelog = []


class APIVersionManager:
    """Gestor de versiones de API."""
    
    def __init__(self):
        """Inicializa el gestor de versiones."""
        self.versions: Dict[str, VersionInfo] = {}
        self.default_version = APIVersion.V1.value
        
        # Registrar versiones
        self._register_versions()
    
    def _register_versions(self):
        """Registra las versiones disponibles."""
        # Versión 1.0
        self.versions["v1"] = VersionInfo(
            version="v1",
            release_date=datetime(2024, 1, 1),
            deprecated=False
        )
        
        # Versión 2.0 (futura)
        self.versions["v2"] = VersionInfo(
            version="v2",
            release_date=datetime(2024, 6, 1),
            deprecated=False,
            changelog=[
                "Nuevos endpoints de streaming",
                "Mejoras en batch processing",
                "Nuevos formatos de respuesta"
            ]
        )
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """
        Obtiene información de una versión.
        
        Args:
            version: Versión a consultar
        
        Returns:
            Información de versión o None
        """
        return self.versions.get(version)
    
    def is_version_supported(self, version: str) -> bool:
        """
        Verifica si una versión está soportada.
        
        Args:
            version: Versión a verificar
        
        Returns:
            True si está soportada
        """
        if version not in self.versions:
            return False
        
        version_info = self.versions[version]
        
        # Verificar si está deprecada y expirada
        if version_info.deprecated and version_info.end_of_life:
            if datetime.now() > version_info.end_of_life:
                return False
        
        return True
    
    def get_supported_versions(self) -> List[str]:
        """
        Obtiene lista de versiones soportadas.
        
        Returns:
            Lista de versiones
        """
        return [
            v for v, info in self.versions.items()
            if self.is_version_supported(v)
        ]
    
    def get_latest_version(self) -> str:
        """
        Obtiene la versión más reciente.
        
        Returns:
            Versión más reciente
        """
        supported = self.get_supported_versions()
        if not supported:
            return self.default_version
        
        # Retornar la más reciente por fecha
        latest = max(
            supported,
            key=lambda v: self.versions[v].release_date
        )
        return latest
    
    def deprecate_version(
        self,
        version: str,
        end_of_life: Optional[datetime] = None
    ):
        """
        Depreca una versión.
        
        Args:
            version: Versión a deprecar
            end_of_life: Fecha de fin de soporte
        """
        if version in self.versions:
            self.versions[version].deprecated = True
            self.versions[version].deprecation_date = datetime.now()
            if end_of_life:
                self.versions[version].end_of_life = end_of_life
            logger.info(f"Versión {version} deprecada")
    
    def get_version_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de versiones.
        
        Returns:
            Resumen
        """
        return {
            "default_version": self.default_version,
            "latest_version": self.get_latest_version(),
            "supported_versions": self.get_supported_versions(),
            "versions": {
                v: {
                    "release_date": info.release_date.isoformat(),
                    "deprecated": info.deprecated,
                    "deprecation_date": (
                        info.deprecation_date.isoformat()
                        if info.deprecation_date else None
                    ),
                    "end_of_life": (
                        info.end_of_life.isoformat()
                        if info.end_of_life else None
                    )
                }
                for v, info in self.versions.items()
            }
        }


