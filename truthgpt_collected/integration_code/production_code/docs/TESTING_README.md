# 🧪 Sistema de Testing Integrado

## ✨ Características

- ✅ **Suite de tests completa**: Tests para todos los módulos
- ✅ **Resultados detallados**: Información por módulo
- ✅ **Exportación**: Resultados en JSON
- ✅ **Integración con CLI**: Ejecución desde línea de comandos

## 🎯 Uso

### Ejecutar Todos los Tests

```python
from testing_suite import run_tests

results = run_tests("test_results.json")
print(f"Tests pasados: {results['total_passed']}/{results['total_tests']}")
```

### Tests por Módulo

```python
from testing_suite import IntegratedTestSuite

suite = IntegratedTestSuite()

# Test de memoria
result = suite.test_memory_module()
print(f"Memory: {result.tests_passed}/{result.tests_total}")

# Test de redundancia
result = suite.test_redundancy_module()
print(f"Redundancy: {result.tests_passed}/{result.tests_total}")
```

### CLI

```bash
# Ejecutar todos los tests
python cli_unified.py test

# Con salida detallada
python cli_unified.py test --verbose

# Exportar resultados
python cli_unified.py test --output test_results.json
```

## 📊 Módulos Testeados

- ✅ Memory module
- ✅ Redundancy module
- ✅ Pipeline module
- ✅ Config Manager
- ✅ Monitoring System

## 🎉 Resultado

Sistema completo de testing con:
- ✅ Tests automáticos
- ✅ Resultados detallados
- ✅ Exportación de resultados
- ✅ Integración con CLI

