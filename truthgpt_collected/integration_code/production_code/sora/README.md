# Sora - Generación de Video y Contenido Multimodal

Este módulo contiene implementaciones de productos tipo Sora 2 para generación de video, audio, imagen y contenido multimodal usando la infraestructura de `production_code`.

## ✨ Mejoras v2.0

- ✅ **Validación robusta**: Validación con Pydantic y sistema de validación personalizado
- ✅ **Manejo de errores mejorado**: Sistema completo de manejo de errores con recuperación
- ✅ **Sistema de monitoreo**: Monitoreo de métricas y alertas en tiempo real
- ✅ **Utilidades de testing**: Helpers y utilidades para facilitar testing
- ✅ **Utilidades de producción**: Configuración, health checks y logging estructurado
- ✅ **Integración mejorada**: Mejor integración con módulos core y otros módulos
- ✅ **Optimizaciones de rendimiento**: Flash attention, mixed precision, mejor manejo de memoria
- ✅ **Utilidades de exportación**: Funciones para guardar videos en múltiples formatos (MP4, GIF, frames)
- ✅ **Mejor manejo de errores**: Validaciones mejoradas y mensajes de error más informativos
- ✅ **Soporte para múltiples formatos**: Exportación a OpenCV, PIL, GIF, frames individuales
- ✅ **Procesamiento de video**: Redimensionamiento, normalización, suavizado temporal
- ✅ **Video-to-Video**: Transformación de videos existentes con estilización y mejora
- ✅ **Diffusion Schedulers**: Múltiples schedulers (Linear, Cosine, Quadratic, Sigmoid, DDPM, DDIM)
- ✅ **Ejemplos avanzados**: Ejemplos completos mostrando todas las capacidades
- ✅ **Performance Utilities**: Suite completa de herramientas de benchmarking y optimización
- ✅ **Tests Completos**: 50+ tests cubriendo todos los módulos y casos de uso
- ✅ **API REST Server**: Servidor FastAPI completo con endpoints para todas las funcionalidades
- ✅ **CLI Tools**: Herramientas de línea de comandos para uso fácil
- ✅ **Experiment Tracking**: Integración completa con wandb y mlflow
- ✅ **Rate Limiting**: Sistema de rate limiting para API
- ✅ **Advanced Processing**: Procesamiento avanzado (color grading, filtros, estabilización)
- ✅ **Video Cache**: Sistema de caché inteligente para videos generados
- ✅ **Batch Processing**: Procesamiento en lote de múltiples videos
- ✅ **Async Queue**: Sistema de colas asíncronas para procesamiento escalable
- ✅ **Webhooks**: Sistema de notificaciones vía webhooks
- ✅ **Video Quality**: Análisis y validación de calidad de videos
- ✅ **Presets**: Configuraciones predefinidas para diferentes casos de uso

## 📁 Estructura

```
sora/
├── __init__.py              # Exports principales
├── sora_base.py             # Clases base mejoradas para generación de video
├── text_to_video.py         # Generación de video desde texto mejorada
├── image_to_video.py        # Animación de imágenes estáticas mejorada
├── video_to_video.py        # Transformación de videos existentes (NUEVO)
├── diffusion_scheduler.py   # Schedulers para proceso de difusión (NUEVO)
├── video_utils.py           # Utilidades para procesamiento y exportación
├── example_usage.py         # Ejemplos básicos de uso
├── advanced_examples.py     # Ejemplos avanzados (NUEVO)
└── README.md                # Este archivo
```

## 🚀 Uso Rápido

### Text-to-Video

```python
from sora import TextToVideoConfig, TextToVideoModule
import torch

# Crear configuración
config = TextToVideoConfig(
    hidden_dim=512,
    video_length=16,
    resolution=(256, 256),
    fps=24
)

# Crear modelo
model = TextToVideoModule(config)
model.eval()

# Generar video desde texto
prompt = "A beautiful sunset over the ocean"
video, metadata = model.generate_from_text(prompt, num_inference_steps=10)

print(f"Video generado: {video.shape}")
print(f"Métricas: {metadata}")
```

### Image-to-Video

