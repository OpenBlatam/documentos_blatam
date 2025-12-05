#!/usr/bin/env python3
"""
Utilidades para el código de producción.

Incluye:
- Type hints mejorados
- Funciones de utilidad
- Helpers para validación
- Logging estructurado
- Caching
- Retry logic
- Configuración
"""

from typing import Dict, Any, Optional, Tuple, List, Union, TypeVar, Generic, Callable
from functools import wraps, lru_cache
import torch
from pathlib import Path
import logging

try:
    from typing_extensions import Protocol, runtime_checkable, TypedDict
    TYPING_EXTENSIONS_AVAILABLE = True
except ImportError:
    TYPING_EXTENSIONS_AVAILABLE = False
    Protocol = object
    runtime_checkable = lambda x: x
    TypedDict = dict

try:
    from typeguard import typechecked
    TYPEGUARD_AVAILABLE = True
except ImportError:
    TYPEGUARD_AVAILABLE = False
    def typechecked(func):
        return func

T = TypeVar('T')
Tensor = torch.Tensor


@runtime_checkable
class Configurable(Protocol):
    """Protocolo para objetos configurables."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        ...
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Configurable':
        """Crea desde diccionario."""
        ...


@runtime_checkable
class Savable(Protocol):
    """Protocolo para objetos que se pueden guardar."""
    
    def save(self, path: Union[str, Path]) -> None:
        """Guarda el objeto."""
        ...
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'Savable':
        """Carga el objeto."""
        ...


if TYPING_EXTENSIONS_AVAILABLE:
    class ModelMetadata(TypedDict, total=False):
        """Metadata del modelo."""
        model_name: str
        total_parameters: int
        trainable_parameters: int
        forward_count: int
        device: str
        dtype: str
else:
    ModelMetadata = Dict[str, Any]


@typechecked
def validate_tensor_shape(
    tensor: Tensor,
    expected_shape: Tuple[int, ...],
    name: str = "tensor"
) -> None:
    """
    Valida que un tensor tenga la forma esperada.
    
    Args:
        tensor: Tensor a validar
        expected_shape: Forma esperada
        name: Nombre del tensor para mensajes de error
    
    Raises:
        ValueError: Si la forma no coincide
    """
    if tensor.shape != expected_shape:
        raise ValueError(
            f"{name} debe tener shape {expected_shape}, "
            f"recibido: {tensor.shape}"
        )


@typechecked
def safe_tensor_operation(
    operation: Any,
    *args: Any,
    default_value: Optional[Tensor] = None,
    **kwargs: Any
) -> Optional[Tensor]:
    """
    Ejecuta una operación de tensor de forma segura.
    
    Args:
        operation: Función a ejecutar
        *args: Argumentos posicionales
        default_value: Valor por defecto en caso de error
        **kwargs: Argumentos nombrados
    
    Returns:
        Resultado de la operación o default_value si hay error
    """
    try:
        return operation(*args, **kwargs)
    except Exception:
        return default_value


@typechecked
def get_device_info(device: Union[str, torch.device]) -> Dict[str, Any]:
    """
    Obtiene información sobre un dispositivo.
    
    Args:
        device: Dispositivo
    
    Returns:
        Diccionario con información del dispositivo
    """
    device_obj = torch.device(device) if isinstance(device, str) else device
    
    info = {
        'device': str(device_obj),
        'type': device_obj.type,
    }
    
    if device_obj.type == 'cuda':
        if torch.cuda.is_available():
            info['index'] = device_obj.index
            info['cuda_available'] = True
            info['cuda_device_count'] = torch.cuda.device_count()
        else:
            info['cuda_available'] = False
    
    return info


@typechecked
def format_number(num: Union[int, float], precision: int = 2) -> str:
    """
    Formatea un número para visualización.
    
    Args:
        num: Número a formatear
        precision: Precisión decimal
    
    Returns:
        String formateado
    """
    if isinstance(num, int):
        return f"{num:,}"
    else:
        return f"{num:,.{precision}f}"


try:
    from cachetools import TTLCache, LRUCache, cached
    from cachetools.keys import hashkey
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    def cached(cache=None):
        def decorator(func):
            return func
        return decorator


try:
    from backoff import on_exception, expo
    BACKOFF_AVAILABLE = True
except ImportError:
    BACKOFF_AVAILABLE = False
    def on_exception(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


if CACHETOOLS_AVAILABLE:
    @cached(cache=TTLCache(maxsize=128, ttl=3600))
    def cached_tensor_operation(key: str, operation: Callable, *args, **kwargs):
        """Operación de tensor con cache TTL."""
        return operation(*args, **kwargs)


def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 1.0):
    """
    Decorador para reintentar operaciones que fallan.
    
    Args:
        max_attempts: Número máximo de intentos
        backoff_factor: Factor de espera exponencial
    """
    def decorator(func: Callable) -> Callable:
        if TENACITY_AVAILABLE:
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=backoff_factor)
            )
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
        elif BACKOFF_AVAILABLE:
            @on_exception(expo, Exception, max_tries=max_attempts)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            raise
                        import time
                        time.sleep(backoff_factor * (2 ** attempt))
                return None
        return wrapper
    return decorator


try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def load_environment_variables(env_file: Optional[Union[str, Path]] = None) -> None:
    """
    Carga variables de entorno desde un archivo .env.
    
    Args:
        env_file: Ruta al archivo .env (por defecto busca .env en el directorio actual)
    """
    if DOTENV_AVAILABLE:
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()


try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_config_from_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Carga configuración desde un archivo YAML.
    
    Args:
        path: Ruta al archivo YAML
    
    Returns:
        Diccionario con la configuración
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")
    
    if YAML_AVAILABLE:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    else:
        raise ImportError("PyYAML no está instalado. Instala con: pip install pyyaml")


try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False


def load_config_from_toml(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Carga configuración desde un archivo TOML.
    
    Args:
        path: Ruta al archivo TOML
    
    Returns:
        Diccionario con la configuración
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")
    
    if TOML_AVAILABLE:
        with open(path, 'r') as f:
            return toml.load(f)
    else:
        raise ImportError("toml no está instalado. Instala con: pip install toml")


try:
    from hydra import compose, initialize
    from omegaconf import OmegaConf
    HYDRA_AVAILABLE = True
except ImportError:
    HYDRA_AVAILABLE = False


def load_hydra_config(config_path: str = "config", config_name: str = "config") -> Any:
    """
    Carga configuración usando Hydra.
    
    Args:
        config_path: Ruta al directorio de configuración
        config_name: Nombre del archivo de configuración
    
    Returns:
        Configuración de Hydra
    """
    if HYDRA_AVAILABLE:
        with initialize(config_path=config_path, version_base=None):
            cfg = compose(config_name=config_name)
            return OmegaConf.to_container(cfg, resolve=True)
    else:
        raise ImportError("Hydra no está instalado. Instala con: pip install hydra-core")


try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False


def init_wandb(project: str, config: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Any]:
    """
    Inicializa Weights & Biases para experiment tracking.
    
    Args:
        project: Nombre del proyecto
        config: Configuración del experimento
        **kwargs: Argumentos adicionales para wandb.init
    
    Returns:
        Objeto wandb o None si no está disponible
    """
    if WANDB_AVAILABLE:
        return wandb.init(project=project, config=config, **kwargs)
    return None


try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_system_info() -> Dict[str, Any]:
    """
    Obtiene información del sistema.
    
    Returns:
        Diccionario con información del sistema
    """
    info = {}
    
    if PSUTIL_AVAILABLE:
        info['cpu_count'] = psutil.cpu_count()
        info['cpu_percent'] = psutil.cpu_percent(interval=1)
        info['memory_total'] = psutil.virtual_memory().total
        info['memory_available'] = psutil.virtual_memory().available
        info['memory_percent'] = psutil.virtual_memory().percent
        
        if torch.cuda.is_available():
            info['gpu_count'] = torch.cuda.device_count()
            info['gpu_memory'] = {}
            for i in range(torch.cuda.device_count()):
                info['gpu_memory'][f'gpu_{i}'] = {
                    'total': torch.cuda.get_device_properties(i).total_memory,
                    'allocated': torch.cuda.memory_allocated(i),
                    'cached': torch.cuda.memory_reserved(i)
                }
    
    return info


try:
    from memory_profiler import profile
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    def profile(func):
        return func


def profile_memory(func: Callable) -> Callable:
    """
    Decorador para perfilar el uso de memoria de una función.
    
    Args:
        func: Función a perfilar
    
    Returns:
        Función decorada
    """
    if MEMORY_PROFILER_AVAILABLE:
        return profile(func)
    return func


try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, *args, **kwargs):
        return iterable


def progress_bar(iterable, desc: Optional[str] = None, **kwargs):
    """
    Crea una barra de progreso para un iterable.
    
    Args:
        iterable: Iterable a procesar
        desc: Descripción de la barra de progreso
        **kwargs: Argumentos adicionales para tqdm
    
    Returns:
        Iterable con barra de progreso
    """
    if TQDM_AVAILABLE:
        return tqdm(iterable, desc=desc, **kwargs)
    return iterable


_LOGGER_INITIALIZED = False


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Set up and return a logger instance.
    
    This function ensures logging is only configured once and provides
    a consistent logging interface across all modules.
    
    Args:
        name: Logger name (typically __name__). If None, uses root logger.
    
    Returns:
        Configured logger instance
    """
    global _LOGGER_INITIALIZED
    
    try:
        import structlog
        if not _LOGGER_INITIALIZED:
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.add_log_level,
                    structlog.dev.ConsoleRenderer(),
                ],
                wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(),
                cache_logger_on_first_use=True,
            )
            _LOGGER_INITIALIZED = True
        return structlog.get_logger(name or __name__)
    except ImportError:
        if not _LOGGER_INITIALIZED:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            _LOGGER_INITIALIZED = True
        
        return logging.getLogger(name or __name__)


