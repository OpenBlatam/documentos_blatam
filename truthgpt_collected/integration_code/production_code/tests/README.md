# Tests - Production Code

Suite completa de tests para el código de producción de modelos de papers.

## Estructura

```
tests/
├── __init__.py
├── conftest.py              # Fixtures y configuración compartida
├── test_base_config.py      # Tests para BasePaperConfig
├── test_base_module.py      # Tests para BasePaperModule
├── test_malto_module.py     # Tests para MALTOModule
├── test_inference_modules.py # Tests para módulos de inferencia (VLLM, etc.)
├── test_integration.py      # Tests de integración
├── test_improve_models.py   # Tests para improve_models.py
└── README.md                # Este archivo
```

## Ejecutar Tests

### Todos los tests
```bash
pytest
```

### Tests específicos
```bash
pytest tests/test_base_config.py
pytest tests/test_malto_module.py::TestMALTOModule::test_forward_pass_basic
```

### Con cobertura
```bash
pytest --cov=core --cov=research --cov=inference
```

### Tests marcados
```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Verbose
```bash
pytest -v
pytest -vv  # Más verbose
```

## Cobertura

Los tests cubren:

- ✅ **BasePaperConfig**: Validación, serialización, edge cases
- ✅ **BasePaperModule**: Inicialización, validación, métricas, save/load
- ✅ **MALTOModule**: Forward pass, uncertainty quantification, NLI validation
- ✅ **Módulos de inferencia**: VLLM y otros
- ✅ **Integración**: Workflows completos, serialización, métricas
- ✅ **improve_models.py**: Mejora automática de modelos

## Fixtures

Las fixtures disponibles en `conftest.py`:

- `temp_dir`: Directorio temporal para archivos de test
- `sample_config`: Configuración de ejemplo
- `sample_hidden_states`: Tensor de hidden states de ejemplo
- `sample_hidden_states_small`: Tensor pequeño
- `sample_hidden_states_large`: Tensor grande
- `device`: Device a usar (cuda/cpu)
- `dtype`: Dtype a usar

## Escribir Nuevos Tests

### Template básico
```python
import pytest
import torch
from core.paper_base import BasePaperConfig

def test_example():
    """Descripción del test."""
    config = BasePaperConfig(hidden_dim=512)
    assert config.hidden_dim == 512
```

### Usar fixtures
```python
def test_with_fixture(sample_config, sample_hidden_states):
    """Test usando fixtures."""
    assert sample_config.hidden_dim == 512
    assert sample_hidden_states.shape == (2, 10, 512)
```

### Tests parametrizados
```python
@pytest.mark.parametrize("hidden_dim", [128, 256, 512, 768, 1024])
def test_multiple_dims(hidden_dim):
    """Test con múltiples valores."""
    config = BasePaperConfig(hidden_dim=hidden_dim)
    assert config.hidden_dim == hidden_dim
```

## Marcadores

- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración
- `@pytest.mark.slow`: Tests lentos
- `@pytest.mark.gpu`: Tests que requieren GPU

## Troubleshooting

### Error: Module not found
```bash
# Asegúrate de estar en el directorio correcto
cd production_code
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
```

### Error: CUDA not available
Los tests funcionan tanto con CPU como GPU. Si no hay CUDA disponible, se usa CPU automáticamente.

### Tests lentos
Usa marcadores para excluir tests lentos:
```bash
pytest -m "not slow"
```



