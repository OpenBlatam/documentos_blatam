# Librerías Implementadas de requirements.txt

Este documento describe las librerías de `requirements.txt` que han sido implementadas en el código.

## Resumen

Se han creado módulos avanzados que integran las principales librerías de `requirements.txt` con manejo de errores y fallbacks apropiados.

## Módulos Creados

### 1. `core/advanced_utils.py`

Módulo principal que integra múltiples librerías:

#### Serialización
- **orjson**: Serialización JSON de alto rendimiento
- **msgpack**: Serialización binaria eficiente

#### Caching
- **cachetools**: Caché en memoria con TTL, LRU, LFU
- **redis**: Caché distribuido con Redis
- **diskcache**: Caché persistente en disco
- **aiocache**: Caché asíncrono

#### Configuración
- **hydra-core**: Gestión avanzada de configuración
- **omegaconf**: Configuración estructurada
- **pydantic-settings**: Configuración con validación
- **dynaconf**: Configuración dinámica

#### Logging
- **structlog**: Logging estructurado
- **python-json-logger**: Logging en formato JSON

#### Visualización y UI
- **rich**: Consola enriquecida con tablas, paneles, progreso

#### Monitoreo
- **prometheus-client**: Métricas de Prometheus
- **psutil**: Métricas del sistema
- **memory-profiler**: Profiling de memoria

#### Procesamiento Paralelo
- **joblib**: Procesamiento paralelo eficiente

#### Validación
- **jsonschema**: Validación con esquemas JSON
- **cerberus**: Validación de datos

#### Utilidades de Fecha
- **arrow**: Manipulación de fechas
- **python-dateutil**: Utilidades de fecha

### 2. `core/llm_advanced.py`

Módulo para LLMs y RAG:

#### LLM Frameworks
- **langchain**: Framework para aplicaciones LLM
- **langchain-community**: Extensiones de LangChain
- **llama-index**: Framework de indexación para LLM

#### Conteo de Tokens
- **tiktoken**: Conteo preciso de tokens

#### Embeddings
- **sentence-transformers**: Modelos de embeddings

#### Vector Databases
- **chromadb**: Base de datos vectorial
- **pinecone-client**: Base de datos vectorial en la nube
- **weaviate-client**: Base de datos vectorial
- **qdrant-client**: Base de datos vectorial

#### Búsqueda de Similitud
- **faiss-cpu**: Búsqueda de similitud eficiente

#### Prompt Engineering
- **guidance**: Framework para prompt engineering
- **outlines**: Generación estructurada

### 3. `core/visualization_advanced.py`

Módulo de visualización:

#### Visualización
- **matplotlib**: Gráficos 2D
- **seaborn**: Visualización estadística
- **plotly**: Gráficos interactivos

## Mejoras en Módulos Existentes

### `core/monitoring.py`

Se ha mejorado para integrar:
- **prometheus-client**: Métricas de Prometheus opcionales
- **psutil**: Métricas del sistema mejoradas

### `core/utils.py`

Ya incluía integración con:
- **typing-extensions**: Type hints avanzados
- **typeguard**: Validación de tipos
- **cachetools**: Caché básico
- **backoff**: Retry con backoff
- **tenacity**: Retry avanzado
- **python-dotenv**: Variables de entorno
- **pyyaml**: YAML
- **toml**: TOML
- **hydra-core**: Configuración Hydra
- **wandb**: Experiment tracking
- **psutil**: Información del sistema
- **memory-profiler**: Profiling de memoria
- **tqdm**: Barras de progreso
- **structlog**: Logging estructurado

## Uso

### Ejemplo Básico

```python
from core.advanced_utils import (
    serialize_json,
    CacheManager,
    get_console,
    print_table
)

# Serialización
data = {"key": "value"}
json_bytes = serialize_json(data)

# Caching
cache = CacheManager(backend="memory")
cache.set("key", "value")
value = cache.get("key")

# Rich Console
console = get_console()
console.print("[bold green]Hello![/bold green]")
```

### Ejemplo LLM

```python
from core.llm_advanced import (
    AdvancedLLMClient,
    TokenCounter,
    AdvancedVectorStore
)

# Cliente LLM
client = AdvancedLLMClient(provider="openai", use_langchain=True)

# Conteo de tokens
counter = TokenCounter(model="gpt-3.5-turbo")
tokens = counter.count_tokens("Hello, world!")

# Vector Store
vector_store = AdvancedVectorStore(backend="chroma")
```

### Ejemplo Visualización

```python
from core.visualization_advanced import AdvancedVisualizer

viz = AdvancedVisualizer(backend="plotly")
viz.plot_line(x=[1, 2, 3], y=[1, 4, 9], title="Example")
```

## Archivo de Ejemplo

Ver `examples/example_advanced_libraries.py` para ejemplos completos de uso de todas las librerías.

## Manejo de Dependencias Opcionales

Todas las librerías se importan con bloques `try/except` para manejar casos donde no estén instaladas. El código proporciona fallbacks apropiados cuando las librerías no están disponibles.

## Notas

- Las librerías se importan de forma opcional con manejo de errores
- Se proporcionan fallbacks cuando las librerías no están disponibles
- Los módulos están diseñados para ser extensibles y fáciles de usar
- Se mantiene compatibilidad con código existente

## Próximos Pasos

Para usar estas librerías:

1. Instalar las dependencias: `pip install -r requirements.txt`
2. Importar los módulos necesarios
3. Usar las funciones y clases proporcionadas
4. Consultar los ejemplos en `examples/example_advanced_libraries.py`


