#!/usr/bin/env python3
"""
Ejemplo de Uso del Sistema Integrado
======================================

Demuestra cómo usar todos los módulos juntos.
"""

import torch
from integration_pipeline import create_integrated_pipeline

def example_basic_pipeline():
    """Ejemplo básico de pipeline."""
    print("=" * 60)
    print("Ejemplo 1: Pipeline Básico")
    print("=" * 60)
    
    # Crear pipeline
    pipeline = create_integrated_pipeline(
        enable_memory=True,
        enable_redundancy=True
    )
    
    # Procesar datos
    data = torch.randn(20, 32, 512)
    output, metadata = pipeline.process_pipeline(data)
    
    print(f"Input shape: {data.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Memory used: {metadata.get('memory_used', False)}")
    print(f"Redundancy used: {metadata.get('redundancy_used', False)}")


def example_with_memory():
    """Ejemplo con memoria."""
    print("\n" + "=" * 60)
    print("Ejemplo 2: Procesamiento con Memoria")
    print("=" * 60)
    
    pipeline = create_integrated_pipeline(enable_memory=True)
    
    # Procesar múltiples veces para ver memoria en acción
    for i in range(5):
        data = torch.randn(5, 16, 256)
        output, metadata = pipeline.process_with_memory(
            data,
            metadata={'iteration': i}
        )
        print(f"Iteración {i}: Episodios en memoria: {metadata.get('memory_episodes', 0)}")


def example_with_redundancy():
    """Ejemplo con redundancia."""
    print("\n" + "=" * 60)
    print("Ejemplo 3: Procesamiento con Redundancia")
    print("=" * 60)
    
    pipeline = create_integrated_pipeline(enable_redundancy=True)
    
    # Crear datos con redundancia
    base_data = torch.randn(1, 32, 512)
    redundant_data = torch.cat([base_data] * 10, dim=0)  # 10 copias
    
    output, metadata = pipeline.process_with_redundancy(redundant_data)
    
    print(f"Input: {redundant_data.shape}")
    print(f"Output: {output.shape}")
    if 'redundancy_stats' in metadata:
        stats = metadata['redundancy_stats']
        print(f"Reducción: {stats.get('reduction_rate', 0):.2%}")


def example_chat_with_memory():
    """Ejemplo de chat con memoria."""
    print("\n" + "=" * 60)
    print("Ejemplo 4: Chat con Memoria")
    print("=" * 60)
    
    try:
        pipeline = create_integrated_pipeline(
            enable_memory=True,
            enable_chat=True,
            chat_config={'provider': 'openai'}
        )
        
        # Chat
        response1 = pipeline.chat_with_memory("Mi nombre es Juan")
        print(f"Respuesta 1: {response1.get('response', 'N/A')[:50]}...")
        
        response2 = pipeline.chat_with_memory("¿Cuál es mi nombre?")
        print(f"Respuesta 2: {response2.get('response', 'N/A')[:50]}...")
        
    except Exception as e:
        print(f"Chat no disponible: {e}")


def example_statistics():
    """Ejemplo de estadísticas."""
    print("\n" + "=" * 60)
    print("Ejemplo 5: Estadísticas del Pipeline")
    print("=" * 60)
    
    pipeline = create_integrated_pipeline(
        enable_memory=True,
        enable_redundancy=True
    )
    
    # Procesar varios datos
    for i in range(10):
        data = torch.randn(10, 16, 256)
        pipeline.process_pipeline(data)
    
    # Obtener estadísticas
    stats = pipeline.get_pipeline_stats()
    
    print(f"Total procesado: {stats['total_processed']}")
    print(f"Operaciones de memoria: {stats['memory_operations']}")
    print(f"Operaciones de redundancia: {stats['redundancy_operations']}")
    
    if 'memory_stats' in stats:
        print(f"Episodios en memoria: {stats['memory_stats'].get('episodic_size', 0)}")
    
    if 'redundancy_stats' in stats:
        print(f"Total reducido: {stats['redundancy_stats'].get('total_reduced', 0)}")


def example_save_state():
    """Ejemplo de guardar estado."""
    print("\n" + "=" * 60)
    print("Ejemplo 6: Guardar Estado")
    print("=" * 60)
    
    pipeline = create_integrated_pipeline(enable_memory=True)
    
    # Procesar algunos datos
    for i in range(5):
        data = torch.randn(5, 16, 256)
        pipeline.process_pipeline(data)
    
    # Guardar estado
    success = pipeline.save_pipeline_state("pipeline_state_example.json")
    print(f"Estado guardado: {success}")


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("Ejemplos del Sistema Integrado")
    print("=" * 60 + "\n")
    
    try:
        example_basic_pipeline()
        example_with_memory()
        example_with_redundancy()
        example_chat_with_memory()
        example_statistics()
        example_save_state()
        
        print("\n" + "=" * 60)
        print("✅ Todos los ejemplos completados!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

