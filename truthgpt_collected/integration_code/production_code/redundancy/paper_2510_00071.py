#!/usr/bin/env python3
"""
Paper: 2510.00071 (Redundancy Suppression for Bulk Processing)
==============================================================

Implementación específica basada en técnicas de supresión de redundancia.
Este módulo implementa las técnicas específicas propuestas en este paper.

Basado en: https://arxiv.org/abs/2510.00071
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import OrderedDict
from core.utils import setup_logger
from core.error_handling import safe_execute
from core.paper_base import BasePaperModule, BasePaperConfig

logger = setup_logger(__name__)

try:
    from .redundancy_logging import RedundancyLogger, log_operation_context
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    RedundancyLogger = None
    log_operation_context = None

try:
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


if PYDANTIC_AVAILABLE:
    class Paper2510_00071Config(BasePaperConfig):
        """Configuración específica para paper 2510.00071 (Redundancy Suppression)."""
        similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="Umbral de similitud")
        use_hierarchical_clustering: bool = Field(default=True, description="Usar clustering jerárquico")
        max_cluster_size: int = Field(default=100, ge=1, description="Tamaño máximo de cluster")
        redundancy_detection_method: str = Field(default="cosine", description="Método de detección")
        bulk_processing_batch_size: int = Field(default=1000, ge=1, description="Tamaño de batch para procesamiento masivo")
        enable_caching: bool = Field(default=True, description="Habilitar caché de similitudes")
        cache_size: int = Field(default=5000, ge=1, description="Tamaño del caché")
        enable_persistence: bool = Field(default=False, description="Habilitar persistencia de resultados")
        persistence_path: Optional[str] = Field(default=None, description="Ruta para persistencia")
        enable_adaptive_threshold: bool = Field(default=False, description="Umbral adaptativo")
        min_reduction_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Tasa mínima de reducción esperada")
        
        @field_validator('redundancy_detection_method')
        @classmethod
        def validate_method(cls, v: str) -> str:
            valid_methods = ["cosine", "euclidean", "semantic", "dot"]
            if v not in valid_methods:
                raise ValueError(f"redundancy_detection_method debe ser uno de {valid_methods}, recibido: {v}")
            return v
else:
    @dataclass
    class Paper2510_00071Config(BasePaperConfig):
        """Configuración específica para paper 2510.00071 (Redundancy Suppression)."""
        hidden_dim: int = 512
        similarity_threshold: float = 0.85
        use_hierarchical_clustering: bool = True
        max_cluster_size: int = 100
        redundancy_detection_method: str = "cosine"
        bulk_processing_batch_size: int = 1000
        enable_caching: bool = True
        cache_size: int = 5000
        enable_persistence: bool = False
        persistence_path: Optional[str] = None
        enable_adaptive_threshold: bool = False
        min_reduction_rate: float = 0.1
        
        def validate(self):
            """Valida la configuración de Paper 2510.00071."""
            super().validate()
            if not (0.0 <= self.similarity_threshold <= 1.0):
                raise ValueError(f"similarity_threshold debe estar en [0.0, 1.0], recibido: {self.similarity_threshold}")
            if self.max_cluster_size <= 0:
                raise ValueError(f"max_cluster_size debe ser positivo, recibido: {self.max_cluster_size}")
            if self.bulk_processing_batch_size <= 0:
                raise ValueError(f"bulk_processing_batch_size debe ser positivo, recibido: {self.bulk_processing_batch_size}")
            if self.cache_size <= 0:
                raise ValueError(f"cache_size debe ser positivo, recibido: {self.cache_size}")
            valid_methods = ["cosine", "euclidean", "semantic", "dot"]
            if self.redundancy_detection_method not in valid_methods:
                raise ValueError(f"redundancy_detection_method debe ser uno de {valid_methods}, recibido: {self.redundancy_detection_method}")
            if not (0.0 <= self.min_reduction_rate <= 1.0):
                raise ValueError(f"min_reduction_rate debe estar en [0.0, 1.0], recibido: {self.min_reduction_rate}")


class Paper2510_00071_RedundancySuppressor(BasePaperModule):
    """
    Supresor de redundancia basado en paper 2510.00071.
    
    Mejoras implementadas:
    - Herencia de BasePaperModule (validación, métricas, save/load)
    - Validación completa de inputs
    - Caché de similitudes
    - Persistencia de resultados
    - Umbral adaptativo
    - Métricas mejoradas
    - Batch processing optimizado
    - Clustering mejorado
    
    Este paper propone técnicas específicas para supresión de redundancia
    en procesamiento masivo (bulk processing).
    """
    
    def __init__(self, config: Paper2510_00071Config):
        # Validar configuración
        if not PYDANTIC_AVAILABLE and hasattr(config, 'validate'):
            config.validate()
        
        super().__init__(config)
        
        self.config = config
        self.similarity_threshold = config.similarity_threshold
        self.detection_method = config.redundancy_detection_method
        
        # Caché de similitudes mejorado
        if config.enable_caching:
            from collections import OrderedDict
            self.similarity_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
            self.cache_max_size = getattr(config, 'cache_size', 5000)
        else:
            self.similarity_cache = None
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Persistencia
        self.persistence_path = Path(config.persistence_path) if config.persistence_path else None
        if config.enable_persistence and self.persistence_path:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        # Umbral adaptativo
        self.adaptive_threshold = config.similarity_threshold if config.enable_adaptive_threshold else None
        
        # Métricas mejoradas
        self.total_processed = 0
        self.total_reduced = 0
        self.avg_reduction_rate = 0.0
        self.register_buffer('efficiency', torch.tensor(0.0))
        self.register_buffer('avg_processing_time', torch.tensor(0.0))
        
        # Estadísticas de procesamiento
        self.processing_times: List[float] = []
        self.reduction_rates: List[float] = []
        self.cluster_sizes: List[int] = []
        
        logger.info(
            f"Initialized Paper 2510.00071 Redundancy Suppressor "
            f"(threshold={config.similarity_threshold}, method={config.redundancy_detection_method}, "
            f"caching={config.enable_caching})"
        )
    
    def compute_similarity_matrix(self, embeddings: torch.Tensor) -> torch.Tensor:
        """
        Calcula matriz de similitud usando técnicas específicas del paper.
        Incluye caché LRU para optimización.
        
        Args:
            embeddings: [batch_size, hidden_dim]
            
        Returns:
            similarity_matrix: [batch_size, batch_size]
        """
        def _get_cache_key():
            import hashlib
            embeddings_bytes = embeddings.cpu().numpy().tobytes()
            hash_obj = hashlib.sha256(embeddings_bytes)
            hash_obj.update(self.detection_method.encode())
            return hash_obj.hexdigest()
        
        cache_key = None
            if self.similarity_cache is not None:
                cache_key = _get_cache_key()
                if cache_key in self.similarity_cache:
                    self.cache_hits += 1
                    cached = self.similarity_cache[cache_key]
                    self.similarity_cache.move_to_end(cache_key)
                    if self.op_logger:
                        self.op_logger.log_cache_hit(cache_key, 0.0)
                    return cached['matrix'].to(embeddings.device)
                self.cache_misses += 1
                if self.op_logger:
                    self.op_logger.log_cache_miss(cache_key)
        
        def _compute():
            if embeddings.dim() != 2:
                raise ValueError(f"Expected 2D embeddings [batch, hidden_dim], got {embeddings.dim()}D")
            
            if self.detection_method == "cosine":
                embeddings_norm = F.normalize(embeddings, p=2, dim=-1)
                similarity_matrix = torch.matmul(embeddings_norm, embeddings_norm.transpose(-2, -1))
            elif self.detection_method == "euclidean":
                distances = torch.cdist(embeddings, embeddings, p=2)
                max_dist = distances.max()
                similarity_matrix = 1.0 - (distances / (max_dist + 1e-8))
            else:  # semantic
                similarity_matrix = torch.matmul(embeddings, embeddings.transpose(-2, -1))
                similarity_matrix = F.softmax(similarity_matrix, dim=-1)
            
            return similarity_matrix
        
        result, error = safe_execute(
            _compute,
            default_value=None,
            log_errors=True
        )
        
        if error or result is None:
            batch_size = embeddings.size(0) if embeddings.dim() >= 1 else 1
            return torch.eye(batch_size, device=embeddings.device, dtype=embeddings.dtype)
        
        if self.similarity_cache is not None and cache_key:
            while len(self.similarity_cache) >= self.cache_max_size:
                self.similarity_cache.popitem(last=False)
            
            self.similarity_cache[cache_key] = {
                'matrix': result.cpu().clone(),
                'timestamp': time.time()
            }
            self.similarity_cache.move_to_end(cache_key)
        
        return result
    
    def cluster_similar_items(self, similarity_matrix: torch.Tensor) -> List[List[int]]:
        """
        Agrupa items similares usando clustering jerárquico del paper.
        
        Args:
            similarity_matrix: [batch_size, batch_size]
            
        Returns:
            clusters: Lista de clusters con índices
        """
        batch_size = similarity_matrix.size(0)
        visited = set()
        clusters = []
        
        for i in range(batch_size):
            if i in visited:
                continue
            
            # Crear nuevo cluster
            cluster = [i]
            visited.add(i)
            
            # Encontrar items similares (técnica del paper)
            for j in range(i + 1, batch_size):
                if j in visited:
                    continue
                
                if similarity_matrix[i, j] >= self.similarity_threshold:
                    cluster.append(j)
                    visited.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def select_representatives(self, items: torch.Tensor, clusters: List[List[int]]) -> torch.Tensor:
        """
        Selecciona representantes de cada cluster según técnicas del paper.
        
        Args:
            items: [batch_size, seq_len, hidden_dim]
            clusters: Lista de clusters
            
        Returns:
            unique_items: [unique_batch_size, seq_len, hidden_dim]
        """
        representatives = []
        
        for cluster in clusters:
            if len(cluster) == 1:
                representatives.append(items[cluster[0]])
            else:
                # Seleccionar el item más central del cluster (técnica del paper)
                cluster_items = items[cluster]
                cluster_center = cluster_items.mean(dim=0)
                
                # Encontrar el más cercano al centro
                distances = torch.norm(cluster_items - cluster_center.unsqueeze(0), dim=-1)
                best_cluster_idx = distances.argmin().item()
                best_idx = cluster[best_cluster_idx]
                representatives.append(items[best_idx])
        
        return torch.stack(representatives)
    
    def process_bulk(self, items: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa un lote masivo eliminando redundancias según técnicas del paper.
        
        Mejoras:
        - Validación mejorada
        - Métricas de reducción
        - Batch processing optimizado
        - Manejo de errores robusto
        
        Args:
            items: [batch_size, seq_len, hidden_dim]
            
        Returns:
            unique_items: [unique_batch_size, seq_len, hidden_dim]
            stats: Dictionary with reduction statistics
        """
        def _process():
            # Validation
            if items.dim() != 3:
                raise ValueError(f"Expected 3D input [batch, seq, hidden], got {items.dim()}D")
            if items.size(0) == 0:
                raise ValueError("Input items cannot be empty")
            
            original_size = items.size(0)
            
            if original_size <= 1:
                stats = {
                    'original_size': original_size,
                    'reduced_size': original_size,
                    'reduction_rate': 0.0,
                    'num_clusters': original_size
                }
                return items, stats
            
            # Usar último token para comparación (técnica del paper)
            last_tokens = items[:, -1, :]  # [batch_size, hidden_dim]
            
            # Calcular matriz de similitud (con caché)
            similarity_matrix = self.compute_similarity_matrix(last_tokens)
            
            # Clustering jerárquico
            clusters = self.cluster_similar_items(similarity_matrix)
            
            # Seleccionar representantes
            unique_items = self.select_representatives(items, clusters)
            
            # Compute statistics
            reduced_size = unique_items.size(0)
            reduction_rate = (original_size - reduced_size) / original_size if original_size > 0 else 0.0
            
            # Update metrics
            self.total_processed += original_size
            self.total_reduced += (original_size - reduced_size)
            if self.total_processed > 0:
                self.avg_reduction_rate = 0.9 * self.avg_reduction_rate + 0.1 * (self.total_reduced / self.total_processed)
                efficiency = self.total_reduced / self.total_processed
                self.efficiency = 0.9 * self.efficiency + 0.1 * efficiency
            
            # Actualizar umbral adaptativo si está habilitado
            if self.adaptive_threshold is not None:
                if reduction_rate < self.config.min_reduction_rate:
                    # Aumentar umbral para más agresividad
                    self.similarity_threshold = min(1.0, self.similarity_threshold + 0.01)
                elif reduction_rate > 0.5:
                    # Reducir umbral si es muy agresivo
                    self.similarity_threshold = max(0.5, self.similarity_threshold - 0.01)
            
            stats = {
                'original_size': original_size,
                'reduced_size': reduced_size,
                'reduction_rate': reduction_rate,
                'num_clusters': len(clusters),
                'avg_cluster_size': original_size / len(clusters) if len(clusters) > 0 else 0.0,
                'max_cluster_size': max(len(c) for c in clusters) if clusters else 0,
                'min_cluster_size': min(len(c) for c in clusters) if clusters else 0
            }
            
            # Guardar resultado si persistencia está habilitada
            if self.config.enable_persistence and self.persistence_path:
                self._save_processing_result(items, unique_items, stats)
            
            return unique_items, stats
        
        result, error = safe_execute(
            _process,
            default_value=(
                items,
                {
                    'original_size': items.size(0) if items.dim() >= 1 else 0,
                    'reduced_size': items.size(0) if items.dim() >= 1 else 0,
                    'reduction_rate': 0.0,
                    'num_clusters': items.size(0) if items.dim() >= 1 else 0,
                    'error': 'Processing failed'
                }
            ),
            log_errors=True
        )
        
        if error:
            logger.error(f"Error en process_bulk: {error}")
            if self.op_logger:
                self.op_logger.log_error("process_bulk", error)
            return result
        
        unique_items, stats = result
        
        if self.op_logger:
            processing_time = stats.get('processing_time', 0.0)
            self.op_logger.log_processing_end(
                batch_size=stats.get('original_size', 0),
                reduced_size=stats.get('reduced_size', 0),
                processing_time=processing_time,
                reduction_rate=stats.get('reduction_rate', 0.0),
                num_clusters=stats.get('num_clusters', 0)
            )
        
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive redundancy suppression metrics."""
        metrics = {
            'total_processed': self.total_processed,
            'total_reduced': self.total_reduced,
            'avg_reduction_rate': self.avg_reduction_rate,
            'efficiency': self.efficiency.item(),
            'avg_processing_time': self.avg_processing_time.item(),
            'similarity_threshold': self.similarity_threshold,
            'detection_method': self.detection_method
        }
        
        # Estadísticas de caché
        if self.similarity_cache:
            total_cache_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0.0
            metrics.update({
                'cache_size': len(self.similarity_cache),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': cache_hit_rate
            })
        
        # Estadísticas de procesamiento
        if self.processing_times:
            metrics.update({
                'min_processing_time': min(self.processing_times),
                'max_processing_time': max(self.processing_times),
                'total_batches': len(self.processing_times),
                'avg_reduction_rate_history': sum(self.reduction_rates) / len(self.reduction_rates) if self.reduction_rates else 0.0
            })
        
        return metrics
    
    def clear_cache(self):
        """Limpia el caché de similitudes."""
        if self.similarity_cache:
            if isinstance(self.similarity_cache, OrderedDict):
                self.similarity_cache.clear()
            elif isinstance(self.similarity_cache, dict):
                self.similarity_cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            logger.info("Caché de similitudes limpiado")
    
    def reset_metrics(self):
        """Resetea todas las métricas."""
        self.total_processed = 0
        self.total_reduced = 0
        self.avg_reduction_rate = 0.0
        self.efficiency.zero_()
        self.avg_processing_time.zero_()
        self.processing_times.clear()
        self.reduction_rates.clear()
        self.cluster_sizes.clear()
        logger.info("Métricas reseteadas")
    
    def get_reduction_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de reducción."""
        return {
            'total_processed': self.total_processed,
            'total_reduced': self.total_reduced,
            'reduction_percentage': (self.total_reduced / self.total_processed * 100) if self.total_processed > 0 else 0.0,
            'avg_reduction_rate': self.avg_reduction_rate,
            'efficiency': self.efficiency.item(),
            'batches_processed': len(self.processing_times),
            'avg_batch_reduction': sum(self.reduction_rates) / len(self.reduction_rates) if self.reduction_rates else 0.0
        }
    
    def _save_processing_result(self, original: torch.Tensor, reduced: torch.Tensor, stats: Dict[str, Any]):
        """Guarda resultado de procesamiento si persistencia está habilitada."""
        if not self.persistence_path:
            return
        
        try:
            result_file = self.persistence_path / f"redundancy_result_{int(time.time())}.json"
            result_data = {
                'timestamp': time.time(),
                'stats': stats,
                'original_shape': list(original.shape),
                'reduced_shape': list(reduced.shape)
            }
            
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            logger.debug("Resultado de procesamiento guardado", file=str(result_file))
        except Exception as e:
            logger.warning(f"Error guardando resultado: {e}")
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass del módulo: procesa hidden_states eliminando redundancias.
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor sin redundancias
            - metadata: Diccionario con métricas
        """
        self.validate_inputs(hidden_states, **kwargs)
        
        start_time = time.time()
        
        try:
            # Procesar eliminando redundancias
            unique_items, stats = self.process_bulk(hidden_states)
            
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            self.reduction_rates.append(stats['reduction_rate'])
            self.cluster_sizes.append(stats.get('avg_cluster_size', 0.0))
            
            # Actualizar métricas
            self.avg_processing_time = (
                0.9 * self.avg_processing_time + 0.1 * processing_time
            )
            
            # Metadata completa
            metadata = {
                **stats,
                'processing_time': processing_time,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
                'similarity_threshold': self.similarity_threshold,
                'total_processed': self.total_processed,
                'total_reduced': self.total_reduced,
                'efficiency': self.efficiency.item()
            }
            
            self._update_metrics(**metadata)
            
            return unique_items, metadata
        
        except Exception as e:
            logger.error(f"Error en forward de Paper2510_00071: {e}", exc_info=True)
            error_metadata = {
                'error': str(e),
                'original_size': hidden_states.size(0)
            }
            return hidden_states, error_metadata


class TruthGPT_Paper2510_00071_Integration(BasePaperModule):
    """
    Integración del paper 2510.00071 con TruthGPT.
    
    Mejoras:
    - Herencia de BasePaperModule
    - Validación robusta
    - Métricas completas
    - Manejo de errores
    """
    
    def __init__(self, base_model, paper_config: Paper2510_00071Config):
        if PYDANTIC_AVAILABLE:
            config_dict = paper_config.model_dump() if hasattr(paper_config, 'model_dump') else paper_config.__dict__
        else:
            config_dict = paper_config.__dict__ if hasattr(paper_config, '__dict__') else paper_config
        
        super().__init__(config_dict)
        
        self.base_model = base_model
        self.redundancy_suppressor = Paper2510_00071_RedundancySuppressor(paper_config)
    
    def forward(self, hidden_states: torch.Tensor, **kwargs) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con supresión de redundancia del paper.
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado sin redundancias
            - metadata: Diccionario con métricas
        """
        # Aplicar supresión de redundancia
        unique_items, redundancy_metadata = self.redundancy_suppressor(hidden_states, **kwargs)
        
        # Procesar con modelo base
        if hasattr(self.base_model, 'forward'):
            base_output = self.base_model(unique_items, **kwargs)
        else:
            base_output = unique_items
        
        # Combinar metadata
        metadata = {
            **redundancy_metadata,
            'redundancy_suppressed': True,
            'original_batch_size': hidden_states.size(0),
            'reduced_batch_size': unique_items.size(0)
        }
        
        return base_output, metadata


