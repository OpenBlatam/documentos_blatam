# Production Code - Modelos de Papers

Este directorio contiene los modelos de producción implementados basados en los papers de investigación. Todos los modelos aquí son implementaciones completas que heredan de `BasePaperModule` y están listos para uso en producción.

## Estructura

```
production_code/
├── api/                       # ✅ Capa de Presentación (API, rutas, middleware)
│   ├── routes/                # ✅ 8 módulos de rutas organizados
│   ├── auth.py                # ✅ Autenticación opcional
│   ├── middleware.py          # ✅ Todos los middlewares
│   └── api_utils.py           # ✅ Validación de API
├── services/                  # ✅ Capa de Aplicación (lógica de negocio)
│   ├── memory_service.py
│   ├── pipeline_service.py
│   └── ...
├── application/               # ✅ Application Layer (DI Container)
│   └── service_container.py   # ✅ Dependency Injection
├── core/                      # ✅ Capa Core (utilidades y base)
│   ├── paper_base.py          # Clase base para todos los modelos
│   ├── config_manager.py      # ✅ Config consolidado
│   ├── api_utils.py           # HTTP/web utilities
│   └── ...
├── research/                  # Modelos de investigación
├── inference/                 # Modelos de optimización de inferencia
├── memory/                    # Modelos relacionados con memoria
├── techniques/                # Técnicas específicas
├── best/                      # Mejores modelos seleccionados
├── code_modules/              # ✅ Modelos relacionados con código (renombrado)
├── redundancy/                # Modelos de redundancia
├── architecture/              # Arquitecturas de modelos
├── multimodal_api/           # API multimodal
├── sora/                      # Módulo Sora para generación de video
├── model_data/                # Gestión de datos de modelos
├── static/                    # Archivos estáticos (interfaz web)
│   └── chat.html              # Interfaz web del chat
├── examples/                  # Ejemplos de uso
├── docs/                      # Documentación organizada
│   ├── README.md              # Índice de documentación
│   └── archive/               # Documentación antigua archivada
├── tests/                     # Tests del sistema
├── chat_server.py             # Servidor de chat
├── api_server.py              # ✅ Servidor API (entry point)
├── application.py             # ✅ Application factory (nuevo)
├── api_unified.py             # ⚠️ Deprecated (compatibility shim)
├── cli.py                     # CLI simple con Click
├── cli_unified.py             # CLI completo unificado
├── docs/architecture/          # Documentación de arquitectura por capas
│   └── layers.md               # Guía de capas, reglas de importación y checklist
└── README.md                   # Este archivo
```

## Características (Production-Ready)

- **Modelos Completos**: Todos los archivos aquí son modelos completos con arquitecturas de redes neuronales, no scripts simples
- **Base Unificada Mejorada**: Todos los modelos heredan de `BasePaperModule` mejorado con:
  - Validación de inputs automática
  - Manejo robusto de errores
  - Métodos de serialización (save/load)
  - Métricas y logging mejorados
  - Información del modelo (parámetros, device, dtype)
  - **NUEVO**: Sistema de cache LRU inteligente
  - **NUEVO**: Soporte para gradient checkpointing
  - **NUEVO**: Forward pass con cache opcional
- **Validaciones Robustas**: 
  - Validación de configuración en cada modelo
  - Validación de inputs en forward pass
  - Detección de NaN/Inf en tensores
  - Validación de dimensiones
- **Manejo de Errores**: 
  - Try-except en métodos críticos
  - Valores por defecto en caso de error
  - Logging detallado de errores
- **Regularización**: Dropout añadido en modelos clave para mejor generalización
- **Métricas Mejoradas**: Métricas adicionales (std, max, min) para mejor monitoreo
- **Organizados por Categoría**: Los modelos están organizados en subdirectorios según su propósito
- **NUEVO: Sistema de Registry**: Auto-descubrimiento y gestión de papers
- **NUEVO: Sistema de Benchmarking**: Utilidades para medir rendimiento
- **NUEVO: Sistema de Testing**: Suite completa de tests automáticos
- **NUEVO: Sistema de Chat Conversacional**: Interfaz tipo ChatGPT con API REST e interfaz web

