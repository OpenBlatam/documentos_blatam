#!/usr/bin/env python3
"""
Model Data Collector
====================

Recolecta datos de modelos: información, métricas, parámetros, benchmarks, etc.
"""

import torch
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
import time
import json

from core.paper_base import BasePaperModule, BasePaperConfig
from core.benchmark import BenchmarkRunner, BenchmarkResult
from core.utils import setup_logger
from core.error_handling import safe_execute, ValidationError

from .constants import (
    DEFAULT_BENCHMARK_WARMUP_RUNS,
    DEFAULT_BENCHMARK_NUM_RUNS,
    DEFAULT_DEVICE,
    DEFAULT_BENCHMARK_SIZES
)

logger = setup_logger(__name__)


@dataclass
class ModelData:
    """Datos recopilados de un modelo."""
    model_name: str
    model_class: str
    paper_id: Optional[str] = None
    category: Optional[str] = None
    
    # Información del modelo
    model_info: Dict[str, Any] = field(default_factory=dict)
    
    # Configuración
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Métricas del modelo
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Información de parámetros
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Benchmarks
    benchmarks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata adicional
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    collected_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convierte a JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ModelDataCollector:
    """
    Recolector de datos de modelos.
    
    Recolecta:
    - Información del modelo (parámetros, device, dtype)
    - Métricas acumuladas
    - Configuración
    - Resultados de benchmarks
    - Metadata adicional
    """
    
    def __init__(
        self,
        include_benchmarks: bool = True,
        benchmark_config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el recolector.
        
        Args:
            include_benchmarks: Si True, incluye benchmarks
            benchmark_config: Configuración para benchmarks
        
        Raises:
            ValidationError: Si la configuración de benchmarks es inválida
        """
        self.include_benchmarks = include_benchmarks
        self.benchmark_config = benchmark_config or {
            'device': DEFAULT_DEVICE,
            'warmup_runs': DEFAULT_BENCHMARK_WARMUP_RUNS,
            'num_runs': DEFAULT_BENCHMARK_NUM_RUNS
        }
        
        if benchmark_config:
            if 'warmup_runs' in benchmark_config and benchmark_config['warmup_runs'] < 0:
                raise ValidationError("warmup_runs debe ser >= 0")
            if 'num_runs' in benchmark_config and benchmark_config['num_runs'] < 1:
                raise ValidationError("num_runs debe ser >= 1")
        
        self._benchmark_runner: Optional[BenchmarkRunner] = None
    
    def collect_model_data(
        self,
        model: BasePaperModule,
        paper_id: Optional[str] = None,
        category: Optional[str] = None,
        run_benchmarks: bool = True,
        benchmark_sizes: Optional[List[Dict[str, int]]] = None
    ) -> ModelData:
        """
        Recolecta todos los datos de un modelo.
        
        Args:
            model: Modelo del cual recolectar datos
            paper_id: ID del paper (opcional)
            category: Categoría del paper (opcional)
            run_benchmarks: Si True, ejecuta benchmarks
            benchmark_sizes: Tamaños para benchmarks (opcional)
        
        Returns:
            ModelData con todos los datos recopilados
        """
        logger.info(
            "Recolectando datos del modelo",
            model_name=model.__class__.__name__,
            paper_id=paper_id
        )
        
        # Información básica
        model_name = model.__class__.__name__
        model_class = f"{model.__class__.__module__}.{model.__class__.__name__}"
        
        # Información del modelo
        model_info = self._collect_model_info(model)
        
        # Configuración
        config = self._collect_config(model)
        
        # Métricas
        metrics = self._collect_metrics(model)
        
        # Parámetros
        parameters = self._collect_parameters(model)
        
        # Benchmarks
        benchmarks = []
        if self.include_benchmarks and run_benchmarks:
            benchmarks = self._collect_benchmarks(
                model,
                benchmark_sizes=benchmark_sizes
            )
        
        # Metadata adicional
        metadata = self._collect_metadata(model)
        
        return ModelData(
            model_name=model_name,
            model_class=model_class,
            paper_id=paper_id,
            category=category,
            model_info=model_info,
            config=config,
            metrics=metrics,
            parameters=parameters,
            benchmarks=benchmarks,
            metadata=metadata
        )
    
    def _collect_model_info(self, model: BasePaperModule) -> Dict[str, Any]:
        """Recolecta información del modelo."""
        def _get_info():
            return model.get_model_info()
        
        info, error = safe_execute(_get_info, default_value={})
        if error:
            logger.warning("Error al obtener información del modelo", error=str(error))
        
        return info or {}
    
    def _collect_config(self, model: BasePaperModule) -> Dict[str, Any]:
        """Recolecta configuración del modelo."""
        def _get_config():
            return model.config.to_dict()
        
        config, error = safe_execute(_get_config, default_value={})
        if error:
            logger.warning("Error al obtener configuración", error=str(error))
        
        return config or {}
    
    def _collect_metrics(self, model: BasePaperModule) -> Dict[str, Any]:
        """Recolecta métricas del modelo."""
        def _get_metrics():
            return model.get_metrics()
        
        metrics, error = safe_execute(_get_metrics, default_value={})
        if error:
            logger.warning("Error al obtener métricas", error=str(error))
        
        return metrics or {}
    
    def _collect_parameters(self, model: BasePaperModule) -> Dict[str, Any]:
        """Recolecta información de parámetros."""
        def _collect():
            total_params = model.count_parameters(trainable_only=False)
            trainable_params = model.count_parameters(trainable_only=True)
            
            # Información detallada de capas
            layer_info = []
            for name, param in model.named_parameters():
                layer_info.append({
                    'name': name,
                    'shape': list(param.shape),
                    'numel': param.numel(),
                    'requires_grad': param.requires_grad,
                    'dtype': str(param.dtype)
                })
            
            return {
                'total_parameters': total_params,
                'trainable_parameters': trainable_params,
                'non_trainable_parameters': total_params - trainable_params,
                'layers': layer_info,
                'num_layers': len(layer_info)
            }
        
        result, error = safe_execute(_collect, default_value={}, log_errors=False)
        
        if error:
            logger.warning("Error al recolectar parámetros", error=str(error))
        
        return result
    
    def _collect_benchmarks(
        self,
        model: BasePaperModule,
        benchmark_sizes: Optional[List[Dict[str, int]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recolecta resultados de benchmarks.
        
        Args:
            model: Modelo a benchmarkear
            benchmark_sizes: Lista de configuraciones de tamaño (opcional)
        
        Returns:
            Lista de resultados de benchmarks
        """
        if benchmark_sizes is None:
            benchmark_sizes = DEFAULT_BENCHMARK_SIZES.copy()
        
        if not benchmark_sizes:
            logger.warning("No se proporcionaron tamaños de benchmark")
            return []
        
        benchmarks = []
        
        if self._benchmark_runner is None:
            self._benchmark_runner = BenchmarkRunner(**self.benchmark_config)
        
        for size_config in benchmark_sizes:
            def _run_benchmark():
                result = self._benchmark_runner.benchmark(
                    model,
                    batch_size=size_config.get('batch_size', 1),
                    seq_len=size_config.get('seq_len', 128)
                )
                
                return {
                    'batch_size': result.batch_size,
                    'seq_len': result.seq_len,
                    'hidden_dim': result.hidden_dim,
                    'forward_time': result.forward_time,
                    'backward_time': result.backward_time,
                    'memory_used': result.memory_used,
                    'throughput': result.throughput,
                    'latency': result.latency,
                    'metadata': result.metadata
                }
            
            result, error = safe_execute(_run_benchmark, default_value=None, log_errors=False)
            
            if error:
                logger.warning(
                    "Error en benchmark",
                    batch_size=size_config.get('batch_size'),
                    seq_len=size_config.get('seq_len'),
                    error=str(error)
                )
            elif result:
                benchmarks.append(result)
        
        return benchmarks
    
    def _collect_metadata(self, model: BasePaperModule) -> Dict[str, Any]:
        """Recolecta metadata adicional."""
        metadata = {}
        
        # Cache stats
        def _get_cache_stats():
            return model.get_cache_stats()
        
        cache_result, _ = safe_execute(_get_cache_stats, default_value=None, log_errors=False)
        if cache_result:
            metadata['cache_stats'] = cache_result
        
        # Device y dtype
        def _get_model_info():
            return model.get_model_info()
        
        info_result, _ = safe_execute(_get_model_info, default_value=None, log_errors=False)
        if info_result:
            metadata['device'] = info_result.get('device', 'unknown')
            metadata['dtype'] = info_result.get('dtype', 'unknown')
        
        # Training mode
        metadata['training_mode'] = model.training
        
        return metadata
    
    def collect_batch(
        self,
        models: List[BasePaperModule],
        paper_ids: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        run_benchmarks: bool = True
    ) -> List[ModelData]:
        """
        Recolecta datos de múltiples modelos.
        
        Args:
            models: Lista de modelos
            paper_ids: IDs de papers (opcional)
            categories: Categorías (opcional)
            run_benchmarks: Si True, ejecuta benchmarks
        
        Returns:
            Lista de ModelData
        """
        results = []
        
        for idx, model in enumerate(models):
            paper_id = paper_ids[idx] if paper_ids and idx < len(paper_ids) else None
            category = categories[idx] if categories and idx < len(categories) else None
            
            data = self.collect_model_data(
                model,
                paper_id=paper_id,
                category=category,
                run_benchmarks=run_benchmarks
            )
            results.append(data)
        
        return results


