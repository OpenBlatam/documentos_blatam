#!/usr/bin/env python3
"""
Ejemplo de Uso de Librerías Avanzadas
======================================

Este ejemplo muestra cómo usar las librerías integradas de requirements.txt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.advanced_utils import (
    serialize_json,
    deserialize_json,
    CacheManager,
    get_console,
    print_table,
    print_panel,
    AdvancedConfigManager,
    PrometheusMetricsCollector,
    get_system_metrics,
    setup_structured_logging,
    get_structured_logger,
    validate_json_schema
)

from core.llm_advanced import (
    AdvancedLLMClient,
    TokenCounter,
    AdvancedVectorStore,
    PromptEngineer
)

from core.visualization_advanced import (
    AdvancedVisualizer,
    create_metrics_dashboard
)

import numpy as np


def example_serialization():
    """Ejemplo de serialización con orjson y msgpack."""
    print("\n" + "="*60)
    print("Ejemplo 1: Serialización Avanzada")
    print("="*60)
    
    data = {
        "name": "Test",
        "values": [1, 2, 3, 4, 5],
        "nested": {"key": "value"}
    }
    
    json_bytes = serialize_json(data)
    print(f"JSON serializado (orjson): {len(json_bytes)} bytes")
    
    deserialized = deserialize_json(json_bytes)
    print(f"Datos deserializados: {deserialized}")
    print("✅ Serialización completada\n")


def example_caching():
    """Ejemplo de caching con múltiples backends."""
    print("="*60)
    print("Ejemplo 2: Caching Avanzado")
    print("="*60)
    
    cache = CacheManager(backend="memory", maxsize=100, ttl=3600)
    
    cache.set("key1", "value1")
    cache.set("key2", {"nested": "data"})
    
    value1 = cache.get("key1")
    value2 = cache.get("key2")
    
    print(f"Valor 1: {value1}")
    print(f"Valor 2: {value2}")
    print("✅ Caching completado\n")


def example_rich_console():
    """Ejemplo de Rich Console."""
    print("="*60)
    print("Ejemplo 3: Rich Console")
    print("="*60)
    
    console = get_console()
    if console:
        console.print("[bold green]¡Hola desde Rich![/bold green]")
        console.print("[italic]Texto en cursiva[/italic]")
    
    data = [
        {"Nombre": "Alice", "Edad": 30, "Ciudad": "Madrid"},
        {"Nombre": "Bob", "Edad": 25, "Ciudad": "Barcelona"},
        {"Nombre": "Charlie", "Edad": 35, "Ciudad": "Valencia"}
    ]
    
    print_table(data, title="Tabla de Ejemplo")
    
    print_panel("Este es un panel de ejemplo", title="Panel")
    print("✅ Rich Console completado\n")


def example_configuration():
    """Ejemplo de configuración avanzada."""
    print("="*60)
    print("Ejemplo 4: Configuración Avanzada")
    print("="*60)
    
    try:
        config = AdvancedConfigManager(
            config_type="pydantic",
            test_key="test_value",
            another_key=123
        )
        
        value = config.get("test_key", "default")
        print(f"Valor de configuración: {value}")
        print("✅ Configuración completada\n")
    except Exception as e:
        print(f"⚠️  Configuración no disponible: {e}\n")


def example_system_metrics():
    """Ejemplo de métricas del sistema."""
    print("="*60)
    print("Ejemplo 5: Métricas del Sistema")
    print("="*60)
    
    metrics = get_system_metrics()
    if metrics:
        print(f"CPU Count: {metrics.get('cpu', {}).get('count', 'N/A')}")
        print(f"Memory Percent: {metrics.get('memory', {}).get('percent', 'N/A')}%")
        print("✅ Métricas del sistema completadas\n")
    else:
        print("⚠️  psutil no disponible\n")


def example_structured_logging():
    """Ejemplo de logging estructurado."""
    print("="*60)
    print("Ejemplo 6: Logging Estructurado")
    print("="*60)
    
    setup_structured_logging(level="INFO", use_json=False)
    logger = get_structured_logger(__name__)
    
    logger.info("Mensaje de información", extra_data="valor")
    logger.warning("Mensaje de advertencia", user_id=123)
    print("✅ Logging estructurado completado\n")


def example_token_counting():
    """Ejemplo de conteo de tokens."""
    print("="*60)
    print("Ejemplo 7: Conteo de Tokens")
    print("="*60)
    
    try:
        counter = TokenCounter(model="gpt-3.5-turbo")
        
        text = "Este es un texto de ejemplo para contar tokens."
        token_count = counter.count_tokens(text)
        
        print(f"Texto: {text}")
        print(f"Tokens: {token_count}")
        print("✅ Conteo de tokens completado\n")
    except Exception as e:
        print(f"⚠️  tiktoken no disponible: {e}\n")


def example_visualization():
    """Ejemplo de visualización avanzada."""
    print("="*60)
    print("Ejemplo 8: Visualización Avanzada")
    print("="*60)
    
    try:
        viz = AdvancedVisualizer(backend="matplotlib")
        
        x = list(range(10))
        y = [i**2 for i in x]
        
        viz.plot_line(
            x, y,
            title="Gráfico de Ejemplo",
            xlabel="X",
            ylabel="Y",
            save_path="example_plot.png"
        )
        
        print("✅ Visualización completada (guardada en example_plot.png)\n")
    except Exception as e:
        print(f"⚠️  Visualización no disponible: {e}\n")


def example_validation():
    """Ejemplo de validación con JSON Schema."""
    print("="*60)
    print("Ejemplo 9: Validación JSON Schema")
    print("="*60)
    
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        },
        "required": ["name", "age"]
    }
    
    valid_data = {"name": "Alice", "age": 30}
    invalid_data = {"name": "Bob", "age": -5}
    
    is_valid1, error1 = validate_json_schema(valid_data, schema)
    is_valid2, error2 = validate_json_schema(invalid_data, schema)
    
    print(f"Datos válidos: {is_valid1}")
    print(f"Datos inválidos: {is_valid2}, Error: {error2}")
    print("✅ Validación completada\n")


def example_metrics_dashboard():
    """Ejemplo de dashboard de métricas."""
    print("="*60)
    print("Ejemplo 10: Dashboard de Métricas")
    print("="*60)
    
    try:
        metrics = {
            "Loss": [0.5, 0.4, 0.3, 0.2, 0.1],
            "Accuracy": [0.6, 0.7, 0.8, 0.9, 0.95],
            "F1 Score": [0.55, 0.65, 0.75, 0.85, 0.92]
        }
        
        create_metrics_dashboard(metrics, save_path="metrics_dashboard.html")
        print("✅ Dashboard creado (guardado en metrics_dashboard.html)\n")
    except Exception as e:
        print(f"⚠️  Dashboard no disponible: {e}\n")


def main():
    """Ejecuta todos los ejemplos."""
    print("\n" + "="*60)
    print("EJEMPLOS DE USO DE LIBRERÍAS AVANZADAS")
    print("="*60)
    
    example_serialization()
    example_caching()
    example_rich_console()
    example_configuration()
    example_system_metrics()
    example_structured_logging()
    example_token_counting()
    example_visualization()
    example_validation()
    example_metrics_dashboard()
    
    print("="*60)
    print("✅ TODOS LOS EJEMPLOS COMPLETADOS")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

