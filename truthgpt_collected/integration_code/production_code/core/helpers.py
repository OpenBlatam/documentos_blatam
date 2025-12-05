#!/usr/bin/env python3
"""
Helper Utilities for Paper Modules
===================================

Utilidades auxiliares y funciones de conveniencia.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional, List, Tuple, Callable, TypeVar, Union
from functools import wraps
import time

T = TypeVar('T')

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


def timing_decorator(func: Callable) -> Callable:
    """
    Decorador para medir tiempo de ejecución.
    
    Args:
        func: Función a decorar
    
    Returns:
        Función decorada
    
    Usage:
        @timing_decorator
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start
            logger.debug(
                "Función ejecutada",
                function=func.__name__,
                time=f"{elapsed:.4f}s"
            )
    return wrapper


def device_decorator(device: str = 'cuda') -> Callable[[Callable], Callable]:
    """
    Decorador para mover inputs a un dispositivo.
    
    Args:
        device: Dispositivo destino
    
    Returns:
        Decorador de función
    
    Usage:
        @device_decorator('cuda')
        def my_function(tensor):
            return tensor * 2
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            new_args = []
            for arg in args:
                if isinstance(arg, torch.Tensor):
                    new_args.append(arg.to(device))
                else:
                    new_args.append(arg)
            
            new_kwargs = {}
            for k, v in kwargs.items():
                if isinstance(v, torch.Tensor):
                    new_kwargs[k] = v.to(device)
                else:
                    new_kwargs[k] = v
            
            return func(*new_args, **new_kwargs)
        return wrapper
    return decorator


def count_parameters(module: nn.Module, trainable_only: bool = False) -> int:
    """
    Cuenta parámetros de un módulo.
    
    Args:
        module: Módulo
        trainable_only: Si True, solo cuenta entrenables
    
    Returns:
        Número de parámetros
    """
    if trainable_only:
        return sum(p.numel() for p in module.parameters() if p.requires_grad)
    return sum(p.numel() for p in module.parameters())


def get_model_size_mb(module: nn.Module) -> float:
    """
    Calcula el tamaño del modelo en MB.
    
    Args:
        module: Módulo
    
    Returns:
        Tamaño en MB
    """
    param_size = 0
    buffer_size = 0
    
    for param in module.parameters():
        param_size += param.nelement() * param.element_size()
    
    for buffer in module.buffers():
        buffer_size += buffer.nelement() * buffer.element_size()
    
    size_mb = (param_size + buffer_size) / 1024**2
    return size_mb


def freeze_module(module: nn.Module, freeze: bool = True):
    """
    Congela o descongela parámetros de un módulo.
    
    Args:
        module: Módulo
        freeze: Si True, congela; si False, descongela
    """
    for param in module.parameters():
        param.requires_grad = not freeze
    
    logger.info(
        "Módulo congelado" if freeze else "Módulo descongelado",
        module=module.__class__.__name__
    )


def get_gradient_norm(module: nn.Module) -> float:
    """
    Calcula la norma de los gradientes.
    
    Args:
        module: Módulo
    
    Returns:
        Norma de gradientes
    """
    total_norm = 0.0
    for param in module.parameters():
        if param.grad is not None:
            param_norm = param.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = total_norm ** (1. / 2)
    return total_norm


def clip_gradients(module: nn.Module, max_norm: float = 1.0) -> float:
    """
    Aplica gradient clipping.
    
    Args:
        module: Módulo
        max_norm: Norma máxima
    
    Returns:
        Norma total de los gradientes antes del clipping
    """
    total_norm = torch.nn.utils.clip_grad_norm_(module.parameters(), max_norm)
    logger.debug(f"Gradientes recortados (max_norm={max_norm}, total_norm={total_norm.item()})")
    return total_norm.item()


def create_summary(module: BasePaperModule) -> Dict[str, Any]:
    """
    Crea un resumen completo de un módulo.
    
    Args:
        module: Módulo
    
    Returns:
        Diccionario con resumen
    """
    info = module.get_model_info()
    
    return {
        'name': info['model_name'],
        'parameters': {
            'total': info['total_parameters'],
            'trainable': info['trainable_parameters'],
            'non_trainable': info['non_trainable_parameters']
        },
        'size_mb': get_model_size_mb(module),
        'device': info['device'],
        'dtype': info['dtype'],
        'forward_count': info['forward_count'],
        'config': info['config']
    }


def compare_modules(modules: List[BasePaperModule]) -> Dict[str, Any]:
    """
    Compara múltiples módulos.
    
    Args:
        modules: Lista de módulos
    
    Returns:
        Diccionario con comparación
    """
    summaries = [create_summary(m) for m in modules]
    
    return {
        'modules': summaries,
        'total_parameters': [s['parameters']['total'] for s in summaries],
        'sizes_mb': [s['size_mb'] for s in summaries],
        'largest': max(summaries, key=lambda s: s['parameters']['total']),
        'smallest': min(summaries, key=lambda s: s['parameters']['total'])
    }


def get_gpu_memory_stats(device_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas de memoria GPU.
    
    Args:
        device_id: ID del dispositivo (None = todos)
    
    Returns:
        Diccionario con estadísticas
    """
    if not torch.cuda.is_available():
        return {'available': False}
    
    def _get_stats():
        device_count = torch.cuda.device_count()
        stats = {
            'available': True,
            'device_count': device_count,
            'current_device': torch.cuda.current_device(),
            'devices': []
        }
        
        devices_to_check = [device_id] if device_id is not None else range(device_count)
        
        for i in devices_to_check:
            if i >= device_count:
                continue
                
            torch.cuda.set_device(i)
            device_stats = {
                'device_id': i,
                'device_name': torch.cuda.get_device_name(i),
                'memory_allocated_mb': torch.cuda.memory_allocated(i) / 1024**2,
                'memory_reserved_mb': torch.cuda.memory_reserved(i) / 1024**2,
                'max_memory_allocated_mb': torch.cuda.max_memory_allocated(i) / 1024**2,
                'max_memory_reserved_mb': torch.cuda.max_memory_reserved(i) / 1024**2
            }
            
            if hasattr(torch.cuda, 'get_device_properties'):
                props = torch.cuda.get_device_properties(i)
                device_stats['total_memory_mb'] = props.total_memory / 1024**2
                device_stats['major'] = props.major
                device_stats['minor'] = props.minor
                device_stats['multi_processor_count'] = props.multi_processor_count
            
            stats['devices'].append(device_stats)
        
        return stats
    
    result, error = safe_execute(_get_stats, default_value={'available': False}, log_errors=False)
    return result


