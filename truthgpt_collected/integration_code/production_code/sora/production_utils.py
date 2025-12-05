#!/usr/bin/env python3
"""
Production Utils - Utilidades para Producción
==============================================

Utilidades adicionales para uso en producción.
"""

import torch
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import json
import time
from datetime import datetime

from core.utils import setup_logger

logger = setup_logger(__name__)


class ProductionConfig:
    """
    Configuración para producción.
    
    Agrupa configuraciones comunes para despliegue en producción.
    """
    
    def __init__(
        self,
        enable_caching: bool = True,
        enable_monitoring: bool = True,
        enable_logging: bool = True,
        log_level: str = "INFO",
        max_retries: int = 3,
        timeout: float = 300.0,
        enable_health_checks: bool = True
    ):
        """
        Inicializa configuración de producción.
        
        Args:
            enable_caching: Habilitar caché
            enable_monitoring: Habilitar monitoreo
            enable_logging: Habilitar logging
            log_level: Nivel de logging
            max_retries: Número máximo de reintentos
            timeout: Timeout en segundos
            enable_health_checks: Habilitar health checks
        """
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring
        self.enable_logging = enable_logging
        self.log_level = log_level
        self.max_retries = max_retries
        self.timeout = timeout
        self.enable_health_checks = enable_health_checks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'enable_caching': self.enable_caching,
            'enable_monitoring': self.enable_monitoring,
            'enable_logging': self.enable_logging,
            'log_level': self.log_level,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'enable_health_checks': self.enable_health_checks
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ProductionConfig':
        """Crea desde diccionario."""
        return cls(**config_dict)


class HealthChecker:
    """
    Health checker para el módulo Sora.
    
    Verifica el estado de salud de los componentes.
    """
    
    def __init__(self):
        """Inicializa el health checker."""
        self.checks: Dict[str, Callable] = {}
        self.last_check: Optional[datetime] = None
    
    def register_check(self, name: str, check_func: Callable):
        """
        Registra un check de salud.
        
        Args:
            name: Nombre del check
            check_func: Función que retorna (is_healthy, message)
        """
        self.checks[name] = check_func
    
    def check_all(self) -> Dict[str, Any]:
        """
        Ejecuta todos los checks.
        
        Returns:
            Diccionario con resultados de checks
        """
        results = {}
        all_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                is_healthy, message = check_func()
                results[name] = {
                    'healthy': is_healthy,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                if not is_healthy:
                    all_healthy = False
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'message': f"Error en check: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                }
                all_healthy = False
        
        self.last_check = datetime.now()
        
        return {
            'overall_health': 'healthy' if all_healthy else 'unhealthy',
            'checks': results,
            'timestamp': self.last_check.isoformat()
        }
    
    def is_healthy(self) -> bool:
        """
        Verifica si el sistema está saludable.
        
        Returns:
            True si está saludable
        """
        results = self.check_all()
        return results['overall_health'] == 'healthy'


class ProductionLogger:
    """
    Logger para producción.
    
    Proporciona logging estructurado para producción.
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Inicializa el logger de producción.
        
        Args:
            log_file: Archivo de log (opcional)
        """
        self.log_file = log_file
        self.logs: List[Dict[str, Any]] = []
    
    def log_event(
        self,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ):
        """
        Registra un evento.
        
        Args:
            event_type: Tipo de evento
            message: Mensaje
            metadata: Metadata adicional
            level: Nivel de log
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'event_type': event_type,
            'message': message,
            'metadata': metadata or {}
        }
        
        self.logs.append(log_entry)
        
        if self.log_file:
            self._write_to_file(log_entry)
        
        # También loguear con el logger estándar
        if level == "ERROR":
            logger.error(f"[{event_type}] {message}", **(metadata or {}))
        elif level == "WARNING":
            logger.warning(f"[{event_type}] {message}", **(metadata or {}))
        else:
            logger.info(f"[{event_type}] {message}", **(metadata or {}))
    
    def _write_to_file(self, log_entry: Dict[str, Any]):
        """Escribe entrada de log a archivo."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error escribiendo log: {e}")
    
    def get_logs(
        self,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene logs filtrados.
        
        Args:
            event_type: Filtrar por tipo de evento
            level: Filtrar por nivel
            limit: Límite de resultados
        
        Returns:
            Lista de logs
        """
        filtered = self.logs
        
        if event_type:
            filtered = [log for log in filtered if log['event_type'] == event_type]
        
        if level:
            filtered = [log for log in filtered if log['level'] == level]
        
        if limit:
            filtered = filtered[-limit:]
        
        return filtered
    
    def export_logs(self, output_path: Path):
        """
        Exporta logs a archivo.
        
        Args:
            output_path: Path de salida
        """
        with open(output_path, 'w') as f:
            json.dump(self.logs, f, indent=2)


def create_production_environment(
    config: Optional[ProductionConfig] = None
) -> Dict[str, Any]:
    """
    Crea entorno de producción.
    
    Args:
        config: Configuración de producción
    
    Returns:
        Diccionario con componentes de producción
    """
    if config is None:
        config = ProductionConfig()
    
    components = {
        'config': config,
        'health_checker': HealthChecker(),
        'logger': ProductionLogger()
    }
    
    # Registrar checks básicos
    def check_torch():
        try:
            import torch
            return True, "PyTorch disponible"
        except ImportError:
            return False, "PyTorch no disponible"
    
    def check_gpu():
        try:
            import torch
            if torch.cuda.is_available():
                return True, f"GPU disponible: {torch.cuda.get_device_name(0)}"
            return True, "GPU no disponible (CPU mode)"
        except Exception as e:
            return False, f"Error verificando GPU: {e}"
    
    components['health_checker'].register_check('torch', check_torch)
    components['health_checker'].register_check('gpu', check_gpu)
    
    return components


