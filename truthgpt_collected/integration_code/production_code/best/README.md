# Best Techniques Papers Module

Este módulo contiene implementaciones de las mejores técnicas de papers de investigación para mejorar el rendimiento de modelos de lenguaje.

## 📚 Papers Incluidos

### Paper 2506.10848v2
- **Técnicas**: Adaptive Layer Normalization y Gated Attention
- **Componentes**: `AdaptiveLayerNorm`, `GatedAttention`, `Paper2506_10848v2_BestTechniques`
- **URL**: https://arxiv.org/html/2506.10848v2

### Paper 2510.04871v1
- **Técnicas**: Ensemble Attention con Weighted Combination
- **Componentes**: `EnsembleAttention`, `Paper2510_04871v1_BestTechniques`
- **URL**: https://arxiv.org/html/2510.04871v1

## 🚀 Uso Rápido

### Paper 2506.10848v2 - Adaptive Layer Norm + Gated Attention

```python
from best import Paper2506_10848v2Config, Paper2506_10848v2_BestTechniques
import torch

# Crear configuración
config = Paper2506_10848v2Config(
    hidden_dim=512,
    num_heads=8,
    use_adaptive_layer_norm=True,
    use_gated_attention=True
)

# Crear modelo
model = Paper2506_10848v2_BestTechniques(config)

# Forward pass
x = torch.randn(2, 32, 512)  # [batch, seq, hidden_dim]
output = model(x)
print(f"Output shape: {output.shape}")

# Con attention mask
attention_mask = torch.ones(2, 32, dtype=torch.bool)
output = model(x, attention_mask=attention_mask)
```

### Paper 2510.04871v1 - Ensemble Attention

```python
from best import Paper2510_04871v1Config, Paper2510_04871v1_BestTechniques
import torch

# Crear configuración
config = Paper2510_04871v1Config(
    hidden_dim=512,
    num_heads=8,
    num_ensemble_heads=4,
    use_ensemble_attention=True,
    use_residual_connections=True
)

# Crear modelo
model = Paper2510_04871v1_BestTechniques(config)

# Forward pass
x = torch.randn(2, 32, 512)
output = model(x)
print(f"Output shape: {output.shape}")
```

## 🔧 Características Avanzadas

### Mixed Precision (FP16/BF16)

```python
# Usar mixed precision para inferencia más rápida
output = model(x, use_autocast=True)
```

### Gradient Checkpointing

```python
# Habilitar para ahorrar memoria
model.enable_gradient_checkpointing(True)
model.train()
```

### Compilación con torch.compile

```python
# Compilar para mejor rendimiento (PyTorch 2.0+)
compiled_model = model.compile_model(mode="reduce-overhead")
```

### Optimización para Inferencia

```python
# Optimizar para inferencia
model.optimize_for_inference()
```

### Estimación de Memoria

```python
# Estimar uso de memoria para diferentes configuraciones
memory_info = model.estimate_memory_usage(
    batch_size=4,
    seq_len=128,
    dtype=torch.float16
)
print(f"Total estimated: {memory_info['total_estimated_mb']:.2f} MB")
```

### Serialización

```python
# Guardar modelo
model.save_state_dict("model.pt")

# Cargar modelo
loaded_model = Paper2506_10848v2_BestTechniques.load_state_dict("model.pt")
```

### Métricas

```python
# Obtener métricas
metrics = model.get_metrics()
print(metrics)

# Resetear métricas
model.reset_metrics()

# Información del modelo
info = model.get_model_info()
print(f"Total parameters: {info['total_parameters']:,}")
```

## 📊 Benchmarking

```python
from best import Paper2506_10848v2_BestTechniques, Paper2506_10848v2Config
import torch

config = Paper2506_10848v2Config()
model = Paper2506_10848v2_BestTechniques(config)

# Benchmark básico
result = model.benchmark(
    batch_size=4,
    seq_len=128,
    num_runs=10
)
print(f"Average forward time: {result['avg_time']:.4f}s")
print(f"Throughput: {result['throughput']:.2f} tokens/s")
```

## 🎯 Integración con TruthGPT

```python
from best import (
    TruthGPT_Paper2506_10848v2_Integration,
    Paper2506_10848v2Config
)
import torch.nn as nn

# Modelo base (ejemplo)
base_model = nn.Sequential(
    nn.Linear(512, 512),
    nn.ReLU()
)

# Integrar técnicas del paper
config = Paper2506_10848v2Config()
enhanced_model = TruthGPT_Paper2506_10848v2_Integration(
    base_model,
    config
)

# Usar modelo mejorado
x = torch.randn(2, 32, 512)
output = enhanced_model(x)
```