```python
from sora import ImageToVideoConfig, ImageToVideoModule
import torch
from PIL import Image
import torchvision.transforms as transforms

# Crear configuración
config = ImageToVideoConfig(
    hidden_dim=512,
    video_length=16,
    resolution=(256, 256),
    motion_strength=0.5
)

# Crear modelo
model = ImageToVideoModule(config)
model.eval()

# Cargar imagen
image = Image.open("image.jpg")
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor()
])
image_tensor = transform(image).unsqueeze(0)

# Animar imagen
video, metadata = model.animate_image(
    image_tensor,
    num_inference_steps=10,
    motion_strength=0.7
)

print(f"Video animado: {video.shape}")
```

### Video-to-Video

```python
from sora import VideoToVideoConfig, VideoToVideoModule
import torch

# Crear configuración
config = VideoToVideoConfig(
    hidden_dim=512,
    video_length=16,
    resolution=(256, 256),
    style_strength=0.6,
    enhancement_mode="denoise",
    temporal_consistency=0.8
)

# Crear modelo
model = VideoToVideoModule(config)
model.eval()

# Video de entrada
input_video = torch.randn(1, 16, 3, 256, 256)

# Referencia de estilo (opcional)
style_reference = torch.randn(1, 3, 256, 256)

# Transformar video
video, metadata = model.transform_video(
    input_video,
    style_reference=style_reference,
    num_inference_steps=10
)

print(f"Video transformado: {video.shape}")
```

### Diffusion Schedulers

```python
from sora import DiffusionScheduler, SchedulerType

# Crear scheduler
scheduler = DiffusionScheduler(
    num_train_timesteps=1000,
    scheduler_type=SchedulerType.COSINE
)

# Configurar timesteps para inferencia
timesteps = scheduler.set_timesteps(50)

# Usar en proceso de difusión
for t in timesteps:
    # ... proceso de denoising ...
    prev_sample = scheduler.step(model_output, t, sample)
```

## 🏗️ Arquitectura

### Base Classes

- **`VideoGenerationConfig`**: Configuración base para todos los módulos de video
- **`VideoGenerationModule`**: Módulo base con arquitectura temporal y espacial

### Componentes Clave

1. **TemporalAttention**: Atención temporal para coherencia entre frames
2. **SpatialConvBlock**: Procesamiento espacial de frames individuales
3. **Time Embedding**: Embeddings temporales para difusión

## 📊 Características

- ✅ Integración completa con `BasePaperModule`
- ✅ **Validación robusta con Pydantic** (validación automática de configuraciones)
- ✅ **Optimizaciones de rendimiento**:
  - Flash attention cuando está disponible
  - Mixed precision training
  - Mejor manejo de memoria
- ✅ **Utilidades de exportación**:
  - Guardar videos en MP4 (OpenCV)
  - Crear GIFs animados
  - Exportar frames individuales
  - Normalización y procesamiento
- ✅ Manejo de errores integrado con mensajes informativos
- ✅ Sistema de métricas y logging estructurado
- ✅ Save/Load de modelos
- ✅ Cache LRU opcional
- ✅ Gradient checkpointing
- ✅ Soporte para múltiples dispositivos

## 🔧 Configuración

### VideoGenerationConfig

```python
config = VideoGenerationConfig(
    hidden_dim=512,           # Dimensión de hidden states
    video_length=16,          # Número de frames
    resolution=(512, 512),   # Resolución (height, width)
    fps=24,                  # Frames por segundo
    temporal_layers=4,        # Capas de atención temporal
    diffusion_steps=50,      # Pasos de difusión
    latent_dim=256,          # Dimensión del espacio latente
    channels=3,              # Canales de salida (RGB)
    use_mixed_precision=False,  # Usar mixed precision (FP16)
    attention_dropout=0.1,   # Dropout en atención
    spatial_blocks=2          # Número de bloques espaciales
)
```

### TextToVideoConfig

```python
config = TextToVideoConfig(
    text_encoder_dim=768,     # Dimensión del encoder de texto
    text_encoder_layers=6,    # Capas del encoder
    max_text_length=128,      # Longitud máxima del texto
    use_clip=True             # Usar CLIP para encoding
)
```

### ImageToVideoConfig