## Uso

### Ejemplo Básico

```python
from research.paper_malto import MALTOModule, MALTOConfig
import torch

# Crear configuración
config = MALTOConfig(
    hidden_dim=512,
    uncertainty_threshold=0.5,
    mitigation_strength=0.4
)

# Crear modelo
model = MALTOModule(config)

# Usar modelo
hidden_states = torch.randn(2, 10, 512)  # [batch, seq, hidden_dim]
output, metadata = model(hidden_states)

print(f"Output shape: {output.shape}")
print(f"Métricas: {metadata}")
```

### Guardar y Cargar Modelos

```python
# Guardar modelo
model.save_model("modelo_malto.pt")

# Cargar modelo
loaded_model = MALTOModule.load_model("modelo_malto.pt", config=config)
```

### Obtener Información del Modelo

```python
# Información completa
info = model.get_model_info()
print(f"Parámetros totales: {info['total_parameters']:,}")
print(f"Parámetros entrenables: {info['trainable_parameters']:,}")

# Contar parámetros
total = model.count_parameters()
trainable = model.count_parameters(trainable_only=True)
```

### Métricas

```python
# Obtener métricas acumuladas
metrics = model.get_metrics()
print(metrics)

# Resetear métricas
model.reset_metrics()
```

### Experiment Tracking

```python
from core.experiment_tracking import ExperimentTracker

# Inicializar tracking
with ExperimentTracker(project="my-project", experiment_name="exp-1") as tracker:
    # Log métricas
    tracker.log_metrics({"loss": 0.5, "accuracy": 0.9}, step=1)
    
    # Log parámetros
    tracker.log_params({"learning_rate": 0.001, "batch_size": 32})
    
    # Guardar modelo
    tracker.log_model(model, name="best_model")
```

### Gestión de Configuración

```python
from core.config_manager import ConfigManager

# Cargar desde YAML
manager = ConfigManager("config.yaml")

# Obtener valores
hidden_dim = manager.get("model.hidden_dim", default=512)

# Establecer valores
manager.set("model.hidden_dim", 1024)

# Guardar configuración
manager.save("new_config.json", format="json")
```

### Caching y Retry

```python
from core.utils import retry_on_failure, cached_tensor_operation

# Operación con retry
@retry_on_failure(max_attempts=3, backoff_factor=1.0)
def train_model():
    # código de entrenamiento
    pass

# Operación con cache
result = cached_tensor_operation("key", expensive_operation, *args)
```

### Procesamiento de Datos

```python
from core.data_utils import (
    tensor_to_dataframe,
    normalize_tensor,
    statistical_analysis,
    plot_tensor_distribution
)

# Convertir tensor a DataFrame
df = tensor_to_dataframe(hidden_states, columns=["feature_1", "feature_2"])

# Normalizar tensor
normalized, stats = normalize_tensor(tensor, method="standard")

# Análisis estadístico
stats = statistical_analysis(tensor)

# Visualizar distribución
plot_tensor_distribution(tensor, title="Hidden States Distribution")
```

### APIs

```python
from core.api_utils import create_fastapi_app, http_get

# Crear API FastAPI
app = create_fastapi_app(title="ML API", version="1.0.0")

@app.get("/predict")
async def predict(data: dict):
    # lógica de predicción
    return {"prediction": result}

# Petición HTTP
response = http_get("https://api.example.com/data")
```

## Arquitectura en Capas

Para facilitar la evolución del sistema, la base de código se organiza en cuatro capas con dependencias dirigidas:

