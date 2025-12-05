#!/usr/bin/env python3
"""
Ejemplo de Uso del Gestor de Configuración
===========================================

Demuestra cómo usar el sistema de configuración centralizado.
"""

from core.config_manager import (
    ConfigManager,
    ModuleType,
    get_config_manager,
    create_from_config
)


def example_basic_usage():
    """Ejemplo básico de uso."""
    print("=" * 60)
    print("Ejemplo 1: Uso Básico")
    print("=" * 60)
    
    # Crear gestor
    config_manager = ConfigManager()
    
    # Obtener configuración
    memory_config = config_manager.get_config(ModuleType.MEMORY)
    print(f"Memory config: {memory_config}")
    
    # Actualizar configuración
    config_manager.update_config(ModuleType.MEMORY, memory_dim=1024)
    updated_config = config_manager.get_config(ModuleType.MEMORY)
    print(f"Updated memory_dim: {updated_config['memory_dim']}")


def example_save_load():
    """Ejemplo de guardar y cargar."""
    print("\n" + "=" * 60)
    print("Ejemplo 2: Guardar y Cargar")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    # Modificar configuraciones
    config_manager.update_config(ModuleType.MEMORY, memory_dim=1024, max_memory_size=20000)
    config_manager.update_config(ModuleType.REDUNDANCY, similarity_threshold=0.9)
    
    # Guardar
    config_manager.save_config("example_config.json")
    print("Configuración guardada")
    
    # Cargar
    new_manager = ConfigManager("example_config.json")
    loaded_config = new_manager.get_config(ModuleType.MEMORY)
    print(f"Configuración cargada: memory_dim={loaded_config['memory_dim']}")


def example_create_from_config():
    """Ejemplo de crear módulos desde configuración."""
    print("\n" + "=" * 60)
    print("Ejemplo 3: Crear Módulos desde Configuración")
    print("=" * 60)
    
    config_manager = get_config_manager()
    
    # Crear módulo de memoria
    memory = create_from_config(ModuleType.MEMORY, config_manager)
    if memory:
        print(f"✅ Memoria creada: {type(memory).__name__}")
        stats = memory.get_episodic_stats()
        print(f"   Episodios: {stats['episodic_size']}")
    
    # Crear módulo de redundancia
    redundancy = create_from_config(ModuleType.REDUNDANCY, config_manager)
    if redundancy:
        print(f"✅ Redundancia creada: {type(redundancy).__name__}")


def example_validation():
    """Ejemplo de validación."""
    print("\n" + "=" * 60)
    print("Ejemplo 4: Validación")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    # Validar configuración válida
    valid, errors = config_manager.validate_config(ModuleType.MEMORY)
    print(f"Memory config válida: {valid}")
    if errors:
        print(f"Errores: {errors}")
    
    # Configuración inválida
    config_manager.update_config(ModuleType.MEMORY, memory_dim=-1)
    valid, errors = config_manager.validate_config(ModuleType.MEMORY)
    print(f"Memory config válida (después de cambio inválido): {valid}")
    if errors:
        print(f"Errores: {errors}")


def example_reset():
    """Ejemplo de reset."""
    print("\n" + "=" * 60)
    print("Ejemplo 5: Reset a Defaults")
    print("=" * 60)
    
    config_manager = ConfigManager()
    
    # Modificar
    config_manager.update_config(ModuleType.MEMORY, memory_dim=2048)
    print(f"Antes del reset: {config_manager.get_config(ModuleType.MEMORY)['memory_dim']}")
    
    # Reset
    config_manager.reset_to_defaults(ModuleType.MEMORY)
    print(f"Después del reset: {config_manager.get_config(ModuleType.MEMORY)['memory_dim']}")


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("Ejemplos del Gestor de Configuración")
    print("=" * 60 + "\n")
    
    try:
        example_basic_usage()
        example_save_load()
        example_create_from_config()
        example_validation()
        example_reset()
        
        print("\n" + "=" * 60)
        print("✅ Todos los ejemplos completados!")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