```python
config = ImageToVideoConfig(
    image_encoder_dim=512,     # Dimensión del encoder de imagen
    motion_strength=0.5,      # Fuerza del movimiento (0.0-1.0)
    use_vae=True              # Usar VAE para encoding
)
```

## 🛠️ Utilidades de Video

### Exportación

```python
from sora import save_video_opencv, create_video_gif, save_video_frames

# Guardar como MP4
save_video_opencv(video, "output.mp4", fps=24)

# Crear GIF
create_video_gif(video, "output.gif", fps=24)

# Guardar frames individuales
save_video_frames(video, "frames/", prefix="frame")
```

### Procesamiento

```python
from sora import normalize_video, resize_video, temporal_smooth

# Normalizar video
video_norm = normalize_video(video, method="tanh")

# Redimensionar
video_resized = resize_video(video, size=(256, 256))

# Suavizar temporalmente
video_smooth = temporal_smooth(video, kernel_size=3)
```

## 🎨 Video-to-Video

### Características

- **Estilización**: Transferencia de estilo usando AdaIN
- **Mejora de calidad**: Denoising, upscaling, colorization
- **Consistencia temporal**: Preservación de estructura temporal
- **Múltiples modos**: Diferentes modos de mejora

### Modos de Mejora

- `denoise`: Reducción de ruido
- `upscale`: Mejora de resolución
- `colorize`: Colorización automática

## ⏱️ Diffusion Schedulers

### Tipos Disponibles

- **LINEAR**: Programación lineal (DDPM estándar)
- **COSINE**: Programación coseno (mejor para alta calidad)
- **QUADRATIC**: Programación cuadrática
- **SIGMOID**: Programación sigmoide
- **DDPM/DDIM**: Schedulers estándar de difusión

### Uso

```python
from sora import DiffusionScheduler, SchedulerType

scheduler = DiffusionScheduler(
    num_train_timesteps=1000,
    beta_start=0.0001,
    beta_end=0.02,
    scheduler_type=SchedulerType.COSINE
)
```

## ⚡ Performance Utilities

### Benchmarking

```python
from sora import benchmark_video_generation, TextToVideoModule, TextToVideoConfig

config = TextToVideoConfig(hidden_dim=256, video_length=16)
model = TextToVideoModule(config)

# Benchmark
results = benchmark_video_generation(
    model,
    input_shape=(1, 16, 3, 256, 256),
    num_runs=10
)

print(f"Mean time: {results['mean_time_ms']:.2f} ms")
print(f"FPS: {results['fps']:.2f}")
```

### Optimización

```python
from sora import optimize_model_for_inference, compile_model, optimize_batch_size

# Optimizar para inferencia
optimized_model = optimize_model_for_inference(model)

# Compilar con torch.compile (PyTorch 2.0+)
compiled_model = compile_model(model, mode="reduce-overhead")

# Encontrar batch size óptimo
optimal_batch = optimize_batch_size(model, base_shape=(16, 3, 256, 256))
```

### Perfilado de Memoria

```python
from sora import profile_memory_usage, estimate_model_size

# Perfilar uso de memoria
memory_info = profile_memory_usage(model, input_shape=(1, 16, 3, 256, 256))
print(f"Peak memory: {memory_info['peak_memory_mb']:.2f} MB")

# Estimar tamaño del modelo
size_info = estimate_model_size(model)
print(f"Model size: {size_info['total_size_mb']:.2f} MB")
```

## 🧪 Tests

Suite completa de tests disponible en `tests/test_sora.py`:

```bash
# Ejecutar todos los tests de Sora
pytest tests/test_sora.py

# Tests específicos
pytest tests/test_sora.py::TestTextToVideoModule
pytest tests/test_sora.py::TestVideoToVideoModule

# Con cobertura
pytest tests/test_sora.py --cov=sora
```

### Cobertura de Tests

- ✅ Configuraciones y validación
- ✅ Todos los módulos (Text-to-Video, Image-to-Video, Video-to-Video)
- ✅ Diffusion schedulers
- ✅ Utilidades de video
- ✅ Tests de integración
- ✅ Save/Load de modelos
- ✅ Edge cases y manejo de errores

## 🌐 API REST Server

### Iniciar Servidor

```bash
# Usando CLI
sora serve --host 0.0.0.0 --port 8000

# O directamente
python -m sora.api_server --host 0.0.0.0 --port 8000
```

