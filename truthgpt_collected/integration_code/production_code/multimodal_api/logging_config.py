#!/usr/bin/env python3
"""
Configuración Avanzada de Logging para la API Multimodal.

Sistema de logging estructurado con rotación, niveles y formateo avanzado.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

try:
    from core.utils import setup_logger
    CORE_LOGGING_AVAILABLE = True
except ImportError:
    CORE_LOGGING_AVAILABLE = False


class StructuredFormatter(logging.Formatter):
    """Formateador estructurado para logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea un log record como JSON estructurado.
        
        Args:
            record: Log record
        
        Returns:
            String JSON formateado
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar campos adicionales si existen
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "modality"):
            log_data["modality"] = record.modality
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        # Agregar excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class APILoggingConfig:
    """Configuración de logging para la API."""
    
    def __init__(
        self,
        log_dir: str = "./logs",
        log_level: str = "INFO",
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_json_logging: bool = False
    ):
        """
        Inicializa la configuración de logging.
        
        Args:
            log_dir: Directorio para logs
            log_level: Nivel de logging
            enable_file_logging: Habilitar logging a archivo
            enable_console_logging: Habilitar logging a consola
            max_bytes: Tamaño máximo de archivo antes de rotar
            backup_count: Número de backups a mantener
            enable_json_logging: Habilitar formato JSON
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.enable_json_logging = enable_json_logging
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Formateador
        if self.enable_json_logging:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Handler para archivo
        if self.enable_file_logging:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "api.log",
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Handler separado para errores
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "errors.log",
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
        
        # Handler para consola
        if self.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtiene un logger con nombre.
        
        Args:
            name: Nombre del logger
        
        Returns:
            Logger configurado
        """
        return logging.getLogger(name)
    
    def log_request(
        self,
        logger: logging.Logger,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None
    ):
        """
        Registra un request.
        
        Args:
            logger: Logger a usar
            method: Método HTTP
            path: Ruta
            status_code: Código de estado
            duration: Duración en segundos
            user_id: ID de usuario (opcional)
        """
        extra = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration
        }
        if user_id:
            extra["user_id"] = user_id
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        logger.log(level, f"{method} {path} - {status_code} - {duration:.3f}s", extra=extra)
    
    def log_task(
        self,
        logger: logging.Logger,
        task_id: str,
        modality: str,
        status: str,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Registra una tarea.
        
        Args:
            logger: Logger a usar
            task_id: ID de tarea
            modality: Modalidad
            status: Estado
            duration: Duración (opcional)
            error: Error (opcional)
        """
        extra = {
            "task_id": task_id,
            "modality": modality,
            "status": status
        }
        if duration:
            extra["duration"] = duration
        if error:
            extra["error"] = error
        
        level = logging.ERROR if error else logging.INFO
        logger.log(level, f"Task {task_id} - {modality} - {status}", extra=extra)