def clear_gpu_cache(device_id: Optional[int] = None) -> None:
    """
    Limpia la caché de GPU.
    
    Args:
        device_id: ID del dispositivo (None = todos)
    """
    if not torch.cuda.is_available():
        return
    
    def _clear():
        if device_id is not None:
            torch.cuda.empty_cache(device_id)
        else:
            torch.cuda.empty_cache()
    
    safe_execute(_clear, log_errors=True)


def auto_select_device(prefer_gpu: bool = True) -> torch.device:
    """
    Selecciona automáticamente el mejor dispositivo disponible.
    
    Args:
        prefer_gpu: Si preferir GPU sobre CPU
    
    Returns:
        Dispositivo seleccionado
    """
    if prefer_gpu and torch.cuda.is_available():
        return torch.device('cuda')
    return torch.device('cpu')


def move_to_device(
    tensor: torch.Tensor,
    device: Union[str, torch.device],
    non_blocking: bool = False
) -> torch.Tensor:
    """
    Mueve un tensor a un dispositivo de forma segura.
    
    Args:
        tensor: Tensor a mover
        device: Dispositivo destino
        non_blocking: Si usar transferencia no bloqueante
    
    Returns:
        Tensor en el dispositivo destino
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"tensor debe ser torch.Tensor, recibido: {type(tensor)}")
    
    device_obj = torch.device(device) if isinstance(device, str) else device
    return tensor.to(device_obj, non_blocking=non_blocking)


def batch_tensor(
    tensor: torch.Tensor,
    batch_size: int,
    dim: int = 0
) -> List[torch.Tensor]:
    """
    Divide un tensor en batches.
    
    Args:
        tensor: Tensor a dividir
        batch_size: Tamaño de cada batch
        dim: Dimensión a lo largo de la cual dividir
    
    Returns:
        Lista de tensores (batches)
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"tensor debe ser torch.Tensor, recibido: {type(tensor)}")
    if batch_size <= 0:
        raise ValueError(f"batch_size debe ser > 0, recibido: {batch_size}")
    
    total_size = tensor.size(dim)
    batches = []
    
    for i in range(0, total_size, batch_size):
        end_idx = min(i + batch_size, total_size)
        slices = [slice(None)] * tensor.dim()
        slices[dim] = slice(i, end_idx)
        batches.append(tensor[tuple(slices)])
    
    return batches


