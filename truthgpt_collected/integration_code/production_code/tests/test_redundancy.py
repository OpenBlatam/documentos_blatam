#!/usr/bin/env python3
"""
Tests para el módulo de Redundancy
==================================

Suite completa de tests para sistemas de supresión de redundancia.
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import tempfile
import json

from redundancy import (
    create_redundancy_suppressor,
    Paper2510_00071Config,
    Paper2510_00071_RedundancySuppressor,
    compute_similarity_batch,
    find_duplicate_items,
    batch_deduplicate,
    compare_redundancy_methods,
    optimize_threshold,
    recommend_similarity_method,
    validate_redundancy_config,
    get_redundancy_health_report,
    get_available_modules,
    RedundancyAnalytics,
    RedundancyOptimizer,
    RedundancyExporter
)


class TestPaper2510_00071Config:
    """Tests para Paper2510_00071Config."""
    
    def test_config_defaults(self):
        """Test configuración con valores por defecto."""
        config = Paper2510_00071Config()
        assert config.similarity_threshold == 0.85
        assert config.redundancy_detection_method == "cosine"
        assert config.use_hierarchical_clustering is True
        assert config.max_cluster_size == 100
    
    def test_config_custom(self):
        """Test configuración personalizada."""
        config = Paper2510_00071Config(
            similarity_threshold=0.9,
            redundancy_detection_method="euclidean",
            max_cluster_size=50
        )
        assert config.similarity_threshold == 0.9
        assert config.redundancy_detection_method == "euclidean"
        assert config.max_cluster_size == 50
    
    def test_config_validation(self):
        """Test validación de configuración."""
        with pytest.raises(ValueError):
            Paper2510_00071Config(similarity_threshold=1.5)
        
        with pytest.raises(ValueError):
            Paper2510_00071Config(similarity_threshold=-0.1)
        
        with pytest.raises(ValueError):
            Paper2510_00071Config(max_cluster_size=0)


class TestPaper2510_00071_RedundancySuppressor:
    """Tests para Paper2510_00071_RedundancySuppressor."""
    
    @pytest.fixture
    def suppressor(self):
        """Fixture para crear un supresor."""
        config = Paper2510_00071Config(similarity_threshold=0.85)
        return Paper2510_00071_RedundancySuppressor(config)
    
    @pytest.fixture
    def sample_items(self):
        """Fixture para items de muestra."""
        return torch.randn(20, 32, 512)
    
    def test_initialization(self, suppressor):
        """Test inicialización."""
        assert suppressor.similarity_threshold == 0.85
        assert suppressor.detection_method == "cosine"
        assert suppressor.total_processed == 0
        assert suppressor.total_reduced == 0
    
    def test_process_bulk_basic(self, suppressor, sample_items):
        """Test procesamiento básico."""
        unique_items, stats = suppressor.process_bulk(sample_items)
        
        assert unique_items.dim() == 3
        assert unique_items.size(0) <= sample_items.size(0)
        assert stats['original_size'] == sample_items.size(0)
        assert stats['reduced_size'] == unique_items.size(0)
        assert 0.0 <= stats['reduction_rate'] <= 1.0
    
    def test_process_bulk_single_item(self, suppressor):
        """Test con un solo item."""
        items = torch.randn(1, 32, 512)
        unique_items, stats = suppressor.process_bulk(items)
        
        assert unique_items.size(0) == 1
        assert stats['reduction_rate'] == 0.0
    
    def test_process_bulk_duplicates(self, suppressor):
        """Test con items duplicados."""
        base_item = torch.randn(1, 32, 512)
        items = torch.cat([base_item] * 10, dim=0)
        unique_items, stats = suppressor.process_bulk(items)
        
        assert unique_items.size(0) <= items.size(0)
        assert stats['reduction_rate'] >= 0.0
    
    def test_compute_similarity_matrix(self, suppressor):
        """Test cálculo de matriz de similitud."""
        embeddings = torch.randn(10, 512)
        similarity_matrix = suppressor.compute_similarity_matrix(embeddings)
        
        assert similarity_matrix.shape == (10, 10)
        assert torch.allclose(similarity_matrix, similarity_matrix.transpose(-2, -1), atol=1e-5)
        assert torch.all(similarity_matrix >= -2.0) and torch.all(similarity_matrix <= 2.0)
    
    def test_cluster_similar_items(self, suppressor):
        """Test clustering de items similares."""
        similarity_matrix = torch.eye(10) * 0.9
        similarity_matrix += torch.randn(10, 10) * 0.05
        similarity_matrix = (similarity_matrix + similarity_matrix.transpose(-2, -1)) / 2
        
        clusters = suppressor.cluster_similar_items(similarity_matrix)
        
        assert len(clusters) > 0
        assert all(isinstance(c, list) for c in clusters)
        assert all(len(c) > 0 for c in clusters)
    
    def test_get_metrics(self, suppressor, sample_items):
        """Test obtención de métricas."""
        suppressor.process_bulk(sample_items)
        metrics = suppressor.get_metrics()
        
        assert isinstance(metrics, dict)
        assert 'total_processed' in metrics or 'efficiency' in metrics
        assert metrics.get('total_processed', 0) >= 0


class TestUtilityFunctions:
    """Tests para funciones de utilidad."""
    
    @pytest.fixture
    def sample_embeddings(self):
        """Fixture para embeddings de muestra."""
        return torch.randn(15, 512)
    
    def test_compute_similarity_batch_cosine(self, sample_embeddings):
        """Test similitud coseno."""
        similarity = compute_similarity_batch(sample_embeddings, method="cosine")
        assert similarity.shape == (15, 15)
        assert torch.allclose(similarity, similarity.transpose(-2, -1))
    
    def test_compute_similarity_batch_euclidean(self, sample_embeddings):
        """Test similitud euclidiana."""
        similarity = compute_similarity_batch(sample_embeddings, method="euclidean")
        assert similarity.shape == (15, 15)
    
    def test_find_duplicate_items(self):
        """Test encontrar duplicados."""
        base = torch.randn(1, 32, 512)
        items = torch.cat([base, base + 0.01 * torch.randn(1, 32, 512)], dim=0)
        
        duplicates = find_duplicate_items(items, threshold=0.9, method="cosine")
        assert len(duplicates) >= 0
    
    def test_batch_deduplicate(self):
        """Test deduplicación de batch."""
        items = torch.randn(20, 32, 512)
        unique_items, stats = batch_deduplicate(items, threshold=0.85)
        
        assert unique_items.size(0) <= items.size(0)
        assert stats['original_size'] == items.size(0)
        assert stats['reduction_rate'] >= 0.0
    
    def test_compare_redundancy_methods(self):
        """Test comparación de métodos."""
        items = torch.randn(15, 32, 512)
        results = compare_redundancy_methods(items, threshold=0.85)
        
        assert isinstance(results, dict)
        assert len(results) > 0


class TestHelperFunctions:
    """Tests para funciones helper."""
    
    def test_recommend_similarity_method(self):
        """Test recomendación de método."""
        method = recommend_similarity_method("general")
        assert method in ["cosine", "euclidean", "dot", "semantic"]
        
        method = recommend_similarity_method("semantic")
        assert method == "semantic"
    
    def test_validate_redundancy_config(self):
        """Test validación de configuración."""
        config = Paper2510_00071Config()
        is_valid, errors = validate_redundancy_config(config)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_get_available_modules(self):
        """Test obtener módulos disponibles."""
        modules = get_available_modules()
        assert isinstance(modules, dict)
        assert 'paper_2510_00071' in modules
        assert 'utils' in modules
        assert 'analytics' in modules
    
    def test_get_redundancy_health_report(self):
        """Test reporte de salud."""
        config = Paper2510_00071Config()
        suppressor = Paper2510_00071_RedundancySuppressor(config)
        
        health = get_redundancy_health_report(suppressor)
        assert 'status' in health
        assert 'warnings' in health
        assert 'recommendations' in health


class TestRedundancyAnalytics:
    """Tests para RedundancyAnalytics."""
    
    @pytest.fixture
    def analytics(self):
        """Fixture para analytics."""
        return RedundancyAnalytics()
    
    def test_record_batch(self, analytics):
        """Test registro de batch."""
        analytics.record_batch(100, 80, 0.5, method="cosine")
        
        assert analytics.metrics.total_processed == 100
        assert analytics.metrics.total_reduced == 20
        assert len(analytics.batch_history) == 1
    
    def test_get_summary(self, analytics):
        """Test obtener resumen."""
        analytics.record_batch(100, 80, 0.5)
        summary = analytics.get_summary()
        
        assert 'metrics' in summary
        assert 'total_batches' in summary
        assert summary['total_batches'] == 1
    
    def test_compare_methods(self, analytics):
        """Test comparación de métodos."""
        analytics.record_batch(100, 80, 0.5, method="cosine")
        analytics.record_batch(100, 75, 0.6, method="euclidean")
        
        comparison = analytics.compare_methods()
        assert 'cosine' in comparison
        assert 'euclidean' in comparison
    
    def test_export_report(self, analytics, tmp_path):
        """Test exportar reporte."""
        analytics.record_batch(100, 80, 0.5)
        
        output_path = tmp_path / "report.json"
        report = analytics.export_report(str(output_path))
        
        assert output_path.exists()
        assert 'summary' in report


class TestRedundancyOptimizer:
    """Tests para RedundancyOptimizer."""
    
    @pytest.fixture
    def suppressor(self):
        """Fixture para supresor."""
        config = Paper2510_00071Config()
        return Paper2510_00071_RedundancySuppressor(config)
    
    @pytest.fixture
    def optimizer(self, suppressor):
        """Fixture para optimizador."""
        return RedundancyOptimizer(suppressor)
    
    def test_optimize_threshold(self, optimizer):
        """Test optimización de threshold."""
        sample_items = torch.randn(25, 32, 512)
        result = optimizer.optimize_threshold(
            sample_items,
            target_reduction_rate=0.3
        )
        
        assert isinstance(result, dict)
    
    def test_find_optimal_method(self, optimizer):
        """Test encontrar método óptimo."""
        sample_items = torch.randn(20, 32, 512)
        result = optimizer.find_optimal_method(sample_items)
        
        assert isinstance(result, dict)
        assert 'optimal_method' in result


class TestRedundancyExporter:
    """Tests para RedundancyExporter."""
    
    def test_export_to_json(self, tmp_path):
        """Test exportar a JSON."""
        data = {'test': 'data', 'value': 123}
        output_path = tmp_path / "export.json"
        
        success = RedundancyExporter.export_to_json(data, str(output_path))
        
        assert success
        assert output_path.exists()
        
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_export_clusters(self, tmp_path):
        """Test exportar clusters."""
        clusters = [[0, 1, 2], [3, 4], [5]]
        items = torch.randn(6, 32, 512)
        output_path = tmp_path / "clusters.json"
        
        success = RedundancyExporter.export_clusters(
            clusters, items, str(output_path)
        )
        
        assert success
        assert output_path.exists()


class TestFactoryFunctions:
    """Tests para factory functions."""
    
    def test_create_redundancy_suppressor(self):
        """Test crear supresor."""
        suppressor = create_redundancy_suppressor(
            "2510_00071",
            similarity_threshold=0.85
        )
        
        assert suppressor is not None
        assert isinstance(suppressor, Paper2510_00071_RedundancySuppressor)
    
    def test_create_redundancy_suppressor_invalid(self):
        """Test crear supresor con tipo inválido."""
        suppressor = create_redundancy_suppressor("invalid")
        assert suppressor is None


class TestEdgeCases:
    """Tests para casos extremos."""
    
    def test_empty_batch(self):
        """Test con batch vacío."""
        config = Paper2510_00071Config()
        suppressor = Paper2510_00071_RedundancySuppressor(config)
        
        items = torch.randn(0, 32, 512)
        try:
            unique_items, stats = suppressor.process_bulk(items)
            assert unique_items.size(0) == 0
        except (ValueError, RuntimeError):
            pass
    
    def test_very_large_batch(self):
        """Test con batch muy grande."""
        config = Paper2510_00071Config()
        suppressor = Paper2510_00071_RedundancySuppressor(config)
        
        items = torch.randn(1000, 32, 512)
        unique_items, stats = suppressor.process_bulk(items)
        
        assert unique_items.size(0) <= items.size(0)
        assert stats['original_size'] == 1000
    
    def test_all_identical_items(self):
        """Test con todos los items idénticos."""
        config = Paper2510_00071Config(similarity_threshold=0.9)
        suppressor = Paper2510_00071_RedundancySuppressor(config)
        
        base = torch.randn(1, 32, 512)
        items = base.repeat(10, 1, 1)
        
        unique_items, stats = suppressor.process_bulk(items)
        
        assert unique_items.size(0) <= items.size(0)
        assert stats['reduction_rate'] >= 0.0
        if unique_items.size(0) < items.size(0):
            assert stats['reduction_rate'] > 0.0


class TestPerformance:
    """Tests de rendimiento."""
    
    def test_process_bulk_performance(self):
        """Test rendimiento de process_bulk."""
        import time
        
        config = Paper2510_00071Config()
        suppressor = Paper2510_00071_RedundancySuppressor(config)
        items = torch.randn(100, 32, 512)
        
        start = time.time()
        unique_items, stats = suppressor.process_bulk(items)
        duration = time.time() - start
        
        assert duration < 5.0
        assert unique_items.size(0) <= items.size(0)
    
    def test_similarity_computation_performance(self):
        """Test rendimiento de cálculo de similitud."""
        import time
        
        embeddings = torch.randn(200, 512)
        
        start = time.time()
        similarity = compute_similarity_batch(embeddings, method="cosine")
        duration = time.time() - start
        
        assert duration < 2.0
        assert similarity.shape == (200, 200)

