#!/usr/bin/env python3
"""
Utilidades Avanzadas - Integración de Librerías de requirements.txt
===================================================================

Este módulo integra y proporciona interfaces unificadas para las librerías
listadas en requirements.txt, con manejo de errores y fallbacks apropiados.
"""

from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, Tuple
from functools import wraps
import json
from pathlib import Path
import time
import logging

T = TypeVar('T')

# ============================================================================
# Serialización Avanzada
# ============================================================================

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


def serialize_json(data: Any, use_orjson: bool = True) -> bytes:
    """
    Serializa datos a JSON usando orjson si está disponible.
    
    Args:
        data: Datos a serializar
        use_orjson: Si True, usa orjson (más rápido)
    
    Returns:
        Bytes serializados
    """
    if use_orjson and ORJSON_AVAILABLE:
        return orjson.dumps(data)
    return json.dumps(data).encode('utf-8')


def deserialize_json(data: Union[bytes, str], use_orjson: bool = True) -> Any:
    """
    Deserializa datos desde JSON.
    
    Args:
        data: Datos serializados
        use_orjson: Si True, usa orjson
    
    Returns:
        Datos deserializados
    """
    if use_orjson and ORJSON_AVAILABLE:
        if isinstance(data, str):
            data = data.encode('utf-8')
        return orjson.loads(data)
    
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def serialize_msgpack(data: Any) -> bytes:
    """
    Serializa datos usando MessagePack.
    
    Args:
        data: Datos a serializar
    
    Returns:
        Bytes serializados
    """
    if MSGPACK_AVAILABLE:
        return msgpack.packb(data)
    raise ImportError("msgpack no está instalado. Instala con: pip install msgpack")


def deserialize_msgpack(data: bytes) -> Any:
    """
    Deserializa datos desde MessagePack.
    
    Args:
        data: Datos serializados
    
    Returns:
        Datos deserializados
    """
    if MSGPACK_AVAILABLE:
        return msgpack.unpackb(data, raw=False)
    raise ImportError("msgpack no está instalado. Instala con: pip install msgpack")


# ============================================================================
# Caching Avanzado
# ============================================================================

try:
    from cachetools import TTLCache, LRUCache, LFUCache, cached, Cache
    from cachetools.keys import hashkey
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import diskcache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False

try:
    import aiocache
    from aiocache import Cache as AsyncCache
    AIOCACHE_AVAILABLE = True
except ImportError:
    AIOCACHE_AVAILABLE = False


class CacheManager:
    """Gestor de caché unificado con múltiples backends."""
    
    def __init__(
        self,
        backend: str = "memory",
        maxsize: int = 128,
        ttl: int = 3600,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        disk_cache_path: Optional[Path] = None
    ):
        """
        Inicializa el gestor de caché.
        
        Args:
            backend: Backend a usar ("memory", "redis", "disk")
            maxsize: Tamaño máximo del caché
            ttl: Tiempo de vida en segundos
            redis_host: Host de Redis
            redis_port: Puerto de Redis
            disk_cache_path: Ruta para caché en disco
        """
        self.backend = backend
        self.maxsize = maxsize
        self.ttl = ttl
        
        if backend == "memory" and CACHETOOLS_AVAILABLE:
            self.cache: Cache = TTLCache(maxsize=maxsize, ttl=ttl)
        elif backend == "redis" and REDIS_AVAILABLE:
            self.cache = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        elif backend == "disk" and DISKCACHE_AVAILABLE:
            path = disk_cache_path or Path.home() / ".cache" / "production_code"
            self.cache = diskcache.Cache(str(path), size_limit=maxsize * 1024 * 1024)
        else:
            self.cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché."""
        try:
            if self.backend == "redis" and REDIS_AVAILABLE:
                value = self.cache.get(key)
                return json.loads(value) if value else None
            elif self.backend == "disk" and DISKCACHE_AVAILABLE:
                return self.cache.get(key)
            else:
                return self.cache.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establece un valor en el caché."""
        try:
            ttl = ttl or self.ttl
            if self.backend == "redis" and REDIS_AVAILABLE:
                self.cache.setex(key, ttl, json.dumps(value))
            elif self.backend == "disk" and DISKCACHE_AVAILABLE:
                self.cache.set(key, value, expire=ttl)
            else:
                self.cache[key] = value
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Elimina un valor del caché."""
        try:
            if self.backend == "redis" and REDIS_AVAILABLE:
                return bool(self.cache.delete(key))
            elif self.backend == "disk" and DISKCACHE_AVAILABLE:
                return self.cache.delete(key)
            else:
                del self.cache[key]
                return True
        except Exception:
            return False
    
    def clear(self) -> None:
        """Limpia todo el caché."""
        try:
            if self.backend == "redis" and REDIS_AVAILABLE:
                self.cache.flushdb()
            elif self.backend == "disk" and DISKCACHE_AVAILABLE:
                self.cache.clear()
            else:
                self.cache.clear()
        except Exception:
            pass


# ============================================================================
# Rich Console y Visualización
# ============================================================================

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Table = None
    Progress = None


def get_console() -> Optional[Any]:
    """Obtiene una instancia de Rich Console."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_table(data: List[Dict[str, Any]], title: Optional[str] = None) -> None:
    """
    Imprime una tabla usando Rich.
    
    Args:
        data: Lista de diccionarios con datos
        title: Título opcional de la tabla
    """
    if not RICH_AVAILABLE:
        print(json.dumps(data, indent=2))
        return
    
    console = Console()
    if not data:
        console.print("No hay datos para mostrar")
        return
    
    table = Table(title=title)
    for key in data[0].keys():
        table.add_column(key)
    
    for row in data:
        table.add_row(*[str(row.get(key, "")) for key in data[0].keys()])
    
    console.print(table)