### Endpoints Disponibles

**Generación de Video:**
- `POST /api/v1/text-to-video`: Genera video desde texto (síncrono)
- `POST /api/v1/text-to-video/batch`: Procesa batch de videos
- `POST /api/v1/text-to-video/async`: Encola tarea asíncrona
- `POST /api/v1/image-to-video`: Anima imagen estática

**Gestión de Tareas:**
- `GET /api/v1/tasks/{task_id}`: Obtiene estado de tarea
- `GET /api/v1/tasks/{task_id}/result`: Obtiene resultado de tarea

**Caché:**
- `GET /api/v1/cache/stats`: Estadísticas de caché
- `DELETE /api/v1/cache`: Limpia caché

**Cola:**
- `GET /api/v1/queue/stats`: Estadísticas de cola

**Otros:**
- `GET /api/v1/videos/{video_id}`: Descarga video generado
- `GET /api/v1/models`: Lista modelos cargados
- `GET /api/v1/metrics`: Métricas de API
- `GET /api/v1/rate-limit`: Información de rate limiting
- `GET /health`: Health check
- `GET /docs`: Documentación interactiva (Swagger UI)

### Ejemplo de Uso

```python
import requests

# Generar video desde texto
response = requests.post(
    "http://localhost:8000/api/v1/text-to-video",
    json={
        "prompt": "A beautiful sunset over the ocean",
        "num_inference_steps": 20,
        "fps": 24,
        "resolution": [256, 256]
    }
)

result = response.json()
video_id = result["video_id"]
download_url = result["download_url"]

# Descargar video
video_response = requests.get(f"http://localhost:8000{download_url}")
with open("output.mp4", "wb") as f:
    f.write(video_response.content)
```

## 🖥️ CLI Tools

### Instalación

```bash
# Asegúrate de tener click y rich instalados
pip install click rich
```

### Comandos Disponibles

```bash
# Generar video desde texto
sora text2video "A beautiful sunset" --output video.mp4 --steps 20

# Animar imagen
sora image2video image.jpg --output animated.mp4 --motion-strength 0.7

# Benchmark de rendimiento
sora benchmark --frames 16 --runs 10

# Información del modelo
sora model-info --hidden-dim 512 --frames 16

# Iniciar servidor API
sora serve --port 8000
```

### Opciones Comunes

- `--output, -o`: Archivo de salida
- `--steps, -s`: Pasos de inferencia
- `--seed`: Semilla para reproducibilidad
- `--fps`: Frames por segundo
- `--resolution, -r`: Resolución (height,width)
- `--frames, -f`: Número de frames
- `--hidden-dim`: Dimensión hidden

## 📊 Experiment Tracking

### Uso Básico

```python
from sora import SoraExperimentTracker, TextToVideoModule, TextToVideoConfig
import time

config = TextToVideoConfig(hidden_dim=512, video_length=16)
model = TextToVideoModule(config)
model.eval()

# Crear tracker
with SoraExperimentTracker(
    project="sora-experiments",
    experiment_name="text2video-test",
    use_wandb=True
) as tracker:
    # Generar video
    start_time = time.time()
    video, metadata = model.generate_from_text("A beautiful sunset")
    generation_time = time.time() - start_time
    
    # Loggear generación
    tracker.log_text_to_video(
        prompt="A beautiful sunset",
        video=video,
        metadata=metadata,
        generation_time=generation_time,
        config=config,
        video_path="output.mp4"
    )
```

## 🚦 Rate Limiting

### Configuración

```python
from sora import RateLimiter

limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000
)

# Verificar si está permitido
allowed, error = limiter.is_allowed(client_id="user123")
if not allowed:
    print(f"Rate limit: {error}")

# Obtener requests restantes
remaining = limiter.get_remaining(client_id="user123")
print(f"Remaining: {remaining}")
```

## 🎨 Advanced Processing

### Color Grading

```python
from sora import apply_color_grading

# Aplicar color grading
video_graded = apply_color_grading(
    video,
    brightness=0.1,
    contrast=1.2,
    saturation=1.3,
    hue=0.05
)
```

### Filtros Temporales

