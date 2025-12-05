#!/usr/bin/env python3
"""
Paper Registry System for Production Code
==========================================

Sistema de registro y gestión de módulos de papers en producción.
Incluye auto-descubrimiento, cache, y carga optimizada.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Tuple, Union
from dataclasses import dataclass, field
from collections import OrderedDict
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from .paper_base import BasePaperModule, BasePaperConfig
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class PaperInfo:
    """Información de un paper."""
    paper_id: str
    paper_name: str
    module_path: Path
    module_name: str
    category: str
    config_class: Optional[str] = None
    module_class: Optional[str] = None
    enabled: bool = True
    load_count: int = 0
    last_loaded: Optional[float] = None
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class LoadedModule:
    """Módulo cargado."""
    info: PaperInfo
    config_class: Type[BasePaperConfig]
    module_class: Type[BasePaperModule]
    instance: Optional[BasePaperModule] = None
    loaded: bool = False
    load_time: float = 0.0
    error: Optional[str] = None


class PaperRegistry:
    """
    Registry centralizado para módulos de papers en producción.
    
    Características:
    - Auto-descubrimiento de papers
    - Cache LRU de módulos cargados
    - Thread-safe
    - Carga lazy
    - Estadísticas de uso
    """
    
    CATEGORIES = {
        'research': 'research',
        'inference': 'inference',
        'memory': 'memory',
        'techniques': 'techniques',
        'best': 'best',
        'code': 'code',
        'redundancy': 'redundancy',
        'architecture': 'architecture'
    }
    
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        max_cache_size: int = 50,
        enable_auto_discovery: bool = True
    ):
        """
        Inicializa el registry.
        
        Args:
            base_dir: Directorio base donde buscar papers
            max_cache_size: Tamaño máximo del cache LRU
            enable_auto_discovery: Si True, descubre papers automáticamente
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.max_cache_size = max_cache_size
        self.registry: Dict[str, PaperInfo] = {}
        self.loaded_modules: OrderedDict[str, LoadedModule] = OrderedDict()
        self._lock = threading.RLock()
        
        self.stats = {
            'total_papers': 0,
            'loaded_papers': 0,
            'failed_loads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_load_time': 0.0
        }
        
        if enable_auto_discovery:
            self.discover_papers()
    
    def discover_papers(self):
        """Descubre automáticamente todos los papers."""
        with self._lock:
            logger.info(f"Descubriendo papers... (base_dir={self.base_dir})")
            
            for category, dir_name in self.CATEGORIES.items():
                category_dir = self.base_dir / dir_name
                if not category_dir.exists():
                    continue
                
                for paper_file in category_dir.glob("paper_*.py"):
                    def _register():
                        return self._register_paper(paper_file, category)
                    
                    _, error = safe_execute(_register, default_value=None, log_errors=False)
                    
                    if error:
                        logger.warning(
                            "Error al registrar paper",
                            file=str(paper_file),
                            error=str(error)
                        )
            
            self.stats['total_papers'] = len(self.registry)
            logger.info(
                "Descubrimiento completado",
                total_papers=self.stats['total_papers']
            )
    
    def _register_paper(self, paper_file: Path, category: str) -> None:
        """
        Registra un paper en el registry.
        
        Args:
            paper_file: Ruta al archivo del paper
            category: Categoría del paper
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not isinstance(paper_file, Path):
            raise ValueError(f"paper_file debe ser Path, recibido: {type(paper_file)}")
        
        if not paper_file.exists():
            raise ValueError(f"paper_file no existe: {paper_file}")
        
        if not paper_file.is_file():
            raise ValueError(f"paper_file no es un archivo: {paper_file}")
        
        if not isinstance(category, str) or not category:
            raise ValueError(f"category debe ser un string no vacío, recibido: {category}")
        
        if category not in self.CATEGORIES:
            logger.warning(
                "Categoría no reconocida",
                category=category,
                file=str(paper_file),
                valid_categories=list(self.CATEGORIES.keys())
            )
        
        paper_id = paper_file.stem.replace('paper_', '')
        
        if not paper_id:
            raise ValueError(f"paper_id no puede estar vacío después de procesar: {paper_file}")
        
        if paper_id in self.registry:
            existing_info = self.registry[paper_id]
            logger.warning(
                "Paper ya registrado, sobrescribiendo",
                paper_id=paper_id,
                old_path=str(existing_info.module_path),
                new_path=str(paper_file)
            )
        
        module_name = paper_file.stem
        
        info = PaperInfo(
            paper_id=paper_id,
            paper_name=paper_id,
            module_path=paper_file,
            module_name=module_name,
            category=category
        )
        
        self.registry[paper_id] = info
    
    def list_papers(
        self,
        category: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[PaperInfo]:
        """
        Lista todos los papers registrados.
        
        Args:
            category: Filtrar por categoría
            enabled_only: Solo papers habilitados
        
        Returns:
            Lista de PaperInfo
        """
        with self._lock:
            papers = list(self.registry.values())
            
            if category:
                papers = [p for p in papers if p.category == category]
            
            if enabled_only:
                papers = [p for p in papers if p.enabled]
            
            return papers
    
    def get_paper_info(self, paper_id: str) -> Optional[PaperInfo]:
        """
        Obtiene información de un paper.
        
        Args:
            paper_id: ID del paper
        
        Returns:
            PaperInfo o None si no existe
        
        Raises:
            ValueError: Si paper_id está vacío o es None
        """
        if not paper_id or not isinstance(paper_id, str):
            raise ValueError("paper_id no puede estar vacío o ser None")
        
        return self.registry.get(paper_id)
    
    def load_paper(
        self,
        paper_id: str,
        config: Optional[BasePaperConfig] = None,
        force_reload: bool = False
    ) -> Optional[BasePaperModule]:
        """
        Carga un paper.
        
        Args:
            paper_id: ID del paper
            config: Configuración (opcional)
            force_reload: Si True, fuerza recarga
        
        Returns:
            Instancia del módulo o None si falla
        
        Raises:
            ValueError: Si paper_id está vacío o es None
        """
        if not paper_id or not isinstance(paper_id, str):
            raise ValueError("paper_id no puede estar vacío o ser None")
        
        with self._lock:
            if paper_id in self.loaded_modules and not force_reload:
                module = self.loaded_modules[paper_id]
                self.loaded_modules.move_to_end(paper_id)
                self.stats['cache_hits'] += 1
                
                if module.loaded and module.instance is not None:
                    info = self.registry.get(paper_id)
                    if info:
                        info.load_count += 1
                        info.last_loaded = time.time()
                    return module.instance
                else:
                    self.stats['cache_misses'] += 1
            else:
                self.stats['cache_misses'] += 1
            
            info = self.registry.get(paper_id)
            if not info:
                logger.error(f"Paper no encontrado: {paper_id}")
                return None
            
            if not info.enabled:
                logger.warning(f"Paper deshabilitado: {paper_id}")
                return None
            
            start_time = time.time()
            
            def _load():
                return self._load_paper_module(info, config)
            
            loaded, error = safe_execute(_load, default_value=None, log_errors=False)
            
            if error:
                self.stats['failed_loads'] += 1
                info.error_count += 1
                info.last_error = str(error)
                logger.error(
                    "Excepción al cargar paper",
                    paper_id=paper_id,
                    error=str(error)
                )
                return None
            
            if not loaded:
                self.stats['failed_loads'] += 1
                return None
            
            load_time = time.time() - start_time
            
            if loaded.loaded:
                self._evict_if_needed()
                self.loaded_modules[paper_id] = loaded
                self.loaded_modules.move_to_end(paper_id)
                
                info.load_count += 1
                info.last_loaded = time.time()
                self.stats['loaded_papers'] += 1
                self.stats['total_load_time'] += load_time
                
                logger.info(
                    "Paper cargado",
                    paper_id=paper_id,
                    load_time=f"{load_time:.3f}s"
                )
                
                return loaded.instance
            else:
                self.stats['failed_loads'] += 1
                if loaded.error:
                    info.error_count += 1
                    info.last_error = loaded.error
                    logger.error(
                        "Error al cargar paper",
                        paper_id=paper_id,
                        error=loaded.error
                    )
                return None
    
    def _load_paper_module(
        self,
        info: PaperInfo,
        config: Optional[BasePaperConfig]
    ) -> LoadedModule:
        """
        Carga un módulo de paper.
        
        Args:
            info: Información del paper a cargar
            config: Configuración opcional para el módulo
        
        Returns:
            LoadedModule con el módulo cargado o información de error
        """
        if info is None:
            raise ValueError("info no puede ser None")
        
        if not isinstance(info.module_path, Path) or not info.module_path.exists():
            loaded = LoadedModule(info=info, config_class=None, module_class=None)
            loaded.error = f"Ruta de módulo no existe: {info.module_path}"
            return loaded
        
        loaded = LoadedModule(info=info, config_class=None, module_class=None)
        
        def _load_module() -> Tuple[Optional[Tuple[Type[BasePaperConfig], Type[BasePaperModule], BasePaperModule]], Optional[str]]:
            """Función interna para cargar el módulo."""
            spec = importlib.util.spec_from_file_location(
                info.module_name,
                info.module_path
            )
            if spec is None or spec.loader is None:
                return None, "No se pudo crear spec del módulo"
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[info.module_name] = module
            spec.loader.exec_module(module)
            
            config_class: Optional[Type[BasePaperConfig]] = None
            module_class: Optional[Type[BasePaperModule]] = None
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePaperConfig) and
                    attr != BasePaperConfig):
                    if config_class is not None:
                        logger.warning(
                            "Múltiples clases Config encontradas, usando la última",
                            paper_id=info.paper_id,
                            class_name=attr_name
                        )
                    config_class = attr
                    info.config_class = attr_name
                if (isinstance(attr, type) and
                    issubclass(attr, BasePaperModule) and
                    attr != BasePaperModule):
                    if module_class is not None:
                        logger.warning(
                            "Múltiples clases Module encontradas, usando la última",
                            paper_id=info.paper_id,
                            class_name=attr_name
                        )
                    module_class = attr
                    info.module_class = attr_name
            
            if config_class is None:
                return None, "No se encontró clase Config que herede de BasePaperConfig"
            
            if module_class is None:
                return None, "No se encontró clase Module que herede de BasePaperModule"
            
            if config is None:
                config = config_class()
            elif not isinstance(config, config_class):
                return None, f"Config proporcionado no es instancia de {config_class.__name__}"
            
            instance = module_class(config)
            if not isinstance(instance, BasePaperModule):
                return None, f"Instancia creada no es BasePaperModule: {type(instance)}"
            
            return (config_class, module_class, instance), None
        
        result, error = safe_execute(_load_module, default_value=None, log_errors=False)
        
        if error:
            loaded.error = str(error)
            logger.error(
                "Error al cargar módulo",
                paper_id=info.paper_id,
                error=str(error),
                error_type=type(error).__name__
            )
            return loaded
        
        if result is None:
            loaded.error = "Error desconocido al cargar módulo"
            return loaded
        
        module_result, module_error = result
        
        if module_error is not None or module_result is None:
            error_msg = module_error if module_error else "Error desconocido al cargar módulo"
            loaded.error = error_msg
            logger.error(f"Error interno al cargar módulo (paper_id={info.paper_id}): {error_msg}")
            return loaded
        
        if not isinstance(module_result, tuple) or len(module_result) != 3:
            loaded.error = f"Resultado inválido del módulo: esperado tupla de 3 elementos, recibido {type(module_result)}"
            return loaded
        
        config_class, module_class, instance = module_result
        
        if not isinstance(config_class, type) or not issubclass(config_class, BasePaperConfig):
            loaded.error = f"config_class inválido: {type(config_class)}"
            return loaded
        
        if not isinstance(module_class, type) or not issubclass(module_class, BasePaperModule):
            loaded.error = f"module_class inválido: {type(module_class)}"
            return loaded
        
        if not isinstance(instance, BasePaperModule):
            loaded.error = f"instance inválido: {type(instance)}"
            return loaded
        
        loaded.config_class = config_class
        loaded.module_class = module_class
        loaded.instance = instance
        loaded.loaded = True
        
        return loaded
    
    def _evict_if_needed(self):
        """Evicta módulos del cache si es necesario."""
        while len(self.loaded_modules) >= self.max_cache_size:
            oldest_key = next(iter(self.loaded_modules))
            del self.loaded_modules[oldest_key]
            logger.debug("Módulo evictado del cache", paper_id=oldest_key)
    
    def unload_paper(self, paper_id: str) -> None:
        """
        Descarga un paper del cache.
        
        Args:
            paper_id: ID del paper
        
        Raises:
            ValueError: Si paper_id está vacío o es None
        """
        if not paper_id or not isinstance(paper_id, str):
            raise ValueError("paper_id no puede estar vacío o ser None")
        
        with self._lock:
            if paper_id in self.loaded_modules:
                del self.loaded_modules[paper_id]
                logger.info(f"Paper descargado: {paper_id}")
    
    def clear_cache(self):
        """Limpia todo el cache."""
        with self._lock:
            self.loaded_modules.clear()
            logger.info("Cache limpiado")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registry."""
        with self._lock:
            cache_hit_rate = 0.0
            total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
            if total_requests > 0:
                cache_hit_rate = self.stats['cache_hits'] / total_requests
            
            avg_load_time = 0.0
            if self.stats['loaded_papers'] > 0:
                avg_load_time = self.stats['total_load_time'] / self.stats['loaded_papers']
            
            return {
                **self.stats,
                'cache_hit_rate': cache_hit_rate,
                'avg_load_time': avg_load_time,
                'cached_papers': len(self.loaded_modules),
                'max_cache_size': self.max_cache_size
            }
    
    def search_papers(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[PaperInfo]:
        """
        Busca papers.
        
        Args:
            query: Texto a buscar en nombres
            category: Filtrar por categoría
        
        Returns:
            Lista de papers que coinciden
        """
        papers = list(self.registry.values())
        
        if category:
            papers = [p for p in papers if p.category == category]
        
        if query:
            query_lower = query.lower()
            papers = [
                p for p in papers
                if query_lower in p.paper_id.lower() or
                   query_lower in p.paper_name.lower()
            ]
        
        return sorted(papers, key=lambda p: p.load_count, reverse=True)


_global_registry: Optional[PaperRegistry] = None


def get_registry(
    base_dir: Optional[Union[str, Path]] = None,
    **kwargs: Any
) -> PaperRegistry:
    """
    Obtiene el registry global (singleton).
    
    Args:
        base_dir: Directorio base
        **kwargs: Argumentos adicionales para PaperRegistry
    
    Returns:
        Instancia del registry
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = PaperRegistry(base_dir, **kwargs)
    
    return _global_registry

