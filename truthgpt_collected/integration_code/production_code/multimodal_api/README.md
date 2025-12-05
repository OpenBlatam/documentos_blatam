# API de Generación Multimodal

API unificada para todos los tipos de generación multimodal.

## Descripción

Esta API proporciona un endpoint único para múltiples modalidades de generación:
- **Text-to-Video**: Generación de videos desde texto
- **Text-to-Image**: Generación de imágenes desde texto
- **Text-to-Audio**: Generación de audio desde texto
- **Image-to-Video**: Animación de imágenes estáticas
- **Video-to-Video**: Transformación de videos existentes
- **Audio-to-Audio**: Transformación de audio
- **3D Generation**: Generación de modelos 3D
- **Multimodal Content**: Contenido que combina múltiples modalidades

## Características

- ✅ **Endpoint único** para múltiples modalidades
- ✅ **Rate limiting inteligente** con priorización de tareas
- ✅ **Caching optimizado** para respuestas frecuentes
- ✅ **Escalabilidad automática** basada en carga
- ✅ **Monitoring integrado** con métricas en tiempo real
- ✅ **Integración** con `core/api_utils.py` como base

## Estructura

```
multimodal_api/
├── __init__.py
├── README.md
├── api_server.py          # Servidor principal de la API
├── endpoints.py            # Definición de endpoints
├── models.py               # Modelos de datos (Pydantic)
├── example_usage.py        # Ejemplos de uso
├── generators/             # Módulos de generación por modalidad
│   └── __init__.py
├── middleware/             # Middleware personalizado
│   ├── __init__.py
│   ├── rate_limiter.py     # Rate limiting inteligente
│   ├── cache.py            # Sistema de cache optimizado
│   └── monitoring.py       # Monitoring y métricas
└── utils/                  # Utilidades
    └── __init__.py
```

## Instalación

```bash
# Asegúrate de tener las dependencias instaladas
pip install fastapi uvicorn pydantic

# Opcional: Para cache con Redis
pip install redis
```

## Uso Básico

### Iniciar el servidor

```python
from multimodal_api import MultimodalAPIServer

# Inicializar servidor con configuración personalizada
from multimodal_api.middleware import RateLimitConfig, CacheConfig

rate_limit_config = RateLimitConfig(
    max_requests=100,
    window_seconds=60,
    strategy="sliding_window"
)

cache_config = CacheConfig(
    default_ttl=3600,
    backend="memory"  # o "redis" para producción
)

server = MultimodalAPIServer(
    rate_limit_config=rate_limit_config,
    cache_config=cache_config
)

# Ejecutar servidor
server.run(host="0.0.0.0", port=8000)
```

### Usar la API

```python
import requests

# Generar video
response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "modality": "video",
        "generation_type": "text_to_video",
        "prompt": "A beautiful sunset over the ocean",
        "parameters": {
            "duration": 10,
            "resolution": "512x512",
            "fps": 24
        },
        "priority": 5
    }
)

task = response.json()
print(f"Tarea creada: {task['task_id']}")

# Verificar estado
status = requests.get(f"http://localhost:8000/api/v1/task/{task['task_id']}")
print(status.json())
```

## Endpoints

### POST /api/v1/generate
Generación unificada para todas las modalidades.

**Request:**
```json
{
  "modality": "video|image|audio|3d|multimodal",
  "generation_type": "text_to_video",
  "prompt": "Descripción del contenido a generar",
  "parameters": {
    "duration": 5,
    "resolution": "512x512",
    "style": "realistic"
  },
  "priority": 5,
  "callback_url": "https://..."
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "pending|processing|completed|failed",
  "created_at": "2024-01-01T00:00:00",
  "progress": 0.0,
  "result": null,
  "error": null
}
```

### GET /api/v1/task/{task_id}
Obtiene el estado de una tarea.

### POST /api/v1/generate/batch
Generación en batch de múltiples contenidos.

### GET /api/v1/tasks
Lista tareas con filtros opcionales.

### DELETE /api/v1/task/{task_id}
Cancela una tarea pendiente.

### GET /health
Health check con estadísticas del sistema.

## Rate Limiting

El sistema implementa rate limiting inteligente con:
- **Múltiples estrategias**: Fixed Window, Sliding Window, Token Bucket
- **Priorización**: Tareas de alta prioridad tienen más límite
- **Headers informativos**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## Caching

Sistema de cache con:
- **TTL configurable** por tipo de contenido
- **Backend flexible**: Memoria o Redis
- **Invalidación por patrón**
- **Estadísticas de hit/miss**

