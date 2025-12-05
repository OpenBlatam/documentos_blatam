# Módulo de Redundancia

Sistema de supresión de redundancia para procesamiento masivo (bulk processing) basado en el paper 2510.00071.

## Características

- ✅ **Detección de redundancia** con múltiples métodos (cosine, euclidean, semantic)
- ✅ **Clustering jerárquico** optimizado
- ✅ **Procesamiento masivo** eficiente
- ✅ **Métricas de reducción** y estadísticas detalladas
- ✅ **Selección inteligente** de representantes
- ✅ **Batch processing** optimizado
- ✅ **Caché LRU avanzado** para matrices de similitud
- ✅ **Procesador optimizado** para batches grandes
- ✅ **Optimizaciones GPU** con soporte CUDA
- ✅ **Procesamiento paralelo** para batches grandes
- ✅ **Precisión mixta (FP16)** para mejor rendimiento
- ✅ **Analytics avanzados** y optimización de parámetros
- ✅ **Benchmarking** integrado
- ✅ **Exportación** de reportes y datos
- ✅ **Suite completa de tests** (34 tests)
- ✅ **Logging estructurado** con contexto y métricas
- ✅ **Perfiles de configuración** predefinidos (speed, balanced, quality, etc.)
- ✅ **Utilidades de debugging** con logging detallado y profiling
- ✅ **Sistema de alertas** con reglas configurables
- ✅ **Utilidades de testing** con generadores de datos y helpers
- ✅ **Sistema de plugins** extensible para personalización
- ✅ **Sistema de serialización** avanzado con versionado y compresión

## Instalación

El módulo está integrado en el proyecto. Asegúrate de tener las dependencias instaladas:

```bash
pip install torch numpy
```

## Uso Básico

### Crear un supresor de redundancia

```python
from redundancy import create_redundancy_suppressor

suppressor = create_redundancy_suppressor(
    "2510_00071",
    similarity_threshold=0.85,
    redundancy_detection_method="cosine"
)
```

### Procesar un batch

```python
import torch

items = torch.randn(100, 32, 512)  # [batch_size, seq_len, hidden_dim]
unique_items, stats = suppressor.process_bulk(items)

print(f"Items originales: {stats['original_size']}")
print(f"Items únicos: {stats['reduced_size']}")
print(f"Tasa de reducción: {stats['reduction_rate']:.2%}")
```

## Configuración

### Paper2510_00071Config

```python
from redundancy import Paper2510_00071Config

config = Paper2510_00071Config(
    similarity_threshold=0.85,              # Umbral de similitud (0.0-1.0)
    use_hierarchical_clustering=True,       # Usar clustering jerárquico
    max_cluster_size=100,                   # Tamaño máximo de cluster
    redundancy_detection_method="cosine",  # Método: "cosine", "euclidean", "semantic"
    bulk_processing_batch_size=1000         # Tamaño de batch para procesamiento masivo
)
```

## Funciones de Utilidad

### Encontrar duplicados

```python
from redundancy import find_duplicate_items

items = torch.randn(50, 32, 512)
duplicates = find_duplicate_items(items, threshold=0.85, method="cosine")

for idx1, idx2, similarity in duplicates:
    print(f"Items {idx1} y {idx2} son similares: {similarity:.3f}")
```

### Deduplicación de batch

```python
from redundancy import batch_deduplicate

items = torch.randn(100, 32, 512)
unique_items, stats = batch_deduplicate(
    items,
    threshold=0.85,
    method="cosine",
    keep_strategy="first"  # "first", "last", "center"
)
```

### Comparar métodos

```python
from redundancy import compare_redundancy_methods

items = torch.randn(50, 32, 512)
results = compare_redundancy_methods(items, threshold=0.85)

for method, result in results.items():
    print(f"{method}: {result['reduction_rate']:.2%} reducción")
```

### Optimizar threshold

```python
from redundancy import optimize_threshold

items = torch.randn(100, 32, 512)
result = optimize_threshold(
    items,
    method="cosine",
    target_reduction_rate=0.3,  # 30% de reducción objetivo
    threshold_range=(0.7, 0.95),
    num_samples=20
)

print(f"Threshold óptimo: {result['optimal_threshold']:.3f}")
```

## Analytics

### Sistema de analytics

