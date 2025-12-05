#!/usr/bin/env python3
"""
Gestor de Configuración Centralizado
=====================================

Sistema unificado para gestionar configuraciones de todos los módulos.

Este módulo proporciona:
- Gestión centralizada de configuraciones
- Factory function para crear módulos desde configuraciones
- Validación de configuraciones
- Soporte para múltiples formatos (JSON, YAML, TOML, Hydra)
- Variables de entorno
- Funciones de utilidad para verificar disponibilidad

Ejemplo:
    >>> manager = get_config_manager()
    >>> config = manager.get_config(ModuleType.MEMORY)
    >>> module = create_from_config(ModuleType.MEMORY, manager)
"""

__version__ = '2.0.0'

from typing import Dict, Any, Optional, Union, Tuple, List
from pathlib import Path
import os
import json
import yaml
from dataclasses import dataclass, asdict
from enum import Enum

from .utils import (
    load_config_from_yaml,
    load_config_from_toml,
    load_hydra_config,
    load_environment_variables,
    YAML_AVAILABLE,
    TOML_AVAILABLE,
    HYDRA_AVAILABLE,
    DOTENV_AVAILABLE,
    setup_logger
)
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# Module Types and Config Classes
class ModuleType(str, Enum):
    """Tipos de módulos disponibles."""
    MEMORY = "memory"
    REDUNDANCY = "redundancy"
    SORA = "sora"
    CHAT = "chat"
    PIPELINE = "pipeline"


@dataclass
class MemoryConfig:
    """Configuración para módulo de memoria."""
    memory_dim: int = 512
    max_memory_size: int = 10000
    retrieval_k: int = 10
    enable_cache: bool = True
    enable_persistence: bool = True
    enable_compression: bool = False
    enable_prioritization: bool = True
    persistence_path: Optional[str] = None


@dataclass
class RedundancyConfig:
    """Configuración para módulo de redundancia."""
    similarity_threshold: float = 0.85
    redundancy_detection_method: str = "cosine"
    enable_caching: bool = True
    enable_adaptive_threshold: bool = False
    cache_size: int = 5000


@dataclass
class SoraConfig:
    """Configuración para módulo Sora."""
    hidden_dim: int = 512
    video_length: int = 16
    resolution: tuple = (512, 512)
    fps: int = 24
    enable_memory: bool = True
    enable_redundancy: bool = True


@dataclass
class ChatConfig:
    """Configuración para módulo de chat."""
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    enable_memory: bool = True


@dataclass
class PipelineConfig:
    """Configuración para pipeline integrado."""
    enable_memory: bool = True
    enable_redundancy: bool = True
    enable_video: bool = False
    enable_chat: bool = False
    memory_config: Optional[MemoryConfig] = None
    redundancy_config: Optional[RedundancyConfig] = None
    sora_config: Optional[SoraConfig] = None
    chat_config: Optional[ChatConfig] = None


