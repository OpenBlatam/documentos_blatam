"""
ImageHandler - Manejador de imágenes
"""

import os
from pathlib import Path
from typing import Optional, List
from PIL import Image
import io

from ..config import ConfigManager
from ..logger import LoggerManager

class ImageHandler:
    """Manejador de imágenes"""
    
    def __init__(self, config: ConfigManager, logger: LoggerManager):
        self.config = config
        self.logger = logger.get_logger()
        self.image_quality = config.get('image_quality', 300)
    
    def process_image(self, image_path: str, 
                     max_width: Optional[int] = None,
                     max_height: Optional[int] = None) -> Optional[str]:
        """Procesa una imagen"""
        if not os.path.exists(image_path):
            self.logger.warning(f"Imagen no encontrada: {image_path}")
            return None
        
        try:
            with Image.open(image_path) as img:
                # Redimensionar si es necesario
                if max_width or max_height:
                    img.thumbnail((max_width or 2000, max_height or 2000), Image.Resampling.LANCZOS)
                
                # Guardar procesada
                output_path = self._get_processed_path(image_path)
                img.save(output_path, quality=95, optimize=True)
                
                return output_path
        
        except Exception as e:
            self.logger.error(f"Error procesando imagen {image_path}: {e}")
            return None
    
    def extract_images_from_markdown(self, markdown_content: str, 
                                   base_path: str = "") -> List[str]:
        """Extrae rutas de imágenes del Markdown"""
        import re
        
        # Patrón para imágenes en Markdown
        pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(pattern, markdown_content)
        
        images = []
        for match in matches:
            # Resolver ruta relativa
            if not os.path.isabs(match):
                full_path = os.path.join(base_path, match)
            else:
                full_path = match
            
            if os.path.exists(full_path):
                images.append(full_path)
        
        return images
    
    def _get_processed_path(self, original_path: str) -> str:
        """Obtiene ruta para imagen procesada"""
        temp_dir = Path(self.config.get('temp_directory', '/tmp'))
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = Path(original_path).stem
        extension = Path(original_path).suffix
        
        return str(temp_dir / f"{original_name}_processed{extension}")



