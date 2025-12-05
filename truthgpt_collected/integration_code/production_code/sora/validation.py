#!/usr/bin/env python3
"""
Validation - Validación Mejorada
=================================

Sistema de validación robusto para el módulo Sora.
"""

import torch
from typing import Any, Optional, Tuple, List, Dict
from pathlib import Path
import re

from core.utils import setup_logger

logger = setup_logger(__name__)


class ValidationError(Exception):
    """Excepción para errores de validación."""
    pass


class SoraValidator:
    """
    Validador para el módulo Sora.
    
    Proporciona validación robusta para configuraciones,
    inputs y outputs.
    """
    
    @staticmethod
    def validate_resolution(resolution: Any) -> Tuple[int, int]:
        """
        Valida resolución.
        
        Args:
            resolution: Resolución a validar
        
        Returns:
            Tupla (height, width) validada
        
        Raises:
            ValidationError: Si la resolución no es válida
        """
        if isinstance(resolution, (list, tuple)):
            if len(resolution) != 2:
                raise ValidationError(
                    f"Resolución debe tener 2 elementos (height, width), recibido: {resolution}"
                )
            height, width = resolution
        else:
            raise ValidationError(
                f"Resolución debe ser lista o tupla, recibido: {type(resolution)}"
            )
        
        if not isinstance(height, int) or not isinstance(width, int):
            raise ValidationError(
                f"Height y width deben ser enteros, recibido: height={type(height)}, width={type(width)}"
            )
        
        if height <= 0 or width <= 0:
            raise ValidationError(
                f"Height y width deben ser positivos, recibido: {height}x{width}"
            )
        
        if height > 4096 or width > 4096:
            raise ValidationError(
                f"Resolución muy grande (max 4096x4096), recibido: {height}x{width}"
            )
        
        if height % 8 != 0 or width % 8 != 0:
            logger.warning(
                f"Resolución no es múltiplo de 8, puede causar problemas: {height}x{width}"
            )
        
        return (int(height), int(width))
    
    @staticmethod
    def validate_video_length(video_length: Any) -> int:
        """
        Valida longitud de video.
        
        Args:
            video_length: Longitud a validar
        
        Returns:
            Longitud validada
        
        Raises:
            ValidationError: Si la longitud no es válida
        """
        if not isinstance(video_length, int):
            raise ValidationError(
                f"video_length debe ser entero, recibido: {type(video_length)}"
            )
        
        if video_length <= 0:
            raise ValidationError(
                f"video_length debe ser positivo, recibido: {video_length}"
            )
        
        if video_length > 1024:
            raise ValidationError(
                f"video_length muy grande (max 1024), recibido: {video_length}"
            )
        
        return int(video_length)
    
    @staticmethod
    def validate_fps(fps: Any) -> int:
        """
        Valida FPS.
        
        Args:
            fps: FPS a validar
        
        Returns:
            FPS validado
        
        Raises:
            ValidationError: Si el FPS no es válido
        """
        if not isinstance(fps, (int, float)):
            raise ValidationError(
                f"fps debe ser número, recibido: {type(fps)}"
            )
        
        fps = int(fps)
        
        if fps <= 0:
            raise ValidationError(
                f"fps debe ser positivo, recibido: {fps}"
            )
        
        if fps > 120:
            raise ValidationError(
                f"fps muy alto (max 120), recibido: {fps}"
            )
        
        return fps
    
    @staticmethod
    def validate_hidden_dim(hidden_dim: Any) -> int:
        """
        Valida dimensión hidden.
        
        Args:
            hidden_dim: Dimensión a validar
        
        Returns:
            Dimensión validada
        
        Raises:
            ValidationError: Si la dimensión no es válida
        """
        if not isinstance(hidden_dim, int):
            raise ValidationError(
                f"hidden_dim debe ser entero, recibido: {type(hidden_dim)}"
            )
        
        if hidden_dim < 64:
            raise ValidationError(
                f"hidden_dim muy pequeño (min 64), recibido: {hidden_dim}"
            )
        
        if hidden_dim > 2048:
            raise ValidationError(
                f"hidden_dim muy grande (max 2048), recibido: {hidden_dim}"
            )
        
        if hidden_dim % 64 != 0:
            logger.warning(
                f"hidden_dim no es múltiplo de 64, puede causar problemas: {hidden_dim}"
            )
        
        return int(hidden_dim)
    
    @staticmethod
    def validate_prompt(prompt: Any, max_length: int = 1000) -> str:
        """
        Valida prompt de texto.
        
        Args:
            prompt: Prompt a validar
            max_length: Longitud máxima
        
        Returns:
            Prompt validado
        
        Raises:
            ValidationError: Si el prompt no es válido
        """
        if not isinstance(prompt, str):
            raise ValidationError(
                f"prompt debe ser string, recibido: {type(prompt)}"
            )
        
        prompt = prompt.strip()
        
        if not prompt:
            raise ValidationError("prompt no puede estar vacío")
        
        if len(prompt) > max_length:
            raise ValidationError(
                f"prompt muy largo (max {max_length} caracteres), recibido: {len(prompt)}"
            )
        
        return prompt
    
    @staticmethod
    def validate_video_tensor(video: Any, expected_shape: Optional[Tuple] = None) -> torch.Tensor:
        """
        Valida tensor de video.
        
        Args:
            video: Tensor a validar
            expected_shape: Shape esperado (opcional)
        
        Returns:
            Tensor validado
        
        Raises:
            ValidationError: Si el tensor no es válido
        """
        if not isinstance(video, torch.Tensor):
            raise ValidationError(
                f"video debe ser torch.Tensor, recibido: {type(video)}"
            )
        
        if video.dim() != 5:
            raise ValidationError(
                f"video debe tener 5 dimensiones [batch, frames, channels, height, width], "
                f"recibido: {video.shape}"
            )
        
        B, T, C, H, W = video.shape
        
        if B <= 0 or T <= 0 or C <= 0 or H <= 0 or W <= 0:
            raise ValidationError(
                f"Dimensiones de video deben ser positivas, recibido: {video.shape}"
            )
        
        if C not in [1, 3, 4]:
            raise ValidationError(
                f"Canales debe ser 1, 3 o 4, recibido: {C}"
            )
        
        if expected_shape and video.shape != expected_shape:
            raise ValidationError(
                f"Shape de video no coincide con esperado. "
                f"Esperado: {expected_shape}, recibido: {video.shape}"
            )
        
        if video.isnan().any() or video.isinf().any():
            raise ValidationError("Video contiene valores NaN o Inf")
        
        return video
    
    @staticmethod
    def validate_path(path: Any, must_exist: bool = False, must_be_file: bool = False) -> Path:
        """
        Valida path.
        
        Args:
            path: Path a validar
            must_exist: Si el path debe existir
            must_be_file: Si el path debe ser archivo
        
        Returns:
            Path validado
        
        Raises:
            ValidationError: Si el path no es válido
        """
        if isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            raise ValidationError(
                f"path debe ser str o Path, recibido: {type(path)}"
            )
        
        if must_exist and not path.exists():
            raise ValidationError(f"Path no existe: {path}")
        
        if must_be_file and not path.is_file():
            raise ValidationError(f"Path no es archivo: {path}")
        
        return path
    
    @staticmethod
    def validate_seed(seed: Any) -> Optional[int]:
        """
        Valida semilla.
        
        Args:
            seed: Semilla a validar
        
        Returns:
            Semilla validada o None
        
        Raises:
            ValidationError: Si la semilla no es válida
        """
        if seed is None:
            return None
        
        if not isinstance(seed, int):
            raise ValidationError(
                f"seed debe ser entero o None, recibido: {type(seed)}"
            )
        
        if seed < 0:
            raise ValidationError(
                f"seed debe ser no negativo, recibido: {seed}"
            )
        
        return int(seed)
    
    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """
        Valida configuración.
        
        Args:
            config: Configuración a validar
            required_fields: Campos requeridos
        
        Returns:
            Configuración validada
        
        Raises:
            ValidationError: Si la configuración no es válida
        """
        if not isinstance(config, dict):
            raise ValidationError(
                f"config debe ser dict, recibido: {type(config)}"
            )
        
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValidationError(
                f"Campos requeridos faltantes: {missing_fields}"
            )
        
        return config