class ConfigManager:
    """
    Gestor centralizado de configuraciones.
    
    Permite cargar, guardar y gestionar configuraciones
    de todos los módulos desde un solo lugar.
    
    Soporta múltiples formatos y fuentes:
    - Archivos YAML, TOML, JSON
    - Variables de entorno
    - Hydra
    - Configuraciones específicas por módulo
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Inicializa gestor de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        self.config_path = Path(config_path) if config_path else None
        self.config: Dict[str, Any] = {}  # Generic config (for file-based)
        self.configs: Dict[str, Any] = {}  # Module-specific configs
        
        # Configuraciones por defecto para módulos
        self.default_configs = {
            ModuleType.MEMORY.value: MemoryConfig(),
            ModuleType.REDUNDANCY.value: RedundancyConfig(),
            ModuleType.SORA.value: SoraConfig(),
            ModuleType.CHAT.value: ChatConfig(),
            ModuleType.PIPELINE.value: PipelineConfig()
        }
        
        if DOTENV_AVAILABLE:
            load_environment_variables()
        
        # Cargar configuración si existe
        if self.config_path and self.config_path.exists():
            self.load_config_file(self.config_path)
        else:
            # Usar configuraciones por defecto para módulos
            self.configs = {k: asdict(v) for k, v in self.default_configs.items()}
    
    def load_config_file(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Carga configuración desde un archivo (método genérico).
        
        Args:
            path: Ruta al archivo de configuración
        
        Returns:
            Diccionario con la configuración
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.yaml' or suffix == '.yml':
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML no está instalado. Instala con: pip install pyyaml")
            
            def _load_yaml():
                return load_config_from_yaml(path)
            
            result, error = safe_execute(_load_yaml, default_value=None, log_errors=True)
            if error:
                raise IOError(f"Error cargando YAML: {error}")
            self.config = result
            # Also update module configs if file contains module configs
            if isinstance(result, dict) and any(k in result for k in [e.value for e in ModuleType]):
                self.configs.update({k: v for k, v in result.items() if k in [e.value for e in ModuleType]})
        
        elif suffix == '.toml':
            if not TOML_AVAILABLE:
                raise ImportError("toml no está instalado. Instala con: pip install toml")
            
            def _load_toml():
                return load_config_from_toml(path)
            
            result, error = safe_execute(_load_toml, default_value=None, log_errors=True)
            if error:
                raise IOError(f"Error cargando TOML: {error}")
            self.config = result
            if isinstance(result, dict) and any(k in result for k in [e.value for e in ModuleType]):
                self.configs.update({k: v for k, v in result.items() if k in [e.value for e in ModuleType]})
        
        elif suffix == '.json':
            def _load_json():
                if ORJSON_AVAILABLE:
                    with open(path, 'rb') as f:
                        return orjson.loads(f.read())
                else:
                    with open(path, 'r') as f:
                        return json.load(f)
            
            result, error = safe_execute(_load_json, default_value=None, log_errors=True)
            if error:
                raise IOError(f"Error cargando JSON: {error}")
            self.config = result
            if isinstance(result, dict) and any(k in result for k in [e.value for e in ModuleType]):
                self.configs.update({k: v for k, v in result.items() if k in [e.value for e in ModuleType]})
        
        else:
            raise ValueError(f"Formato de archivo no soportado: {suffix}")
        
        return self.config
    
    def load_config(self, filepath: Optional[Union[str, Path]] = None) -> bool:
        """
        Carga configuración desde archivo (método de compatibilidad para módulos).
        
        Args:
            filepath: Ruta del archivo (opcional, usa self.config_path si no se proporciona)
        
        Returns:
            True si se cargó exitosamente
        """
        path = Path(filepath) if filepath else self.config_path
        
        if not path or not path.exists():
            logger.warning(f"Archivo de configuración no encontrado: {path}")
            return False
        
        try:
            self.load_config_file(path)
            logger.info(f"Configuración cargada desde {path}")
            return True
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return False
    
    def get_config(self, module_type: Union[ModuleType, str]) -> Dict[str, Any]:
        """
        Obtiene configuración de un módulo.
        
        Args:
            module_type: Tipo de módulo
        
        Returns:
            Diccionario con configuración
        """
        module_key = module_type.value if isinstance(module_type, ModuleType) else module_type
        
        if module_key not in self.configs:
            if module_key in self.default_configs:
                self.configs[module_key] = asdict(self.default_configs[module_key])
            else:
                logger.warning(f"Configuración no encontrada para {module_key}, usando defaults")
                return {}
        
        return self.configs[module_key]
    
    def set_config(self, module_type: Union[ModuleType, str], config: Dict[str, Any]):
        """
        Establece configuración de un módulo.
        
        Args:
            module_type: Tipo de módulo
            config: Diccionario con configuración
        """
        module_key = module_type.value if isinstance(module_type, ModuleType) else module_type
        self.configs[module_key] = config
        logger.info(f"Configuración actualizada para {module_key}")
    
    def update_config(self, module_type: Union[ModuleType, str], **kwargs):
        """
        Actualiza configuración parcialmente.
        
        Args:
            module_type: Tipo de módulo
            **kwargs: Valores a actualizar
        """
        module_key = module_type.value if isinstance(module_type, ModuleType) else module_type
        
        if module_key not in self.configs:
            self.configs[module_key] = {}
        
        self.configs[module_key].update(kwargs)
        logger.info(f"Configuración parcialmente actualizada para {module_key}")
    
    def save_config(self, filepath: Optional[Union[str, Path]] = None, format: str = 'json') -> bool:
        """
        Guarda configuración en archivo.
        
        Args:
            filepath: Ruta del archivo (opcional, usa self.config_path si no se proporciona)
            format: Formato ('json' o 'yaml')
        
        Returns:
            True si se guardó exitosamente
        """
        path = Path(filepath) if filepath else self.config_path
        
        if not path:
            logger.warning("No se especificó ruta para guardar configuración")
            return False
        
        def _save_config():
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json' or path.suffix == '.json':
                with open(path, 'w') as f:
                    json.dump(self.configs, f, indent=2, default=str)
            elif format == 'yaml' or path.suffix in ['.yaml', '.yml']:
                with open(path, 'w') as f:
                    yaml.dump(self.configs, f, default_flow_style=False)
            else:
                logger.error(f"Formato no soportado: {format}")
                return False
            
            return True
        
        result, error = safe_execute(_save_config, default_value=False, log_errors=False)
        
        if error:
            logger.error(f"Error guardando configuración: {error}")
            return False
        
        if result:
            logger.info(f"Configuración guardada en {path}")
        
        return result
    
    def reset_to_defaults(self, module_type: Optional[Union[ModuleType, str]] = None):
        """
        Resetea configuración a valores por defecto.
        
        Args:
            module_type: Tipo de módulo (opcional, resetea todos si no se especifica)
        """
        if module_type:
            module_key = module_type.value if isinstance(module_type, ModuleType) else module_type
            if module_key in self.default_configs:
                self.configs[module_key] = asdict(self.default_configs[module_key])
                logger.info(f"Configuración reseteada para {module_key}")
        else:
            self.configs = {k: asdict(v) for k, v in self.default_configs.items()}
            logger.info("Todas las configuraciones reseteadas")
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        Obtiene todas las configuraciones.
        
        Returns:
            Diccionario con todas las configuraciones
        """
        return self.configs.copy()
    
    def validate_config(self, module_type: Union[ModuleType, str]) -> Tuple[bool, List[str]]:
        """
        Valida configuración de un módulo.
        
        Args:
            module_type: Tipo de módulo
        
        Returns:
            Tuple (es_válida, lista_de_errores)
        """
        module_key = module_type.value if isinstance(module_type, ModuleType) else module_type
        config = self.get_config(module_key)
        errors = []
        
        if module_key == ModuleType.MEMORY.value:
            if 'memory_dim' in config and config['memory_dim'] <= 0:
                errors.append("memory_dim debe ser > 0")
            if 'max_memory_size' in config and config['max_memory_size'] <= 0:
                errors.append("max_memory_size debe ser > 0")
        
        elif module_key == ModuleType.REDUNDANCY.value:
            if 'similarity_threshold' in config:
                threshold = config['similarity_threshold']
                if not (0.0 <= threshold <= 1.0):
                    errors.append("similarity_threshold debe estar en [0.0, 1.0]")
        
        elif module_key == ModuleType.SORA.value:
            if 'hidden_dim' in config and config['hidden_dim'] <= 0:
                errors.append("hidden_dim debe ser > 0")
            if 'video_length' in config and config['video_length'] <= 0:
                errors.append("video_length debe ser > 0")
        
        return len(errors) == 0, errors
    
    def load_hydra_config(self, config_path: str = "config", config_name: str = "config") -> Dict[str, Any]:
        """
        Carga configuración usando Hydra.
        
        Args:
            config_path: Ruta al directorio de configuración
            config_name: Nombre del archivo de configuración
        
        Returns:
            Diccionario con la configuración
        """
        if not HYDRA_AVAILABLE:
            raise ImportError("Hydra no está instalado. Instala con: pip install hydra-core")
        
        def _load_hydra():
            return load_hydra_config(config_path, config_name)
        
        result, error = safe_execute(_load_hydra, default_value=None, log_errors=True)
        if error:
            raise IOError(f"Error cargando configuración Hydra: {error}")
        self.config = result
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave (puede usar notación de punto, ej: "model.hidden_dim")
            default: Valor por defecto
        
        Returns:
            Valor de configuración o default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave (puede usar notación de punto)
            value: Valor a establecer
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, other: Dict[str, Any]):
        """
        Actualiza la configuración con otro diccionario.
        
        Args:
            other: Diccionario con valores a actualizar
        """
        self._deep_update(self.config, other)
    
    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Actualiza recursivamente un diccionario."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get_from_env(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de variable de entorno.
        
        Args:
            key: Nombre de la variable de entorno
            default: Valor por defecto
        
        Returns:
            Valor de la variable de entorno o default
        """
        return os.getenv(key, default)
    
    def save(self, path: Union[str, Path], format: str = "json"):
        """
        Guarda la configuración en un archivo.
        
        Args:
            path: Ruta donde guardar
            format: Formato ("json", "yaml", "toml")
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            if ORJSON_AVAILABLE:
                with open(path, 'wb') as f:
                    f.write(orjson.dumps(self.config, option=orjson.OPT_INDENT_2))
            else:
                with open(path, 'w') as f:
                    json.dump(self.config, f, indent=2)
        
        elif format == "yaml":
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML no está instalado")
            import yaml
            with open(path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        
        elif format == "toml":
            if not TOML_AVAILABLE:
                raise ImportError("toml no está instalado")
            import toml
            with open(path, 'w') as f:
                toml.dump(self.config, f)
        
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def __getitem__(self, key: str) -> Any:
        """Acceso mediante corchetes."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """Asignación mediante corchetes."""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Verifica si una clave existe."""
        return self.get(key) is not None


# Instancia global
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Union[str, Path]] = None) -> ConfigManager:
    """
    Obtiene instancia global del gestor de configuración.
    
    Args:
        config_path: Ruta al archivo de configuración
    
    Returns:
        Instancia de ConfigManager
    """
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_path)
    
    return _global_config_manager


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene el estado de disponibilidad de todos los módulos soportados.
    
    Returns:
        Diccionario con el estado de disponibilidad de cada módulo.
        
    Example:
        >>> modules = get_available_modules()
        >>> if modules['memory']:
        ...     print("Módulo de memoria disponible")
    """
    availability = {}
    
    # Verificar memory
    def _check_memory():
        from memory import create_memory_system
        return True
    
    result, _ = safe_execute(_check_memory, default_value=False, log_errors=False)
    availability['memory'] = result
    
    # Verificar redundancy
    def _check_redundancy():
        from redundancy import create_redundancy_suppressor
        return True
    
    result, _ = safe_execute(_check_redundancy, default_value=False, log_errors=False)
    availability['redundancy'] = result
    
    # Verificar sora
    def _check_sora():
        from sora import create_video_generator
        return True
    
    result, _ = safe_execute(_check_sora, default_value=False, log_errors=False)
    availability['sora'] = result
    
    # Verificar pipeline
    def _check_pipeline():
        from integration_pipeline import create_integrated_pipeline
        return True
    
    result, _ = safe_execute(_check_pipeline, default_value=False, log_errors=False)
    availability['pipeline'] = result
    
    # Verificar pydantic
    availability['pydantic'] = PYDANTIC_AVAILABLE
    
    return availability


def validate_module_config(module_type: Union[ModuleType, str], config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida una configuración para un módulo específico.
    
    Args:
        module_type: Tipo de módulo a validar
        config: Diccionario con la configuración a validar
    
    Returns:
        Tuple (es_válida, lista_de_errores).
        
    Example:
        >>> config = {'memory_dim': 512, 'max_memory_size': 10000}
        >>> is_valid, errors = validate_module_config(ModuleType.MEMORY, config)
        >>> if not is_valid:
        ...     print(f"Errores: {errors}")
    """
    manager = ConfigManager()
    manager.set_config(module_type, config)
    return manager.validate_config(module_type)