import asyncio
from typing import Awaitable


async def async_safe_execute(
    func: Callable[..., Awaitable[T]],
    default_value: Optional[T] = None,
    log_errors: bool = True,
    *args: Any,
    **kwargs: Any
) -> Tuple[Optional[T], Optional[Exception]]:
    """
    Ejecuta una función asíncrona de forma segura, capturando excepciones.
    
    Args:
        func: Función asíncrona a ejecutar
        default_value: Valor por defecto si falla
        log_errors: Si True, registra errores
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
    
    Returns:
        Tupla (resultado, excepción)
    """
    try:
        result = await func(*args, **kwargs)
        return result, None
    except Exception as e:
        if log_errors:
            logger = setup_logger(__name__)
            logger.error(
                "Error en ejecución asíncrona segura",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
        return default_value, e


def batch_process(
    items: List[T],
    batch_size: int,
    processor: Callable[[List[T]], Any],
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Procesa items en lotes.
    
    Args:
        items: Lista de items a procesar
        batch_size: Tamaño del lote
        processor: Función que procesa un lote
        max_workers: Número máximo de workers (opcional)
    
    Returns:
        Lista de resultados
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        result = processor(batch)
        results.append(result)
    return results


def ensure_list(value: Union[T, List[T]]) -> List[T]:
    """
    Asegura que un valor sea una lista.
    
    Args:
        value: Valor que puede ser un item o una lista
    
    Returns:
        Lista con el valor
    """
    if isinstance(value, list):
        return value
    return [value]


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Divide una lista en chunks de tamaño fijo.
    
    Args:
        items: Lista a dividir
        chunk_size: Tamaño de cada chunk
    
    Returns:
        Lista de chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
