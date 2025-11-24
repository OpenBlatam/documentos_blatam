"""
LoggerManager - Sistema de logging profesional
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class ColoredFormatter(logging.Formatter):
    """Formateador con colores para consola"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """Formateador JSON para logs estructurados"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)

class LoggerManager:
    """Gestor profesional de logging"""
    
    def __init__(self, name: str = "FrameworkConversion", 
                 log_dir: Optional[str] = None,
                 level: str = "INFO",
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True):
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Evitar duplicados
        if self.logger.handlers:
            return
        
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Formateadores
        console_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        file_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
        
        console_formatter = ColoredFormatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
        json_formatter = JSONFormatter()
        
        # Handler de consola
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Handler de archivo (rotación por tamaño)
        if enable_file:
            file_handler = RotatingFileHandler(
                self.log_dir / "conversion.log",
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Handler JSON (rotación diaria)
        if enable_json:
            json_handler = TimedRotatingFileHandler(
                self.log_dir / "conversion.json.log",
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(json_formatter)
            self.logger.addHandler(json_handler)
        
        # Handler de errores
        error_handler = RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
    
    def get_logger(self) -> logging.Logger:
        """Obtiene el logger"""
        return self.logger
    
    def log_conversion_start(self, source_file: str, target_format: str):
        """Log de inicio de conversión"""
        self.logger.info(f"Iniciando conversión: {source_file} → {target_format}")
    
    def log_conversion_success(self, source_file: str, output_file: str, duration: float):
        """Log de conversión exitosa"""
        self.logger.info(f"Conversión exitosa: {output_file} (duración: {duration:.2f}s)")
    
    def log_conversion_error(self, source_file: str, error: Exception):
        """Log de error en conversión"""
        self.logger.error(f"Error en conversión: {source_file}", exc_info=error)
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log de rendimiento"""
        extra_data = {'operation': operation, 'duration': duration}
        if details:
            extra_data.update(details)
        
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, "", 0, 
            f"Performance: {operation}", (), None, extra=extra_data
        )
        record.extra_data = extra_data
        self.logger.handle(record)



