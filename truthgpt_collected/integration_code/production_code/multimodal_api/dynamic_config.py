#!/usr/bin/env python3
"""
Sistema de Configuración Dinámica para la API Multimodal.

Permite cambiar configuración en tiempo de ejecución sin reiniciar.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """Cambio de configuración."""
    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class DynamicConfigManager:
    """Gestor de configuración dinámica."""
    
    def __init__(self, config_file: str = "./dynamic_config.json"):
        """
        Inicializa el gestor de configuración dinámica.
        
        Args:
            config_file: Archivo de configuración
        """
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.change_history: List[ConfigChange] = []
        self.watchers: Dict[str, list] = {}  # key -> [callbacks]
        
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración desde archivo."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuración dinámica cargada desde {self.config_file}")
            except Exception as e:
                logger.warning(f"Error cargando configuración dinámica: {e}")
                self.config = {}
        else:
            # Configuración por defecto
            self.config = {
                "rate_limit_max_requests": 100,
                "rate_limit_window_seconds": 60,
                "cache_ttl": 3600,
                "max_workers": 4,
                "enable_deduplication": True,
                "enable_analytics": True
            }
            self._save_config()
    
    def _save_config(self):
        """Guarda la configuración a archivo."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando configuración dinámica: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto
        
        Returns:
            Valor de configuración
        """
        return self.config.get(key, default)
    
    def set(
        self,
        key: str,
        value: Any,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Nuevo valor
            changed_by: Usuario que hizo el cambio
            reason: Razón del cambio
        """
        old_value = self.config.get(key)
        
        self.config[key] = value
        
        # Registrar cambio
        change = ConfigChange(
            key=key,
            old_value=old_value,
            new_value=value,
            timestamp=datetime.now(),
            changed_by=changed_by,
            reason=reason
        )
        self.change_history.append(change)
        
        # Mantener solo últimos 1000 cambios
        if len(self.change_history) > 1000:
            self.change_history = self.change_history[-1000:]
        
        # Notificar watchers
        if key in self.watchers:
            for callback in self.watchers[key]:
                try:
                    callback(key, old_value, value)
                except Exception as e:
                    logger.error(f"Error en watcher para {key}: {e}")
        
        self._save_config()
        logger.info(f"Configuración actualizada: {key} = {value}")
    
    def watch(self, key: str, callback: callable):
        """
        Observa cambios en una clave.
        
        Args:
            key: Clave a observar
            callback: Función callback (key, old_value, new_value)
        """
        if key not in self.watchers:
            self.watchers[key] = []
        self.watchers[key].append(callback)
        logger.info(f"Watcher registrado para: {key}")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Obtiene toda la configuración.
        
        Returns:
            Configuración completa
        """
        return self.config.copy()
    
    def get_change_history(self, key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene historial de cambios.
        
        Args:
            key: Filtrar por clave (opcional)
        
        Returns:
            Historial de cambios
        """
        changes = self.change_history
        
        if key:
            changes = [c for c in changes if c.key == key]
        
        return [
            {
                "key": c.key,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "timestamp": c.timestamp.isoformat(),
                "changed_by": c.changed_by,
                "reason": c.reason
            }
            for c in changes
        ]


