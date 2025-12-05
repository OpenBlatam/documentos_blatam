#!/usr/bin/env python3
"""
Módulo para experiment tracking y logging de experimentos.

Incluye integración con:
- Weights & Biases (wandb)
- MLflow (opcional)
- Logging estructurado
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path
import torch

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

from .utils import setup_logger

logger = setup_logger(__name__)


class ExperimentTracker:
    """
    Tracker unificado para experimentos de ML.
    
    Soporta múltiples backends:
    - Weights & Biases
    - MLflow
    - Logging estructurado local
    """
    
    def __init__(
        self,
        project: str,
        experiment_name: Optional[str] = None,
        use_wandb: bool = True,
        use_mlflow: bool = False,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Inicializa el tracker de experimentos.
        
        Args:
            project: Nombre del proyecto
            experiment_name: Nombre del experimento
            use_wandb: Si True, usa Weights & Biases
            use_mlflow: Si True, usa MLflow
            config: Configuración del experimento
            **kwargs: Argumentos adicionales
        """
        self.project = project
        self.experiment_name = experiment_name or f"experiment_{torch.randint(0, 10000, (1,)).item()}"
        self.config = config or {}
        self.use_wandb = use_wandb and WANDB_AVAILABLE
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        
        self.wandb_run = None
        self.mlflow_run = None
        
        if self.use_wandb:
            try:
                self.wandb_run = wandb.init(
                    project=project,
                    name=experiment_name,
                    config=config,
                    **kwargs
                )
                logger.info("Weights & Biases inicializado", project=project, experiment=experiment_name)
            except Exception as e:
                logger.warning("Error inicializando wandb", error=str(e))
                self.use_wandb = False
        
        if self.use_mlflow:
            try:
                mlflow.set_experiment(project)
                self.mlflow_run = mlflow.start_run(run_name=experiment_name)
                if config:
                    mlflow.log_params(config)
                logger.info("MLflow inicializado", project=project, experiment=experiment_name)
            except Exception as e:
                logger.warning("Error inicializando MLflow", error=str(e))
                self.use_mlflow = False
    
    def log_metrics(self, metrics: Dict[str, Union[int, float]], step: Optional[int] = None):
        """
        Registra métricas.
        
        Args:
            metrics: Diccionario de métricas
            step: Paso del entrenamiento (opcional)
        """
        if self.use_wandb and self.wandb_run:
            wandb.log(metrics, step=step)
        
        if self.use_mlflow and self.mlflow_run:
            mlflow.log_metrics(metrics, step=step)
        
        logger.info("Métricas registradas", metrics=metrics, step=step)
    
    def log_params(self, params: Dict[str, Any]):
        """
        Registra parámetros.
        
        Args:
            params: Diccionario de parámetros
        """
        if self.use_wandb and self.wandb_run:
            wandb.config.update(params)
        
        if self.use_mlflow and self.mlflow_run:
            mlflow.log_params(params)
        
        logger.info("Parámetros registrados", params=params)
    
    def log_model(self, model: torch.nn.Module, name: str = "model"):
        """
        Registra un modelo.
        
        Args:
            model: Modelo de PyTorch
            name: Nombre del modelo
        """
        from .error_handling import safe_execute
        
        if self.use_wandb and self.wandb_run:
            def save_wandb():
                torch.save(model.state_dict(), f"/tmp/{name}.pt")
                artifact = wandb.Artifact(name, type="model")
                artifact.add_file(f"/tmp/{name}.pt")
                wandb.log_artifact(artifact)
            
            _, error = safe_execute(save_wandb, default_value=None, log_errors=True)
            if error:
                logger.warning("Error guardando modelo en wandb", error=str(error))
        
        if self.use_mlflow and self.mlflow_run:
            def save_mlflow():
                mlflow.pytorch.log_model(model, name)
            
            _, error = safe_execute(save_mlflow, default_value=None, log_errors=True)
            if error:
                logger.warning("Error guardando modelo en MLflow", error=str(error))
    
    def log_artifact(self, path: Union[str, Path], name: Optional[str] = None):
        """
        Registra un artefacto (archivo).
        
        Args:
            path: Ruta al archivo
            name: Nombre del artefacto
        """
        path = Path(path)
        if not path.exists():
            logger.warning("Artefacto no encontrado", path=str(path))
            return
        
        if self.use_wandb and self.wandb_run:
            try:
                artifact = wandb.Artifact(name or path.name, type="file")
                artifact.add_file(str(path))
                wandb.log_artifact(artifact)
            except Exception as e:
                logger.warning("Error guardando artefacto en wandb", error=str(e))
        
        if self.use_mlflow and self.mlflow_run:
            try:
                mlflow.log_artifact(str(path))
            except Exception as e:
                logger.warning("Error guardando artefacto en MLflow", error=str(e))
    
    def finish(self):
        """Finaliza el tracking del experimento."""
        if self.use_wandb and self.wandb_run:
            wandb.finish()
        
        if self.use_mlflow and self.mlflow_run:
            mlflow.end_run()
        
        logger.info("Tracking finalizado", experiment=self.experiment_name)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.finish()
        return False

