#!/usr/bin/env python3
"""
Performance Utilities - Utilidades de Rendimiento para Sora
============================================================

Utilidades para optimizar y medir el rendimiento de generación de video.
"""

import torch
import time
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import functools


@contextmanager
def torch_inference_mode():
    """Context manager para modo de inferencia optimizado."""
    with torch.inference_mode():
        yield


@contextmanager
def torch_autocast(enabled: bool = True, dtype: torch.dtype = torch.float16):
    """Context manager para mixed precision."""
    if enabled and torch.cuda.is_available():
        with torch.cuda.amp.autocast(enabled=enabled, dtype=dtype):
            yield
    else:
        yield


def benchmark_video_generation(
    model: torch.nn.Module,
    input_shape: tuple,
    num_runs: int = 10,
    warmup_runs: int = 3,
    device: Optional[torch.device] = None
) -> Dict[str, Any]:
    """
    Benchmark de generación de video.
    
    Args:
        model: Modelo a benchmarkear
        input_shape: Shape del input (batch, frames, channels, height, width)
        num_runs: Número de runs para promediar
        warmup_runs: Número de warmup runs
        device: Device a usar
    
    Returns:
        Diccionario con métricas de rendimiento
    """
    if device is None:
        device = next(model.parameters()).device
    
    model.eval()
    
    # Warmup
    dummy_input = torch.randn(*input_shape, device=device)
    with torch.no_grad():
        for _ in range(warmup_runs):
            _ = model(dummy_input)
    
    # Sincronizar si CUDA
    if device.type == 'cuda':
        torch.cuda.synchronize()
    
    # Benchmark
    times = []
    with torch.no_grad():
        for _ in range(num_runs):
            if device.type == 'cuda':
                torch.cuda.synchronize()
            
            start = time.time()
            _ = model(dummy_input)
            
            if device.type == 'cuda':
                torch.cuda.synchronize()
            
            end = time.time()
            times.append(end - start)
    
    # Calcular estadísticas
    times_tensor = torch.tensor(times)
    mean_time = times_tensor.mean().item()
    std_time = times_tensor.std().item()
    min_time = times_tensor.min().item()
    max_time = times_tensor.max().item()
    
    # Calcular throughput (frames por segundo)
    batch_size, num_frames = input_shape[0], input_shape[1]
    total_frames = batch_size * num_frames
    fps = total_frames / mean_time
    
    return {
        'mean_time_ms': mean_time * 1000,
        'std_time_ms': std_time * 1000,
        'min_time_ms': min_time * 1000,
        'max_time_ms': max_time * 1000,
        'fps': fps,
        'total_frames': total_frames,
        'num_runs': num_runs,
    }


def optimize_model_for_inference(model: torch.nn.Module) -> torch.nn.Module:
    """
    Optimiza modelo para inferencia.
    
    Args:
        model: Modelo a optimizar
    
    Returns:
        Modelo optimizado
    """
    model.eval()
    
    # Fusionar operaciones si es posible
    if hasattr(torch.jit, 'script'):
        try:
            model = torch.jit.script(model)
        except Exception:
            pass
    
    return model


def profile_memory_usage(
    model: torch.nn.Module,
    input_shape: tuple,
    device: Optional[torch.device] = None
) -> Dict[str, Any]:
    """
    Perfila uso de memoria del modelo.
    
    Args:
        model: Modelo a perfilar
        input_shape: Shape del input
        device: Device a usar
    
    Returns:
        Diccionario con información de memoria
    """
    if device is None:
        device = next(model.parameters()).device
    
    if device.type != 'cuda':
        return {'error': 'Memory profiling solo disponible para CUDA'}
    
    model.eval()
    dummy_input = torch.randn(*input_shape, device=device)
    
    # Limpiar cache
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    
    # Forward pass
    with torch.no_grad():
        _ = model(dummy_input)
    
    # Obtener estadísticas
    peak_memory = torch.cuda.max_memory_allocated(device) / (1024 ** 2)  # MB
    current_memory = torch.cuda.memory_allocated(device) / (1024 ** 2)  # MB
    
    # Limpiar
    del dummy_input
    torch.cuda.empty_cache()
    
    return {
        'peak_memory_mb': peak_memory,
        'current_memory_mb': current_memory,
        'device': str(device),
    }


