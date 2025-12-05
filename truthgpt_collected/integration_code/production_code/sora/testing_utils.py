#!/usr/bin/env python3
"""
Testing Utils - Utilidades para Testing
========================================

Utilidades para facilitar testing del módulo Sora.
"""

import torch
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import tempfile
import shutil

from core.utils import setup_logger

logger = setup_logger(__name__)


class SoraTestHelper:
    """
    Helper para testing del módulo Sora.
    
    Proporciona utilidades para crear fixtures, mocks y helpers de testing.
    """
    
    @staticmethod
    def create_dummy_video(
        batch_size: int = 1,
        frames: int = 8,
        channels: int = 3,
        height: int = 64,
        width: int = 64,
        device: str = "cpu"
    ) -> torch.Tensor:
        """
        Crea un video dummy para testing.
        
        Args:
            batch_size: Tamaño del batch
            frames: Número de frames
            channels: Número de canales
            height: Altura
            width: Ancho
            device: Dispositivo
        
        Returns:
            Tensor de video dummy
        """
        return torch.randn(
            batch_size, frames, channels, height, width,
            device=device
        )
    
    @staticmethod
    def create_dummy_config(
        config_type: str = "text_to_video",
        **overrides
    ) -> Dict[str, Any]:
        """
        Crea configuración dummy para testing.
        
        Args:
            config_type: Tipo de configuración
            **overrides: Valores a sobrescribir
        
        Returns:
            Diccionario de configuración
        """
        base_config = {
            'hidden_dim': 128,
            'video_length': 4,
            'resolution': (64, 64),
            'fps': 8,
            'diffusion_steps': 5
        }
        
        if config_type == "image_to_video":
            base_config['motion_strength'] = 0.5
        
        base_config.update(overrides)
        return base_config
    
    @staticmethod
    def create_temp_dir(prefix: str = "sora_test_") -> Path:
        """
        Crea directorio temporal para testing.
        
        Args:
            prefix: Prefijo del directorio
        
        Returns:
            Path al directorio temporal
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        return temp_dir
    
    @staticmethod
    def cleanup_temp_dir(temp_dir: Path):
        """
        Limpia directorio temporal.
        
        Args:
            temp_dir: Path al directorio temporal
        """
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @staticmethod
    def assert_video_shape(
        video: torch.Tensor,
        expected_shape: Tuple[int, ...]
    ):
        """
        Assert para shape de video.
        
        Args:
            video: Tensor de video
            expected_shape: Shape esperado
        
        Raises:
            AssertionError: Si el shape no coincide
        """
        assert video.shape == expected_shape, \
            f"Shape esperado {expected_shape}, recibido {video.shape}"
    
    @staticmethod
    def assert_video_valid(video: torch.Tensor):
        """
        Assert para validar video.
        
        Args:
            video: Tensor de video
        
        Raises:
            AssertionError: Si el video no es válido
        """
        assert isinstance(video, torch.Tensor), "Video debe ser torch.Tensor"
        assert video.dim() == 5, f"Video debe tener 5 dimensiones, recibido {video.dim()}"
        assert not video.isnan().any(), "Video contiene NaN"
        assert not video.isinf().any(), "Video contiene Inf"
        assert video.min() >= 0 and video.max() <= 1, \
            f"Video debe estar en rango [0, 1], recibido [{video.min()}, {video.max()}]"
    
    @staticmethod
    def create_mock_model(config: Dict[str, Any]):
        """
        Crea modelo mock para testing.
        
        Args:
            config: Configuración del modelo
        
        Returns:
            Modelo mock
        """
        class MockModel:
            def __init__(self, config):
                self.config = config
                self.eval_called = False
            
            def eval(self):
                self.eval_called = True
                return self
            
            def forward(self, *args, **kwargs):
                return self.generate_dummy_output()
            
            def generate_dummy_output(self):
                batch_size = 1
                frames = self.config.get('video_length', 8)
                channels = 3
                height, width = self.config.get('resolution', (64, 64))
                return (
                    torch.randn(batch_size, frames, channels, height, width),
                    {'num_frames': frames, 'fps': self.config.get('fps', 8)}
                )
        
        return MockModel(config)
    
    @staticmethod
    def compare_videos(
        video1: torch.Tensor,
        video2: torch.Tensor,
        tolerance: float = 1e-5
    ) -> Dict[str, Any]:
        """
        Compara dos videos.
        
        Args:
            video1: Primer video
            video2: Segundo video
            tolerance: Tolerancia para comparación
        
        Returns:
            Diccionario con resultados de comparación
        """
        assert video1.shape == video2.shape, \
            f"Shapes deben coincidir: {video1.shape} vs {video2.shape}"
        
        diff = (video1 - video2).abs()
        mse = diff.mean().item()
        max_diff = diff.max().item()
        
        are_equal = mse < tolerance
        
        return {
            'are_equal': are_equal,
            'mse': mse,
            'max_diff': max_diff,
            'tolerance': tolerance
        }