- **Presentación** (`api/`, `api_server.py`, `chat_server.py`, `cli*.py`, `dashboard.html`): ✅ Exponen interfaces HTTP/WebSocket/CLI/UI, validan DTOs con Pydantic y delegan en servicios de aplicación. Utilizan un `ServiceContainer` registrado en `app.state`/`Depends` para desacoplar implementaciones.
- **Aplicación** (`services/`, `application/`, `integration_pipeline.py`, `monitoring_system.py`): ✅ Implementan casos de uso y orquestan módulos de dominio a través de fachadas como `PipelineService`, `ChatService`, `MemoryService`. Aplican políticas transversales (reintentos, cuotas, métricas).
- **Dominio** (`core/`, `memory/`, `research/`, `inference/`, `architecture/`, `techniques/`, `code_modules/`, `best/`, `redundancy/`, `model_data/`): ✅ Define entidades, validaciones y contratos (`Protocol`/`ABC`) como `MemoryModule`, `ChatEngine`, `ConfigRepository`. No depende de frameworks externos.
- **Infraestructura** (`infrastructure/`, `core/config_manager.py`, `core/api_utils.py`, adaptadores concretos): ✅ Implementa los contratos de dominio con proveedores reales (FastAPI, httpx, Ray, storage, observabilidad) y expone factories en `infrastructure/providers/*`.

Las reglas de dependencia, el mapa de imports permitidos, los eventos de observabilidad y el checklist para nuevos módulos se detallan en `docs/architecture/layers.md`, junto con instrucciones para migraciones progresivas.

### ✅ Mejoras Arquitectónicas Completadas

**Versión 2.0.0** - Todas las mejoras arquitectónicas han sido completadas:

- ✅ **6 fases de mejoras** completadas exitosamente
- ✅ **Duplicación eliminada**: 5 archivos duplicados consolidados (~1,900 líneas)
- ✅ **Imports estandarizados**: 100% usando rutas de módulo
- ✅ **Estructura organizada**: Arquitectura en capas implementada
- ✅ **23 funciones API mejoradas**: Docstrings completos y manejo de errores consistente
- ✅ **23 funciones reutilizables creadas**: Decoradores, helpers, response utils, validation helpers
- ✅ **25+ documentos creados**: Guías completas y ejemplos de uso
- ✅ **Compatibilidad**: 0 breaking changes, 100% compatible hacia atrás

**Ver `RESUMEN_FINAL_COMPLETO.md` para detalles completos.**

### Computación Distribuida

```python
from core.distributed_utils import (
    init_ray,
    parallel_tensor_operations,
    distributed_training_setup
)

# Inicializar Ray
init_ray(num_cpus=4, num_gpus=2)

# Operaciones paralelas
results = parallel_tensor_operations([op1, op2, op3], *args)

# Entrenamiento distribuido
config = distributed_training_setup(backend="nccl")
```

## Mejoras con Librerías Modernas

Este código ha sido mejorado con librerías modernas de Python:

### Core
- **Pydantic**: Validación robusta de configuraciones
- **Structlog**: Logging estructurado para mejor trazabilidad
- **orjson**: Serialización JSON más rápida
- **Rich**: Output mejorado en scripts
- **typing-extensions**: Type hints mejorados

### Configuración y Gestión
- **Hydra/OmegaConf**: Gestión avanzada de configuración
- **PyYAML/TOML**: Soporte para múltiples formatos
- **python-dotenv**: Variables de entorno

### Experiment Tracking
- **Weights & Biases (wandb)**: Tracking de experimentos
- **MLflow**: Alternativa para experiment tracking

### Performance y Utilidades
- **cachetools**: Caching avanzado (TTL, LRU)
- **joblib**: Procesamiento paralelo
- **backoff/tenacity**: Retry logic con backoff exponencial
- **tqdm**: Progress bars
- **memory-profiler/psutil**: Profiling y monitoreo
- **prometheus-client**: Métricas para Prometheus

### Procesamiento de Datos
- **pandas**: Manipulación y análisis de datos
- **scipy**: Computación científica y estadística
- **scikit-learn**: Machine learning y preprocesamiento

### Visualización
- **matplotlib**: Gráficos estáticos
- **seaborn**: Visualización estadística
- **plotly**: Gráficos interactivos

### Computación Distribuida
- **Ray**: Computación distribuida y paralela
- **Dask**: Procesamiento paralelo de datos

### APIs y Servicios Web
- **FastAPI**: Framework moderno para APIs
- **Flask**: Framework web ligero
- **aiohttp/httpx**: Clientes HTTP asíncronos
- **requests**: Cliente HTTP síncrono

