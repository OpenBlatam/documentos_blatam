"""
ConfigManager - Gestión avanzada de configuración
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import yaml

@dataclass
class WordConfig:
    """Configuración para documentos Word"""
    default_font: str = "Calibri"
    default_font_size: int = 11
    title_font: str = "Calibri"
    title_font_size: int = 16
    heading_font_size: int = 14
    page_margin_top: float = 1.0
    page_margin_bottom: float = 1.0
    page_margin_left: float = 1.0
    page_margin_right: float = 1.0
    include_toc: bool = True
    include_header: bool = True
    include_footer: bool = True
    header_text: str = ""
    footer_text: str = ""
    page_numbering: bool = True
    custom_styles: Dict[str, Any] = None

@dataclass
class ExcelConfig:
    """Configuración para documentos Excel"""
    default_font: str = "Calibri"
    default_font_size: int = 11
    header_font_size: int = 12
    header_bold: bool = True
    header_bg_color: str = "#1F4E78"
    header_text_color: str = "#FFFFFF"
    auto_filter: bool = True
    freeze_panes: bool = True
    auto_width: bool = True
    conditional_formatting: bool = True
    data_validation: bool = True
    charts_enabled: bool = True
    pivot_tables: bool = False

@dataclass
class ConversionConfig:
    """Configuración general de conversión"""
    input_directory: str = ""
    output_directory: str = ""
    temp_directory: str = ""
    preserve_formatting: bool = True
    include_images: bool = True
    image_quality: int = 300
    max_file_size_mb: int = 50
    timeout_seconds: int = 300
    parallel_processing: bool = False
    max_workers: int = 4
    error_handling: str = "strict"  # strict, warn, ignore
    log_level: str = "INFO"
    word: WordConfig = None
    excel: ExcelConfig = None

class ConfigManager:
    """Gestor avanzado de configuración"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = ConversionConfig()
        self.config.word = WordConfig()
        self.config.excel = ExcelConfig()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        else:
            self._set_defaults()
    
    def _set_defaults(self):
        """Establece valores por defecto"""
        base_dir = Path(__file__).parent.parent.parent
        self.config.input_directory = str(base_dir)
        self.config.output_directory = str(base_dir / "output")
        self.config.temp_directory = str(base_dir / "temp")
    
    def load_from_file(self, config_file: str):
        """Carga configuración desde archivo"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                
                self._load_dict(data)
        except Exception as e:
            raise ValueError(f"Error cargando configuración: {e}")
    
    def _load_dict(self, data: Dict[str, Any]):
        """Carga configuración desde diccionario"""
        # Configuración general
        for key, value in data.items():
            if key == 'word' and isinstance(value, dict):
                self.config.word = WordConfig(**value)
            elif key == 'excel' and isinstance(value, dict):
                self.config.excel = ExcelConfig(**value)
            elif hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def save_to_file(self, config_file: str, format: str = 'json'):
        """Guarda configuración a archivo"""
        data = asdict(self.config)
        
        # Convertir dataclasses a dict
        if self.config.word:
            data['word'] = asdict(self.config.word)
        if self.config.excel:
            data['excel'] = asdict(self.config.excel)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            if format == 'yaml':
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene valor de configuración"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Establece valor de configuración"""
        keys = key.split('.')
        obj = self.config
        
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            else:
                return False
        
        if hasattr(obj, keys[-1]):
            setattr(obj, keys[-1], value)
            return True
        
        return False
    
    def validate(self) -> tuple[bool, list[str]]:
        """Valida la configuración"""
        errors = []
        
        # Validar directorios
        if not os.path.exists(self.config.input_directory):
            errors.append(f"Directorio de entrada no existe: {self.config.input_directory}")
        
        # Crear directorios de salida si no existen
        os.makedirs(self.config.output_directory, exist_ok=True)
        os.makedirs(self.config.temp_directory, exist_ok=True)
        
        # Validar valores numéricos
        if self.config.image_quality < 72 or self.config.image_quality > 600:
            errors.append("image_quality debe estar entre 72 y 600")
        
        if self.config.max_file_size_mb < 1:
            errors.append("max_file_size_mb debe ser mayor a 0")
        
        return len(errors) == 0, errors