## 📈 Características

- ✅ **Adaptive Layer Normalization**: Normalización adaptativa con parámetros aprendibles
- ✅ **Gated Attention**: Mecanismo de atención con gating
- ✅ **Ensemble Attention**: Múltiples cabezas de atención con combinación ponderada
- ✅ **Mixed Precision**: Soporte para FP16/BF16 con autocast
- ✅ **Gradient Checkpointing**: Ahorro de memoria durante entrenamiento
- ✅ **Compilación**: Soporte para torch.compile (PyTorch 2.0+)
- ✅ **Serialización**: Guardar y cargar modelos fácilmente
- ✅ **Métricas**: Tracking de métricas de rendimiento
- ✅ **Benchmarking**: Métodos integrados para medir rendimiento
- ✅ **Estimación de Memoria**: Cálculo de uso de memoria para diferentes configuraciones
- ✅ **Validación**: Validación robusta de inputs
- ✅ **NaN/Inf Detection**: Detección automática de valores problemáticos

## 🔍 Componentes Individuales

### AdaptiveLayerNorm

```python
from best import AdaptiveLayerNorm

norm = AdaptiveLayerNorm(hidden_dim=512)
x = torch.randn(2, 32, 512)
output = norm(x)
metrics = norm.get_metrics()
```

### GatedAttention

```python
from best import GatedAttention

attn = GatedAttention(hidden_dim=512, num_heads=8)
x = torch.randn(2, 32, 512)
output = attn(x)
metrics = attn.get_metrics()
```

### EnsembleAttention

```python
from best import EnsembleAttention

ensemble = EnsembleAttention(
    hidden_dim=512,
    num_heads=8,
    num_ensemble=4,
    use_weighted_combination=True
)
x = torch.randn(2, 32, 512)
output = ensemble(x)
metrics = ensemble.get_metrics()
```

## 🔄 Comparación entre Papers

```python
from best import PaperComparator

comparator = PaperComparator()
comparison = comparator.full_comparison()

print(f"Faster model: {comparison.differences['performance']['faster']}")
print(f"More efficient: {comparison.differences['memory']['more_efficient']}")

comparator.print_comparison_report(comparison)
```

## 🔍 Análisis Avanzado

### Análisis de Capas

```python
analysis = model.analyze_layers()
print(f"Total layers: {analysis['total_layers']}")
print(f"Layer types: {analysis['layer_types']}")
```

### Conversión de Dtype

```python
model.convert_dtype(torch.float16)
```

### Análisis de Gradientes

```python
# Obtener norma de gradientes
grad_norm = model.get_gradient_norm()

# Analizar gradientes
grad_analysis = model.analyze_gradients()
print(f"Total norm: {grad_analysis['total_norm']:.4f}")
print(f"Parameters with gradients: {grad_analysis['param_count']}")

# Clipping de gradientes
clipped_norm = model.clip_gradients(max_norm=1.0)
```

### Exportación de Modelos

```python
# Exportar a ONNX
model.export_to_onnx('model.onnx', input_shape=(1, 128, 512))

# Exportar a TorchScript
model.export_to_torchscript('model.pt', method='trace')
```

### Setup de Entrenamiento

```python
# Setup optimizer
optimizer = model.setup_optimizer(learning_rate=1e-4, optimizer_type='adamw')

# Setup scheduler
scheduler = model.setup_scheduler(
    optimizer,
    scheduler_type='cosine',
    max_steps=1000
)

# Freeze/unfreeze parámetros
model.freeze_parameters(freeze=True)
```

### Health Check y Validación

```python
# Health check
health = model.health_check()
print(f"Status: {health['status']}")

# Validación del modelo
validation = model.validate_model()
if validation['valid']:
    print("Model is valid")
else:
    print(f"Issues: {validation['issues']}")
```

### Reporte Completo

```python
# Generar reporte completo del modelo
report = model.generate_comprehensive_report(
    include_benchmark=True,
    include_memory_estimation=True
)

print(f"Status: {report['health']['status']}")
print(f"Parameters: {report['model_info']['total_parameters']:,}")
print(f"Memory: {report['memory_estimation']['total_estimated_mb']:.2f} MB")
```

## 📝 Ejemplos Completos

Ver `example_usage.py` para ejemplos más detallados (19 ejemplos incluidos).

## 🛠️ Requisitos

- PyTorch >= 1.9.0
- Python >= 3.7
- torch.compile requiere PyTorch >= 2.0.0

## 📚 Referencias

- Paper 2506.10848v2: https://arxiv.org/html/2506.10848v2
- Paper 2510.04871v1: https://arxiv.org/html/2510.04871v1