### Bases de Datos
- **SQLAlchemy**: ORM para bases de datos
- **Alembic**: Migraciones de esquema

### Testing Avanzado
- **hypothesis**: Property-based testing
- **faker**: Generación de datos de prueba
- **pytest-mock**: Mocking avanzado

### Seguridad
- **cryptography**: Operaciones criptográficas
- **bcrypt**: Hashing de contraseñas

### Utilidades
- **python-dateutil/pytz/arrow**: Manejo de fechas y zonas horarias
- **transformers**: Modelos pre-entrenados de Hugging Face
- **datasets**: Datasets listos para usar
- **accelerate**: Optimización de entrenamiento
- **bitsandbytes**: Cuantización de modelos

### Documentación
- **Sphinx**: Generación de documentación
- **mkdocs**: Documentación interactiva

### Procesamiento de Archivos
- **Pillow**: Procesamiento de imágenes
- **opencv-python**: Computer vision
- **PyPDF2/PyMuPDF**: Procesamiento de PDFs
- **python-docx**: Documentos Word
- **openpyxl**: Archivos Excel
- **pytesseract**: OCR

### Cloud Storage
- **boto3**: AWS S3
- **google-cloud-storage**: Google Cloud Storage
- **azure-storage-blob**: Azure Blob Storage

### Caching y Colas
- **redis/aioredis**: Caching en memoria
- **celery**: Task queue
- **kafka-python**: Message queue

### Observabilidad
- **OpenTelemetry**: Distributed tracing
- **prometheus-client**: Métricas

### NLP y Texto
- **spacy**: Procesamiento de lenguaje natural
- **nltk**: NLP toolkit
- **sentence-transformers**: Embeddings de oraciones

### Optimización
- **JAX**: Computación acelerada
- **Numba**: JIT compilation
- **Cython**: Optimización de código

### Testing Avanzado
- **pytest-xdist**: Tests paralelos
- **hypothesis**: Property-based testing
- **faker**: Datos de prueba

### Seguridad Avanzada
- **bandit**: Security linter
- **safety**: Verificación de vulnerabilidades
- **PyJWT**: Tokens JWT

### CLI y Desarrollo
- **Click**: CLI profesional
- **pytest**: Testing framework
- **black/ruff**: Code formatting y linting
- **mypy**: Type checking estático

Ver `IMPROVEMENTS.md` para detalles completos.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso del CLI

El proyecto incluye un CLI mejorado con Click:

```bash
# Mejorar modelos
python cli.py improve

# Refactorizar imports
python cli.py refactor-imports

# Mostrar configuración
python cli.py config-show --config config.yaml

# Inicializar experiment tracking
python cli.py track --project my-project --name experiment-1

# Ejecutar tests
python cli.py test

# Información del sistema
python cli.py info
```

## Nuevas Funcionalidades

### Sistema de Registry

```python
from core import get_registry

registry = get_registry()

# Listar papers
papers = registry.list_papers(category='research')

# Cargar paper
module = registry.load_paper('malto')

# Buscar papers
results = registry.search_papers(query='reasoning')

# Estadísticas
stats = registry.get_statistics()
```

### Sistema de Benchmarking

```python
from core import BenchmarkRunner

runner = BenchmarkRunner(device='cuda', num_runs=10)
result = runner.benchmark(module, batch_size=4, seq_len=128)

print(f"Throughput: {result.throughput:.2f} tokens/s")
print(f"Latency: {result.latency:.2f} ms")
```

### Sistema de Testing

```python
from core import run_tests

summary = run_tests(module, device='cuda')
print(f"Pass rate: {summary['pass_rate']:.2%}")
```

### Sistema de Cache

```python
# Habilitar cache
module.enable_cache(enable=True, max_size=10)
module.eval()

# Usar cache en forward
output, metadata = module.forward_with_cache(hidden_states)

# Estadísticas
stats = module.get_cache_stats()
```

### Gradient Checkpointing

```python
# Habilitar para ahorrar memoria
module.enable_gradient_checkpointing(enable=True)
```