```python
from redundancy import RedundancyAnalytics, Paper2510_00071_RedundancySuppressor, Paper2510_00071Config
import time

analytics = RedundancyAnalytics()
config = Paper2510_00071Config()
suppressor = Paper2510_00071_RedundancySuppressor(config)

for batch in batches:
    items = batch
    start_time = time.time()
    unique_items, stats = suppressor.process_bulk(items)
    processing_time = time.time() - start_time
    
    analytics.record_batch(
        items.size(0),
        unique_items.size(0),
        processing_time,
        method="cosine"
    )

summary = analytics.get_summary()
print(f"Tasa promedio de reducción: {summary['metrics']['avg_reduction_rate']:.2%}")

# Comparar métodos
comparison = analytics.compare_methods()
for method, stats in comparison.items():
    print(f"{method}: {stats['avg_reduction_rate']:.2%}")

# Exportar reporte
analytics.export_report("redundancy_report.json")
```

## Optimización

### Optimizador de parámetros

```python
from redundancy import RedundancyOptimizer, Paper2510_00071_RedundancySuppressor, Paper2510_00071Config

config = Paper2510_00071Config()
suppressor = Paper2510_00071_RedundancySuppressor(config)
optimizer = RedundancyOptimizer(suppressor)

# Optimizar threshold
sample_items = torch.randn(50, 32, 512)
result = optimizer.optimize_threshold(
    sample_items,
    target_reduction_rate=0.3
)

# Encontrar método óptimo
result = optimizer.find_optimal_method(sample_items, threshold=0.85)
```

## Exportación

### Exportar reportes

```python
from redundancy import RedundancyExporter

# Exportar a JSON
data = {
    'stats': {...},
    'metrics': {...}
}
RedundancyExporter.export_to_json(data, "report.json")

# Exportar clusters
clusters = [[0, 1, 2], [3, 4], [5, 6, 7, 8]]
items = torch.randn(9, 32, 512)
RedundancyExporter.export_clusters(clusters, items, "clusters.json")
```

## Métodos de Detección

### Cosine Similarity
- **Ventaja**: Rápido y eficiente
- **Uso**: General, recomendado para embeddings normalizados
- **Rango**: 0.0 - 1.0

### Euclidean Distance
- **Ventaja**: Considera magnitudes
- **Uso**: Cuando la magnitud es importante
- **Rango**: Convertido a similitud (0.0 - 1.0)

### Semantic Similarity
- **Ventaja**: Captura relaciones semánticas
- **Uso**: Para embeddings semánticos avanzados
- **Rango**: 0.0 - 1.0 (softmax)

### Logging Estructurado

```python
from redundancy import RedundancyLogger, log_operation_context, log_function_call

logger = RedundancyLogger("my_module")

logger.log_processing_start(
    batch_size=100,
    method="cosine",
    threshold=0.85
)

with log_operation_context("process_batch", batch_id="123"):
    unique_items, stats = suppressor.process_bulk(items)

@log_function_call
def my_processing_function(items):
    return suppressor.process_bulk(items)
```

### Perfiles de Configuración

```python
from redundancy import (
    PerformanceProfile,
    create_config_from_profile,
    get_recommended_profile,
    RedundancyConfigManager
)

# Crear configuración desde perfil
speed_config = create_config_from_profile(PerformanceProfile.SPEED)

# Recomendación automática
profile = get_recommended_profile("speed", data_size=10000)

# Gestor de configuración
config_manager = RedundancyConfigManager()
config_manager.load_profile(PerformanceProfile.QUALITY)
config_manager.update_config({'similarity_threshold': 0.90})
```

### Debugging

```python
from redundancy import create_redundancy_debugger

debugger = create_redundancy_debugger(enabled=True)

# Medir tiempo de operación
result = debugger.time_operation("process", suppressor.process_bulk, items)

# Obtener estadísticas
stats = debugger.get_operation_stats()
print(f"Operaciones: {stats['total_operations']}")

# Exportar reporte
debugger.export_debug_report("debug_report.json")
```

### Sistema de Alertas