## Monitoring

Métricas disponibles:
- Total de requests
- Tasa de errores
- Tiempo promedio de respuesta
- Tareas activas
- Estadísticas por modalidad

## Integración

Esta API utiliza la infraestructura existente en `core/`:
- `core/api_utils.py` - Utilidades base para APIs
- `core/distributed_utils.py` - Escalabilidad distribuida
- `core/experiment_tracking.py` - Tracking de experimentos
- `core/performance.py` - Optimización de rendimiento

## Ejemplos

Ver `example_usage.py` para ejemplos completos de uso.

## Desarrollo

Ver `PRODUCTOS_SORA2_LIKE.md` sección 7.1 para más detalles sobre la implementación.

## Nuevas Funcionalidades

### ✅ Sistema de Cola de Tareas
- Procesamiento asíncrono con priorización
- Múltiples workers concurrentes
- Callbacks automáticos
- Estadísticas de cola

### ✅ Integración con Sora
- Generadores de video integrados
- Text-to-Video
- Image-to-Video
- Preparado para Video-to-Video

### ✅ Sistema de Autenticación
- API Keys
- JWT (preparado)
- Rate limiting por usuario

### ✅ Configuración Mejorada
- Variables de entorno
- Configuración centralizada
- Fácil personalización

### ✅ Tests
- Tests para modelos
- Tests para rate limiting
- Base para tests de endpoints

### ✅ Script de Ejecución
- `run_server.py` para fácil inicio
- Argumentos de línea de comandos
- Configuración flexible

## Estructura Completa

```
multimodal_api/
├── __init__.py
├── README.md
├── api_server.py          # Servidor principal
├── endpoints.py            # Endpoints REST
├── models.py               # Modelos Pydantic
├── config.py               # Configuración
├── task_queue.py           # Cola de tareas asíncrona
├── auth.py                 # Autenticación
├── run_server.py           # Script de ejecución
├── example_usage.py        # Ejemplos
├── generators/             # Generadores por modalidad
│   ├── __init__.py
│   └── video_generator.py  # Generador de video (integra Sora)
├── middleware/             # Middleware
│   ├── __init__.py
│   ├── rate_limiter.py
│   ├── cache.py
│   └── monitoring.py
├── utils/                  # Utilidades
│   └── __init__.py
└── tests/                  # Tests
    ├── __init__.py
    ├── test_models.py
    └── test_rate_limiter.py
```

## Ejecución

### Opción 1: Script de ejecución
```bash
python -m multimodal_api.run_server
python -m multimodal_api.run_server --host 0.0.0.0 --port 8000 --reload
```

### Opción 2: Desde código
```python
from multimodal_api import MultimodalAPIServer

server = MultimodalAPIServer()
server.run()
```

## Configuración con Variables de Entorno

```bash
# Servidor
export API_HOST=0.0.0.0
export API_PORT=8000

# Rate Limiting
export RATE_LIMIT_MAX_REQUESTS=100
export RATE_LIMIT_WINDOW_SECONDS=60

# Cache
export CACHE_BACKEND=redis
export CACHE_REDIS_URL=redis://localhost:6379/0

# Queue
export QUEUE_MAX_WORKERS=4

# Autenticación
export AUTH_ENABLED=true
export JWT_SECRET_KEY=your-secret-key
```

## Funcionalidades Completadas

- [x] Implementar generadores reales por modalidad (Video, Image, Audio)
- [x] Integración con cola de procesamiento asíncrona
- [x] Sistema de almacenamiento de archivos
- [x] Validación robusta de parámetros
- [x] Sistema de webhooks robusto con firmas HMAC
- [x] Autenticación y autorización básica (API Keys + JWT)
- [x] Rate limiting inteligente con priorización
- [x] Caching optimizado (memoria + Redis)
- [x] Monitoring y métricas avanzadas
- [x] WebSockets para updates en tiempo real
- [x] Sistema de reintentos automáticos
- [x] Tests básicos
- [x] Script de ejecución
- [x] Configuración flexible con variables de entorno
- [x] Endpoint de estadísticas
- [x] Documentación OpenAPI mejorada
- [x] Sistema de métricas con histogramas y percentiles

## WebSockets

La API soporta WebSockets para recibir actualizaciones en tiempo real:

### Conectar a una tarea específica
```python
import asyncio
import websockets
import json

async def listen_to_task(task_id: str):
    uri = f"ws://localhost:8000/ws/task/{task_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Update: {data}")

# Ejecutar
asyncio.run(listen_to_task("your-task-id"))
```

