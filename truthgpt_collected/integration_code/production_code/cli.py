#!/usr/bin/env python3
"""
CLI mejorado para el código de producción usando Click.

Proporciona comandos para:
- Mejorar modelos
- Refactorizar imports
- Ejecutar tests
- Gestionar configuraciones
"""

from pathlib import Path
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    CLICK_AVAILABLE = True
    RICH_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    RICH_AVAILABLE = False

from core.utils import setup_logger

logger = setup_logger(__name__)

if RICH_AVAILABLE:
    console = Console()
else:
    console = None


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """CLI para gestión de modelos de producción."""
    pass


@cli.command()
@click.option('--base-dir', default='.', type=click.Path(exists=True), help='Directorio base')
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
def improve(base_dir: str, verbose: bool):
    """Mejora automáticamente todos los modelos."""
    from improve_models import main as improve_main
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    if RICH_AVAILABLE:
        console.print(Panel.fit("[bold blue]Mejorando Modelos[/bold blue]", title="Model Improver"))
    
    improve_main()


@cli.command()
@click.option('--base-dir', default='.', type=click.Path(exists=True), help='Directorio base')
def refactor_imports(base_dir: str):
    """Refactoriza imports en todos los archivos."""
    from refactor_imports import main as refactor_main
    
    if RICH_AVAILABLE:
        console.print(Panel.fit("[bold blue]Refactorizando Imports[/bold blue]", title="Import Refactor"))
    
    refactor_main()


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Archivo de configuración')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'toml']), default='json', help='Formato de salida')
@click.option('--output', '-o', type=click.Path(), help='Archivo de salida')
def config_show(config: Optional[str], format: str, output: Optional[str]):
    """Muestra o convierte configuración."""
    from core.config_manager import ConfigManager
    
    if not config:
        click.echo("Error: Se requiere un archivo de configuración con --config")
        return
    
    try:
        manager = ConfigManager(config)
        
        if output:
            manager.save(output, format)
            click.echo(f"Configuración guardada en {output} ({format})")
        else:
            if RICH_AVAILABLE:
                table = Table(title="Configuración")
                table.add_column("Clave", style="cyan")
                table.add_column("Valor", style="green")
                
                def add_to_table(data, prefix=""):
                    for key, value in data.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            add_to_table(value, full_key)
                        else:
                            table.add_row(full_key, str(value))
                
                add_to_table(manager.config)
                console.print(table)
            else:
                import json
                click.echo(json.dumps(manager.config, indent=2))
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option('--project', '-p', required=True, help='Nombre del proyecto')
@click.option('--name', '-n', help='Nombre del experimento')
@click.option('--config', '-c', type=click.Path(exists=True), help='Archivo de configuración')
@click.option('--wandb/--no-wandb', default=True, help='Usar Weights & Biases')
@click.option('--mlflow/--no-mlflow', default=False, help='Usar MLflow')
def track(project: str, name: Optional[str], config: Optional[str], wandb: bool, mlflow: bool):
    """Inicializa tracking de experimentos."""
    from core.experiment_tracking import ExperimentTracker
    from core.config_manager import ConfigManager
    
    config_dict = {}
    if config:
        manager = ConfigManager(config)
        config_dict = manager.config
    
    tracker = ExperimentTracker(
        project=project,
        experiment_name=name,
        use_wandb=wandb,
        use_mlflow=mlflow,
        config=config_dict
    )
    
    click.echo(f"Tracking inicializado: {project}")
    if name:
        click.echo(f"Experimento: {name}")


@cli.command()
@click.option('--pattern', '-p', default='test_*.py', help='Patrón de archivos de test')
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
@click.option('--coverage', is_flag=True, help='Ejecutar con coverage')
def test(pattern: str, verbose: bool, coverage: bool):
    """Ejecuta tests."""
    import subprocess
    import sys
    
    cmd = ['pytest', pattern]
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov', '.', '--cov-report', 'html'])
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: pytest no está instalado. Instala con: pip install pytest", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Muestra información del sistema."""
    from core.utils import get_system_info
    
    info = get_system_info()
    
    if RICH_AVAILABLE:
        table = Table(title="Información del Sistema")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")
        
        for key, value in info.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    table.add_row(f"{key}.{sub_key}", str(sub_value))
            else:
                table.add_row(key, str(value))
        
        console.print(table)
    else:
        import json
        click.echo(json.dumps(info, indent=2))


if __name__ == '__main__':
    if CLICK_AVAILABLE:
        cli()
    else:
        print("Error: Click no está instalado. Instala con: pip install click")
        print("Usando comandos directos...")
        from improve_models import main
        main()



