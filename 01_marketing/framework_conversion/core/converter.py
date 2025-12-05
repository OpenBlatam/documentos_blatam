"""
DocumentConverter - Core del framework de conversión
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
import markdown
from markdown.extensions import codehilite, tables, fenced_code, toc
import html2text

from .config import ConfigManager
from .logger import LoggerManager
from .processors.word_processor import WordProcessor
from .processors.excel_processor import ExcelProcessor
from .utils.validator import DocumentValidator
from .utils.image_handler import ImageHandler
from .utils.markdown_parser import MarkdownParser

class DocumentConverter:
    """Convertidor principal de documentos"""
    
    def __init__(self, config: Optional[ConfigManager] = None, 
                 logger: Optional[LoggerManager] = None):
        self.config = config or ConfigManager()
        self.logger = logger or LoggerManager()
        self.validator = DocumentValidator(self.config, self.logger)
        self.image_handler = ImageHandler(self.config, self.logger)
        self.markdown_parser = MarkdownParser(self.config, self.logger)
        
        # Procesadores
        self.word_processor = WordProcessor(self.config, self.logger, self.image_handler)
        self.excel_processor = ExcelProcessor(self.config, self.logger)
        
        # Validar configuración
        is_valid, errors = self.config.validate()
        if not is_valid:
            for error in errors:
                self.logger.get_logger().warning(error)
    
    def convert_file(self, input_file: str, 
                    output_formats: List[str] = ['word', 'excel'],
                    output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Convierte un archivo a los formatos especificados
        
        Args:
            input_file: Ruta del archivo de entrada
            output_formats: Lista de formatos de salida ['word', 'excel']
            output_dir: Directorio de salida (opcional)
        
        Returns:
            Diccionario con rutas de archivos generados
        """
        start_time = datetime.now()
        self.logger.log_conversion_start(input_file, ', '.join(output_formats))
        
        results = {}
        
        try:
            # Validar archivo de entrada
            if not self.validator.validate_input_file(input_file):
                raise ValueError(f"Archivo de entrada inválido: {input_file}")
            
            # Leer y parsear Markdown
            markdown_content = self._read_file(input_file)
            parsed_content = self.markdown_parser.parse(markdown_content)
            
            # Determinar directorio de salida
            output_directory = output_dir or self.config.get('output_directory')
            os.makedirs(output_directory, exist_ok=True)
            
            base_name = Path(input_file).stem
            
            # Convertir a cada formato
            for format_type in output_formats:
                try:
                    if format_type.lower() == 'word':
                        output_file = self.word_processor.convert(
                            parsed_content, 
                            base_name, 
                            output_directory
                        )
                        results['word'] = output_file
                    
                    elif format_type.lower() == 'excel':
                        output_file = self.excel_processor.convert(
                            parsed_content,
                            base_name,
                            output_directory
                        )
                        results['excel'] = output_file
                    
                    else:
                        self.logger.get_logger().warning(f"Formato no soportado: {format_type}")
                
                except Exception as e:
                    self.logger.log_conversion_error(input_file, e)
                    results[format_type] = None
            
            # Log de éxito
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_conversion_success(input_file, str(results), duration)
            
            return results
        
        except Exception as e:
            self.logger.log_conversion_error(input_file, e)
            raise
    
    def convert_directory(self, input_dir: str,
                         output_formats: List[str] = ['word', 'excel'],
                         recursive: bool = True,
                         pattern: str = "*.md") -> Dict[str, List[str]]:
        """
        Convierte todos los archivos de un directorio
        
        Args:
            input_dir: Directorio de entrada
            output_formats: Formatos de salida
            recursive: Buscar recursivamente
            pattern: Patrón de archivos (ej: "*.md")
        
        Returns:
            Diccionario con resultados por formato
        """
        results = {fmt: [] for fmt in output_formats}
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"Directorio no existe: {input_dir}")
        
        # Buscar archivos
        if recursive:
            files = list(input_path.rglob(pattern))
        else:
            files = list(input_path.glob(pattern))
        
        self.logger.get_logger().info(f"Encontrados {len(files)} archivos para convertir")
        
        # Procesar cada archivo
        for file_path in files:
            try:
                file_results = self.convert_file(
                    str(file_path),
                    output_formats
                )
                
                for fmt, output_file in file_results.items():
                    if output_file:
                        results[fmt].append(output_file)
            
            except Exception as e:
                self.logger.get_logger().error(f"Error procesando {file_path}: {e}")
        
        return results
    
    def _read_file(self, file_path: str) -> str:
        """Lee un archivo"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_supported_formats(self) -> List[str]:
        """Obtiene formatos soportados"""
        return ['word', 'excel']
    
    def get_conversion_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema de conversión"""
        return {
            'version': '2.0.0',
            'supported_formats': self.get_supported_formats(),
            'config': {
                'input_directory': self.config.get('input_directory'),
                'output_directory': self.config.get('output_directory'),
                'preserve_formatting': self.config.get('preserve_formatting'),
                'include_images': self.config.get('include_images')
            }
        }