```python
from redundancy import create_redundancy_alert_system, AlertLevel

alert_system = create_redundancy_alert_system()

# Verificar alertas
context = {
    'error_rate': 0.15,
    'reduction_rate': 0.03,
    'processing_time': 6.0
}
alerts = alert_system.check_alerts(context)

# Registrar handler personalizado
def handle_critical(alert):
    print(f"ALERTA CRÍTICA: {alert.message}")

alert_system.register_handler(AlertLevel.CRITICAL, handle_critical)

# Obtener resumen
summary = alert_system.get_alert_summary()
```

### Utilidades de Testing

```python
from redundancy import RedundancyTestUtils, create_test_suppressor, run_quick_test

# Generar datos de prueba
test_items = RedundancyTestUtils.generate_test_items(
    batch_size=100,
    duplicate_ratio=0.3
)

# Crear supresor de prueba
suppressor = create_test_suppressor(similarity_threshold=0.85)

# Test rápido
result = run_quick_test(suppressor, test_items, expected_min_reduction=0.2)
print(f"Test pasado: {result['passed']}")

# Verificar sin duplicados
is_unique = RedundancyTestUtils.assert_no_duplicates(test_items)
```

### Sistema de Plugins

```python
from redundancy import (
    register_plugin,
    get_plugin,
    list_plugins,
    SimilarityMethodPlugin,
    PluginType
)

# Crear plugin personalizado
class MySimilarityPlugin(SimilarityMethodPlugin):
    def get_metadata(self):
        return PluginMetadata(
            name="my_similarity",
            version="1.0.0",
            description="Mi método de similitud",
            author="Yo",
            plugin_type=PluginType.SIMILARITY_METHOD
        )
    
    def initialize(self):
        return True
    
    def compute_similarity(self, embeddings, **kwargs):
        # Implementación personalizada
        return similarity_matrix

# Registrar plugin
plugin = MySimilarityPlugin()
register_plugin(plugin)

# Usar plugin
plugin = get_plugin("my_similarity")
similarity = plugin.compute_similarity(embeddings)

# Listar plugins
all_plugins = list_plugins()
```

### Serialización Avanzada

```python
from redundancy import create_serializer

# Crear serializador
serializer = create_serializer(compress=True, include_metadata=True)

# Serializar datos
data = {'items': items, 'stats': stats}
serialized = serializer.serialize(data, format="json")

# Guardar en archivo
serializer.save_to_file(data, "backup.json")

# Cargar desde archivo
loaded_data = serializer.load_from_file("backup.json")
```

## Ejemplos Completos

Ver `example_usage.py` para ejemplos detallados de uso.

```bash
python redundancy/example_usage.py
```

## Funciones Helper Avanzadas

### Health Report

```python
from redundancy import get_redundancy_health_report

health = get_redundancy_health_report(suppressor)
print(f"Estado: {health['status']}")
print(f"Advertencias: {health['warnings']}")
print(f"Recomendaciones: {health['recommendations']}")
```

### Merge de Supresores

```python
from redundancy import merge_redundancy_suppressors

result = merge_redundancy_suppressors(
    source_suppressor,
    target_suppressor,
    merge_strategy="metrics"  # "metrics", "config", "both"
)
```

### Exportar/Importar Estado

```python
from redundancy import export_suppressor_state, import_suppressor_state

# Exportar
export_suppressor_state(suppressor, "state.json", include_metrics=True)

# Importar
import_suppressor_state(suppressor, "state.json", load_metrics=True)
```

### Validación de Configuración

```python
from redundancy import validate_redundancy_config

is_valid, errors = validate_redundancy_config(config, strict=True)
if not is_valid:
    print(f"Errores: {errors}")
```

### Recomendación de Método

```python
from redundancy import recommend_similarity_method

method = recommend_similarity_method(
    use_case="semantic",
    performance_priority="accuracy"
)
```

### Integración con Memoria

```python
from redundancy import (
    create_redundancy_suppressor,
    RedundancyMemoryIntegration
)

suppressor = create_redundancy_suppressor('2510_00071')
integration = RedundancyMemoryIntegration(suppressor, memory_system)

episodes = torch.randn(100, 32, 512)
optimized_episodes, stats = integration.optimize_memory_episodes(episodes)
```

### Procesamiento en Streaming

```python
from redundancy import RedundancyStreamingProcessor

processor = RedundancyStreamingProcessor(
    suppressor,
    buffer_size=100,
    flush_interval=5.0
)

for item in data_stream:
    unique_item = processor.add_item(item)
    if unique_item is not None:
        process(unique_item)
```

