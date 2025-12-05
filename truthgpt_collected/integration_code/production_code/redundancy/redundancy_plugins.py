#!/usr/bin/env python3
"""
Sistema de Plugins para Redundancy
===================================

Sistema extensible de plugins para personalizar y extender funcionalidades
del módulo de redundancia.
"""

from typing import Dict, Any, Optional, List, Callable, Type, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import inspect
import time

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class PluginType(Enum):
    """Tipos de plugins disponibles."""
    SIMILARITY_METHOD = "similarity_method"
    CLUSTERING_ALGORITHM = "clustering_algorithm"
    SELECTION_STRATEGY = "selection_strategy"
    PREPROCESSOR = "preprocessor"
    POSTPROCESSOR = "postprocessor"
    METRIC_CALCULATOR = "metric_calculator"
    CUSTOM = "custom"


@dataclass
class PluginMetadata:
    """Metadatos de un plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    """
    Clase base para todos los plugins.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el plugin.
        
        Args:
            config: Configuración del plugin
        """
        self.config = config or {}
        self.metadata = self.get_metadata()
        self.enabled = True
        self.initialized = False
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Retorna los metadatos del plugin."""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Inicializa el plugin.
        
        Returns:
            True si la inicialización fue exitosa
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Valida la configuración del plugin.
        
        Returns:
            True si la configuración es válida
        """
        return True
    
    def cleanup(self):
        """Limpia recursos del plugin."""
        pass


class SimilarityMethodPlugin(BasePlugin):
    """
    Plugin para métodos de similitud personalizados.
    """
    
    @abstractmethod
    def compute_similarity(
        self,
        embeddings: Any,
        **kwargs
    ) -> Any:
        """
        Calcula la similitud entre embeddings.
        
        Args:
            embeddings: Tensor de embeddings
            **kwargs: Argumentos adicionales
        
        Returns:
            Matriz de similitud
        """
        pass


class ClusteringAlgorithmPlugin(BasePlugin):
    """
    Plugin para algoritmos de clustering personalizados.
    """
    
    @abstractmethod
    def cluster(
        self,
        similarity_matrix: Any,
        threshold: float,
        **kwargs
    ) -> List[List[int]]:
        """
        Agrupa items similares.
        
        Args:
            similarity_matrix: Matriz de similitud
            threshold: Umbral de similitud
            **kwargs: Argumentos adicionales
        
        Returns:
            Lista de clusters (cada cluster es una lista de índices)
        """
        pass


class SelectionStrategyPlugin(BasePlugin):
    """
    Plugin para estrategias de selección de representantes.
    """
    
    @abstractmethod
    def select_representatives(
        self,
        clusters: List[List[int]],
        items: Any,
        **kwargs
    ) -> List[int]:
        """
        Selecciona representantes de cada cluster.
        
        Args:
            clusters: Lista de clusters
            items: Items originales
            **kwargs: Argumentos adicionales
        
        Returns:
            Lista de índices de representantes
        """
        pass


class PreprocessorPlugin(BasePlugin):
    """
    Plugin para preprocesamiento de datos.
    """
    
    @abstractmethod
    def preprocess(
        self,
        items: Any,
        **kwargs
    ) -> Any:
        """
        Preprocesa items antes del procesamiento.
        
        Args:
            items: Items a preprocesar
            **kwargs: Argumentos adicionales
        
        Returns:
            Items preprocesados
        """
        pass


class PostprocessorPlugin(BasePlugin):
    """
    Plugin para postprocesamiento de resultados.
    """
    
    @abstractmethod
    def postprocess(
        self,
        items: Any,
        stats: Dict[str, Any],
        **kwargs
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Postprocesa resultados después del procesamiento.
        
        Args:
            items: Items procesados
            stats: Estadísticas del procesamiento
            **kwargs: Argumentos adicionales
        
        Returns:
            Tupla (items postprocesados, stats actualizados)
        """
        pass


