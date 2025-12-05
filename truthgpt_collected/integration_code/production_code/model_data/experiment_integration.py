#!/usr/bin/env python3
"""
Experiment Integration
======================

Integración con sistemas de experiment tracking (wandb, mlflow).
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import time

from .data_collector import ModelData
from .constants import DEFAULT_PROJECT_NAME
from core.experiment_tracking import ExperimentTracker
from core.utils import setup_logger

logger = setup_logger(__name__)


class ExperimentIntegration:
    """
    Integración con sistemas de experiment tracking.
    
    Permite enviar datos de modelos a:
    - Weights & Biases (wandb)
    - MLflow
    """
    
    def __init__(
        self,
        project: str = DEFAULT_PROJECT_NAME,
        use_wandb: bool = True,
        use_mlflow: bool = False
    ):
        """
        Inicializa la integración.
        
        Args:
            project: Nombre del proyecto
            use_wandb: Si True, usa wandb
            use_mlflow: Si True, usa mlflow
        
        Raises:
            ValueError: Si project está vacío
        """
        if not project or not project.strip():
            raise ValueError("project no puede estar vacío")
        
        self.project = project
        self.use_wandb = use_wandb
        self.use_mlflow = use_mlflow
        self._tracker: Optional[ExperimentTracker] = None
    
    def log_model_data(
        self,
        model_data: ModelData,
        experiment_name: Optional[str] = None
    ):
        """
        Registra datos de un modelo en el sistema de tracking.
        
        Args:
            model_data: Datos del modelo
            experiment_name: Nombre del experimento (opcional)
        """
        if not self._tracker:
            exp_name = experiment_name or f"{model_data.model_name}_{int(time.time())}"
            self._tracker = ExperimentTracker(
                project=self.project,
                experiment_name=exp_name,
                use_wandb=self.use_wandb,
                use_mlflow=self.use_mlflow,
                config=model_data.config
            )
        
        # Métricas del modelo
        metrics = {
            'total_parameters': model_data.parameters.get('total_parameters', 0),
            'trainable_parameters': model_data.parameters.get('trainable_parameters', 0),
            'forward_count': model_data.metrics.get('forward_count', 0),
        }
        
        # Agregar métricas de benchmarks
        if model_data.benchmarks:
            for i, benchmark in enumerate(model_data.benchmarks):
                if benchmark.get('throughput'):
                    metrics[f'benchmark_{i}_throughput'] = benchmark['throughput']
                if benchmark.get('latency'):
                    metrics[f'benchmark_{i}_latency'] = benchmark['latency']
                if benchmark.get('forward_time'):
                    metrics[f'benchmark_{i}_forward_time'] = benchmark['forward_time']
        
        self._tracker.log_metrics(metrics)
        
        # Metadata
        metadata = {
            'model_name': model_data.model_name,
            'paper_id': model_data.paper_id,
            'category': model_data.category,
            'device': model_data.metadata.get('device', 'unknown'),
            'dtype': model_data.metadata.get('dtype', 'unknown')
        }
        
        self._tracker.log_params(metadata)
        
        logger.info("Datos del modelo registrados en experiment tracking", model_name=model_data.model_name)
    
    def log_batch(
        self,
        model_data_list: List[ModelData],
        experiment_name: Optional[str] = None
    ):
        """
        Registra múltiples modelos.
        
        Args:
            model_data_list: Lista de ModelData
            experiment_name: Nombre del experimento (opcional)
        """
        for model_data in model_data_list:
            self.log_model_data(model_data, experiment_name=experiment_name)
    
    def finish(self):
        """Finaliza el tracking."""
        if self._tracker:
            self._tracker.finish()
            self._tracker = None