def estimate_model_size(model: torch.nn.Module, dtype: torch.dtype = torch.float32) -> Dict[str, Any]:
    """
    Estima el tamaño del modelo en memoria.
    
    Args:
        model: Modelo a analizar
        dtype: Dtype a usar para estimación
    
    Returns:
        Diccionario con información de tamaño
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Tamaño por parámetro según dtype
    bytes_per_param = {
        torch.float32: 4,
        torch.float16: 2,
        torch.int8: 1,
        torch.bfloat16: 2,
    }.get(dtype, 4)
    
    total_size_mb = (total_params * bytes_per_param) / (1024 ** 2)
    trainable_size_mb = (trainable_params * bytes_per_param) / (1024 ** 2)
    
    return {
        'total_parameters': total_params,
        'trainable_parameters': trainable_params,
        'total_size_mb': total_size_mb,
        'trainable_size_mb': trainable_size_mb,
        'dtype': str(dtype),
        'bytes_per_param': bytes_per_param,
    }


def cache_activations(model: torch.nn.Module, enable: bool = True):
    """
    Habilita/deshabilita cache de activaciones.
    
    Args:
        model: Modelo
        enable: Si habilitar cache
    """
    for module in model.modules():
        if hasattr(module, 'cache_activations'):
            module.cache_activations = enable


def compile_model(model: torch.nn.Module, mode: str = "reduce-overhead") -> torch.nn.Module:
    """
    Compila modelo para mejor rendimiento (PyTorch 2.0+).
    
    Args:
        model: Modelo a compilar
        mode: Modo de compilación ("default", "reduce-overhead", "max-autotune")
    
    Returns:
        Modelo compilado
    """
    if hasattr(torch, 'compile'):
        try:
            return torch.compile(model, mode=mode)
        except Exception as e:
            print(f"Warning: Could not compile model: {e}")
            return model
    else:
        print("Warning: torch.compile not available (requires PyTorch 2.0+)")
        return model


def measure_latency(
    func: Callable,
    *args,
    num_runs: int = 100,
    warmup_runs: int = 10,
    **kwargs
) -> Dict[str, float]:
    """
    Mide latencia de una función.
    
    Args:
        func: Función a medir
        *args: Argumentos posicionales
        num_runs: Número de runs
        warmup_runs: Número de warmup runs
        **kwargs: Argumentos keyword
    
    Returns:
        Diccionario con métricas de latencia
    """
    # Warmup
    for _ in range(warmup_runs):
        _ = func(*args, **kwargs)
    
    # Medir
    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        _ = func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)
    
    times_tensor = torch.tensor(times)
    
    return {
        'mean_ms': times_tensor.mean().item() * 1000,
        'std_ms': times_tensor.std().item() * 1000,
        'min_ms': times_tensor.min().item() * 1000,
        'max_ms': times_tensor.max().item() * 1000,
        'p50_ms': times_tensor.median().item() * 1000,
        'p95_ms': torch.quantile(times_tensor, 0.95).item() * 1000,
        'p99_ms': torch.quantile(times_tensor, 0.99).item() * 1000,
    }


def optimize_batch_size(
    model: torch.nn.Module,
    base_shape: tuple,
    max_batch_size: int = 32,
    device: Optional[torch.device] = None
) -> int:
    """
    Encuentra el batch size óptimo para el modelo.
    
    Args:
        model: Modelo
        base_shape: Shape base (sin batch dimension)
        max_batch_size: Batch size máximo a probar
        device: Device a usar
    
    Returns:
        Batch size óptimo
    """
    if device is None:
        device = next(model.parameters()).device
    
    model.eval()
    optimal_batch = 1
    
    for batch_size in range(1, max_batch_size + 1):
        try:
            input_shape = (batch_size,) + base_shape
            dummy_input = torch.randn(*input_shape, device=device)
            
            with torch.no_grad():
                _ = model(dummy_input)
            
            optimal_batch = batch_size
            
            if device.type == 'cuda':
                torch.cuda.empty_cache()
        except RuntimeError as e:
            if "out of memory" in str(e):
                break
            raise
    
    return optimal_batch