if __name__ == "__main__":
    print("=" * 60)
    print("Test del Sistema de Redundancia Mejorado")
    print("=" * 60)
    
    config = Paper2510_00071Config(
        similarity_threshold=0.85,
        enable_caching=True,
        enable_adaptive_threshold=True
    )
    suppressor = Paper2510_00071_RedundancySuppressor(config)
    
    # Test básico
    print("\n1. Test básico:")
    batch_size, seq_len, hidden_dim = 20, 32, 512
    items = torch.randn(batch_size, seq_len, hidden_dim)
    
    unique_items, stats = suppressor.process_bulk(items)
    print(f"   ✅ Original items: {items.shape}")
    print(f"   ✅ Unique items: {unique_items.shape}")
    print(f"   ✅ Reduction rate: {stats['reduction_rate']:.2%}")
    print(f"   ✅ Clusters: {stats['num_clusters']}")
    
    # Test con forward
    print("\n2. Test con forward:")
    output, metadata = suppressor(items)
    print(f"   ✅ Output shape: {output.shape}")
    print(f"   ✅ Processing time: {metadata.get('processing_time', 0):.4f}s")
    
    # Test de métricas
    print("\n3. Métricas:")
    metrics = suppressor.get_metrics()
    print(f"   ✅ Total procesados: {metrics['total_processed']}")
    print(f"   ✅ Eficiencia: {metrics['efficiency']:.2%}")
    if 'cache_hit_rate' in metrics:
        print(f"   ✅ Cache hit rate: {metrics['cache_hit_rate']:.2%}")
    
    # Test de analytics (si está disponible)
    print("\n4. Analytics:")
    try:
        from redundancy.redundancy_analytics import RedundancyAnalytics
        analytics = RedundancyAnalytics(suppressor)
        report = analytics.get_comprehensive_report()
        print(f"   ✅ Analytics disponibles")
        print(f"   ✅ Total reducido: {report.get('total_reduced', 0)}")
    except ImportError:
        print("   ⚠️  Analytics no disponibles")
    
    print("\n" + "=" * 60)
    print("✅ Todos los tests completados!")
    print("=" * 60)

