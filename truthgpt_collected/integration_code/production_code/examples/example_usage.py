#!/usr/bin/env python3
"""
Ejemplo de uso de las nuevas funcionalidades mejoradas.

Este script demuestra:
- Configuración avanzada
- Experiment tracking
- Caching y retry
- Logging estructurado
"""

from pathlib import Path
import torch

from core.config_manager import ConfigManager
from core.experiment_tracking import ExperimentTracker
from core.utils import (
    setup_logger,
    retry_on_failure,
    get_system_info,
    progress_bar,
    load_environment_variables
)

logger = setup_logger(__name__)


def example_config_manager():
    """Ejemplo de uso del ConfigManager."""
    logger.info("Ejemplo: ConfigManager")
    
    # Crear configuración de ejemplo
    config_data = {
        "model": {
            "hidden_dim": 512,
            "num_layers": 6,
            "dropout": 0.1
        },
        "training": {
            "batch_size": 32,
            "learning_rate": 0.001,
            "epochs": 10
        }
    }
    
    # Guardar como JSON
    manager = ConfigManager()
    manager.config = config_data
    manager.save("example_config.json", format="json")
    
    # Cargar configuración
    loaded_manager = ConfigManager("example_config.json")
    
    # Acceder a valores
    hidden_dim = loaded_manager.get("model.hidden_dim")
    logger.info("Config cargado", hidden_dim=hidden_dim)
    
    # Actualizar valores
    loaded_manager.set("model.hidden_dim", 1024)
    logger.info("Config actualizado", new_hidden_dim=loaded_manager.get("model.hidden_dim"))


def example_experiment_tracking():
    """Ejemplo de experiment tracking."""
    logger.info("Ejemplo: Experiment Tracking")
    
    config = {
        "model": {"hidden_dim": 512},
        "training": {"batch_size": 32, "learning_rate": 0.001}
    }
    
    # Inicializar tracking (sin wandb/mlflow para el ejemplo)
    with ExperimentTracker(
        project="example-project",
        experiment_name="test-experiment",
        use_wandb=False,
        use_mlflow=False,
        config=config
    ) as tracker:
        # Simular entrenamiento
        for epoch in range(3):
            # Log métricas
            metrics = {
                "loss": 1.0 - epoch * 0.2,
                "accuracy": 0.5 + epoch * 0.15
            }
            tracker.log_metrics(metrics, step=epoch)
            logger.info("Métricas registradas", epoch=epoch, metrics=metrics)


@retry_on_failure(max_attempts=3, backoff_factor=1.0)
def example_retry_function():
    """Ejemplo de función con retry."""
    logger.info("Ejemplo: Retry Logic")
    
    # Simular operación que puede fallar
    import random
    if random.random() < 0.5:
        raise ValueError("Operación falló")
    
    logger.info("Operación exitosa")
    return "success"


def example_progress_bar():
    """Ejemplo de progress bar."""
    logger.info("Ejemplo: Progress Bar")
    
    # Simular procesamiento con progress bar
    items = list(range(10))
    for item in progress_bar(items, desc="Procesando"):
        # Simular trabajo
        import time
        time.sleep(0.1)


def example_system_info():
    """Ejemplo de información del sistema."""
    logger.info("Ejemplo: System Info")
    
    info = get_system_info()
    logger.info("Información del sistema", info=info)


def main():
    """Función principal."""
    logger.info("Iniciando ejemplos de uso")
    
    # Cargar variables de entorno si existe .env
    load_environment_variables()
    
    try:
        example_config_manager()
        example_experiment_tracking()
        example_retry_function()
        example_progress_bar()
        example_system_info()
        
        logger.info("Todos los ejemplos completados exitosamente")
    
    except Exception as e:
        logger.error("Error en ejemplos", error=str(e))
        raise


if __name__ == "__main__":
    main()


