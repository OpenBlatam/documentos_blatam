#!/usr/bin/env python3
"""
Analytics y Optimización para Sora
===================================

Análisis avanzado, optimización y métricas para generación de video.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import numpy as np
from pathlib import Path
import json
import time
from datetime import datetime
from collections import defaultdict

from core.utils import setup_logger

logger = setup_logger(__name__)

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


class SoraAnalytics:
    """Analytics avanzados para generación de video."""
    
    def __init__(self, video_module):
        """
        Inicializa analytics.
        
        Args:
            video_module: Instancia de VideoGenerationModule
        """
        self.video_module = video_module
        self.generation_history = []
        logger.info("SoraAnalytics inicializado")
    
    def analyze_generation_quality(self, video: torch.Tensor, metadata: Dict = None) -> Dict[str, Any]:
        """
        Analiza calidad de generación de video.
        
        Args:
            video: Tensor de video [batch, frames, height, width, channels]
            metadata: Metadata de generación
        
        Returns:
            Diccionario con análisis de calidad
        """
        analysis = {
            'timestamp': time.time(),
            'video_shape': list(video.shape),
            'quality_metrics': {}
        }
        
        # Estadísticas básicas
        analysis['quality_metrics']['mean'] = float(video.mean().item())
        analysis['quality_metrics']['std'] = float(video.std().item())
        analysis['quality_metrics']['min'] = float(video.min().item())
        analysis['quality_metrics']['max'] = float(video.max().item())
        
        # Análisis temporal
        if video.dim() >= 2:
            frame_means = video.mean(dim=tuple(range(2, video.dim())))
            analysis['quality_metrics']['temporal_variance'] = float(frame_means.var().item())
            analysis['quality_metrics']['temporal_stability'] = float(1.0 / (1.0 + frame_means.var().item()))
        
        # Análisis espacial
        if video.dim() >= 3:
            spatial_variance = video.var(dim=(-2, -1))
            analysis['quality_metrics']['spatial_variance'] = float(spatial_variance.mean().item())
        
        # Detección de artefactos
        # Valores extremos pueden indicar artefactos
        extreme_values = ((video < -2.0) | (video > 2.0)).sum().item()
        total_values = video.numel()
        analysis['quality_metrics']['artifact_ratio'] = extreme_values / total_values if total_values > 0 else 0.0
        
        if metadata:
            analysis['metadata'] = metadata
        
        # Guardar en historial
        self.generation_history.append(analysis)
        
        return analysis
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analiza rendimiento de generaciones.
        
        Returns:
            Diccionario con análisis de rendimiento
        """
        if not self.generation_history:
            return {'error': 'No hay historial de generaciones'}
        
        # Extraer métricas de tiempo
        processing_times = [
            h['metadata'].get('processing_time', 0)
            for h in self.generation_history
            if 'metadata' in h and 'processing_time' in h['metadata']
        ]
        
        # Extraer métricas de calidad
        quality_scores = [
            h['quality_metrics'].get('temporal_stability', 0)
            for h in self.generation_history
            if 'quality_metrics' in h
        ]
        
        return {
            'total_generations': len(self.generation_history),
            'avg_processing_time': np.mean(processing_times) if processing_times else 0.0,
            'min_processing_time': np.min(processing_times) if processing_times else 0.0,
            'max_processing_time': np.max(processing_times) if processing_times else 0.0,
            'avg_quality_score': np.mean(quality_scores) if quality_scores else 0.0,
            'quality_trend': 'improving' if len(quality_scores) > 1 and quality_scores[-1] > quality_scores[0] else 'stable'
        }
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo de analytics.
        
        Returns:
            Diccionario con todos los análisis
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'performance': self.analyze_performance(),
            'generation_count': len(self.generation_history),
            'recent_generations': self.generation_history[-10:] if len(self.generation_history) > 10 else self.generation_history
        }
    
    def visualize_quality_trends(self, save_path: Optional[str] = None):
        """
        Visualiza tendencias de calidad.
        
        Args:
            save_path: Ruta para guardar visualización
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualización no disponible (matplotlib/seaborn)")
            return
        
        if not self.generation_history:
            logger.warning("No hay historial para visualizar")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Calidad temporal
        quality_scores = [
            h['quality_metrics'].get('temporal_stability', 0)
            for h in self.generation_history
            if 'quality_metrics' in h
        ]
        if quality_scores:
            axes[0, 0].plot(quality_scores)
            axes[0, 0].set_title('Temporal Stability Over Time')
            axes[0, 0].set_xlabel('Generation')
            axes[0, 0].set_ylabel('Stability Score')
        
        # 2. Tiempos de procesamiento
        processing_times = [
            h['metadata'].get('processing_time', 0)
            for h in self.generation_history
            if 'metadata' in h and 'processing_time' in h['metadata']
        ]
        if processing_times:
            axes[0, 1].plot(processing_times)
            axes[0, 1].set_title('Processing Time Over Time')
            axes[0, 1].set_xlabel('Generation')
            axes[0, 1].set_ylabel('Time (s)')
        
        # 3. Distribución de calidad
        if quality_scores:
            axes[1, 0].hist(quality_scores, bins=20, edgecolor='black')
            axes[1, 0].set_title('Quality Score Distribution')
            axes[1, 0].set_xlabel('Quality Score')
            axes[1, 0].set_ylabel('Frequency')
        
        # 4. Relación calidad-tiempo
        if quality_scores and processing_times and len(quality_scores) == len(processing_times):
            axes[1, 1].scatter(processing_times, quality_scores)
            axes[1, 1].set_title('Quality vs Processing Time')
            axes[1, 1].set_xlabel('Processing Time (s)')
            axes[1, 1].set_ylabel('Quality Score')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Visualización guardada en {save_path}")
        else:
            plt.show()
        
        plt.close()


class SoraOptimizer:
    """Optimizador para generación de video."""
    
    def __init__(self, video_module):
        """
        Inicializa optimizador.
        
        Args:
            video_module: Instancia de VideoGenerationModule
        """
        self.video_module = video_module
        logger.info("SoraOptimizer inicializado")
    
    def optimize_for_inference(self) -> Dict[str, Any]:
        """
        Optimiza modelo para inferencia.
        
        Returns:
            Diccionario con resultados de optimización
        """
        optimizations = []
        
        # 1. Compilar modelo si está disponible
        try:
            if hasattr(torch, 'compile'):
                self.video_module = torch.compile(self.video_module)
                optimizations.append({'type': 'torch_compile', 'status': 'success'})
        except Exception as e:
            optimizations.append({'type': 'torch_compile', 'status': 'failed', 'error': str(e)})
        
        # 2. Modo evaluación
        self.video_module.eval()
        optimizations.append({'type': 'eval_mode', 'status': 'success'})
        
        # 3. Desactivar gradientes
        for param in self.video_module.parameters():
            param.requires_grad = False
        optimizations.append({'type': 'disable_gradients', 'status': 'success'})
        
        return {
            'optimizations_applied': len([o for o in optimizations if o['status'] == 'success']),
            'details': optimizations
        }
    
    def suggest_optimal_config(self, target_fps: float = 30.0, target_resolution: Tuple[int, int] = (256, 256)) -> Dict[str, Any]:
        """
        Sugiere configuración óptima.
        
        Args:
            target_fps: FPS objetivo
            target_resolution: Resolución objetivo (height, width)
        
        Returns:
            Diccionario con sugerencias
        """
        suggestions = {
            'target_fps': target_fps,
            'target_resolution': target_resolution,
            'recommendations': []
        }
        
        # Analizar configuración actual
        if hasattr(self.video_module, 'config'):
            config = self.video_module.config
            
            # Sugerir número de frames basado en FPS
            optimal_frames = int(target_fps * 2)  # 2 segundos de video
            if hasattr(config, 'video_length'):
                if config.video_length != optimal_frames:
                    suggestions['recommendations'].append({
                        'parameter': 'video_length',
                        'current': config.video_length,
                        'suggested': optimal_frames,
                        'reason': f'Para {target_fps} FPS, se recomiendan {optimal_frames} frames'
                    })
        
        return suggestions


class SoraExporter:
    """Exportador de resultados y métricas."""
    
    def __init__(self, analytics: SoraAnalytics):
        """
        Inicializa exportador.
        
        Args:
            analytics: Instancia de SoraAnalytics
        """
        self.analytics = analytics
        logger.info("SoraExporter inicializado")
    
    def export_report(self, filepath: str) -> bool:
        """
        Exporta reporte completo a JSON.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si se exportó exitosamente
        """
        try:
            report = self.analytics.get_comprehensive_report()
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Reporte exportado a {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exportando reporte: {e}")
            return False


