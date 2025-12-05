#!/usr/bin/env python3
"""
CLI Unificado
=============

Interfaz de línea de comandos unificada para todos los módulos.
"""

import argparse
import sys
from pathlib import Path
import json
from typing import Optional, Any

from core.config_manager import ConfigManager, ModuleType, get_config_manager
from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)

# Constants
DEFAULT_MEMORY_EXPORT = "memory_export.json"
DEFAULT_PIPELINE_STATE = "pipeline_state.json"
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_MONITORING_REPORT = "monitoring_report.json"
DEFAULT_VISUALIZATION = "metrics_visualization.png"
DEFAULT_DOCS_DIR = "docs"
MIN_MEMORY_DIM = 1
MAX_MEMORY_DIM = 10000
MIN_MAX_SIZE = 1
MAX_MAX_SIZE = 1000000
MIN_THRESHOLD = 0.0
MAX_THRESHOLD = 1.0
MIN_PORT = 1
MAX_PORT = 65535
MIN_WORKERS = 1
MAX_WORKERS = 100


def validate_memory_args(args: argparse.Namespace) -> None:
    """Valida argumentos del comando memory."""
    if args.memory_dim is not None:
        if not (MIN_MEMORY_DIM <= args.memory_dim <= MAX_MEMORY_DIM):
            raise ValueError(f"memory_dim must be between {MIN_MEMORY_DIM} and {MAX_MEMORY_DIM}")
    if args.max_size is not None:
        if not (MIN_MAX_SIZE <= args.max_size <= MAX_MAX_SIZE):
            raise ValueError(f"max_size must be between {MIN_MAX_SIZE} and {MAX_MAX_SIZE}")


def cmd_memory(args: argparse.Namespace) -> None:
    """Comando para módulo de memoria."""
    try:
        validate_memory_args(args)
        
        from memory import create_memory_system, MemoryExporter
        
        config_manager = get_config_manager()
        config = config_manager.get_config(ModuleType.MEMORY)
        
        # Actualizar con argumentos de CLI
        if args.memory_dim:
            config['memory_dim'] = args.memory_dim
        if args.max_size:
            config['max_memory_size'] = args.max_size
        
        memory = create_memory_system("2506_15841v2", **config)
        
        if args.action == 'stats':
            stats = memory.get_episodic_stats()
            print(json.dumps(stats, indent=2, default=str))
        
        elif args.action == 'export':
            output_path = args.output or DEFAULT_MEMORY_EXPORT
            exporter = MemoryExporter(memory)
            result, error = safe_execute(
                exporter.export_to_json,
                default_value=False,
                log_errors=True,
                filepath=output_path
            )
            if result:
                print(f"Memoria exportada a {output_path}")
            else:
                logger.error(f"Error exportando memoria: {error}")
                sys.exit(1)
        
        elif args.action == 'clear':
            memory.clear_cache()
            print("Caché limpiado")
        
        else:
            print("Acción no reconocida. Use: stats, export, clear")
            sys.exit(1)
    
    except ImportError as e:
        logger.error(f"Módulo de memoria no disponible: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en comando memory: {e}")
        sys.exit(1)


def validate_redundancy_args(args: argparse.Namespace) -> None:
    """Valida argumentos del comando redundancy."""
    if args.threshold is not None:
        if not (MIN_THRESHOLD <= args.threshold <= MAX_THRESHOLD):
            raise ValueError(f"threshold must be between {MIN_THRESHOLD} and {MAX_THRESHOLD}")