```python
from sora import apply_temporal_filter

# Filtro gaussiano temporal
video_filtered = apply_temporal_filter(
    video,
    filter_type="gaussian",
    kernel_size=5,
    sigma=1.0
)
```

### Estabilización

```python
from sora import stabilize_video, enhance_video_quality

# Estabilizar video
video_stable = stabilize_video(video, method="optical_flow")

# Mejorar calidad
video_enhanced = enhance_video_quality(
    video,
    sharpness=1.2,
    denoise_strength=0.1
)
```

### Mezcla de Videos

```python
from sora import blend_videos

# Mezclar dos videos
video_blended = blend_videos(
    video1,
    video2,
    alpha=0.5,
    blend_mode="linear"
)
```

## 💾 Video Cache

### Uso Básico

```python
from sora import VideoCache
from pathlib import Path

# Crear caché
cache = VideoCache(
    max_size=100,
    ttl_seconds=3600,
    cache_dir=Path("./cache"),
    use_redis=False
)

# Verificar si existe en caché
result = cache.get(
    prompt="A beautiful sunset",
    config={"hidden_dim": 512, "video_length": 16},
    seed=42
)

if result:
    video_path, metadata = result
    print(f"Video encontrado en caché: {video_path}")
else:
    # Generar video
    video, metadata = model.generate_from_text("A beautiful sunset")
    video_path = Path("output.mp4")
    save_video_opencv(video, str(video_path))
    
    # Guardar en caché
    cache.set(
        video_path=video_path,
        metadata=metadata,
        prompt="A beautiful sunset",
        config={"hidden_dim": 512},
        seed=42
    )

# Estadísticas
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2f}%")
```

## 📦 Batch Processing

### Procesar Múltiples Videos

```python
from sora import BatchProcessor, TextToVideoConfig
from pathlib import Path

processor = BatchProcessor(max_workers=4, use_parallel=True)

prompts = [
    "A beautiful sunset",
    "A cat playing piano",
    "A futuristic city"
]

config = TextToVideoConfig(hidden_dim=256, video_length=8)

def progress_callback(current, total, prompt):
    print(f"Procesando {current}/{total}: {prompt}")

results = processor.process_text_to_video_batch(
    prompts=prompts,
    config=config,
    output_dir=Path("./batch_output"),
    progress_callback=progress_callback
)

for result in results:
    if 'error' not in result:
        print(f"Video generado: {result['video_path']}")
```

## 🔄 Async Queue

### Procesamiento Asíncrono

```python
import asyncio
from sora import AsyncVideoQueue, TaskStatus

async def text_to_video_processor(payload):
    """Procesador para text-to-video."""
    prompt = payload['prompt']
    config = payload['config']
    
    # Generar video
    model = TextToVideoModule(config)
    video, metadata = model.generate_from_text(prompt)
    
    return {
        'video': video,
        'metadata': metadata
    }

# Crear cola
queue = AsyncVideoQueue(max_workers=2)
queue.register_processor("text_to_video", text_to_video_processor)

# Iniciar workers
await queue.start_async()

# Encolar tareas
task_id1 = await queue.enqueue(
    "text_to_video",
    {"prompt": "A sunset", "config": config},
    priority=1
)

task_id2 = await queue.enqueue(
    "text_to_video",
    {"prompt": "A cat", "config": config},
    priority=0
)

# Verificar estado
status = await queue.get_status(task_id1)
print(f"Estado: {status['status']}")

# Esperar resultado
result = await queue.get_result(task_id1)
print(f"Video generado: {result}")

# Detener cola
await queue.stop()
```

## 🔔 Webhooks

### Configurar Webhooks

```python
from sora import WebhookManager, Webhook, WebhookEvent

manager = WebhookManager()

# Registrar webhook
webhook = Webhook(
    url="https://example.com/webhook",
    events=[
        WebhookEvent.TASK_COMPLETED,
        WebhookEvent.VIDEO_GENERATED
    ],
    secret="your-secret-key"
)

await manager.register("webhook_1", webhook)

# Enviar notificación
await manager.send(
    WebhookEvent.VIDEO_GENERATED,
    {
        "video_id": "video123",
        "video_path": "/path/to/video.mp4",
        "metadata": {...}
    }
)
```

