#!/usr/bin/env python3
"""
Ejemplos de Uso del Sistema de Memoria
========================================

Demuestra todas las funcionalidades del sistema de memoria mejorado.
"""

import torch
from memory import (
    Paper2506_15841v2Config,
    Paper2506_15841v2_MemorySystem,
    create_memory_system,
    create_chat_with_memory,
    MemoryAnalytics,
    MemoryOptimizer,
    MemoryExporter,
    create_episode_from_text,
    batch_store_episodes,
    get_memory_health_report
)


def example_basic_usage():
    """Ejemplo básico de uso."""
    print("=" * 60)
    print("Ejemplo 1: Uso Básico")
    print("=" * 60)
    
    # Crear configuración
    config = Paper2506_15841v2Config(
        memory_dim=512,
        max_memory_size=1000,
        enable_cache=True,
        enable_persistence=True,
        persistence_path="./memory_data"
    )
    
    # Crear sistema de memoria
    memory = Paper2506_15841v2_MemorySystem(config)
    
    # Almacenar episodios
    for i in range(5):
        episode = torch.randn(512)
        memory.store_episode(episode, metadata={'index': i})
    
    # Recuperar episodios
    query = torch.randn(512)
    retrieved, weights = memory.retrieve_episodes(query, k=3)
    
    print(f"Episodios almacenados: {len(memory.episodic_memory)}")
    print(f"Episodios recuperados: {retrieved.shape}")
    print(f"Pesos: {weights.shape}")


def example_with_tags():
    """Ejemplo con tags y priorización."""
    print("\n" + "=" * 60)
    print("Ejemplo 2: Tags y Priorización")
    print("=" * 60)
    
    config = Paper2506_15841v2Config(memory_dim=256)
    memory = Paper2506_15841v2_MemorySystem(config)
    
    # Almacenar con tags y prioridad
    memory.store_episode_with_tags(
        episode=torch.randn(256),
        tags=['programming', 'python', 'important'],
        priority=0.9,
        metadata={'topic': 'Python basics'}
    )
    
    memory.store_episode_with_tags(
        episode=torch.randn(256),
        tags=['programming', 'javascript'],
        priority=0.7,
        metadata={'topic': 'JavaScript basics'}
    )
    
    # Recuperar por tags
    query = torch.randn(256)
    retrieved, weights = memory.retrieve_by_tags(query, tags=['programming'], k=5)
    
    print(f"Episodios con tag 'programming': {retrieved.shape[1]}")
    
    # Obtener episodios prioritarios
    priority_indices = memory.get_episodes_by_priority(min_priority=0.8)
    print(f"Episodios de alta prioridad: {len(priority_indices)}")


def example_compression():
    """Ejemplo de compresión."""
    print("\n" + "=" * 60)
    print("Ejemplo 3: Compresión de Memoria")
    print("=" * 60)
    
    config = Paper2506_15841v2Config(
        memory_dim=512,
        enable_compression=True,
        compression_ratio=0.5
    )
    memory = Paper2506_15841v2_MemorySystem(config)
    
    # Almacenar muchos episodios
    for i in range(100):
        memory.store_episode(torch.randn(512), metadata={'index': i})
    
    print(f"Episodios antes de compresión: {len(memory.episodic_memory)}")
    
    # Comprimir
    compressed = memory.compress_memory()
    print(f"Episodios comprimidos: {compressed}")


def example_analytics():
    """Ejemplo de analytics."""
    print("\n" + "=" * 60)
    print("Ejemplo 4: Analytics")
    print("=" * 60)
    
    config = Paper2506_15841v2Config(memory_dim=256)
    memory = Paper2506_15841v2_MemorySystem(config)
    
    # Almacenar algunos episodios
    for i in range(20):
        memory.store_episode(torch.randn(256), metadata={'index': i})
    
    # Recuperar algunos para generar accesos
    for _ in range(10):
        query = torch.randn(256)
        memory.retrieve_episodes(query, k=5)
    
    # Analytics
    analytics = MemoryAnalytics(memory)
    report = analytics.get_comprehensive_report()
    
    print(f"Total accesos: {report['access_patterns']['total_accesses']}")
    print(f"Episodios más accedidos: {len(report['access_patterns']['most_accessed'])}")
    
    # Optimización
    optimizer = MemoryOptimizer(memory)
    result = optimizer.optimize_memory_layout()
    print(f"Optimizaciones aplicadas: {result['optimizations_applied']}")


