# 📊 Sistema de Monitoreo y Métricas

## ✨ Características

- ✅ **MetricsCollector**: Recolección de métricas
- ✅ **HealthMonitor**: Health checks de módulos
- ✅ **SystemMonitor**: Monitor completo del sistema
- ✅ **Visualizaciones**: Gráficos de métricas
- ✅ **Exportación**: Reportes en JSON

## 🎯 Uso

### Recolección de Métricas

```python
from monitoring_system import MetricsCollector

collector = MetricsCollector()

# Contadores
collector.increment("requests.total")
collector.increment("requests.success", 5)

# Gauges
collector.set_gauge("memory.usage", 0.75)

# Histogramas
collector.record_histogram("response.time", 0.15)

# Timers
collector.record_timer("operation.duration", 1.5)

# Obtener resumen
summary = collector.get_metric_summary("requests.total")
```

### Health Checks

```python
from monitoring_system import get_system_monitor

monitor = get_system_monitor()

# Health check de un módulo
health = monitor.health_monitor.check_module("memory")
print(f"Status: {health.status}")

# Health checks de todos
all_health = monitor.health_monitor.check_all()

# Salud general
overall = monitor.health_monitor.get_overall_health()
```

### Estado del Sistema

```python
# Obtener estado completo
status = monitor.get_system_status()

# Exportar reporte
monitor.export_report("system_report.json")

# Visualizar métricas
monitor.visualize_metrics("metrics.png")
```

## 📊 Tipos de Métricas

- **Counter**: Contadores incrementales
- **Gauge**: Valores actuales
- **Histogram**: Distribución de valores
- **Timer**: Duraciones de operaciones

## 🔍 Health Checks

Health checks automáticos para:
- Memory module
- Redundancy module
- (Extensible a otros módulos)

## 📈 Visualizaciones

- Gráficos de barras para counters
- Gráficos horizontales para gauges
- Pie charts para health status
- Timeline para timers

## 🚀 CLI

```bash
# Estado del sistema
python cli_unified.py monitor status

# Health checks
python cli_unified.py monitor health

# Métricas
python cli_unified.py monitor metrics

# Exportar reporte
python cli_unified.py monitor export --output report.json

# Visualizar
python cli_unified.py monitor visualize --output metrics.png
```

## 🎉 Resultado

Sistema completo de monitoreo con:
- ✅ Recolección de métricas
- ✅ Health checks automáticos
- ✅ Visualizaciones
- ✅ Exportación de reportes
- ✅ Integración con CLI