## 📊 Video Quality Analysis

### Analizar Calidad

```python
from sora import VideoQualityAnalyzer

analyzer = VideoQualityAnalyzer()

# Analizar video
metrics = analyzer.analyze(video)
print(f"Temporal Consistency: {metrics['temporal_consistency']}")
print(f"Sharpness: {metrics['sharpness']}")
print(f"Quality Score: {metrics.get('quality_score', 0.0)}")

# Validar calidad
is_valid, validation_metrics = analyzer.validate(
    video,
    min_quality=0.6,
    min_temporal_consistency=0.4
)

if is_valid:
    print("Video pasa validación de calidad")
else:
    print("Video no cumple estándares de calidad")
```

## 🎨 Presets

### Usar Presets

```python
from sora import PresetManager, PresetType

# Obtener configuración con preset
config = PresetManager.get_text_to_video_config(
    preset=PresetType.HIGH_QUALITY,
    resolution=(512, 512)  # Opcional: override
)

model = TextToVideoModule(config)

# Listar presets disponibles
presets = PresetManager.list_presets()
for name, info in presets.items():
    print(f"{name}: {info['description']}")
```

### Presets Disponibles

- **FAST**: Generación rápida, baja calidad (5-10s)
- **BALANCED**: Balance calidad/velocidad (20-30s)
- **HIGH_QUALITY**: Alta calidad (60-90s)
- **ULTRA_QUALITY**: Máxima calidad (3-5min)
- **LOW_RESOURCE**: Mínimos recursos (2-5s)

## ✅ Validation

### Validar Inputs

```python
from sora import SoraValidator

validator = SoraValidator()

# Validar resolución
resolution = validator.validate_resolution((256, 256))

# Validar video length
video_length = validator.validate_video_length(16)

# Validar prompt
prompt = validator.validate_prompt("A beautiful sunset", max_length=500)

# Validar tensor de video
video_tensor = validator.validate_video_tensor(video, expected_shape=(1, 16, 3, 256, 256))
```

## 🛡️ Error Handling

### Manejo de Errores

```python
from sora import (
    handle_errors,
    handle_async_errors,
    ErrorRecovery,
    SoraError,
    GenerationError
)

# Decorador para manejo de errores
@handle_errors(error_class=GenerationError)
def generate_video(prompt: str):
    # Tu código aquí
    pass

# Decorador async
@handle_async_errors(error_class=GenerationError)
async def generate_video_async(prompt: str):
    # Tu código aquí
    pass

# Retry automático
@ErrorRecovery.retry_on_failure(max_attempts=3, backoff_factor=1.0)
def generate_with_retry(prompt: str):
    # Tu código aquí
    pass
```

### Tipos de Errores

- `SoraError`: Error base
- `ConfigurationError`: Error de configuración
- `GenerationError`: Error durante generación
- `ValidationError`: Error de validación
- `ResourceError`: Error de recursos (memoria, GPU)

## 📊 Monitoring

### Monitoreo de Métricas

```python
from sora import SoraMonitor, AlertThreshold

monitor = SoraMonitor(history_size=1000)

# Registrar métricas
monitor.record_metric("generation_time", 2.5)
monitor.record_metric("video_quality", 0.85)

# Registrar múltiples métricas
monitor.record_metrics({
    "memory_usage": 0.7,
    "gpu_usage": 0.6,
    "queue_size": 10
})

# Agregar umbral de alerta
monitor.add_alert_threshold(
    metric_name="generation_time",
    threshold=5.0,
    comparison="gt",
    severity="warning",
    message="Tiempo de generación muy alto"
)

# Obtener estadísticas
stats = monitor.get_statistics("generation_time")
print(f"Mean: {stats['mean']}, Std: {stats['std']}")

# Obtener métricas actuales
current = monitor.get_current_metrics()
print(f"Uptime: {monitor.get_uptime()}")
```

## 🧪 Testing Utils

### Utilidades para Testing