def cmd_redundancy(args: argparse.Namespace) -> None:
    """Comando para módulo de redundancia."""
    try:
        validate_redundancy_args(args)
        
        from redundancy import create_redundancy_suppressor
        
        config_manager = get_config_manager()
        config = config_manager.get_config(ModuleType.REDUNDANCY)
        
        if args.threshold is not None:
            config['similarity_threshold'] = args.threshold
        
        redundancy = create_redundancy_suppressor("2510_00071", **config)
        
        if args.action == 'stats':
            stats = redundancy.get_metrics()
            print(json.dumps(stats, indent=2, default=str))
        
        elif args.action == 'clear':
            redundancy.clear_cache()
            print("Caché limpiado")
        
        else:
            print("Acción no reconocida. Use: stats, clear")
            sys.exit(1)
    
    except ImportError as e:
        logger.error(f"Módulo de redundancia no disponible: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en comando redundancy: {e}")
        sys.exit(1)


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Comando para pipeline integrado."""
    try:
        from integration_pipeline import create_integrated_pipeline
        
        config_manager = get_config_manager()
        config = config_manager.get_config(ModuleType.PIPELINE)
        
        pipeline = create_integrated_pipeline(**config)
        
        if pipeline is None:
            logger.error("No se pudo crear el pipeline")
            sys.exit(1)
        
        if args.action == 'stats':
            stats = pipeline.get_pipeline_stats()
            print(json.dumps(stats, indent=2, default=str))
        
        elif args.action == 'save':
            output_path = args.output or DEFAULT_PIPELINE_STATE
            result = pipeline.save_pipeline_state(output_path)
            if result:
                print(f"Estado guardado en {output_path}")
            else:
                logger.error(f"Error guardando estado en {output_path}")
                sys.exit(1)
        
        else:
            print("Acción no reconocida. Use: stats, save")
            sys.exit(1)
    
    except ImportError as e:
        logger.error(f"Módulo de pipeline no disponible: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en comando pipeline: {e}")
        sys.exit(1)


def cmd_config(args: argparse.Namespace) -> None:
    """Comando para gestión de configuración."""
    try:
        config_manager = get_config_manager(args.config_file)
        
        if args.action == 'show':
            module = args.module or 'all'
            if module == 'all':
                configs = config_manager.get_all_configs()
            else:
                configs = {module: config_manager.get_config(module)}
            print(json.dumps(configs, indent=2, default=str))
        
        elif args.action == 'save':
            output_path = args.output or DEFAULT_CONFIG_FILE
            format_type = args.format or 'json'
            result = config_manager.save_config(output_path, format=format_type)
            if result:
                print(f"Configuración guardada en {output_path}")
            else:
                logger.error(f"Error guardando configuración en {output_path}")
                sys.exit(1)
        
        elif args.action == 'load':
            if not args.input:
                logger.error("Se requiere --input para cargar configuración")
                sys.exit(1)
            if not Path(args.input).exists():
                logger.error(f"Archivo no encontrado: {args.input}")
                sys.exit(1)
            result = config_manager.load_config(args.input)
            if result:
                print(f"Configuración cargada desde {args.input}")
            else:
                logger.error(f"Error cargando configuración desde {args.input}")
                sys.exit(1)
        
        elif args.action == 'reset':
            module = args.module
            config_manager.reset_to_defaults(module)
            print(f"Configuración reseteada{' para ' + module if module else ''}")
        
        elif args.action == 'validate':
            module = args.module or 'all'
            if module == 'all':
                modules = [m.value for m in ModuleType]
            else:
                modules = [module]
            
            all_valid = True
            for mod in modules:
                valid, errors = config_manager.validate_config(mod)
                if valid:
                    print(f"✅ {mod}: válido")
                else:
                    print(f"❌ {mod}: {', '.join(errors)}")
                    all_valid = False
            
            sys.exit(0 if all_valid else 1)
        
        else:
            print("Acción no reconocida. Use: show, save, load, reset, validate")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error en comando config: {e}")
        sys.exit(1)


def cmd_monitor(args):
    """Comando para monitoreo."""
    from monitoring_system import get_system_monitor
    
    monitor = get_system_monitor()
    
    if args.action == 'status':
        status = monitor.get_system_status()
        print(json.dumps(status, indent=2, default=str))
    
    elif args.action == 'health':
        health = monitor.health_monitor.get_overall_health()
        print(json.dumps(health, indent=2, default=str))
    
    elif args.action == 'metrics':
        metrics = monitor.metrics_collector.get_all_metrics()
        print(json.dumps(metrics, indent=2, default=str))
    
    elif args.action == 'export':
        monitor.export_report(args.output or "monitoring_report.json")
        print(f"Reporte exportado a {args.output or 'monitoring_report.json'}")
    
    elif args.action == 'visualize':
        monitor.visualize_metrics(args.output or "metrics_visualization.png")
        print(f"Visualización guardada en {args.output or 'metrics_visualization.png'}")
    
    else:
        print("Acción no reconocida. Use: status, health, metrics, export, visualize")


def cmd_test(args):
    """Comando para testing."""
    from testing_suite import run_tests
    
    results = run_tests(args.output)
    
    print(f"\nTotal tests: {results['total_tests']}")
    print(f"Pasados: {results['total_passed']}")
    print(f"Fallidos: {results['total_failed']}")
    print(f"Tasa de éxito: {results['success_rate']:.2%}")
    
    if args.verbose:
        print("\nPor módulo:")
        for module, module_results in results['modules'].items():
            print(f"  {module}: {module_results['passed']}/{module_results['total']}")
            if module_results['errors']:
                for error in module_results['errors']:
                    print(f"    ❌ {error}")
    
    sys.exit(0 if results['total_failed'] == 0 else 1)


def cmd_docs(args):
    """Comando para generación de documentación."""
    from docs_generator import generate_documentation
    
    output_dir = args.output or "docs"
    generate_documentation(output_dir)
    print(f"Documentación generada en {output_dir}/")


def validate_api_args(args: argparse.Namespace) -> None:
    """Valida argumentos del comando api."""
    if args.port is not None:
        if not (MIN_PORT <= args.port <= MAX_PORT):
            raise ValueError(f"port must be between {MIN_PORT} and {MAX_PORT}")
    if args.workers is not None:
        if not (MIN_WORKERS <= args.workers <= MAX_WORKERS):
            raise ValueError(f"workers must be between {MIN_WORKERS} and {MAX_WORKERS}")


def cmd_api(args: argparse.Namespace) -> None:
    """Comando para iniciar servidor API."""
    try:
        validate_api_args(args)
        
        from api_server import main as api_main
        
        # Pasar argumentos al servidor API
        import sys
        sys.argv = ['api_server.py']
        if args.host:
            sys.argv.extend(['--host', args.host])
        if args.port:
            sys.argv.extend(['--port', str(args.port)])
        if args.reload:
            sys.argv.append('--reload')
        if args.workers:
            sys.argv.extend(['--workers', str(args.workers)])
        
        api_main()
    
    except ImportError as e:
        logger.error(f"Módulo de API no disponible: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en comando api: {e}")
        sys.exit(1)


def main():
    """Función principal del CLI."""
    parser = argparse.ArgumentParser(
        description='CLI Unificado para Sistema de Producción',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='module', help='Módulo a usar')
    
    # Memory
    memory_parser = subparsers.add_parser('memory', help='Módulo de memoria')
    memory_parser.add_argument('action', choices=['stats', 'export', 'clear'], help='Acción a realizar')
    memory_parser.add_argument('--memory-dim', type=int, help='Dimensión de memoria')
    memory_parser.add_argument('--max-size', type=int, help='Tamaño máximo')
    memory_parser.add_argument('--output', '-o', help='Archivo de salida')
    memory_parser.set_defaults(func=cmd_memory)
    
    # Redundancy
    redundancy_parser = subparsers.add_parser('redundancy', help='Módulo de redundancia')
    redundancy_parser.add_argument('action', choices=['stats', 'clear'], help='Acción a realizar')
    redundancy_parser.add_argument('--threshold', type=float, help='Umbral de similitud')
    redundancy_parser.set_defaults(func=cmd_redundancy)
    
    # Pipeline
    pipeline_parser = subparsers.add_parser('pipeline', help='Pipeline integrado')
    pipeline_parser.add_argument('action', choices=['stats', 'save'], help='Acción a realizar')
    pipeline_parser.add_argument('--output', '-o', help='Archivo de salida')
    pipeline_parser.set_defaults(func=cmd_pipeline)
    
    # Config
    config_parser = subparsers.add_parser('config', help='Gestión de configuración')
    config_parser.add_argument('action', choices=['show', 'save', 'load', 'reset', 'validate'], help='Acción a realizar')
    config_parser.add_argument('--module', '-m', help='Módulo específico')
    config_parser.add_argument('--config-file', '-c', help='Archivo de configuración')
    config_parser.add_argument('--input', '-i', help='Archivo de entrada')
    config_parser.add_argument('--output', '-o', help='Archivo de salida')
    config_parser.add_argument('--format', '-f', choices=['json', 'yaml'], help='Formato')
    config_parser.set_defaults(func=cmd_config)
    
    # Monitor
    monitor_parser = subparsers.add_parser('monitor', help='Sistema de monitoreo')
    monitor_parser.add_argument('action', choices=['status', 'health', 'metrics', 'export', 'visualize'], help='Acción a realizar')
    monitor_parser.add_argument('--output', '-o', help='Archivo de salida')
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # Test
    test_parser = subparsers.add_parser('test', help='Sistema de testing')
    test_parser.add_argument('--output', '-o', help='Archivo de salida para resultados')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar detalles')
    test_parser.set_defaults(func=cmd_test)
    
    # Docs
    docs_parser = subparsers.add_parser('docs', help='Generación de documentación')
    docs_parser.add_argument('--output', '-o', default='docs', help='Directorio de salida')
    docs_parser.set_defaults(func=cmd_docs)
    
    # API
    api_parser = subparsers.add_parser('api', help='Servidor API')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host')
    api_parser.add_argument('--port', type=int, default=8000, help=f'Puerto ({MIN_PORT}-{MAX_PORT})')
    api_parser.add_argument('--reload', action='store_true', help='Recargar automáticamente')
    api_parser.add_argument('--workers', type=int, default=1, help=f'Número de workers ({MIN_WORKERS}-{MAX_WORKERS})')
    api_parser.set_defaults(func=cmd_api)
    
    args = parser.parse_args()
    
    if not args.module:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error ejecutando comando: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

