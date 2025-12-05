"""
Framework de Conversión Profesional - Sistema completo y robusto
para conversión de documentos Markdown a Word y Excel.

Versión: 2.0.0
Autor: Sistema Premium
"""

__version__ = "2.0.0"
__author__ = "Sistema Premium"

from .core.converter import DocumentConverter
from .core.config import ConfigManager
from .core.logger import LoggerManager

__all__ = [
    'DocumentConverter',
    'ConfigManager',
    'LoggerManager'
]