```python
from sora import SoraTestHelper

helper = SoraTestHelper()

# Crear video dummy
dummy_video = helper.create_dummy_video(
    batch_size=1,
    frames=8,
    channels=3,
    height=64,
    width=64
)

# Crear configuración dummy
config = helper.create_dummy_config(
    config_type="text_to_video",
    hidden_dim=128
)

# Crear directorio temporal
temp_dir = helper.create_temp_dir()
try:
    # Tu código de testing aquí
    pass
finally:
    helper.cleanup_temp_dir(temp_dir)

# Validar video
helper.assert_video_shape(dummy_video, (1, 8, 3, 64, 64))
helper.assert_video_valid(dummy_video)

# Comparar videos
comparison = helper.compare_videos(video1, video2, tolerance=1e-5)
print(f"Videos iguales: {comparison['are_equal']}")
```

## 🏭 Production Utils

### Configuración de Producción

```python
from sora import ProductionConfig, create_production_environment

# Crear configuración de producción
config = ProductionConfig(
    enable_caching=True,
    enable_monitoring=True,
    enable_logging=True,
    max_retries=3,
    timeout=300.0
)

# Crear entorno de producción
env = create_production_environment(config)

# Health checks
health = env['health_checker'].check_all()
print(f"Overall health: {health['overall_health']}")

# Production logging
logger = env['logger']
logger.log_event(
    event_type="video_generation",
    message="Video generado exitosamente",
    metadata={"video_id": "123", "duration": 2.5},
    level="INFO"
)

# Obtener logs
recent_logs = logger.get_logs(event_type="video_generation", limit=10)
```

## 🚀 Deployment Manager

### Uso Básico

```python
from sora import SoraDeploymentManager, TextToVideoConfig

# Crear manager para variante integrada (memoria + redundancia)
manager = SoraDeploymentManager(
    generator_type="text_to_video",
    variant="integrated",
    video_config_kwargs={
        "hidden_dim": 512,
        "video_length": 16,
        "resolution": (256, 256),
        "fps": 24
    }
)

# Generar video
video, metadata = manager.generate_from_text(
    "A cinematic shot of a futuristic city at night",
    num_inference_steps=25
)

# Health checks
health = manager.health_check()
print(f"Health: {health['overall_health']}")

# Métricas
metrics = manager.get_monitor_metrics(last_n=5)
print(metrics)
```

## 📈 Próximas Funcionalidades

- [x] Video-to-Video (transformación de videos) ✅
- [x] Diffusion Schedulers ✅
- [x] Performance Utilities ✅
- [x] Tests Completos ✅
- [x] API REST Server ✅
- [x] CLI Tools ✅
- [x] Experiment Tracking ✅
- [x] Rate Limiting ✅
- [x] Advanced Processing ✅
- [x] Video Cache ✅
- [x] Batch Processing ✅
- [x] Async Queue ✅
- [x] Webhooks ✅
- [x] Video Quality Analysis ✅
- [x] Presets ✅
- [x] Validation System ✅
- [x] Error Handling ✅
- [x] Monitoring System ✅
- [x] Testing Utils ✅
- [x] Production Utils ✅
- [ ] Audio Generation (text-to-music, voice cloning)
- [ ] Multimodal Content (combinación de modalidades)
- [ ] 3D Generation (modelos y escenas 3D)
- [ ] Control granular (cámara, movimiento, iluminación)
- [ ] Integración con modelos reales (CLIP, Diffusion)

## 🔗 Integración

Este módulo se integra perfectamente con la infraestructura existente:

- **Core**: Usa `BasePaperModule` y `BasePaperConfig`
- **APIs**: Compatible con `core/api_utils.py`
- **Tracking**: Compatible con `core/experiment_tracking.py`
- **Testing**: Compatible con `core/testing.py`
- **Benchmarking**: Compatible con `core/benchmark.py`

## 📝 Ejemplos

Ver `example_video_generation.py` en el directorio raíz para ejemplos completos.

## 🛠️ Desarrollo

Para contribuir o extender este módulo:

1. Extender `VideoGenerationModule` para nuevos tipos de generación
2. Implementar encoders específicos (text, image, audio)
3. Agregar nuevos componentes de arquitectura
4. Integrar con modelos pre-entrenados reales

## 📚 Referencias

- Sora 2 (OpenAI): Generación de video desde texto
- Stable Video Diffusion: Animación de imágenes
- AnimateDiff: Animación de imágenes con difusión
- Video Diffusion Models: Arquitecturas de difusión para video