def print_panel(content: str, title: Optional[str] = None) -> None:
    """
    Imprime un panel usando Rich.
    
    Args:
        content: Contenido del panel
        title: Título opcional
    """
    if not RICH_AVAILABLE:
        print(f"{title}: {content}" if title else content)
        return
    
    console = Console()
    panel = Panel(content, title=title)
    console.print(panel)


# ============================================================================
# Configuración Avanzada
# ============================================================================

try:
    from hydra import compose, initialize
    from omegaconf import OmegaConf, DictConfig
    HYDRA_AVAILABLE = True
except ImportError:
    HYDRA_AVAILABLE = False

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_SETTINGS_AVAILABLE = True
except ImportError:
    PYDANTIC_SETTINGS_AVAILABLE = False

try:
    from dynaconf import Dynaconf
    DYNACONF_AVAILABLE = True
except ImportError:
    DYNACONF_AVAILABLE = False


class AdvancedConfigManager:
    """Gestor de configuración avanzado con múltiples backends."""
    
    def __init__(
        self,
        config_type: str = "pydantic",
        config_path: Optional[Path] = None,
        **kwargs
    ):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_type: Tipo de configuración ("pydantic", "hydra", "dynaconf")
            config_path: Ruta al archivo de configuración
            **kwargs: Argumentos adicionales
        """
        self.config_type = config_type
        self.config_path = config_path
        self.config: Optional[Any] = None
        
        if config_type == "hydra" and HYDRA_AVAILABLE:
            self._load_hydra_config(**kwargs)
        elif config_type == "dynaconf" and DYNACONF_AVAILABLE:
            self._load_dynaconf_config(**kwargs)
        else:
            self._load_pydantic_config(**kwargs)
    
    def _load_hydra_config(self, config_name: str = "config", **kwargs) -> None:
        """Carga configuración usando Hydra."""
        if not HYDRA_AVAILABLE:
            raise ImportError("hydra-core no está instalado")
        
        config_path = kwargs.get("config_path", "config")
        with initialize(config_path=config_path, version_base=None):
            self.config = compose(config_name=config_name)
    
    def _load_dynaconf_config(self, **kwargs) -> None:
        """Carga configuración usando Dynaconf."""
        if not DYNACONF_AVAILABLE:
            raise ImportError("dynaconf no está instalado")
        
        self.config = Dynaconf(**kwargs)
    
    def _load_pydantic_config(self, **kwargs) -> None:
        """Carga configuración usando Pydantic Settings."""
        if PYDANTIC_SETTINGS_AVAILABLE:
            class Settings(BaseSettings):
                model_config = SettingsConfigDict(
                    env_file=self.config_path,
                    env_file_encoding='utf-8',
                    extra='ignore'
                )
            self.config = Settings(**kwargs)
        else:
            self.config = kwargs
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        if self.config_type == "hydra" and HYDRA_AVAILABLE:
            return OmegaConf.select(self.config, key, default=default)
        elif self.config_type == "dynaconf" and DYNACONF_AVAILABLE:
            return getattr(self.config, key, default)
        elif PYDANTIC_SETTINGS_AVAILABLE:
            return getattr(self.config, key, default)
        else:
            return self.config.get(key, default)


# ============================================================================
# Monitoreo y Métricas
# ============================================================================

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from memory_profiler import profile
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False


class PrometheusMetricsCollector:
    """Colector de métricas usando Prometheus."""
    
    def __init__(self, enable_prometheus: bool = True):
        """
        Inicializa el colector de métricas.
        
        Args:
            enable_prometheus: Si True, habilita métricas de Prometheus
        """
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.counters: Dict[str, Any] = {}
        self.gauges: Dict[str, Any] = {}
        self.histograms: Dict[str, Any] = {}
        self.summaries: Dict[str, Any] = {}
    
    def create_counter(self, name: str, description: str = "") -> Optional[Any]:
        """Crea un contador de Prometheus."""
        if not self.enable_prometheus:
            return None
        
        if name not in self.counters:
            self.counters[name] = Counter(name, description)
        return self.counters[name]
    
    def create_gauge(self, name: str, description: str = "") -> Optional[Any]:
        """Crea un gauge de Prometheus."""
        if not self.enable_prometheus:
            return None
        
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, description)
        return self.gauges[name]
    
    def create_histogram(self, name: str, description: str = "") -> Optional[Any]:
        """Crea un histograma de Prometheus."""
        if not self.enable_prometheus:
            return None
        
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description)
        return self.histograms[name]
    
    def start_server(self, port: int = 8000) -> None:
        """Inicia el servidor HTTP de Prometheus."""
        if self.enable_prometheus:
            start_http_server(port)


def get_system_metrics() -> Dict[str, Any]:
    """
    Obtiene métricas del sistema usando psutil.
    
    Returns:
        Diccionario con métricas del sistema
    """
    if not PSUTIL_AVAILABLE:
        return {}
    
    return {
        'cpu': {
            'count': psutil.cpu_count(),
            'percent': psutil.cpu_percent(interval=1),
            'per_cpu': psutil.cpu_percent(interval=1, percpu=True)
        },
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent,
            'used': psutil.virtual_memory().used
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent
        }
    }


# ============================================================================
# Joblib para Procesamiento Paralelo
# ============================================================================

try:
    from joblib import Parallel, delayed, Memory
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


def parallel_process(
    items: List[T],
    func: Callable[[T], Any],
    n_jobs: int = -1,
    backend: str = "threading",
    verbose: int = 0
) -> List[Any]:
    """
    Procesa items en paralelo usando joblib.
    
    Args:
        items: Lista de items a procesar
        func: Función a aplicar a cada item
        n_jobs: Número de trabajos paralelos (-1 para todos los cores)
        backend: Backend a usar ("threading", "multiprocessing")
        verbose: Nivel de verbosidad
    
    Returns:
        Lista de resultados
    """
    if not JOBLIB_AVAILABLE:
        return [func(item) for item in items]
    
    return Parallel(n_jobs=n_jobs, backend=backend, verbose=verbose)(
        delayed(func)(item) for item in items
    )


# ============================================================================
# Logging Estructurado con Structlog
# ============================================================================

try:
    import structlog
    from pythonjsonlogger import jsonlogger
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def setup_structured_logging(
    level: str = "INFO",
    use_json: bool = True,
    add_timestamp: bool = True
) -> None:
    """
    Configura logging estructurado usando structlog.
    
    Args:
        level: Nivel de logging
        use_json: Si True, usa formato JSON
        add_timestamp: Si True, añade timestamps
    """
    if not STRUCTLOG_AVAILABLE:
        logging.basicConfig(level=getattr(logging, level))
        return
    
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
    ]
    
    if add_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))
    
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_structured_logger(name: str) -> Any:
    """
    Obtiene un logger estructurado.
    
    Args:
        name: Nombre del logger
    
    Returns:
        Logger estructurado
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    return logging.getLogger(name)