def create_from_config(
    module_type: Union[ModuleType, str],
    config_manager: Optional[ConfigManager] = None
) -> Optional[Any]:
    """
    Factory function para crear instancia de módulo desde configuración.
    
    Args:
        module_type: Tipo de módulo (ModuleType o string)
        config_manager: Gestor de configuración (opcional, usa global si no se proporciona)
    
    Returns:
        Instancia del módulo o None si hay error.
        
    Raises:
        ValueError: Si module_type no es válido.
        
    Example:
        >>> # Crear módulo de memoria desde configuración
        >>> manager = get_config_manager()
        >>> memory_module = create_from_config(ModuleType.MEMORY, manager)
        >>> 
        >>> # Crear pipeline completo
        >>> pipeline = create_from_config("pipeline")
    """
    # Validación de entrada
    if not isinstance(module_type, (ModuleType, str)):
        raise ValueError(f"module_type debe ser ModuleType o str, recibido: {type(module_type).__name__}")
    
    if isinstance(module_type, str):
        module_type_str = module_type.lower()
        if module_type_str not in [e.value for e in ModuleType]:
            raise ValueError(f"module_type debe ser uno de {[e.value for e in ModuleType]}, recibido: {module_type}")
    else:
        module_type_str = module_type.value
    
    if config_manager is None:
        config_manager = get_config_manager()
    
    if not isinstance(config_manager, ConfigManager):
        raise ValueError(f"config_manager debe ser instancia de ConfigManager, recibido: {type(config_manager).__name__}")
    
    config = config_manager.get_config(module_type)
    
    # Validar configuración antes de crear
    is_valid, errors = config_manager.validate_config(module_type)
    if not is_valid:
        logger.warning(f"Configuración tiene errores: {errors}")
    
    try:
        if module_type_str == ModuleType.MEMORY.value:
            from memory import create_memory_system
            return create_memory_system("2506_15841v2", **config)
        
        elif module_type_str == ModuleType.REDUNDANCY.value:
            from redundancy import create_redundancy_suppressor
            return create_redundancy_suppressor("2510_00071", **config)
        
        elif module_type_str == ModuleType.PIPELINE.value:
            from integration_pipeline import create_integrated_pipeline
            return create_integrated_pipeline(**config)
        
        else:
            logger.warning(f"Tipo de módulo no soportado para creación: {module_type_str}")
            return None
    
    except Exception as e:
        logger.error(
            f"Error creando módulo {module_type_str}: {e}",
            exc_info=True,
            module_type=module_type_str
        )
        return None


__all__ = [
    'ConfigManager',
    'ModuleType',
    'MemoryConfig',
    'RedundancyConfig',
    'SoraConfig',
    'ChatConfig',
    'PipelineConfig',
    'get_config_manager',
    'create_from_config',
    'get_available_modules',
    'validate_module_config',
    'PYDANTIC_AVAILABLE',
    '__version__'
]