class PluginRegistry:
    """
    Registro central de plugins.
    """
    
    def __init__(self):
        """Inicializa el registro."""
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugins_by_type: Dict[PluginType, List[str]] = {
            plugin_type: [] for plugin_type in PluginType
        }
        self._initialized = False
    
    def register(
        self,
        plugin: BasePlugin,
        name: Optional[str] = None
    ) -> bool:
        """
        Registra un plugin.
        
        Args:
            plugin: Instancia del plugin
            name: Nombre opcional (usa metadata.name si no se proporciona)
        
        Returns:
            True si el registro fue exitoso
        """
        def _register():
            plugin_name = name or plugin.metadata.name
            
            if plugin_name in self._plugins:
                logger.warning(f"Plugin '{plugin_name}' ya está registrado, sobrescribiendo")
            
            if not plugin.validate_config():
                logger.error(f"Configuración inválida para plugin '{plugin_name}'")
                return False
            
            if not plugin.initialize():
                logger.error(f"Error inicializando plugin '{plugin_name}'")
                return False
            
            self._plugins[plugin_name] = plugin
            self._plugins_by_type[plugin.metadata.plugin_type].append(plugin_name)
            plugin.initialized = True
            
            logger.info(f"Plugin '{plugin_name}' registrado exitosamente")
            return True
        
        result, error = safe_execute(_register, default_value=False, log_errors=True)
        return result
    
    def unregister(self, name: str) -> bool:
        """
        Desregistra un plugin.
        
        Args:
            name: Nombre del plugin
        
        Returns:
            True si el desregistro fue exitoso
        """
        if name not in self._plugins:
            logger.warning(f"Plugin '{name}' no está registrado")
            return False
        
        plugin = self._plugins[name]
        plugin.cleanup()
        
        plugin_type = plugin.metadata.plugin_type
        if name in self._plugins_by_type[plugin_type]:
            self._plugins_by_type[plugin_type].remove(name)
        
        del self._plugins[name]
        logger.info(f"Plugin '{name}' desregistrado")
        return True
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Obtiene un plugin por nombre.
        
        Args:
            name: Nombre del plugin
        
        Returns:
            Plugin o None si no existe
        """
        return self._plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        Obtiene todos los plugins de un tipo.
        
        Args:
            plugin_type: Tipo de plugin
        
        Returns:
            Lista de plugins
        """
        plugin_names = self._plugins_by_type.get(plugin_type, [])
        return [self._plugins[name] for name in plugin_names if name in self._plugins]
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Lista todos los plugins registrados.
        
        Returns:
            Diccionario con información de plugins
        """
        plugins_info = {}
        for name, plugin in self._plugins.items():
            metadata = plugin.metadata
            plugins_info[name] = {
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'type': metadata.plugin_type.value,
                'enabled': plugin.enabled,
                'initialized': plugin.initialized
            }
        return plugins_info
    
    def clear(self):
        """Limpia todos los plugins registrados."""
        for plugin in self._plugins.values():
            plugin.cleanup()
        self._plugins.clear()
        self._plugins_by_type = {plugin_type: [] for plugin_type in PluginType}


# Instancia global del registro
_global_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """
    Obtiene el registro global de plugins.
    
    Returns:
        Instancia del registro
    """
    return _global_registry


def register_plugin(
    plugin: BasePlugin,
    name: Optional[str] = None
) -> bool:
    """
    Registra un plugin en el registro global.
    
    Args:
        plugin: Instancia del plugin
        name: Nombre opcional
    
    Returns:
        True si el registro fue exitoso
    """
    return _global_registry.register(plugin, name)


def get_plugin(name: str) -> Optional[BasePlugin]:
    """
    Obtiene un plugin por nombre.
    
    Args:
        name: Nombre del plugin
    
    Returns:
        Plugin o None
    """
    return _global_registry.get_plugin(name)


def list_plugins() -> Dict[str, Dict[str, Any]]:
    """
    Lista todos los plugins registrados.
    
    Returns:
        Diccionario con información de plugins
    """
    return _global_registry.list_plugins()


# Plugin de ejemplo: Similarity Method
class JaccardSimilarityPlugin(SimilarityMethodPlugin):
    """Plugin de ejemplo para similitud de Jaccard."""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="jaccard_similarity",
            version="1.0.0",
            description="Método de similitud de Jaccard",
            author="Redundancy Module",
            plugin_type=PluginType.SIMILARITY_METHOD
        )
    
    def initialize(self) -> bool:
        return True
    
    def compute_similarity(self, embeddings: Any, **kwargs) -> Any:
        """
        Calcula similitud de Jaccard (requiere embeddings binarios).
        
        Args:
            embeddings: Tensor de embeddings binarios
            **kwargs: Argumentos adicionales
        
        Returns:
            Matriz de similitud
        """
        import torch
        import torch.nn.functional as F
        
        if not isinstance(embeddings, torch.Tensor):
            embeddings = torch.tensor(embeddings)
        
        embeddings_binary = (embeddings > 0).float()
        
        intersection = torch.matmul(embeddings_binary, embeddings_binary.transpose(-2, -1))
        union = embeddings_binary.sum(dim=-1, keepdim=True) + embeddings_binary.sum(dim=-2, keepdim=True).transpose(-2, -1) - intersection
        
        similarity = intersection / (union + 1e-8)
        return similarity

