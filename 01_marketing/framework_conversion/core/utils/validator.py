"""
DocumentValidator - Validador de documentos
"""

import os
from pathlib import Path
from typing import List, Tuple
from ..config import ConfigManager
from ..logger import LoggerManager

class DocumentValidator:
    """Validador de documentos"""
    
    def __init__(self, config: ConfigManager, logger: LoggerManager):
        self.config = config
        self.logger = logger.get_logger()
    
    def validate_input_file(self, file_path: str) -> bool:
        """Valida archivo de entrada"""
        if not os.path.exists(file_path):
            self.logger.error(f"Archivo no existe: {file_path}")
            return False
        
        if not file_path.endswith('.md'):
            self.logger.warning(f"Archivo no es Markdown: {file_path}")
            return False
        
        # Validar tamaño
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
        max_size = self.config.get('max_file_size_mb', 50)
        
        if file_size > max_size:
            self.logger.error(f"Archivo muy grande: {file_size:.2f} MB (máx: {max_size} MB)")
            return False
        
        return True
    
    def validate_output_directory(self, directory: str) -> Tuple[bool, List[str]]:
        """Valida directorio de salida"""
        errors = []
        
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                errors.append(f"No se puede crear directorio: {e}")
                return False, errors
        
        if not os.access(directory, os.W_OK):
            errors.append(f"Directorio no tiene permisos de escritura: {directory}")
            return False, errors
        
        return True, errors



