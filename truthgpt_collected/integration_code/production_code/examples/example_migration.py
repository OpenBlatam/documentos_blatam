#!/usr/bin/env python3
"""
Ejemplo de Uso del Sistema de Migración
=========================================

Este script demuestra cómo usar las utilidades de migración para
actualizar archivos antiguos a las nuevas convenciones.
"""

from pathlib import Path
from core import (
    migrate_file,
    migrate_directory,
    migrate_logging,
    migrate_validate_method,
    migrate_validate_inputs
)


def example_migrate_single_file():
    """Ejemplo: Migrar un archivo individual."""
    print("=" * 60)
    print("EJEMPLO 1: Migrar Archivo Individual")
    print("=" * 60)
    
    file_path = Path('papers/agents/paper_mars.py')
    
    if not file_path.exists():
        print(f"  ⚠️ Archivo no encontrado: {file_path}")
        return
    
    result = migrate_file(
        file_path,
        operations=['logging', 'validate', 'validate_inputs']
    )
    
    print(f"\n📄 Archivo: {result['file']}")
    print("\n📋 Operaciones:")
    for op_name, op_result in result['operations'].items():
        status = "✓" if op_result['success'] else "✗"
        print(f"  {status} {op_name}:")
        for change in op_result['changes']:
            print(f"    - {change}")


def example_migrate_directory():
    """Ejemplo: Migrar un directorio completo."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Migrar Directorio Completo")
    print("=" * 60)
    
    directory = Path('papers/agents')
    
    if not directory.exists():
        print(f"  ⚠️ Directorio no encontrado: {directory}")
        return
    
    results = migrate_directory(
        directory,
        pattern='paper_*.py',
        operations=['logging', 'validate']
    )
    
    print(f"\n📊 Resumen:")
    print(f"  - Total archivos: {results['total_files']}")
    print(f"  - Exitosos: {results['successful']}")
    print(f"  - Fallidos: {results['failed']}")
    
    print(f"\n📋 Detalles:")
    for file_result in results['files'][:5]:  # Mostrar primeros 5
        if 'error' in file_result:
            print(f"  ✗ {file_result['file']}: {file_result['error']}")
        else:
            ops = file_result.get('operations', {})
            if any(op.get('success') for op in ops.values()):
                print(f"  ✓ {file_result['file']}")
                for op_name, op_result in ops.items():
                    if op_result['success']:
                        print(f"      - {op_name}: {len(op_result['changes'])} cambios")


def example_selective_migration():
    """Ejemplo: Migración selectiva."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Migración Selectiva")
    print("=" * 60)
    
    file_path = Path('papers/agents/paper_mars.py')
    
    if not file_path.exists():
        print(f"  ⚠️ Archivo no encontrado: {file_path}")
        return
    
    print("\n📝 Solo migrar logging:")
    success, changes = migrate_logging(file_path)
    print(f"  {'✓' if success else '✗'} Cambios: {changes}")
    
    print("\n📝 Solo añadir validate():")
    success, changes = migrate_validate_method(file_path)
    print(f"  {'✓' if success else '✗'} Cambios: {changes}")
    
    print("\n📝 Solo añadir validate_inputs():")
    success, changes = migrate_validate_inputs(file_path)
    print(f"  {'✓' if success else '✗'} Cambios: {changes}")


def example_batch_migration():
    """Ejemplo: Migración en batch de múltiples directorios."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Migración en Batch")
    print("=" * 60)
    
    directories = [
        Path('papers/agents'),
        Path('papers/research'),
        Path('papers/inference'),
    ]
    
    total_results = {
        'total_files': 0,
        'successful': 0,
        'failed': 0
    }
    
    for directory in directories:
        if not directory.exists():
            print(f"  ⚠️ Directorio no encontrado: {directory}")
            continue
        
        print(f"\n📁 Migrando: {directory}")
        results = migrate_directory(
            directory,
            pattern='paper_*.py',
            operations=['logging']
        )
        
        total_results['total_files'] += results['total_files']
        total_results['successful'] += results['successful']
        total_results['failed'] += results['failed']
        
        print(f"  - Archivos: {results['total_files']}")
        print(f"  - Exitosos: {results['successful']}")
    
    print(f"\n📊 Resumen Total:")
    print(f"  - Total archivos: {total_results['total_files']}")
    print(f"  - Exitosos: {total_results['successful']}")
    print(f"  - Fallidos: {total_results['failed']}")


if __name__ == "__main__":
    print("\n🚀 EJEMPLOS DE MIGRACIÓN\n")
    
    try:
        example_migrate_single_file()
    except Exception as e:
        print(f"Error en ejemplo 1: {e}")
    
    try:
        example_migrate_directory()
    except Exception as e:
        print(f"Error en ejemplo 2: {e}")
    
    try:
        example_selective_migration()
    except Exception as e:
        print(f"Error en ejemplo 3: {e}")
    
    try:
        example_batch_migration()
    except Exception as e:
        print(f"Error en ejemplo 4: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados")
    print("=" * 60)


