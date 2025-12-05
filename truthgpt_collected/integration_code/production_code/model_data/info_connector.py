#!/usr/bin/env python3
"""
Info Connector
==============

Se conecta a las mejores fuentes de información disponibles:
- Paper Registry
- Benchmarks
- Modelos guardados
- Documentación
- Estadísticas
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
import time

from core.paper_registry import PaperRegistry, get_registry, PaperInfo
from core.benchmark import BenchmarkRunner
from core.paper_base import BasePaperModule, BasePaperConfig
from core.utils import setup_logger
from core.error_handling import safe_execute
from .dependencies import TORCH_AVAILABLE, get_torch

from .constants import DEFAULT_CACHE_TTL, CHECKPOINTS_DIR

logger = setup_logger(__name__)


class InfoConnector:
    """
    Conector a fuentes de información.
    
    Se conecta a:
    - Paper Registry (papers disponibles, estadísticas)
    - Modelos guardados (checkpoints)
    - Benchmarks históricos
    - Documentación de papers
    """
    
    def __init__(
        self,
        registry: Optional[PaperRegistry] = None,
        base_dir: Optional[Path] = None
    ):
        """
        Inicializa el conector.
        
        Args:
            registry: Registry de papers (opcional, se crea uno si no se proporciona)
            base_dir: Directorio base para buscar información
        """
        self.registry = registry or get_registry(base_dir=base_dir)
        self.base_dir = base_dir or Path(__file__).parent.parent
        
        # Cache de información
        self._registry_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = DEFAULT_CACHE_TTL
    
    def get_registry_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene información del registry.
        
        Args:
            force_refresh: Si True, fuerza actualización del cache
        
        Returns:
            Diccionario con información del registry
        """
        # Verificar cache
        if (not force_refresh and
            self._registry_cache is not None and
            self._cache_timestamp is not None and
            time.time() - self._cache_timestamp < self._cache_ttl):
            return self._registry_cache
        
        try:
            # Estadísticas del registry
            stats = self.registry.get_statistics()
            
            # Lista de papers
            papers = self.registry.list_papers()
            papers_info = [
                {
                    'paper_id': p.paper_id,
                    'paper_name': p.paper_name,
                    'category': p.category,
                    'enabled': p.enabled,
                    'load_count': p.load_count,
                    'error_count': p.error_count,
                    'module_path': str(p.module_path)
                }
                for p in papers
            ]
            
            # Papers por categoría
            papers_by_category = {}
            for category in self.registry.CATEGORIES.keys():
                category_papers = self.registry.list_papers(category=category)
                papers_by_category[category] = len(category_papers)
            
            info = {
                'statistics': stats,
                'total_papers': len(papers),
                'papers': papers_info,
                'papers_by_category': papers_by_category,
                'categories': list(self.registry.CATEGORIES.keys()),
                'timestamp': time.time()
            }
            
            # Actualizar cache
            self._registry_cache = info
            self._cache_timestamp = time.time()
            
            return info
        except Exception as e:
            logger.error("Error al obtener información del registry", error=str(e))
            return {}
    
    def get_paper_info(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada de un paper.
        
        Args:
            paper_id: ID del paper
        
        Returns:
            Diccionario con información del paper o None
        """
        try:
            paper_info = self.registry.get_paper_info(paper_id)
            if paper_info is None:
                return None
            
            return {
                'paper_id': paper_info.paper_id,
                'paper_name': paper_info.paper_name,
                'category': paper_info.category,
                'module_path': str(paper_info.module_path),
                'module_name': paper_info.module_name,
                'config_class': paper_info.config_class,
                'module_class': paper_info.module_class,
                'enabled': paper_info.enabled,
                'load_count': paper_info.load_count,
                'last_loaded': paper_info.last_loaded,
                'error_count': paper_info.error_count,
                'last_error': paper_info.last_error
            }
        except Exception as e:
            logger.error("Error al obtener información del paper", paper_id=paper_id, error=str(e))
            return None
    
    def search_papers(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca papers.
        
        Args:
            query: Texto a buscar
            category: Filtrar por categoría
        
        Returns:
            Lista de papers encontrados
        """
        try:
            papers = self.registry.search_papers(query=query, category=category)
            return [
                {
                    'paper_id': p.paper_id,
                    'paper_name': p.paper_name,
                    'category': p.category,
                    'load_count': p.load_count,
                    'enabled': p.enabled
                }
                for p in papers
            ]
        except Exception as e:
            logger.error("Error al buscar papers", query=query, error=str(e))
            return []
    
    def get_best_papers(
        self,
        category: Optional[str] = None,
        top_k: int = 10,
        metric: str = 'load_count'
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los mejores papers según una métrica.
        
        Args:
            category: Filtrar por categoría
            top_k: Número de papers a retornar
            metric: Métrica para ordenar ('load_count', 'error_count')
        
        Returns:
            Lista de mejores papers
        """
        try:
            papers = self.registry.list_papers(category=category, enabled_only=True)
            
            # Ordenar por métrica
            if metric == 'load_count':
                papers.sort(key=lambda p: p.load_count, reverse=True)
            elif metric == 'error_count':
                papers.sort(key=lambda p: p.error_count)
            else:
                papers.sort(key=lambda p: p.load_count, reverse=True)
            
            return [
                {
                    'paper_id': p.paper_id,
                    'paper_name': p.paper_name,
                    'category': p.category,
                    'load_count': p.load_count,
                    'error_count': p.error_count,
                    'metric_value': p.load_count if metric == 'load_count' else p.error_count
                }
                for p in papers[:top_k]
            ]
        except Exception as e:
            logger.error("Error al obtener mejores papers", error=str(e))
            return []
    
    def get_model_checkpoints(
        self,
        paper_id: Optional[str] = None,
        checkpoint_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca checkpoints de modelos guardados.
        
        Args:
            paper_id: Filtrar por paper ID
            checkpoint_dir: Directorio donde buscar checkpoints
        
        Returns:
            Lista de checkpoints encontrados
        """
        if checkpoint_dir is None:
            checkpoint_dir = self.base_dir / CHECKPOINTS_DIR
        
        checkpoints = []
        
        if not checkpoint_dir.exists():
            return checkpoints
        
        if not TORCH_AVAILABLE:
            logger.warning("Torch no disponible, no se pueden cargar checkpoints")
            return checkpoints
        
        try:
            torch = get_torch()
            for checkpoint_file in checkpoint_dir.glob("*.pt"):
                try:
                    # Intentar cargar metadata del checkpoint
                    checkpoint = torch.load(checkpoint_file, map_location='cpu')
                    
                    checkpoint_info = {
                        'path': str(checkpoint_file),
                        'filename': checkpoint_file.name,
                        'size_mb': checkpoint_file.stat().st_size / (1024 * 1024),
                        'model_class': checkpoint.get('model_class', 'unknown'),
                        'model_info': checkpoint.get('model_info', {}),
                        'timestamp': checkpoint_file.stat().st_mtime
                    }
                    
                    # Filtrar por paper_id si se especifica
                    if paper_id:
                        model_name = checkpoint_info['model_class'].lower()
                        if paper_id.lower() not in model_name:
                            continue
                    
                    checkpoints.append(checkpoint_info)
                except Exception as e:
                    logger.warning(
                        "Error al leer checkpoint",
                        file=str(checkpoint_file),
                        error=str(e)
                    )
            
            # Ordenar por timestamp (más recientes primero)
            checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error("Error al buscar checkpoints", error=str(e))
        
        return checkpoints
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Obtiene todos los modelos disponibles.
        
        Returns:
            Diccionario con información de modelos disponibles
        """
        registry_info = self.get_registry_info()
        checkpoints = self.get_model_checkpoints()
        
        return {
            'registry': registry_info,
            'checkpoints': checkpoints,
            'total_available': registry_info.get('total_papers', 0),
            'total_checkpoints': len(checkpoints)
        }
    
    def get_category_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen por categoría.
        
        Returns:
            Diccionario con resumen por categoría
        """
        registry_info = self.get_registry_info()
        papers_by_category = registry_info.get('papers_by_category', {})
        
        summary = {}
        for category, count in papers_by_category.items():
            papers = self.registry.list_papers(category=category, enabled_only=True)
            
            # Calcular estadísticas
            total_loads = sum(p.load_count for p in papers)
            total_errors = sum(p.error_count for p in papers)
            avg_loads = total_loads / count if count > 0 else 0
            
            summary[category] = {
                'count': count,
                'total_loads': total_loads,
                'total_errors': total_errors,
                'avg_loads_per_paper': avg_loads,
                'error_rate': total_errors / total_loads if total_loads > 0 else 0
            }
        
        return summary
    
    def refresh_cache(self):
        """Fuerza actualización del cache."""
        self._registry_cache = None
        self._cache_timestamp = None
        logger.info("Cache refrescado")