Ver `docs/MEJORAS_V6.md` para más detalles.

## Sistema de Chat Conversacional (ChatGPT-like)

El proyecto incluye un sistema completo de chat conversacional similar a ChatGPT:

- **Motor de Chat**: Manejo de conversaciones con historial y contexto
- **API REST**: Endpoints completos para integración
- **Interfaz Web**: UI moderna y responsive
- **Múltiples Proveedores**: OpenAI, Anthropic y modelos locales

### Inicio Rápido

```bash
# Configurar API key
export OPENAI_API_KEY=tu_api_key

# Ejecutar servidor
python chat_server.py

# Acceder a la interfaz web
# http://localhost:8000
```

Ver `docs/CHAT_README.md` para documentación completa del sistema de chat.

---

## 📚 Documentación

### Documentación Principal ⭐
- **`QUICK_START.md`** - Guía de inicio rápido
- **`GUIA_USO_UTILIDADES.md`** ⭐ - Guía completa de uso de utilidades reutilizables
- **`INDICE_DOCUMENTACION_COMPLETO.md`** - Índice completo de toda la documentación
- **`RESUMEN_FINAL_COMPLETO.md`** ⭐ - Resumen ejecutivo completo de todas las mejoras
- **`ARCHITECTURE.md`** - Arquitectura del sistema
- **`IMPORT_STANDARDS.md`** - Estándares de imports

### Mejoras Arquitectónicas
- **`MEJORAS_FINALES_COMPLETAS.md`** - Resumen ejecutivo de mejoras
- **`MEJORAS_ARQUITECTURA_COMPLETAS.md`** - Detalles completos de mejoras
- **`MEJORAS_RUTAS_API.md`** - Mejoras aplicadas a rutas API
- **`MEJORAS_DECORADORES_UTILIDADES.md`** - Decoradores y utilidades creadas
- **`MEJORAS_UTILIDADES_ADICIONALES.md`** - Utilidades adicionales

### Documentación por Fase
- `PHASE1_COMPLETE.md` - API Utils Consolidation
- `PHASE2_COMPLETE.md` - API Entry Points Consolidation
- `PHASE3_COMPLETE.md` - Import Standardization
- `PHASE4_COMPLETE.md` - Config Manager Consolidation
- `PHASE5_COMPLETE.md` - Directory Structure Alignment

### Utilidades Reutilizables
El proyecto incluye **23 funciones reutilizables** organizadas en 4 módulos:

- **`api/decorators.py`** - 3 decoradores para manejo de errores, validación y logging
- **`api/helpers.py`** - 9 funciones helper para requests, archivos y formatos
- **`api/response_utils.py`** - 5 funciones para formatear respuestas API
- **`api/validation_helpers.py`** - 6 funciones para validación de datos

**Ver `GUIA_USO_UTILIDADES.md` para ejemplos completos de uso.**

### Mejoras Futuras
- `MEJORAS_ADICIONALES_RECOMENDADAS.md` - Plan de mejoras futuras
- `MEJORAS_APLICADAS.md` - Mejoras adicionales aplicadas
- `CHANGELOG_MEJORAS.md` - Historial de cambios

---

## 🎉 Estado del Proyecto

**Versión**: 2.0.0  
**Estado**: ✅ Production Ready  
**Mejoras Completadas**: 6/6 fases  
**Última Actualización**: 2025-01-27

### ✅ Mejoras Arquitectónicas Completadas

- ✅ **6 fases de mejoras** completadas exitosamente
- ✅ **Duplicación eliminada**: 5 archivos duplicados consolidados
- ✅ **Imports estandarizados**: 100% usando rutas de módulo
- ✅ **Estructura organizada**: Arquitectura en capas implementada
- ✅ **Compatibilidad**: 0 breaking changes

**Ver `RESUMEN_FINAL_MEJORAS.md` para detalles completos.**

---

## Nota

Este directorio contiene solo los modelos de los papers, excluyendo scripts de utilidad como:
- `paper_extractor.py`
- `paper_loader.py`
- `paper_registry.py`

Estos scripts de utilidad permanecen en el directorio `papers/` original.