### Visualización

```python
from redundancy import RedundancyVisualizer

visualizer = RedundancyVisualizer(output_dir="./reports")
report = visualizer.generate_comprehensive_report(suppressor)
```

### Optimizaciones GPU

```python
from redundancy import (
    GPUOptimizedRedundancyProcessor,
    ParallelRedundancyProcessor,
    optimize_for_device,
    get_gpu_memory_stats
)

# Procesador optimizado para GPU
gpu_processor = GPUOptimizedRedundancyProcessor(
    suppressor,
    device=torch.device('cuda'),
    use_mixed_precision=True
)
unique_items, stats = gpu_processor.process_bulk_gpu(items)

# Procesamiento paralelo
parallel_processor = ParallelRedundancyProcessor(suppressor, max_workers=4)
unique_items, stats = parallel_processor.process_bulk_parallel(items)

# Optimización automática según dispositivo
unique_items, stats = optimize_for_device(items, suppressor)

# Estadísticas de GPU
gpu_stats = get_gpu_memory_stats()
print(f"Memoria GPU: {gpu_stats['memory_allocated_mb']:.2f} MB")
```

### Monitoreo y Observabilidad

```python
from redundancy import create_redundancy_monitor, RedundancyMonitor

# Crear monitor
monitor = create_redundancy_monitor(suppressor, enable_monitoring=True)

# Registrar procesamiento
monitor.record_processing(
    original_size=100,
    reduced_size=80,
    processing_time=0.5,
    success=True
)

# Health check
health = monitor.get_health_check()
print(f"Status: {health.status}")

# Resumen de métricas
summary = monitor.get_metrics_summary()
print(f"Procesados: {summary['processed_count']}")
```

## API Reference

### Clases Principales

- `Paper2510_00071Config`: Configuración del supresor
- `Paper2510_00071_RedundancySuppressor`: Supresor principal
- `TruthGPT_Paper2510_00071_Integration`: Integración con TruthGPT
- `RedundancyAnalytics`: Sistema de analytics
- `RedundancyOptimizer`: Optimizador de parámetros
- `RedundancyExporter`: Exportador de datos

### Funciones de Utilidad

- `create_redundancy_suppressor()`: Factory function
- `get_available_modules()`: Obtener módulos disponibles
- `recommend_similarity_method()`: Recomendar método de similitud
- `estimate_optimal_threshold()`: Estimar threshold óptimo
- `validate_redundancy_config()`: Validar configuración
- `compute_similarity_batch()`: Calcular matriz de similitud
- `find_duplicate_items()`: Encontrar duplicados
- `batch_deduplicate()`: Deduplicar batch
- `calculate_reduction_stats()`: Calcular estadísticas
- `export_redundancy_report()`: Exportar reporte
- `compare_redundancy_methods()`: Comparar métodos
- `optimize_threshold()`: Optimizar threshold

### Funciones Helper

- `get_redundancy_health_report()`: Reporte de salud
- `merge_redundancy_suppressors()`: Fusionar supresores
- `export_suppressor_state()`: Exportar estado
- `import_suppressor_state()`: Importar estado

### Caché y Optimización

- `LRUSimilarityCache`: Caché LRU para matrices de similitud
- `OptimizedRedundancyProcessor`: Procesador optimizado para batches grandes
- `RedundancyBenchmark`: Sistema de benchmarking
- `run_quick_benchmark()`: Benchmark rápido

### Integración con Otros Módulos

- `RedundancyMemoryIntegration`: Integración con módulo de memoria
- `RedundancyPipelineIntegration`: Integración en pipelines
- `RedundancyStreamingProcessor`: Procesador para streaming de datos
- `create_integrated_redundancy_system()`: Crea sistema integrado

### Visualización

- `RedundancyVisualizer`: Genera gráficos y visualizaciones
- Gráficos de reducción a lo largo del tiempo
- Distribución de clusters
- Visualización de matrices de similitud
- Reportes completos con visualizaciones

## Referencias

- Paper: [2510.00071 - Redundancy Suppression for Bulk Processing](https://arxiv.org/abs/2510.00071)

## Licencia

Véase el archivo LICENSE del proyecto principal.

