#!/usr/bin/env python3
"""
Video Quality - Validación y Análisis de Calidad
=================================================

Utilidades para validar y analizar la calidad de videos generados.
"""

import torch
import numpy as np
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from core.utils import setup_logger

logger = setup_logger(__name__)


class VideoQualityAnalyzer:
    """
    Analizador de calidad de video.
    
    Proporciona métricas para evaluar la calidad de videos generados.
    """
    
    def __init__(self):
        """Inicializa el analizador."""
        pass
    
    def analyze(
        self,
        video: torch.Tensor,
        reference: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        """
        Analiza la calidad de un video.
        
        Args:
            video: Video a analizar [batch, frames, channels, height, width]
            reference: Video de referencia (opcional)
        
        Returns:
            Diccionario con métricas de calidad
        """
        metrics = {}
        
        # Métricas básicas
        metrics.update(self._compute_basic_metrics(video))
        
        # Métricas temporales
        metrics.update(self._compute_temporal_metrics(video))
        
        # Métricas espaciales
        metrics.update(self._compute_spatial_metrics(video))
        
        # Comparación con referencia si está disponible
        if reference is not None:
            metrics.update(self._compute_comparison_metrics(video, reference))
        
        return metrics
    
    def _compute_basic_metrics(self, video: torch.Tensor) -> Dict[str, float]:
        """Calcula métricas básicas."""
        B, T, C, H, W = video.shape
        
        mean = video.mean().item()
        std = video.std().item()
        min_val = video.min().item()
        max_val = video.max().item()
        
        return {
            'mean': mean,
            'std': std,
            'min': min_val,
            'max': max_val,
            'dynamic_range': max_val - min_val,
            'frames': T,
            'resolution': f"{H}x{W}",
            'channels': C
        }
    
    def _compute_temporal_metrics(self, video: torch.Tensor) -> Dict[str, float]:
        """Calcula métricas temporales."""
        B, T, C, H, W = video.shape
        
        # Variación temporal (frame-to-frame)
        frame_diffs = []
        for t in range(1, T):
            diff = (video[:, t] - video[:, t-1]).abs().mean().item()
            frame_diffs.append(diff)
        
        temporal_consistency = 1.0 - np.mean(frame_diffs) if frame_diffs else 0.0
        
        # Suavidad temporal
        temporal_smoothness = 1.0 / (1.0 + np.std(frame_diffs)) if frame_diffs else 0.0
        
        return {
            'temporal_consistency': max(0.0, min(1.0, temporal_consistency)),
            'temporal_smoothness': max(0.0, min(1.0, temporal_smoothness)),
            'mean_frame_diff': np.mean(frame_diffs) if frame_diffs else 0.0
        }
    
    def _compute_spatial_metrics(self, video: torch.Tensor) -> Dict[str, float]:
        """Calcula métricas espaciales."""
        B, T, C, H, W = video.shape
        
        # Sharpness (simplificado usando gradientes)
        sharpness_scores = []
        for t in range(T):
            frame = video[0, t].cpu().numpy()
            if CV2_AVAILABLE and len(frame.shape) == 3:
                gray = cv2.cvtColor(frame.transpose(1, 2, 0), cv2.COLOR_RGB2GRAY)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                sharpness = laplacian.var()
                sharpness_scores.append(sharpness)
            else:
                # Fallback: usar gradientes de PyTorch
                grad_x = frame[:, :, 1:] - frame[:, :, :-1]
                grad_y = frame[:, 1:, :] - frame[:, :-1, :]
                sharpness = (grad_x.abs().mean() + grad_y.abs().mean()).item()
                sharpness_scores.append(sharpness)
        
        mean_sharpness = np.mean(sharpness_scores)
        
        # Contraste
        contrast_scores = []
        for t in range(T):
            frame = video[0, t]
            std = frame.std().item()
            contrast_scores.append(std)
        
        mean_contrast = np.mean(contrast_scores)
        
        return {
            'sharpness': mean_sharpness,
            'contrast': mean_contrast,
            'spatial_quality': (mean_sharpness + mean_contrast) / 2.0
        }
    
    def _compute_comparison_metrics(
        self,
        video: torch.Tensor,
        reference: torch.Tensor
    ) -> Dict[str, float]:
        """Calcula métricas de comparación con referencia."""
        # MSE
        mse = ((video - reference) ** 2).mean().item()
        
        # PSNR
        if mse > 0:
            max_val = max(video.max().item(), reference.max().item())
            psnr = 20 * np.log10(max_val / np.sqrt(mse))
        else:
            psnr = float('inf')
        
        # SSIM simplificado
        ssim = self._compute_ssim_simple(video, reference)
        
        return {
            'mse': mse,
            'psnr': psnr,
            'ssim': ssim
        }
    
    def _compute_ssim_simple(
        self,
        video: torch.Tensor,
        reference: torch.Tensor
    ) -> float:
        """Calcula SSIM simplificado."""
        # SSIM simplificado usando media y varianza
        mu1 = video.mean()
        mu2 = reference.mean()
        
        sigma1_sq = video.var()
        sigma2_sq = reference.var()
        sigma12 = ((video - mu1) * (reference - mu2)).mean()
        
        c1 = 0.01 ** 2
        c2 = 0.03 ** 2
        
        ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / \
               ((mu1 ** 2 + mu2 ** 2 + c1) * (sigma1_sq + sigma2_sq + c2))
        
        return ssim.item()
    
    def validate(
        self,
        video: torch.Tensor,
        min_quality: float = 0.5,
        min_temporal_consistency: float = 0.3
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida la calidad de un video.
        
        Args:
            video: Video a validar
            min_quality: Calidad mínima requerida
            min_temporal_consistency: Consistencia temporal mínima
        
        Returns:
            (is_valid, metrics)
        """
        metrics = self.analyze(video)
        
        quality_score = (
            metrics.get('temporal_consistency', 0.0) * 0.4 +
            metrics.get('spatial_quality', 0.0) * 0.3 +
            metrics.get('temporal_smoothness', 0.0) * 0.3
        )
        
        is_valid = (
            quality_score >= min_quality and
            metrics.get('temporal_consistency', 0.0) >= min_temporal_consistency
        )
        
        metrics['quality_score'] = quality_score
        metrics['is_valid'] = is_valid
        
        return is_valid, metrics


