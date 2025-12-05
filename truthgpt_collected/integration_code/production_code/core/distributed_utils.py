#!/usr/bin/env python3
"""
Utilidades para computación distribuida.

Incluye:
- Ray para distribución
- Dask para procesamiento paralelo
- Utilidades para entrenamiento distribuido
"""

from typing import Dict, Any, Optional, List, Callable
import torch

try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False

try:
    import dask
    import dask.array as da
    from dask.distributed import Client, as_completed
    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)


def init_ray(num_cpus: Optional[int] = None, num_gpus: Optional[int] = None):
    """
    Inicializa Ray para computación distribuida.
    
    Args:
        num_cpus: Número de CPUs a usar
        num_gpus: Número de GPUs a usar
    """
    if not RAY_AVAILABLE:
        raise ImportError("Ray no está instalado. Instala con: pip install ray")
    
    def _init_ray():
        if not ray.is_initialized():
            ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
            logger.info("Ray inicializado", num_cpus=num_cpus, num_gpus=num_gpus)
        else:
            logger.info("Ray ya está inicializado")
    
    result, error = safe_execute(_init_ray, default_value=None, log_errors=True)
    if error:
        raise RuntimeError(f"Error inicializando Ray: {error}")


def remote_tensor_operation(operation: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Ejecuta una operación de tensor de forma remota con Ray.
    
    Args:
        operation: Función a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
    
    Returns:
        Resultado de la operación
    """
    return operation(*args, **kwargs)

if RAY_AVAILABLE:
    remote_tensor_operation = ray.remote(remote_tensor_operation)


def init_dask_cluster(n_workers: int = 4, threads_per_worker: int = 2):
    """
    Inicializa un cluster de Dask.
    
    Args:
        n_workers: Número de workers
        threads_per_worker: Threads por worker
    
    Returns:
        Cliente de Dask
    """
    if not DASK_AVAILABLE:
        raise ImportError("Dask no está instalado. Instala con: pip install dask distributed")
    
    def _init_dask():
        return Client(n_workers=n_workers, threads_per_worker=threads_per_worker)
    
    result, error = safe_execute(_init_dask, default_value=None, log_errors=True)
    if error:
        raise RuntimeError(f"Error inicializando cluster Dask: {error}")
    
    logger.info("Cluster Dask inicializado", n_workers=n_workers, threads_per_worker=threads_per_worker)
    return result


def parallel_tensor_operations(operations: List[Callable], *args, **kwargs) -> List[Any]:
    """
    Ejecuta múltiples operaciones de tensor en paralelo.
    
    Args:
        operations: Lista de funciones a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
    
    Returns:
        Lista de resultados
    """
    if RAY_AVAILABLE and ray.is_initialized():
        def _execute_ray():
            futures = [remote_tensor_operation.remote(op, *args, **kwargs) for op in operations]
            return ray.get(futures)
        
        result, error = safe_execute(_execute_ray, default_value=None, log_errors=True)
        if error:
            logger.warning("Error ejecutando con Ray, ejecutando secuencialmente", error=str(error))
            return [op(*args, **kwargs) for op in operations]
        return result
    elif DASK_AVAILABLE:
        def _execute_dask():
            client = init_dask_cluster()
            try:
                futures = [client.submit(op, *args, **kwargs) for op in operations]
                results = [future.result() for future in as_completed(futures)]
                return results
            finally:
                client.close()
        
        result, error = safe_execute(_execute_dask, default_value=None, log_errors=True)
        if error:
            logger.warning("Error ejecutando con Dask, ejecutando secuencialmente", error=str(error))
            return [op(*args, **kwargs) for op in operations]
        return result
    else:
        logger.warning("Ray y Dask no disponibles, ejecutando secuencialmente")
        return [op(*args, **kwargs) for op in operations]


def distributed_training_setup(
    backend: str = "nccl",
    init_method: Optional[str] = None,
    world_size: Optional[int] = None,
    rank: Optional[int] = None
) -> Dict[str, Any]:
    """
    Configura entrenamiento distribuido con PyTorch.
    
    Args:
        backend: Backend de comunicación ("nccl", "gloo", "mpi")
        init_method: Método de inicialización
        world_size: Tamaño del mundo (número de procesos)
        rank: Rango del proceso actual
    
    Returns:
        Diccionario con configuración
    """
    if not torch.distributed.is_available():
        logger.warning("PyTorch distributed no está disponible")
        return {"available": False}
    
    config = {
        "backend": backend,
        "available": True,
        "initialized": torch.distributed.is_initialized()
    }
    
    if torch.distributed.is_initialized():
        config["world_size"] = torch.distributed.get_world_size()
        config["rank"] = torch.distributed.get_rank()
        logger.info("Distributed training configurado", **config)
    else:
        if init_method and world_size is not None and rank is not None:
            torch.distributed.init_process_group(
                backend=backend,
                init_method=init_method,
                world_size=world_size,
                rank=rank
            )
            config["world_size"] = world_size
            config["rank"] = rank
            logger.info("Distributed training inicializado", **config)
    
    return config

