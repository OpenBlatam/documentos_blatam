#!/usr/bin/env python3
"""
Base Paper Classes - Clases Base para Papers (Production-Ready)
================================================================

Clases base mejoradas para Config y Module de papers con validaciones,
manejo de errores y funcionalidades adicionales para producción.

Mejoras con librerías modernas:
- Pydantic para validación de configuración
- Structlog para logging estructurado
- Type hints mejorados
- Mejor serialización con orjson
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List, Union, Callable
from collections import OrderedDict
from functools import lru_cache
import torch
import torch.nn as nn
from pathlib import Path
import time
import threading

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
    from pydantic import ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    from dataclasses import dataclass

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

import json

try:
    from .utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


if PYDANTIC_AVAILABLE:
    class BasePaperConfig(BaseModel):
        """
        Clase base para configuraciones de papers con validación usando Pydantic.
        
        Attributes:
            hidden_dim: Dimensión de los hidden states (default: 512)
        """
        model_config = ConfigDict(
            validate_assignment=True,
            frozen=False,
            extra='forbid',
            str_strip_whitespace=True,
        )
        
        hidden_dim: int = Field(
            default=512,
            ge=1,
            le=32768,
            description="Dimensión de los hidden states"
        )
        
        @field_validator('hidden_dim')
        @classmethod
        def validate_hidden_dim(cls, v: int) -> int:
            """Valida hidden_dim."""
            if v <= 0:
                raise ValueError(f"hidden_dim debe ser > 0, recibido: {v}")
            if v % 2 != 0 and v < 64:
                logger.warning("hidden_dim puede causar problemas en divisiones por 2", hidden_dim=v)
            return v
        
        def to_dict(self) -> Dict[str, Any]:
            """Convierte config a dict."""
            return self.model_dump(exclude_none=True)
        
        @classmethod
        def from_dict(cls, config_dict: Dict[str, Any]) -> 'BasePaperConfig':
            """Crea una instancia desde un diccionario."""
            return cls(**config_dict)
        
        def save(self, path: Union[str, Path]):
            """Guarda la configuración en un archivo JSON."""
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = self.to_dict()
            if ORJSON_AVAILABLE:
                with open(path, 'wb') as f:
                    f.write(orjson.dumps(config_dict, option=orjson.OPT_INDENT_2))
            else:
                with open(path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            
            logger.info("Configuración guardada", path=str(path))
        
        @classmethod
        def load(cls, path: Union[str, Path]) -> 'BasePaperConfig':
            """Carga la configuración desde un archivo JSON."""
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"Configuración no encontrada en {path}")
            
            if ORJSON_AVAILABLE:
                with open(path, 'rb') as f:
                    config_dict = orjson.loads(f.read())
            else:
                with open(path, 'r') as f:
                    config_dict = json.load(f)
            
            return cls.from_dict(config_dict)
else:
    @dataclass
    class BasePaperConfig:
        """
        Clase base para configuraciones de papers con validación (fallback sin Pydantic).
        
        Attributes:
            hidden_dim: Dimensión de los hidden states (default: 512)
        """
        hidden_dim: int = 512
        
        def __post_init__(self):
            """Valida la configuración después de la inicialización."""
            self.validate()
        
        def validate(self):
            """Valida que los valores de configuración sean válidos."""
            if self.hidden_dim <= 0:
                raise ValueError(f"hidden_dim debe ser > 0, recibido: {self.hidden_dim}")
            if self.hidden_dim % 2 != 0 and self.hidden_dim < 64:
                logger.warning(f"hidden_dim={self.hidden_dim} puede causar problemas en divisiones por 2")
        
        def to_dict(self) -> Dict[str, Any]:
            """Convierte config a dict."""
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        
        @classmethod
        def from_dict(cls, config_dict: Dict[str, Any]) -> 'BasePaperConfig':
            """Crea una instancia desde un diccionario."""
            return cls(**config_dict)
        
        def save(self, path: Union[str, Path]):
            """Guarda la configuración en un archivo JSON."""
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            config_dict = self.to_dict()
            if ORJSON_AVAILABLE:
                with open(path, 'wb') as f:
                    f.write(orjson.dumps(config_dict, option=orjson.OPT_INDENT_2))
            else:
                with open(path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            logger.info(f"Configuración guardada en {path}")
        
        @classmethod
        def load(cls, path: Union[str, Path]) -> 'BasePaperConfig':
            """Carga la configuración desde un archivo JSON."""
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"Configuración no encontrada en {path}")
            
            if ORJSON_AVAILABLE:
                with open(path, 'rb') as f:
                    config_dict = orjson.loads(f.read())
            else:
                with open(path, 'r') as f:
                    config_dict = json.load(f)
            
            return cls.from_dict(config_dict)


class ModelError(Exception):
    """Excepción base para errores del modelo."""
    pass


class ValidationError(ModelError):
    """Excepción para errores de validación."""
    pass


class ConfigurationError(ModelError):
    """Excepción para errores de configuración."""
    pass


class BasePaperModule(nn.Module, ABC):
    """
    Clase base mejorada para módulos de papers (Production-Ready).
    
    Incluye:
    - Validación de inputs
    - Manejo de errores robusto
    - Métodos de utilidad para producción
    - Serialización de modelos
    - Métricas y logging mejorados
    
    Todos los papers deben heredar de esta clase.
    """
    
    def __init__(self, config: BasePaperConfig):
        """
        Inicializa el módulo base.
        
        Args:
            config: Configuración del módulo
        
        Raises:
            ConfigurationError: Si la configuración no es válida
        """
        super().__init__()
        if not isinstance(config, BasePaperConfig):
            raise ConfigurationError(
                f"config debe ser instancia de BasePaperConfig, recibido: {type(config)}"
            )
        
        self.config = config
        self._metrics: Dict[str, Any] = {}
        self._forward_count = 0
        self._device: Optional[torch.device] = None
        self._dtype: Optional[torch.dtype] = None
        self._gradient_checkpointing = False
        self._cache_enabled = True
        self._cache: OrderedDict = OrderedDict()
        self._max_cache_size = 10
        self._lock = threading.RLock()
        self._training_mode = True
        
        logger.info(
            "Módulo inicializado",
            module_name=self.__class__.__name__,
            config=config.to_dict()
        )
    
    @abstractmethod
    def forward(self, hidden_states: torch.Tensor, **kwargs: Any) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass del paper.
        
        Args:
            hidden_states: Tensor de shape [batch_size, seq_len, hidden_dim]
            **kwargs: Argumentos adicionales específicos del modelo
        
        Returns:
            Tuple (output, metadata) donde:
            - output: Tensor procesado de shape [batch_size, seq_len, hidden_dim]
            - metadata: Diccionario con métricas e información adicional
        """
        pass
    
    def validate_inputs(self, hidden_states: torch.Tensor, **kwargs: Any) -> None:
        """
        Valida los inputs del forward pass.
        
        Args:
            hidden_states: Tensor a validar
            **kwargs: Argumentos adicionales a validar
        
        Raises:
            ValidationError: Si los inputs no son válidos
            TypeError: Si los tipos no son correctos
        """
        if not isinstance(hidden_states, torch.Tensor):
            raise TypeError(f"hidden_states debe ser torch.Tensor, recibido: {type(hidden_states)}")
        
        if hidden_states.dim() != 3:
            raise ValidationError(
                f"hidden_states debe tener 3 dimensiones [batch, seq, hidden_dim], "
                f"recibido shape: {hidden_states.shape}"
            )
        
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        if batch_size == 0:
            raise ValidationError("batch_size debe ser > 0")
        
        if seq_len == 0:
            raise ValidationError("seq_len debe ser > 0")
        
        if hidden_dim != self.config.hidden_dim:
            raise ValidationError(
                f"hidden_dim del tensor ({hidden_dim}) no coincide con config.hidden_dim "
                f"({self.config.hidden_dim})"
            )
        
        if torch.isnan(hidden_states).any():
            raise ValidationError("hidden_states contiene NaN")
        
        if torch.isinf(hidden_states).any():
            raise ValidationError("hidden_states contiene Inf")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información del modelo.
        
        Returns:
            Diccionario con información del modelo
        """
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'model_name': self.__class__.__name__,
            'config': self.config.to_dict(),
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'non_trainable_parameters': total_params - trainable_params,
            'forward_count': self._forward_count,
            'device': str(self._device) if self._device else 'cpu',
            'dtype': str(self._dtype) if self._dtype else 'unknown'
        }
    
    def count_parameters(self, trainable_only: bool = False) -> int:
        """
        Cuenta el número de parámetros del modelo.
        
        Args:
            trainable_only: Si True, solo cuenta parámetros entrenables
        
        Returns:
            Número de parámetros
        """
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())
    
    def _save_model_internal(self, path: Path, include_config: bool):
        """Implementación interna de save_model para usar con retry."""
        checkpoint = {
            'model_state_dict': self.state_dict(),
            'model_class': self.__class__.__name__,
            'model_info': self.get_model_info()
        }
        
        torch.save(checkpoint, path)
        
        if include_config:
            config_path = path.parent / f"{path.stem}_config.json"
            self.config.save(config_path)
    
    def save_model(self, path: Union[str, Path], include_config: bool = True):
        """
        Guarda el modelo completo.
        
        Args:
            path: Ruta donde guardar el modelo
            include_config: Si True, guarda también la configuración
        
        Raises:
            IOError: Si hay un error al guardar
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            from .error_handling import retry, RetryStrategy
            
            @retry(
                max_attempts=3,
                delay=0.5,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                exceptions=(IOError, OSError, RuntimeError)
            )
            def _save_with_retry():
                self._save_model_internal(path, include_config)
            
            _save_with_retry()
            logger.info("Modelo guardado", path=str(path), include_config=include_config)
        except Exception as e:
            logger.error(
                "Error al guardar modelo",
                path=str(path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise IOError(f"Error al guardar modelo en {path}: {e}") from e
    
    @classmethod
    def _load_model_internal(cls, path: Path, config: Optional[BasePaperConfig]):
        """Implementación interna de load_model para usar con retry."""
        checkpoint = torch.load(path, map_location='cpu')
        
        if config is None:
            config_path = path.parent / f"{path.stem}_config.json"
            if config_path.exists():
                config = BasePaperConfig.load(config_path)
            else:
                raise ConfigurationError(
                    f"Configuración no encontrada en {config_path}. "
                    "Proporciona config explícitamente."
                )
        
        model = cls(config)
        model.load_state_dict(checkpoint['model_state_dict'])
        return model
    
    @classmethod
    def load_model(cls, path: Union[str, Path], config: Optional[BasePaperConfig] = None):
        """
        Carga un modelo guardado.
        
        Args:
            path: Ruta del modelo guardado
            config: Configuración (si no se proporciona, se intenta cargar desde archivo)
        
        Returns:
            Instancia del modelo cargado
        
        Raises:
            FileNotFoundError: Si el modelo no existe
            ConfigurationError: Si hay un error con la configuración
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Modelo no encontrado en {path}")
        
        try:
            from .error_handling import retry, RetryStrategy
            
            @retry(
                max_attempts=3,
                delay=0.5,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                exceptions=(IOError, OSError, RuntimeError, KeyError)
            )
            def _load_with_retry():
                return cls._load_model_internal(path, config)
            
            model = _load_with_retry()
            logger.info("Modelo cargado", path=str(path), model_class=cls.__name__)
            return model
        except Exception as e:
            logger.error(
                "Error al cargar modelo",
                path=str(path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del módulo.
        
        Returns:
            Diccionario con métricas acumuladas
        """
        return {
            **self._metrics,
            'forward_count': self._forward_count,
            'model_info': self.get_model_info()
        }
    
    def reset_metrics(self):
        """Resetea todas las métricas."""
        self._metrics.clear()
        self._forward_count = 0
        logger.debug("Métricas reseteadas", module_name=self.__class__.__name__)
    
    def _update_metrics(self, **kwargs):
        """
        Actualiza métricas internas.
        
        Args:
            **kwargs: Métricas a actualizar
        """
        self._metrics.update(kwargs)
        self._forward_count += 1
    
    def to_device(self, device: Union[str, torch.device]):
        """
        Mueve el modelo a un dispositivo específico.
        
        Args:
            device: Dispositivo destino ('cpu', 'cuda', 'cuda:0', etc.)
        """
        self._device = torch.device(device) if isinstance(device, str) else device
        super().to(self._device)
        logger.info("Modelo movido a dispositivo", device=str(self._device), module_name=self.__class__.__name__)
    
    def set_dtype(self, dtype: torch.dtype):
        """
        Establece el tipo de dato del modelo.
        
        Args:
            dtype: Tipo de dato (torch.float32, torch.float16, etc.)
        """
        self._dtype = dtype
        super().to(dtype=dtype)
        logger.info("Tipo de dato establecido", dtype=str(dtype), module_name=self.__class__.__name__)
    
    def enable_gradient_checkpointing(self, enable: bool = True):
        """
        Habilita o deshabilita gradient checkpointing para ahorrar memoria.
        
        Args:
            enable: Si True, habilita gradient checkpointing
        """
        self._gradient_checkpointing = enable
        logger.info(
            "Gradient checkpointing",
            enabled=enable,
            module_name=self.__class__.__name__
        )
    
    def enable_cache(self, enable: bool = True, max_size: int = 10):
        """
        Habilita o deshabilita el cache de resultados.
        
        Args:
            enable: Si True, habilita el cache
            max_size: Tamaño máximo del cache (LRU)
        """
        self._cache_enabled = enable
        self._max_cache_size = max_size
        if not enable:
            self._cache.clear()
        logger.info(
            "Cache",
            enabled=enable,
            max_size=max_size,
            module_name=self.__class__.__name__
        )
    
    def _get_cache_key(self, hidden_states: torch.Tensor, **kwargs) -> Optional[str]:
        """
        Genera una clave de cache para los inputs.
        
        Args:
            hidden_states: Tensor de entrada
            **kwargs: Argumentos adicionales
        
        Returns:
            Clave de cache o None si no se puede cachear
        """
        if not self._cache_enabled:
            return None
        
        try:
            key_parts = [
                str(hidden_states.shape),
                str(hidden_states.dtype),
                str(hash(hidden_states.data_ptr()))
            ]
            for k, v in sorted(kwargs.items()):
                if isinstance(v, torch.Tensor):
                    key_parts.append(f"{k}:{v.shape}:{v.data_ptr()}")
                else:
                    key_parts.append(f"{k}:{v}")
            return hash(tuple(key_parts))
        except Exception:
            return None
    
    def _get_from_cache(self, cache_key: str) -> Optional[Tuple[torch.Tensor, Dict[str, Any]]]:
        """Obtiene un resultado del cache."""
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, result: Tuple[torch.Tensor, Dict[str, Any]]):
        """Añade un resultado al cache."""
        with self._lock:
            if len(self._cache) >= self._max_cache_size:
                self._cache.popitem(last=False)
            self._cache[cache_key] = result
    
    def clear_cache(self):
        """Limpia el cache de resultados."""
        with self._lock:
            self._cache.clear()
        logger.debug("Cache limpiado", module_name=self.__class__.__name__)
    
    def train(self, mode: bool = True):
        """
        Establece el modo de entrenamiento o evaluación.
        
        Args:
            mode: Si True, modo entrenamiento; si False, modo evaluación
        """
        self._training_mode = mode
        super().train(mode)
        if not mode:
            self.clear_cache()
        return self
    
    def eval(self):
        """Establece el modelo en modo evaluación."""
        return self.train(False)
    
    def forward_with_cache(
        self,
        hidden_states: torch.Tensor,
        use_cache: bool = True,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con soporte de cache opcional.
        
        Args:
            hidden_states: Tensor de entrada
            use_cache: Si True, usa cache si está disponible
            **kwargs: Argumentos adicionales
        
        Returns:
            Tuple (output, metadata)
        """
        cache_key = None
        if use_cache and self._cache_enabled and not self._training_mode:
            cache_key = self._get_cache_key(hidden_states, **kwargs)
            if cache_key is not None:
                cached = self._get_from_cache(cache_key)
                if cached is not None:
                    logger.debug("Cache hit", module_name=self.__class__.__name__)
                    return cached
        
        if self._gradient_checkpointing and self.training:
            output, metadata = torch.utils.checkpoint.checkpoint(
                self.forward,
                hidden_states,
                use_reentrant=False,
                **kwargs
            )
        else:
            output, metadata = self.forward(hidden_states, **kwargs)
        
        if cache_key is not None and not self._training_mode:
            self._add_to_cache(cache_key, (output, metadata))
        
        return output, metadata
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Diccionario con estadísticas del cache
        """
        return {
            'cache_enabled': self._cache_enabled,
            'cache_size': len(self._cache),
            'max_cache_size': self._max_cache_size,
            'cache_keys': list(self._cache.keys()) if len(self._cache) < 20 else f"{len(self._cache)} items"
        }
    
    def __repr__(self) -> str:
        """Representación del modelo."""
        info = self.get_model_info()
        cache_stats = self.get_cache_stats()
        return (
            f"{self.__class__.__name__}(\n"
            f"  config={self.config.to_dict()},\n"
            f"  parameters={info['total_parameters']:,},\n"
            f"  forward_count={self._forward_count},\n"
            f"  cache_size={cache_stats['cache_size']}/{cache_stats['max_cache_size']}\n"
            f")"
        )
