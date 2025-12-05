# Model Data Collection System

Sistema completo para recopilar datos de modelos y conectarse a las mejores fuentes de información disponibles.

## Estructura

```
model_data/
├── __init__.py              # Exporta clases principales
├── data_collector.py        # Recolecta datos de modelos
├── info_connector.py        # Se conecta a fuentes de información
├── data_aggregator.py       # Agrega y analiza datos
├── data_exporter.py         # Exporta datos a diferentes formatos
└── model_data_manager.py    # Gestor principal que coordina todo
```

## Características

### 1. Data Collector (`data_collector.py`)
Recolecta datos completos de modelos:
- Información del modelo (parámetros, device, dtype)
- Métricas acumuladas
- Configuración
- Resultados de benchmarks
- Metadata adicional

### 2. Info Connector (`info_connector.py`)
Se conecta a las mejores fuentes de información:
- **Paper Registry**: Papers disponibles, estadísticas, búsqueda
- **Modelos guardados**: Checkpoints y modelos persistidos
- **Benchmarks históricos**: Resultados de benchmarks previos
- **Categorías**: Análisis por categoría de papers

### 3. Data Aggregator (`data_aggregator.py`)
Agrega y analiza datos de múltiples modelos:
- Estadísticas agregadas por categoría
- Comparación de modelos
- Identificación de mejores modelos
- Análisis de benchmarks y métricas

### 4. Data Exporter (`data_exporter.py`)
Exporta datos a múltiples formatos:
- **JSON**: Datos estructurados
- **CSV**: Tablas para análisis
- **HTML**: Reportes visuales
- **Markdown**: Documentación

### 5. Model Data Manager (`model_data_manager.py`)
Gestor principal que coordina todo:
- Recolección desde registry
- Recolección desde modelos directos
- Agregación y análisis
- Exportación completa

## Uso

### Ejemplo Básico

```python
from model_data import ModelDataManager

# Inicializar gestor
manager = ModelDataManager()

# Recolectar datos desde registry
collected = manager.collect_from_registry(
    category='research',
    run_benchmarks=True,
    limit=10
)

# Agregar datos
aggregated = manager.aggregate_collected_data()

# Exportar reporte
exported = manager.export_all(format='html')
print(f"Reporte exportado: {exported}")
```

### Recolectar Datos de Modelos Específicos

```python
from model_data import ModelDataManager
from research.paper_malto import MALTOModule, MALTOConfig

# Crear modelos
config = MALTOConfig()
model1 = MALTOModule(config)
model2 = MALTOModule(config)

# Recolectar datos
manager = ModelDataManager()
collected = manager.collect_from_models(
    models=[model1, model2],
    paper_ids=['malto', 'malto'],
    categories=['research', 'research'],
    run_benchmarks=True
)
```

### Obtener Información del Registry

```python
from model_data import InfoConnector

connector = InfoConnector()

# Información completa del registry
registry_info = connector.get_registry_info()
print(f"Total papers: {registry_info['total_papers']}")

# Mejores papers
best_papers = connector.get_best_papers(category='research', top_k=5)
for paper in best_papers:
    print(f"{paper['paper_name']}: {paper['load_count']} cargas")

# Buscar papers
results = connector.search_papers(query='reasoning', category='research')
```

### Exportar Datos

```python
from model_data import ModelDataManager, DataExporter

manager = ModelDataManager()

# Recolectar datos
manager.collect_from_registry(category='research', limit=5)

# Exportar a diferentes formatos
exported_json = manager.export_all(format='json')
exported_csv = manager.export_all(format='csv')
exported_html = manager.export_all(format='html')
exported_md = manager.export_all(format='markdown')
```

### Generar Reporte Completo

```python
from model_data import ModelDataManager

manager = ModelDataManager()

# Generar reporte completo
report = manager.get_full_report(
    category='research',
    run_benchmarks=True,
    export_format='html'
)

print(f"Modelos recolectados: {report['collected_models']}")
print(f"Archivos exportados: {report['exported_files']}")
```

## Componentes Detallados

### ModelData

Estructura de datos que contiene toda la información de un modelo:

```python
@dataclass
class ModelData:
    model_name: str
    model_class: str
    paper_id: Optional[str]
    category: Optional[str]
    model_info: Dict[str, Any]
    config: Dict[str, Any]
    metrics: Dict[str, Any]
    parameters: Dict[str, Any]
    benchmarks: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    collected_at: float
    updated_at: float
```

### AggregatedData

Datos agregados de múltiples modelos:

```python
@dataclass
class AggregatedData:
    total_models: int
    categories: Dict[str, int]
    total_parameters: Dict[str, Any]
    benchmark_stats: Dict[str, Any]
    metrics_summary: Dict[str, Any]
    best_models: List[Dict[str, Any]]
    aggregated_at: float
```

## Integración con el Sistema

El sistema se integra perfectamente con:

- **Paper Registry**: Auto-descubrimiento de papers
- **Benchmark System**: Ejecución de benchmarks
- **Model Base**: Información de modelos
- **Export System**: Múltiples formatos de exportación

## Casos de Uso

1. **Análisis de Modelos**: Recolectar y analizar todos los modelos disponibles
2. **Comparación**: Comparar modelos por diferentes métricas
3. **Reportes**: Generar reportes automáticos de estado del sistema
4. **Monitoreo**: Monitorear uso y rendimiento de modelos
5. **Documentación**: Generar documentación automática de modelos

## Notas

- Los benchmarks pueden tomar tiempo dependiendo del número de modelos
- El sistema usa cache para optimizar consultas al registry
- Los datos se pueden exportar a múltiples formatos simultáneamente
- El sistema es thread-safe y puede usarse en producción



