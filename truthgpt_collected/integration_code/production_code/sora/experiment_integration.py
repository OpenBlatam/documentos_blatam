#!/usr/bin/env python3
"""
Experiment Integration - Integración con Experiment Tracking
============================================================

Integración del módulo Sora con sistemas de experiment tracking
(wandb, mlflow) para monitoreo y logging de generaciones de video.
"""

import torch
from typing import Dict, Any, Optional, Union
from pathlib import Path
import time

from core.experiment_tracking import ExperimentTracker
from core.utils import setup_logger

logger = setup_logger(__name__)


class SoraExperimentTracker:
    """
    Tracker especializado para experimentos de generación de video.
    
    Extiende ExperimentTracker con funcionalidades específicas para video.
    """
    
    def __init__(
        self,
        project: str = "sora-video-generation",
        experiment_name: Optional[str] = None,
        use_wandb: bool = True,
        use_mlflow: bool = False,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el tracker de experimentos para Sora.
        
        Args:
            project: Nombre del proyecto
            experiment_name: Nombre del experimento
            use_wandb: Si usar Weights & Biases
            use_mlflow: Si usar MLflow
            config: Configuración del experimento
        """
        self.tracker = ExperimentTracker(
            project=project,
            experiment_name=experiment_name,
            use_wandb=use_wandb,
            use_mlflow=use_mlflow,
            config=config
        )
        self.project = project
        self.experiment_name = experiment_name or self.tracker.experiment_name
    
    def log_video_generation(
        self,
        prompt: Optional[str] = None,
        video_shape: Optional[tuple] = None,
        metadata: Optional[Dict[str, Any]] = None,
        generation_time: Optional[float] = None,
        model_config: Optional[Dict[str, Any]] = None,
        video_path: Optional[Union[str, Path]] = None
    ):
        """
        Registra una generación de video.
        
        Args:
            prompt: Prompt usado (si aplica)
            video_shape: Shape del video generado
            metadata: Metadata adicional
            generation_time: Tiempo de generación en segundos
            model_config: Configuración del modelo
            video_path: Path al video generado (para logging)
        """
        metrics = {}
        
        if video_shape:
            metrics.update({
                'video_batch_size': video_shape[0],
                'video_frames': video_shape[1],
                'video_channels': video_shape[2],
                'video_height': video_shape[3],
                'video_width': video_shape[4],
            })
        
        if generation_time:
            metrics['generation_time_seconds'] = generation_time
            if video_shape:
                fps = video_shape[1] / generation_time
                metrics['generation_fps'] = fps
        
        if metadata:
            # Extraer métricas relevantes de metadata
            for key in ['num_frames', 'fps', 'video_mean', 'video_std', 
                       'latent_mean', 'latent_std', 'text_length']:
                if key in metadata:
                    metrics[f'metadata_{key}'] = metadata[key]
        
        self.tracker.log_metrics(metrics)
        
        params = {}
        if prompt:
            params['prompt'] = prompt[:100]  # Limitar longitud
        if model_config:
            params.update(model_config)
        
        if params:
            self.tracker.log_params(params)
        
        if video_path and Path(video_path).exists():
            try:
                if self.tracker.use_wandb and self.tracker.wandb_run:
                    import wandb
                    wandb.log({"video": wandb.Video(str(video_path))})
                logger.info("Video logged to experiment tracker", path=str(video_path))
            except Exception as e:
                logger.warning(f"Error logging video: {e}")
    
    def log_text_to_video(
        self,
        prompt: str,
        video: torch.Tensor,
        metadata: Dict[str, Any],
        generation_time: float,
        config: Any,
        video_path: Optional[Union[str, Path]] = None
    ):
        """Registra generación text-to-video."""
        self.log_video_generation(
            prompt=prompt,
            video_shape=tuple(video.shape),
            metadata=metadata,
            generation_time=generation_time,
            model_config=config.to_dict() if hasattr(config, 'to_dict') else dict(config),
            video_path=video_path
        )
    
    def log_image_to_video(
        self,
        image_path: Optional[str],
        video: torch.Tensor,
        metadata: Dict[str, Any],
        generation_time: float,
        config: Any,
        video_path: Optional[Union[str, Path]] = None
    ):
        """Registra generación image-to-video."""
        params = {}
        if image_path:
            params['source_image'] = image_path
        
        if hasattr(config, 'motion_strength'):
            params['motion_strength'] = config.motion_strength
        
        self.log_video_generation(
            video_shape=tuple(video.shape),
            metadata=metadata,
            generation_time=generation_time,
            model_config=config.to_dict() if hasattr(config, 'to_dict') else dict(config),
            video_path=video_path
        )
        self.tracker.log_params(params)
    
    def log_benchmark(
        self,
        benchmark_results: Dict[str, Any],
        model_config: Optional[Dict[str, Any]] = None
    ):
        """
        Registra resultados de benchmark.
        
        Args:
            benchmark_results: Resultados del benchmark
            model_config: Configuración del modelo
        """
        metrics = {
            'benchmark_mean_time_ms': benchmark_results.get('mean_time_ms', 0),
            'benchmark_std_time_ms': benchmark_results.get('std_time_ms', 0),
            'benchmark_fps': benchmark_results.get('fps', 0),
            'benchmark_total_frames': benchmark_results.get('total_frames', 0),
        }
        
        self.tracker.log_metrics(metrics)
        
        if model_config:
            self.tracker.log_params(model_config)
    
    def log_model_info(
        self,
        model_info: Dict[str, Any],
        model_config: Optional[Dict[str, Any]] = None
    ):
        """
        Registra información del modelo.
        
        Args:
            model_info: Información del modelo
            model_config: Configuración del modelo
        """
        params = {
            'total_parameters': model_info.get('total_parameters', 0),
            'trainable_parameters': model_info.get('trainable_parameters', 0),
        }
        
        if model_config:
            params.update(model_config)
        
        self.tracker.log_params(params)
    
    def finish(self):
        """Finaliza el experimento."""
        if self.tracker.use_wandb and self.tracker.wandb_run:
            self.tracker.wandb_run.finish()
        
        if self.tracker.use_mlflow and self.tracker.mlflow_run:
            self.tracker.mlflow_run.end_run()
        
        logger.info("Experimento finalizado", experiment=self.experiment_name)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.finish()


def track_video_generation(
    tracker: SoraExperimentTracker,
    generation_func,
    *args,
    **kwargs
) -> tuple:
    """
    Wrapper para trackear generación de video.
    
    Args:
        tracker: Tracker de experimentos
        generation_func: Función de generación
        *args: Argumentos para la función
        **kwargs: Keyword arguments para la función
    
    Returns:
        Resultado de la función de generación
    """
    start_time = time.time()
    
    result = generation_func(*args, **kwargs)
    
    generation_time = time.time() - start_time
    
    if isinstance(result, tuple) and len(result) == 2:
        video, metadata = result
        tracker.log_video_generation(
            video_shape=tuple(video.shape) if hasattr(video, 'shape') else None,
            metadata=metadata if isinstance(metadata, dict) else {},
            generation_time=generation_time
        )
    
    return result


