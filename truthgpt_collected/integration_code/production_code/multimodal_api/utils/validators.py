#!/usr/bin/env python3
"""
Validadores para la API Multimodal.

Validaciones adicionales para requests y parámetros.
"""

from typing import Dict, Any, Optional, List
import re
from pathlib import Path

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def validate_prompt(prompt: str, min_length: int = 1, max_length: int = 5000) -> bool:
    """
    Valida un prompt.
    
    Args:
        prompt: Prompt a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
    
    Returns:
        True si es válido
    
    Raises:
        ValueError: Si el prompt no es válido
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("El prompt debe ser una cadena no vacía")
    
    prompt = prompt.strip()
    
    if len(prompt) < min_length:
        raise ValueError(f"El prompt debe tener al menos {min_length} caracteres")
    
    if len(prompt) > max_length:
        raise ValueError(f"El prompt no puede exceder {max_length} caracteres")
    
    return True


def validate_resolution(resolution: Any) -> tuple:
    """
    Valida y parsea una resolución.
    
    Args:
        resolution: Resolución en formato string o tuple
    
    Returns:
        Tuple (height, width)
    
    Raises:
        ValueError: Si la resolución no es válida
    """
    if isinstance(resolution, tuple):
        if len(resolution) != 2:
            raise ValueError("La resolución debe ser un tuple de 2 elementos")
        height, width = resolution
    elif isinstance(resolution, str):
        # Formato: "512x512" o "512,512"
        if "x" in resolution:
            parts = resolution.split("x")
        elif "," in resolution:
            parts = resolution.split(",")
        else:
            raise ValueError(f"Formato de resolución inválido: {resolution}")
        
        if len(parts) != 2:
            raise ValueError(f"Formato de resolución inválido: {resolution}")
        
        try:
            height = int(parts[0].strip())
            width = int(parts[1].strip())
        except ValueError:
            raise ValueError(f"Resolución debe contener números: {resolution}")
    else:
        raise ValueError(f"Tipo de resolución no soportado: {type(resolution)}")
    
    if height <= 0 or width <= 0:
        raise ValueError(f"Resolución debe ser positiva: {height}x{width}")
    
    # Validar que sea múltiplo de 8 (recomendado)
    if height % 8 != 0 or width % 8 != 0:
        logger.warning(f"Resolución {height}x{width} no es múltiplo de 8, puede afectar rendimiento")
    
    return (height, width)


def validate_duration(duration: Any, min_duration: float = 0.1, max_duration: float = 600.0) -> float:
    """
    Valida una duración.
    
    Args:
        duration: Duración en segundos
        min_duration: Duración mínima
        max_duration: Duración máxima
    
    Returns:
        Duración validada
    
    Raises:
        ValueError: Si la duración no es válida
    """
    try:
        duration = float(duration)
    except (ValueError, TypeError):
        raise ValueError(f"Duración debe ser un número: {duration}")
    
    if duration < min_duration:
        raise ValueError(f"Duración debe ser al menos {min_duration} segundos")
    
    if duration > max_duration:
        raise ValueError(f"Duración no puede exceder {max_duration} segundos")
    
    return duration


def validate_fps(fps: Any, min_fps: int = 1, max_fps: int = 120) -> int:
    """
    Valida FPS.
    
    Args:
        fps: FPS a validar
        min_fps: FPS mínimo
        max_fps: FPS máximo
    
    Returns:
        FPS validado
    
    Raises:
        ValueError: Si FPS no es válido
    """
    try:
        fps = int(fps)
    except (ValueError, TypeError):
        raise ValueError(f"FPS debe ser un número entero: {fps}")
    
    if fps < min_fps:
        raise ValueError(f"FPS debe ser al menos {min_fps}")
    
    if fps > max_fps:
        raise ValueError(f"FPS no puede exceder {max_fps}")
    
    return fps


def validate_image_path(image_path: str) -> Path:
    """
    Valida una ruta de imagen.
    
    Args:
        image_path: Ruta a la imagen
    
    Returns:
        Path validado
    
    Raises:
        ValueError: Si la ruta no es válida
    """
    path = Path(image_path)
    
    if not path.exists():
        raise ValueError(f"La imagen no existe: {image_path}")
    
    if not path.is_file():
        raise ValueError(f"La ruta no es un archivo: {image_path}")
    
    # Validar extensión
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    if path.suffix.lower() not in valid_extensions:
        raise ValueError(f"Formato de imagen no soportado: {path.suffix}")
    
    return path


def validate_parameters(parameters: Dict[str, Any], modality: str) -> Dict[str, Any]:
    """
    Valida parámetros según la modalidad.
    
    Args:
        parameters: Parámetros a validar
        modality: Modalidad de generación
    
    Returns:
        Parámetros validados
    
    Raises:
        ValueError: Si los parámetros no son válidos
    """
    validated = {}
    
    if modality == "video":
        # Validar resolución
        if "resolution" in parameters:
            validated["resolution"] = validate_resolution(parameters["resolution"])
        
        # Validar duración
        if "duration" in parameters:
            validated["duration"] = validate_duration(parameters["duration"])
        
        # Validar FPS
        if "fps" in parameters:
            validated["fps"] = validate_fps(parameters["fps"])
        
        # Otros parámetros de video
        if "style" in parameters:
            validated["style"] = str(parameters["style"])
        
        if "diffusion_steps" in parameters:
            steps = int(parameters["diffusion_steps"])
            if steps < 1 or steps > 1000:
                raise ValueError("diffusion_steps debe estar entre 1 y 1000")
            validated["diffusion_steps"] = steps
    
    elif modality == "image":
        if "resolution" in parameters:
            validated["resolution"] = validate_resolution(parameters["resolution"])
        
        if "style" in parameters:
            validated["style"] = str(parameters["style"])
        
        if "quality" in parameters:
            quality = str(parameters["quality"]).lower()
            if quality not in ["low", "medium", "high", "ultra"]:
                raise ValueError("quality debe ser: low, medium, high, ultra")
            validated["quality"] = quality
    
    elif modality == "audio":
        if "duration" in parameters:
            validated["duration"] = validate_duration(parameters["duration"], max_duration=600.0)
        
        if "style" in parameters:
            validated["style"] = str(parameters["style"])
        
        if "tempo" in parameters:
            tempo = str(parameters["tempo"]).lower()
            if tempo not in ["slow", "medium", "fast"]:
                raise ValueError("tempo debe ser: slow, medium, fast")
            validated["tempo"] = tempo
    
    # Copiar otros parámetros sin validar
    for key, value in parameters.items():
        if key not in validated:
            validated[key] = value
    
    return validated


