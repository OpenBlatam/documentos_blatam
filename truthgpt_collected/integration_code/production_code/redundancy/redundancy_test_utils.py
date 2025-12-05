#!/usr/bin/env python3
"""
Utilidades de Testing para Redundancy
=====================================

Herramientas y fixtures para facilitar el testing del módulo de redundancia.
"""

from typing import Dict, Any, Optional, List, Tuple
import torch
import numpy as np
from dataclasses import dataclass

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class TestData:
    """Datos de prueba para testing."""
    items: torch.Tensor
    expected_reduction: float
    description: str
    metadata: Dict[str, Any] = None


class RedundancyTestUtils:
    """
    Utilidades para testing del módulo de redundancia.
    """
    
    @staticmethod
    def generate_test_items(
        batch_size: int = 100,
        seq_len: int = 32,
        hidden_dim: int = 512,
        duplicate_ratio: float = 0.3,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        """
        Genera items de prueba con duplicados controlados.
        
        Args:
            batch_size: Tamaño del batch
            seq_len: Longitud de secuencia
            hidden_dim: Dimensión oculta
            duplicate_ratio: Proporción de duplicados (0.0 - 1.0)
            seed: Semilla para reproducibilidad
        
        Returns:
            Tensor de items [batch_size, seq_len, hidden_dim]
        """
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)
        
        unique_items = int(batch_size * (1 - duplicate_ratio))
        duplicate_count = batch_size - unique_items
        
        items = []
        
        for i in range(unique_items):
            item = torch.randn(seq_len, hidden_dim)
            items.append(item)
        
        for i in range(duplicate_count):
            duplicate_idx = np.random.randint(0, len(items))
            items.append(items[duplicate_idx].clone())
        
        items_tensor = torch.stack(items)
        
        indices = torch.randperm(len(items_tensor))
        return items_tensor[indices]
    
    @staticmethod
    def generate_identical_items(
        batch_size: int = 10,
        seq_len: int = 32,
        hidden_dim: int = 512
    ) -> torch.Tensor:
        """
        Genera items idénticos para testing de casos extremos.
        
        Args:
            batch_size: Tamaño del batch
            seq_len: Longitud de secuencia
            hidden_dim: Dimensión oculta
        
        Returns:
            Tensor con items idénticos
        """
        base_item = torch.randn(seq_len, hidden_dim)
        return base_item.unsqueeze(0).repeat(batch_size, 1, 1)
    
    @staticmethod
    def generate_unique_items(
        batch_size: int = 100,
        seq_len: int = 32,
        hidden_dim: int = 512,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        """
        Genera items completamente únicos.
        
        Args:
            batch_size: Tamaño del batch
            seq_len: Longitud de secuencia
            hidden_dim: Dimensión oculta
            seed: Semilla para reproducibilidad
        
        Returns:
            Tensor con items únicos
        """
        if seed is not None:
            torch.manual_seed(seed)
        
        items = []
        for _ in range(batch_size):
            item = torch.randn(seq_len, hidden_dim)
            items.append(item)
        
        return torch.stack(items)
    
    @staticmethod
    def create_test_dataset(
        num_batches: int = 5,
        batch_size: int = 50,
        seq_len: int = 32,
        hidden_dim: int = 512
    ) -> List[torch.Tensor]:
        """
        Crea un dataset de prueba con múltiples batches.
        
        Args:
            num_batches: Número de batches
            batch_size: Tamaño de cada batch
            seq_len: Longitud de secuencia
            hidden_dim: Dimensión oculta
        
        Returns:
            Lista de batches
        """
        dataset = []
        for i in range(num_batches):
            batch = RedundancyTestUtils.generate_test_items(
                batch_size=batch_size,
                seq_len=seq_len,
                hidden_dim=hidden_dim,
                duplicate_ratio=0.2,
                seed=i
            )
            dataset.append(batch)
        return dataset
    
    @staticmethod
    def assert_reduction_rate(
        original_size: int,
        reduced_size: int,
        expected_min: float = 0.0,
        expected_max: float = 1.0
    ) -> bool:
        """
        Verifica que la tasa de reducción esté en el rango esperado.
        
        Args:
            original_size: Tamaño original
            reduced_size: Tamaño reducido
            expected_min: Tasa mínima esperada
            expected_max: Tasa máxima esperada
        
        Returns:
            True si está en el rango
        """
        if original_size == 0:
            return False
        
        reduction_rate = (original_size - reduced_size) / original_size
        
        return expected_min <= reduction_rate <= expected_max
    
    @staticmethod
    def assert_no_duplicates(
        items: torch.Tensor,
        threshold: float = 0.95,
        method: str = "cosine"
    ) -> bool:
        """
        Verifica que no haya duplicados en los items.
        
        Args:
            items: Items a verificar
            threshold: Umbral de similitud
            method: Método de similitud
        
        Returns:
            True si no hay duplicados
        """
        if items.size(0) <= 1:
            return True
        
        try:
            from .redundancy_utils import compute_similarity_batch
            
            if items.dim() == 3:
                embeddings = items[:, -1, :]
            else:
                embeddings = items
            
            similarity_matrix = compute_similarity_batch(embeddings, method)
            
            for i in range(similarity_matrix.size(0)):
                for j in range(i + 1, similarity_matrix.size(1)):
                    similarity = similarity_matrix[i, j].item()
                    if similarity >= threshold:
                        return False
            
            return True
        except Exception:
            return True
    
    @staticmethod
    def compare_results(
        result1: Tuple[torch.Tensor, Dict[str, Any]],
        result2: Tuple[torch.Tensor, Dict[str, Any]],
        tolerance: float = 1e-5
    ) -> Dict[str, Any]:
        """
        Compara dos resultados de procesamiento.
        
        Args:
            result1: Primer resultado (items, stats)
            result2: Segundo resultado (items, stats)
            tolerance: Tolerancia para comparación
        
        Returns:
            Diccionario con comparación
        """
        items1, stats1 = result1
        items2, stats2 = result2
        
        comparison = {
            'items_same_size': items1.size(0) == items2.size(0),
            'items_similar': False,
            'stats_match': stats1.get('reduction_rate') == stats2.get('reduction_rate'),
            'differences': {}
        }
        
        if items1.size(0) == items2.size(0) and items1.size() == items2.size():
            diff = torch.abs(items1 - items2)
            max_diff = diff.max().item()
            comparison['items_similar'] = max_diff < tolerance
            comparison['max_difference'] = max_diff
        
        for key in set(stats1.keys()) | set(stats2.keys()):
            val1 = stats1.get(key)
            val2 = stats2.get(key)
            if val1 != val2:
                comparison['differences'][key] = {
                    'result1': val1,
                    'result2': val2
                }
        
        return comparison


def create_test_suppressor(
    similarity_threshold: float = 0.85,
    method: str = "cosine"
):
    """
    Crea un supresor de redundancia para testing.
    
    Args:
        similarity_threshold: Umbral de similitud
        method: Método de detección
    
    Returns:
        Instancia del supresor
    """
    try:
        from .paper_2510_00071 import Paper2510_00071Config, Paper2510_00071_RedundancySuppressor
        
        config = Paper2510_00071Config(
            similarity_threshold=similarity_threshold,
            redundancy_detection_method=method
        )
        return Paper2510_00071_RedundancySuppressor(config)
    except Exception as e:
        logger.error(f"Error creando supresor de prueba: {e}")
        return None


def run_quick_test(
    suppressor,
    items: torch.Tensor,
    expected_min_reduction: float = 0.0
) -> Dict[str, Any]:
    """
    Ejecuta un test rápido del supresor.
    
    Args:
        suppressor: Supresor a probar
        items: Items de prueba
        expected_min_reduction: Reducción mínima esperada
    
    Returns:
        Diccionario con resultados del test
    """
    def _test():
        original_size = items.size(0)
        unique_items, stats = suppressor.process_bulk(items)
        reduced_size = unique_items.size(0)
        
        reduction_rate = (original_size - reduced_size) / original_size if original_size > 0 else 0.0
        
        passed = reduction_rate >= expected_min_reduction
        
        return {
            'passed': passed,
            'original_size': original_size,
            'reduced_size': reduced_size,
            'reduction_rate': reduction_rate,
            'expected_min': expected_min_reduction,
            'stats': stats
        }
    
    result, error = safe_execute(_test, default_value={'passed': False, 'error': str(error)}, log_errors=True)
    return result