# ============================================================================
# Utilidades de Fecha y Hora
# ============================================================================

try:
    import arrow
    from arrow import get
    ARROW_AVAILABLE = True
except ImportError:
    ARROW_AVAILABLE = False

try:
    from dateutil import parser as date_parser, relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False


def parse_datetime(date_string: str) -> Any:
    """
    Parsea una fecha usando arrow o dateutil.
    
    Args:
        date_string: String de fecha
    
    Returns:
        Objeto de fecha parseado
    """
    if ARROW_AVAILABLE:
        return arrow.get(date_string)
    elif DATEUTIL_AVAILABLE:
        return date_parser.parse(date_string)
    else:
        raise ImportError("arrow o python-dateutil deben estar instalados")


# ============================================================================
# Validación Avanzada
# ============================================================================

try:
    from jsonschema import validate, ValidationError as JSONValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

try:
    from cerberus import Validator
    CERBERUS_AVAILABLE = True
except ImportError:
    CERBERUS_AVAILABLE = False


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Valida datos contra un esquema JSON.
    
    Args:
        data: Datos a validar
        schema: Esquema JSON
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not JSONSCHEMA_AVAILABLE:
        return True, None
    
    try:
        validate(instance=data, schema=schema)
        return True, None
    except JSONValidationError as e:
        return False, str(e)


def validate_with_cerberus(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Valida datos usando Cerberus.
    
    Args:
        data: Datos a validar
        schema: Esquema de Cerberus
    
    Returns:
        Tupla (es_válido, errores)
    """
    if not CERBERUS_AVAILABLE:
        return True, None
    
    validator = Validator(schema)
    is_valid = validator.validate(data)
    return is_valid, validator.errors if not is_valid else None

