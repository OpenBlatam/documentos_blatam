#!/usr/bin/env python3
"""
Optimizaciones GPU y Paralelización para Redundancy
===================================================

Optimizaciones avanzadas para aprovechar GPU y procesamiento paralelo.
"""

import torch
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import time
import os

from core.utils import setup_logger
from core.error_handling import safe_execute
from core.helpers import (
    get_gpu_memory_stats as get_gpu_memory_stats_helper,
    clear_gpu_cache,
    auto_select_device,
    move_to_device,
    batch_tensor,
    concatenate_tensors
)

logger = setup_logger(__name__)

try:
    from best import (
        Paper2506_10848v2_BestTechniques,
        Paper2506_10848v2Config,
        GatedAttention,
        AdaptiveLayerNorm
    )
    BEST_AVAILABLE = True
except ImportError:
    BEST_AVAILABLE = False
    Paper2506_10848v2_BestTechniques = None
    Paper2506_10848v2Config = None
    GatedAttention = None
    AdaptiveLayerNorm = None


class GPUOptimizedRedundancyProcessor:
    """
    Procesador de redundancia optimizado para GPU.
    """
    
    def __init__(
        self,
        suppressor: Any,
        device: Optional[torch.device] = None,
        use_mixed_precision: bool = False,
        enable_compile: bool = False
    ):
        """
        Args:
            suppressor: Supresor de redundancia base
            device: Dispositivo a usar (None = auto-detect)
            use_mixed_precision: Si usar precisión mixta (FP16)
            enable_compile: Si compilar con torch.compile (PyTorch 2.0+)
        
        Raises:
            ValueError: Si suppressor es None
        """
        if suppressor is None:
            raise ValueError("suppressor no puede ser None")
        
        self.suppressor = suppressor
        self.device = device or auto_select_device(prefer_gpu=True)
        self.use_mixed_precision = use_mixed_precision and torch.cuda.is_available()
        self.dtype = torch.float16 if self.use_mixed_precision else torch.float32
        self.enable_compile = enable_compile and hasattr(torch, 'compile')
        
        if self.enable_compile and hasattr(torch, 'compile'):
            try:
                self.suppressor = torch.compile(self.suppressor, mode='reduce-overhead')
                logger.info("Suppressor compilado con torch.compile")
            except Exception as e:
                logger.warning(f"No se pudo compilar suppressor: {e}")
                self.enable_compile = False
        
        if self.device.type == 'cuda':
            clear_gpu_cache()
            if self.use_mixed_precision:
                torch.backends.cudnn.benchmark = True
                torch.backends.cudnn.deterministic = False
        
        self._compiled_process = None
        if self.enable_compile:
            self._setup_compiled_process()
        
        logger.info(f"GPU Optimized Processor inicializado en {self.device} (mixed_precision={self.use_mixed_precision}, compile={self.enable_compile})")
    
    def _setup_compiled_process(self):
        """Configura proceso compilado para mejor rendimiento."""
        if hasattr(torch, 'compile') and self.enable_compile:
            try:
                def _process_chunk_compiled(chunk):
                    return self.suppressor.process_bulk(chunk)
                
                self._compiled_process = torch.compile(_process_chunk_compiled, mode='reduce-overhead')
            except Exception as e:
                logger.warning(f"No se pudo compilar proceso: {e}")
                self._compiled_process = None
    
    
    def process_bulk_gpu(
        self,
        items: torch.Tensor,
        chunk_size: Optional[int] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa batch en GPU con optimizaciones.
        
        Args:
            items: Items a procesar [batch_size, seq_len, hidden_dim]
            chunk_size: Tamaño de chunk (None = auto)
        
        Returns:
            Items únicos y estadísticas
        
        Raises:
            ValueError: Si items es None o chunk_size es inválido
            TypeError: Si items no es un tensor
        """
        if items is None:
            raise ValueError("items no puede ser None")
        if not isinstance(items, torch.Tensor):
            raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError(f"chunk_size debe ser > 0, recibido: {chunk_size}")
        def _process():
            batch_size = items.size(0)
            
            actual_chunk_size = chunk_size if chunk_size is not None else min(1000, batch_size)
            
            with torch.no_grad():
                items_gpu = move_to_device(items, self.device, non_blocking=True)
                
                if self.use_mixed_precision:
                    items_gpu = items_gpu.half()
                
                unique_items_list = []
                total_reduced = 0
                
                start_time = time.perf_counter()
                
                for i in range(0, batch_size, actual_chunk_size):
                    end_idx = min(i + actual_chunk_size, batch_size)
                    chunk = items_gpu[i:end_idx]
                    
                    if self._compiled_process:
                        chunk_unique, chunk_stats = self._compiled_process(chunk)
                    else:
                        chunk_unique, chunk_stats = self.suppressor.process_bulk(chunk)
                    
                    unique_items_list.append(chunk_unique)
                    total_reduced += chunk_stats.get('original_size', 0) - chunk_stats.get('reduced_size', 0)
                    
                    if self.device.type == 'cuda' and i % (actual_chunk_size * 5) == 0:
                        clear_gpu_cache()
                
                processing_time = time.perf_counter() - start_time
                
                if unique_items_list:
                    unique_items = concatenate_tensors(unique_items_list, dim=0)
                else:
                    unique_items = items_gpu
                
                if self.use_mixed_precision:
                    unique_items = unique_items.float()
                
                unique_items = unique_items.cpu()
                
                if self.device.type == 'cuda':
                    clear_gpu_cache()
            
            memory_used = None
            if self.device.type == 'cuda':
                memory_used = torch.cuda.max_memory_allocated() / 1024**2
                torch.cuda.reset_peak_memory_stats()
            
            stats = {
                'original_size': batch_size,
                'reduced_size': unique_items.size(0),
                'reduction_rate': (batch_size - unique_items.size(0)) / batch_size if batch_size > 0 else 0.0,
                'device': str(self.device),
                'mixed_precision': self.use_mixed_precision,
                'total_reduced': total_reduced,
                'processing_time_seconds': processing_time,
                'throughput_items_per_sec': batch_size / processing_time if processing_time > 0 else 0.0,
                'memory_used_mb': memory_used,
                'compiled': self.enable_compile
            }
            
            return unique_items, stats
        
        result, error = safe_execute(
            _process,
            default_value=(items, {'error': 'Processing failed'}),
            log_errors=True
        )
        
        return result
    
    def compute_similarity_matrix_gpu(
        self,
        embeddings: torch.Tensor
    ) -> torch.Tensor:
        """
        Calcula matriz de similitud optimizada para GPU.
        
        Args:
            embeddings: [batch_size, hidden_dim]
        
        Returns:
            similarity_matrix: [batch_size, batch_size]
        """
        def _compute():
            with torch.no_grad():
                embeddings_gpu = move_to_device(embeddings, self.device, non_blocking=True)
                
                if self.use_mixed_precision:
                    embeddings_gpu = embeddings_gpu.half()
                
                detection_method = getattr(self.suppressor, 'detection_method', None) or getattr(
                    getattr(self.suppressor, 'config', None), 'redundancy_detection_method', 'cosine'
                )
                
                if detection_method == "cosine":
                    embeddings_norm = F.normalize(embeddings_gpu, p=2, dim=-1)
                    similarity_matrix = torch.matmul(embeddings_norm, embeddings_norm.transpose(-2, -1))
                elif detection_method == "euclidean":
                    distances = torch.cdist(embeddings_gpu, embeddings_gpu, p=2)
                    max_dist = distances.max()
                    similarity_matrix = 1.0 - (distances / (max_dist + 1e-8))
                else:
                    similarity_matrix = torch.matmul(embeddings_gpu, embeddings_gpu.transpose(-2, -1))
                    similarity_matrix = F.softmax(similarity_matrix, dim=-1)
                
                if self.use_mixed_precision:
                    similarity_matrix = similarity_matrix.float()
                
                result = similarity_matrix.cpu()
                
                if self.device.type == 'cuda':
                    clear_gpu_cache()
                
                return result
        
        result, error = safe_execute(
            _compute,
            default_value=torch.eye(embeddings.size(0), device='cpu'),
            log_errors=True
        )
        
        return result


class ParallelRedundancyProcessor:
    """
    Procesador paralelo de redundancia para batches grandes.
    """
    
    def __init__(
        self,
        suppressor: Any,
        max_workers: Optional[int] = None,
        use_processes: bool = False
    ):
        """
        Args:
            suppressor: Supresor de redundancia base
            max_workers: Número máximo de workers
            use_processes: Si usar procesos en lugar de threads
        
        Raises:
            ValueError: Si suppressor es None o max_workers es inválido
        """
        if suppressor is None:
            raise ValueError("suppressor no puede ser None")
        if max_workers is not None and max_workers <= 0:
            raise ValueError(f"max_workers debe ser > 0, recibido: {max_workers}")
        
        self.suppressor = suppressor
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    def process_bulk_parallel(
        self,
        items: torch.Tensor,
        chunk_size: int = 500
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa batch en paralelo.
        
        Args:
            items: Items a procesar [batch_size, seq_len, hidden_dim]
            chunk_size: Tamaño de cada chunk
        
        Returns:
            Items únicos y estadísticas
        
        Raises:
            ValueError: Si items es None o chunk_size es inválido
            TypeError: Si items no es un tensor
        """
        if items is None:
            raise ValueError("items no puede ser None")
        if not isinstance(items, torch.Tensor):
            raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
        if chunk_size <= 0:
            raise ValueError(f"chunk_size debe ser > 0, recibido: {chunk_size}")
        def _process():
            batch_size = items.size(0)
            chunks = [items[i:i + chunk_size] for i in range(0, batch_size, chunk_size)]
            
            unique_items_list = []
            total_reduced = 0
            errors_count = 0
            
            def process_chunk(chunk):
                with torch.no_grad():
                    unique_chunk, stats = self.suppressor.process_bulk(chunk)
                    return unique_chunk, stats
            
            max_workers = self.max_workers or min(len(chunks), 4)
            
            with self.executor_class(max_workers=max_workers) as executor:
                futures = {executor.submit(process_chunk, chunk): i for i, chunk in enumerate(chunks)}
                
                results = [None] * len(chunks)
                
                for future in as_completed(futures):
                    chunk_idx = futures[future]
                    try:
                        unique_chunk, stats = future.result()
                        results[chunk_idx] = (unique_chunk, stats)
                        total_reduced += stats.get('original_size', 0) - stats.get('reduced_size', 0)
                    except Exception as e:
                        errors_count += 1
                        logger.error(f"Error procesando chunk {chunk_idx}: {e}")
                        results[chunk_idx] = (chunks[chunk_idx], {'original_size': chunks[chunk_idx].size(0), 'reduced_size': chunks[chunk_idx].size(0)})
                
                for result in results:
                    if result is not None:
                        unique_items_list.append(result[0])
            
            if unique_items_list:
                unique_items = concatenate_tensors(unique_items_list, dim=0)
            else:
                unique_items = items
            
            stats = {
                'original_size': batch_size,
                'reduced_size': unique_items.size(0),
                'reduction_rate': (batch_size - unique_items.size(0)) / batch_size if batch_size > 0 else 0.0,
                'chunks_processed': len(chunks),
                'total_reduced': total_reduced,
                'parallel': True,
                'errors': errors_count
            }
            
            return unique_items, stats
        
        result, error = safe_execute(
            _process,
            default_value=(items, {'error': 'Processing failed'}),
            log_errors=True
        )
        
        return result


def optimize_for_device(
    items: torch.Tensor,
    suppressor: Any,
    device: Optional[torch.device] = None
) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """
    Optimiza procesamiento según el dispositivo disponible.
    
    Args:
        items: Items a procesar
        suppressor: Supresor de redundancia
        device: Dispositivo (None = auto)
    
    Returns:
        Items únicos y estadísticas
    
    Raises:
        ValueError: Si items o suppressor son None
        TypeError: Si items no es un tensor
    """
    if items is None:
        raise ValueError("items no puede ser None")
    if suppressor is None:
        raise ValueError("suppressor no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if device.type == 'cuda':
        gpu_processor = GPUOptimizedRedundancyProcessor(suppressor, device)
        return gpu_processor.process_bulk_gpu(items)
    else:
        return suppressor.process_bulk(items)


def get_gpu_memory_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas de memoria GPU.
    
    Returns:
        Diccionario con estadísticas
    """
    return get_gpu_memory_stats_helper()


class GPUOptimizedRedundancyWithBestTechniques(GPUOptimizedRedundancyProcessor):
    """
    Procesador GPU optimizado con Best Techniques integradas.
    
    Mejoras adicionales:
    - Gated Attention para mejor procesamiento
    - Adaptive LayerNorm para normalización
    - Mejor calidad en detección de redundancia
    """
    
    def __init__(
        self,
        suppressor: Any,
        device: Optional[torch.device] = None,
        use_mixed_precision: bool = False,
        enable_compile: bool = False,
        enable_best_techniques: bool = True,
        best_config: Optional[Any] = None
    ):
        """
        Args:
            suppressor: Supresor de redundancia base
            device: Dispositivo a usar (None = auto-detect)
            use_mixed_precision: Si usar precisión mixta (FP16)
            enable_compile: Si compilar con torch.compile
            enable_best_techniques: Habilitar Best Techniques
            best_config: Configuración de Best Techniques (opcional)
        
        Raises:
            ValueError: Si suppressor es None
        """
        super().__init__(suppressor, device, use_mixed_precision, enable_compile)
        
        self.enable_best = enable_best_techniques and BEST_AVAILABLE
        
        if self.enable_best:
            if best_config is None:
                hidden_dim = getattr(suppressor.config, 'hidden_dim', 512)
                best_config = Paper2506_10848v2Config(hidden_dim=hidden_dim)
            
            self.best_model = Paper2506_10848v2_BestTechniques(best_config)
            self.best_model = move_to_device(self.best_model, self.device)
            self.best_model.eval()
            
            if self.use_mixed_precision:
                self.best_model = self.best_model.half()
            
            if self.enable_compile and hasattr(torch, 'compile'):
                try:
                    self.best_model = torch.compile(self.best_model, mode='reduce-overhead')
                except Exception as e:
                    logger.warning(f"No se pudo compilar best_model: {e}")
            
            self.adaptive_norm = AdaptiveLayerNorm(hidden_dim=best_config.hidden_dim)
            self.adaptive_norm = move_to_device(self.adaptive_norm, self.device)
            if self.use_mixed_precision:
                self.adaptive_norm = self.adaptive_norm.half()
            
            logger.info("Best Techniques habilitadas en GPU Optimized Processor")
        else:
            self.best_model = None
            self.adaptive_norm = None
    
    def process_bulk_gpu(
        self,
        items: torch.Tensor,
        chunk_size: Optional[int] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa batch en GPU con Best Techniques integradas.
        
        Args:
            items: Items a procesar [batch_size, seq_len, hidden_dim]
            chunk_size: Tamaño de chunk (None = auto)
        
        Returns:
            Items únicos y estadísticas
        """
        if self.enable_best and self.adaptive_norm and self.best_model:
            items = move_to_device(items, self.device, non_blocking=True)
            if self.use_mixed_precision:
                items = items.half()
            
            items = self.adaptive_norm(items)
            items = self.best_model(items)
        
        unique_items, stats = super().process_bulk_gpu(items, chunk_size)
        
        if self.enable_best:
            stats['best_techniques_enabled'] = True
        
        return unique_items, stats


def benchmark_redundancy_processing(
    suppressor: Any,
    items: torch.Tensor,
    num_runs: int = 10,
    warmup_runs: int = 3,
    device: Optional[torch.device] = None
) -> Dict[str, Any]:
    """
    Benchmark de procesamiento de redundancia.
    
    Args:
        suppressor: Supresor de redundancia
        items: Items a procesar
        num_runs: Número de ejecuciones
        warmup_runs: Ejecuciones de calentamiento
        device: Dispositivo a usar
    
    Returns:
        Diccionario con métricas de benchmark
    """
    if suppressor is None:
        raise ValueError("suppressor no puede ser None")
    if items is None:
        raise ValueError("items no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if num_runs <= 0:
        raise ValueError(f"num_runs debe ser > 0, recibido: {num_runs}")
    if warmup_runs < 0:
        raise ValueError(f"warmup_runs debe ser >= 0, recibido: {warmup_runs}")
    
    device = device or (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))
    
    def _benchmark():
        processor = GPUOptimizedRedundancyProcessor(suppressor, device)
        
        for _ in range(warmup_runs):
            _ = processor.process_bulk_gpu(items)
        
        if device.type == 'cuda':
            torch.cuda.synchronize()
        
        times = []
        memory_peaks = []
        
        for _ in range(num_runs):
            if device.type == 'cuda':
                torch.cuda.reset_peak_memory_stats()
            
            start = time.perf_counter()
            unique_items, stats = processor.process_bulk_gpu(items)
            
            if device.type == 'cuda':
                torch.cuda.synchronize()
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
            if device.type == 'cuda':
                memory_peaks.append(torch.cuda.max_memory_allocated() / 1024**2)
        
        times_tensor = torch.tensor(times)
        
        result = {
            'avg_time_seconds': times_tensor.mean().item(),
            'min_time_seconds': times_tensor.min().item(),
            'max_time_seconds': times_tensor.max().item(),
            'std_time_seconds': times_tensor.std().item(),
            'p50_time_seconds': times_tensor.median().item(),
            'p95_time_seconds': torch.quantile(times_tensor, 0.95).item(),
            'p99_time_seconds': torch.quantile(times_tensor, 0.99).item(),
            'throughput_items_per_sec': items.size(0) / times_tensor.mean().item(),
            'device': str(device),
            'num_runs': num_runs
        }
        
        if memory_peaks:
            memory_tensor = torch.tensor(memory_peaks)
            result['avg_memory_mb'] = memory_tensor.mean().item()
            result['max_memory_mb'] = memory_tensor.max().item()
        
        return result
    
    result, error = safe_execute(_benchmark, default_value={}, log_errors=True)
    return result


def optimize_chunk_size(
    suppressor: Any,
    items: torch.Tensor,
    device: Optional[torch.device] = None,
    max_chunk_size: int = 5000,
    min_chunk_size: int = 100
) -> int:
    """
    Encuentra el chunk size óptimo para procesamiento.
    
    Args:
        suppressor: Supresor de redundancia
        items: Items de referencia
        device: Dispositivo a usar
        max_chunk_size: Chunk size máximo a probar
        min_chunk_size: Chunk size mínimo a probar
    
    Returns:
        Chunk size óptimo
    """
    if suppressor is None:
        raise ValueError("suppressor no puede ser None")
    if items is None:
        raise ValueError("items no puede ser None")
    if not isinstance(items, torch.Tensor):
        raise TypeError(f"items debe ser torch.Tensor, recibido: {type(items)}")
    if max_chunk_size <= min_chunk_size:
        raise ValueError(f"max_chunk_size debe ser > min_chunk_size")
    
    device = device or (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))
    processor = GPUOptimizedRedundancyProcessor(suppressor, device)
    
    batch_size = items.size(0)
    optimal_chunk = min_chunk_size
    best_throughput = 0.0
    
    test_sizes = [min_chunk_size, min_chunk_size * 2, min_chunk_size * 4, 
                  min_chunk_size * 8, max_chunk_size]
    test_sizes = [s for s in test_sizes if s <= max_chunk_size and s <= batch_size]
    
    for chunk_size in test_sizes:
        try:
            start = time.perf_counter()
            _, stats = processor.process_bulk_gpu(items, chunk_size=chunk_size)
            elapsed = time.perf_counter() - start
            
            throughput = batch_size / elapsed if elapsed > 0 else 0.0
            
            if throughput > best_throughput:
                best_throughput = throughput
                optimal_chunk = chunk_size
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.debug(f"OOM con chunk_size={chunk_size}")
                break
            raise
    
    return optimal_chunk