def concatenate_tensors(
    tensors: List[torch.Tensor],
    dim: int = 0
) -> torch.Tensor:
    """
    Concatena una lista de tensores de forma segura.
    
    Args:
        tensors: Lista de tensores a concatenar
        dim: Dimensión a lo largo de la cual concatenar
    
    Returns:
        Tensor concatenado
    """
    if not tensors:
        raise ValueError("tensors no puede estar vacío")
    
    if not all(isinstance(t, torch.Tensor) for t in tensors):
        raise TypeError("todos los elementos de tensors deben ser torch.Tensor")
    
    return torch.cat(tensors, dim=dim)


def get_tensor_info(tensor: torch.Tensor) -> Dict[str, Any]:
    """
    Obtiene información detallada de un tensor.
    
    Args:
        tensor: Tensor a analizar
    
    Returns:
        Diccionario con información del tensor
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"tensor debe ser torch.Tensor, recibido: {type(tensor)}")
    
    info = {
        'shape': list(tensor.shape),
        'dtype': str(tensor.dtype),
        'device': str(tensor.device),
        'requires_grad': tensor.requires_grad,
        'numel': tensor.numel(),
        'element_size': tensor.element_size(),
        'memory_size_mb': tensor.numel() * tensor.element_size() / 1024**2
    }
    
    if tensor.numel() > 0:
        info['min'] = tensor.min().item()
        info['max'] = tensor.max().item()
        info['mean'] = tensor.mean().item()
        info['std'] = tensor.std().item()
    
    return info


def ensure_tensor_on_device(
    tensor: torch.Tensor,
    device: Union[str, torch.device],
    non_blocking: bool = False
) -> torch.Tensor:
    """
    Asegura que un tensor esté en el dispositivo especificado.
    
    Args:
        tensor: Tensor a verificar/mover
        device: Dispositivo destino
        non_blocking: Si usar transferencia no bloqueante
    
    Returns:
        Tensor en el dispositivo correcto
    """
    device_obj = torch.device(device) if isinstance(device, str) else device
    
    if tensor.device != device_obj:
        return move_to_device(tensor, device_obj, non_blocking)
    return tensor


def profile_function(
    func: Callable,
    *args: Any,
    **kwargs: Any
) -> Tuple[Any, Dict[str, Any]]:
    """
    Ejecuta una función y perfila su ejecución.
    
    Args:
        func: Función a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
    
    Returns:
        Tupla (resultado, estadísticas)
    """
    start_time = time.perf_counter()
    start_memory = None
    
    if torch.cuda.is_available():
        start_memory = torch.cuda.memory_allocated()
    
    try:
        result = func(*args, **kwargs)
    finally:
        elapsed_time = time.perf_counter() - start_time
        
        stats = {
            'execution_time': elapsed_time,
            'function_name': func.__name__
        }
        
        if start_memory is not None:
            end_memory = torch.cuda.memory_allocated()
            stats['gpu_memory_delta_mb'] = (end_memory - start_memory) / 1024**2
    
    return result, stats


def validate_tensor_device(
    tensor: torch.Tensor,
    expected_device: Union[str, torch.device],
    name: str = "tensor"
) -> None:
    """
    Valida que un tensor esté en el dispositivo esperado.
    
    Args:
        tensor: Tensor a validar
        expected_device: Dispositivo esperado
        name: Nombre del tensor para mensajes de error
    
    Raises:
        ValueError: Si el dispositivo no coincide
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"{name} debe ser torch.Tensor, recibido: {type(tensor)}")
    
    expected = torch.device(expected_device) if isinstance(expected_device, str) else expected_device
    
    if tensor.device != expected:
        raise ValueError(
            f"{name} debe estar en {expected}, pero está en {tensor.device}"
        )