### Conectar para updates generales
```python
uri = "ws://localhost:8000/ws/updates"
async with websockets.connect(uri) as websocket:
    while True:
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Update: {data}")
```

## Sistema de Reintentos

Las tareas fallidas se reintentan automáticamente con backoff exponencial:

```python
from multimodal_api.retry_manager import RetryManager, RetryConfig, RetryStrategy

retry_manager = RetryManager(
    RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
)

# Usar en procesamiento
result = await retry_manager.execute_with_retry(
    task_id="task-123",
    func=process_task,
    *args,
    **kwargs
)
```

## Sistema de Webhooks

Registra webhooks para recibir notificaciones cuando las tareas cambian de estado:

```python
import requests

# Registrar webhook
response = requests.post(
    "http://localhost:8000/webhooks",
    json={
        "webhook_id": "my-webhook",
        "url": "https://my-server.com/webhook",
        "secret": "my-secret-key",
        "events": ["task.completed", "task.failed"]
    }
)

# Ver estadísticas
stats = requests.get("http://localhost:8000/webhooks/stats?webhook_id=my-webhook")
print(stats.json())
```

### Eventos Disponibles
- `task.created` - Tarea creada
- `task.started` - Tarea iniciada
- `task.progress` - Actualización de progreso
- `task.completed` - Tarea completada
- `task.failed` - Tarea fallida
- `task.cancelled` - Tarea cancelada

### Verificación de Firma
Los webhooks incluyen firma HMAC-SHA256 en el header `X-Webhook-Signature`:

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    payload_str = json.dumps(payload, sort_keys=True)
    expected = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Sistema de Métricas

Accede a métricas detalladas del sistema:

```python
import requests

# Obtener métricas
metrics = requests.get("http://localhost:8000/metrics")
data = metrics.json()

print(f"Uptime: {data['uptime_seconds']}s")
print(f"Total requests: {data['counters']['api.requests.total']}")
print(f"P95 latency: {data['histograms']['api.request.duration']['p95']}s")
```

### Tipos de Métricas
- **Counters**: Eventos incrementales (requests, errores)
- **Gauges**: Valores actuales (tareas activas, tamaño de cola)
- **Histograms**: Distribuciones (duración de requests, latencia)
- **Timings**: Duraciones específicas

## Health Checks Avanzados

El sistema incluye health checks detallados para todos los componentes:

```python
# Health check básico
GET /health

# Health check detallado
GET /health/detailed

# Estado de circuit breakers
GET /circuit-breakers

# Estadísticas de load balancer
GET /load-balancer/stats
```

### Componentes Monitoreados
- **Cache**: Hit rate, tamaño, estadísticas
- **Task Queue**: Tamaño, workers, tareas activas
- **Storage**: Archivos, espacio utilizado
- **Rate Limiter**: Requests, límites
- **Generadores**: Estado de inicialización

## Circuit Breaker

Protege el sistema de fallos en cascada:

```python
from multimodal_api import CircuitBreakerManager, CircuitBreakerConfig

# Obtener circuit breaker
breaker = circuit_breaker_manager.get_breaker(
    "video_generator",
    CircuitBreakerConfig(
        failure_threshold=5,
        timeout_seconds=60
    )
)

# Usar en llamadas
try:
    result = await breaker.call_async(
        video_generator.generate,
        prompt, parameters
    )
except Exception as e:
    # Circuit abierto o error
    handle_error(e)
```

## Load Balancer

Distribuye carga entre múltiples backends:

```python
from multimodal_api import LoadBalancer, LoadBalancingStrategy

# Crear load balancer
lb = LoadBalancer(strategy=LoadBalancingStrategy.LEAST_CONNECTIONS)

# Agregar backends
lb.add_backend("worker1", weight=2)
lb.add_backend("worker2", weight=1)

# Seleccionar backend
backend_id = lb.select_backend()

# Registrar métricas
lb.record_request(backend_id, response_time=0.15, success=True)
```

### Estrategias Disponibles
- `ROUND_ROBIN`: Distribución circular
- `RANDOM`: Selección aleatoria
- `LEAST_CONNECTIONS`: Menor número de conexiones
- `WEIGHTED_ROUND_ROBIN`: Round robin ponderado
- `LEAST_RESPONSE_TIME`: Menor tiempo de respuesta

## Deduplicación Inteligente

El sistema detecta y previene requests duplicados:

```python
# Verificar duplicado
is_duplicate, existing_task_id = deduplication_manager.check_duplicate(
    prompt="A beautiful sunset",
    modality="video",
    parameters={"duration": 10}
)

if is_duplicate:
    # Retornar tarea existente
    return get_task(existing_task_id)
```

### Características
- **Detección Exacta**: Hash de prompt + parámetros
- **Detección Semántica**: Similitud usando embeddings (opcional)
- **Ventana Temporal**: Considera duplicados en ventana de tiempo
- **Estadísticas**: Tasa de duplicados, cache hits

### Endpoints
- `GET /deduplication/stats` - Estadísticas de deduplicación
- `POST /deduplication/clear` - Limpiar cache

## Optimización Automática

El sistema sugiere optimizaciones basadas en métricas:

```python
# Obtener sugerencias
GET /optimization/suggestions

{
  "suggestions": [
    {
      "type": "scale_up",
      "priority": "high",
      "message": "Cola grande (50 tareas). Considera aumentar workers.",
      "action": "increase_workers"
    }
  ]
}
```

### Tipos de Sugerencias
- **scale_up**: Aumentar workers
- **scale_down**: Reducir workers
- **performance**: Optimizar rendimiento
- **reliability**: Revisar errores

## Procesamiento de Batch Optimizado

El batch processor optimiza múltiples requests:

```python
from multimodal_api import BatchProcessor, BatchConfig

processor = BatchProcessor(
    BatchConfig(
        max_batch_size=100,
        enable_deduplication=True,
        enable_prioritization=True,
        enable_parallel_processing=True
    )
)

# Procesar batch optimizado
optimized_batch = processor.optimize_batch(batch)
results = await processor.process_batch_parallel(
    optimized_batch,
    process_func,
    max_concurrent=5
)
```

### Optimizaciones
- **Deduplicación**: Elimina requests duplicados
- **Priorización**: Ordena por prioridad
- **Agrupación**: Agrupa por modalidad
- **Procesamiento Paralelo**: Ejecuta en paralelo con límite

## Integración con Memory Module

El sistema puede usar el módulo de memoria para caching inteligente:

```python
# Ver estadísticas de memoria
GET /memory/stats

# Consolidar memoria
POST /memory/consolidate
```

### Características
- **Caching Inteligente**: Usa memoria episódica y semántica
- **Búsqueda Semántica**: Encuentra resultados similares
- **Consolidación**: Optimiza memoria automáticamente

## Versionado de API

El sistema soporta múltiples versiones:

```python
# Obtener información de versiones
GET /version

{
  "default_version": "v1",
  "latest_version": "v2",
  "supported_versions": ["v1", "v2"],
  "versions": {
    "v1": {
      "release_date": "2024-01-01",
      "deprecated": false
    },
    "v2": {
      "release_date": "2024-06-01",
      "deprecated": false
    }
  }
}
```

## Manejo de Errores Avanzado

Errores estructurados con categorización:

```python
# Ver estadísticas de errores
GET /errors/stats

{
  "total_errors": 150,
  "by_category": {
    "validation": 50,
    "rate_limit": 30,
    "processing": 70
  },
  "by_code": {
    "VALIDATION_ERROR": 50,
    "RATE_LIMIT_EXCEEDED": 30
  }
}
```

### Categorías de Errores
- **validation**: Errores de validación
- **authentication**: Errores de autenticación
- **rate_limit**: Rate limit excedido
- **processing**: Errores de procesamiento
- **storage**: Errores de almacenamiento
- **network**: Errores de red
- **internal**: Errores internos

## Próximos Pasos

- [x] WebSockets para updates en tiempo real
- [x] Generadores de imagen y audio completos
- [x] Sistema de reintentos automáticos
- [x] Sistema de webhooks robusto
- [x] Métricas avanzadas
- [x] Health checks avanzados
- [x] Circuit breaker pattern
- [x] Load balancer
- [x] Sistema de deduplicación inteligente
- [x] Optimizador de rendimiento automático
- [x] Procesador de batch optimizado
- [x] Integración con módulo de memory para caching inteligente
- [x] Sistema de versionado de API
- [x] Manejo avanzado de errores
- [x] Streaming de resultados (preparado)
- [ ] Almacenamiento persistente de tareas (Redis/PostgreSQL)
- [ ] Dashboard de monitoreo web
- [ ] Soporte para 3D
- [ ] Streaming de resultados
- [ ] Optimizaciones de rendimiento avanzadas
- [ ] Versionado de API (v1, v2, etc.)
- [ ] Integración con módulo de memoria para caching inteligente