def example_persistence():
    """Ejemplo de persistencia."""
    print("\n" + "=" * 60)
    print("Ejemplo 5: Persistencia")
    print("=" * 60)
    
    config = Paper2506_15841v2Config(
        memory_dim=256,
        enable_persistence=True,
        persistence_path="./memory_data"
    )
    
    # Crear y almacenar
    memory = Paper2506_15841v2_MemorySystem(config)
    for i in range(10):
        memory.store_episode(torch.randn(256), metadata={'index': i})
    
    # Guardar
    memory.save_persisted_memory()
    print(f"Memoria guardada: {len(memory.episodic_memory)} episodios")
    
    # Crear nuevo sistema y cargar
    memory2 = Paper2506_15841v2_MemorySystem(config)
    print(f"Memoria cargada: {len(memory2.episodic_memory)} episodios")


def example_chat_integration():
    """Ejemplo de integración con chat."""
    print("\n" + "=" * 60)
    print("Ejemplo 6: Integración con Chat")
    print("=" * 60)
    
    try:
        from core.chat_engine import ChatEngine
        
        # Crear chat con memoria
        chat = ChatEngine(provider="openai", model="gpt-3.5-turbo")
        
        from memory.chat_memory_integration import ChatMemoryIntegration
        
        memory_config = Paper2506_15841v2Config(memory_dim=512)
        integration = ChatMemoryIntegration(chat, memory_config)
        
        # Chat mejorado con memoria
        response = integration.enhance_chat_with_memory(
            "Hola, ¿cómo estás?",
            store_important=True
        )
        
        print(f"Respuesta: {response['response'][:100]}...")
        print(f"Contextos de memoria: {response['metadata'].get('memory_contexts', 0)}")
        
    except ImportError:
        print("Chat engine no disponible")


def example_factory_functions():
    """Ejemplo de funciones factory."""
    print("\n" + "=" * 60)
    print("Ejemplo 7: Funciones Factory")
    print("=" * 60)
    
    # Crear sistema de memoria usando factory
    memory = create_memory_system(
        "2506_15841v2",
        memory_dim=256,
        max_memory_size=500,
        enable_cache=True
    )
    
    if memory:
        print(f"Sistema creado: {type(memory).__name__}")
        print(f"Configuración: memory_dim={memory.config.memory_dim}")


def example_utilities():
    """Ejemplo de utilidades."""
    print("\n" + "=" * 60)
    print("Ejemplo 8: Utilidades")
    print("=" * 60)
    
    config = Paper2506_15841v2Config(memory_dim=256)
    memory = Paper2506_15841v2_MemorySystem(config)
    
    # Crear episodios desde texto
    episode1 = create_episode_from_text("Python programming", memory_dim=256)
    episode2 = create_episode_from_text("Machine learning", memory_dim=256)
    
    memory.store_episode(episode1)
    memory.store_episode(episode2)
    
    # Comparar episodios
    from memory.memory_utils import compare_episodes
    similarity = compare_episodes(episode1, episode2, method="cosine")
    print(f"Similitud entre episodios: {similarity:.3f}")
    
    # Health report
    health = get_memory_health_report(memory)
    print(f"Estado de salud: {health['status']}")
    if health.get('warnings'):
        print(f"Advertencias: {health['warnings']}")


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("Ejemplos del Sistema de Memoria Mejorado")
    print("=" * 60 + "\n")
    
    try:
        example_basic_usage()
        example_with_tags()
        example_compression()
        example_analytics()
        example_persistence()
        example_chat_integration()
        example_factory_functions()
        example_utilities()
        
        print("\n" + "=" * 60)
        print("✅ Todos los ejemplos completados!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


