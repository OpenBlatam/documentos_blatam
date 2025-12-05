#!/usr/bin/env python3
"""
Sora CLI Tools - Herramientas de Línea de Comandos
===================================================

CLI tools para el módulo Sora usando Click.
"""

import torch
from pathlib import Path
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    CLICK_AVAILABLE = True
    RICH_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    RICH_AVAILABLE = False

from sora import (
    TextToVideoConfig,
    TextToVideoModule,
    ImageToVideoConfig,
    ImageToVideoModule,
    VideoToVideoConfig,
    VideoToVideoModule,
    SoraDeploymentManager,
    save_video_opencv,
    create_video_gif,
    benchmark_video_generation,
    estimate_model_size,
    profile_memory_usage,
)
from core.utils import setup_logger

logger = setup_logger(__name__)

if RICH_AVAILABLE:
    console = Console()
else:
    console = None


@click.group()
@click.version_option(version="2.0.0")
def sora_cli():
    """CLI tools para el módulo Sora - Generación de Video con IA."""
    pass


@sora_cli.command()
@click.argument("prompt", type=str)
@click.option("--output", "-o", type=click.Path(), default="output.mp4", help="Archivo de salida")
@click.option("--steps", "-s", type=int, default=50, help="Pasos de inferencia")
@click.option("--seed", type=int, help="Semilla para reproducibilidad")
@click.option("--fps", type=int, default=24, help="Frames por segundo")
@click.option("--resolution", "-r", type=str, default="256,256", help="Resolución (height,width)")
@click.option("--frames", "-f", type=int, default=16, help="Número de frames")
@click.option("--hidden-dim", type=int, default=512, help="Dimensión hidden")
def text2video(prompt, output, steps, seed, fps, resolution, frames, hidden_dim):
    """Genera video desde texto."""
    if not CLICK_AVAILABLE:
        click.echo("Error: Click no está instalado")
        return
    
    try:
        height, width = map(int, resolution.split(","))
        config = TextToVideoConfig(
            hidden_dim=hidden_dim,
            video_length=frames,
            resolution=(height, width),
            fps=fps,
            diffusion_steps=steps
        )
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creando modelo...", total=None)
                model = TextToVideoModule(config)
                model.eval()
                
                progress.update(task, description="Generando video...")
                with torch.no_grad():
                    video, metadata = model.generate_from_text(
                        prompt,
                        num_inference_steps=steps,
                        seed=seed
                    )
                
                progress.update(task, description="Guardando video...")
                save_video_opencv(video, output, fps=fps)
        
        else:
            click.echo("Creando modelo...")
            model = TextToVideoModule(config)
            model.eval()
            
            click.echo("Generando video...")
            with torch.no_grad():
                video, metadata = model.generate_from_text(
                    prompt,
                    num_inference_steps=steps,
                    seed=seed
                )
            
            click.echo("Guardando video...")
            save_video_opencv(video, output, fps=fps)
        
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[green]✓[/green] Video generado exitosamente\n"
                f"Archivo: {output}\n"
                f"Shape: {video.shape}\n"
                f"Frames: {metadata.get('num_frames')}\n"
                f"FPS: {metadata.get('fps')}",
                title="[bold green]Éxito[/bold green]"
            ))
        else:
            click.echo(f"✓ Video generado: {output}")
            click.echo(f"  Shape: {video.shape}")
            click.echo(f"  Frames: {metadata.get('num_frames')}")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)


@sora_cli.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default="output.mp4", help="Archivo de salida")
@click.option("--motion-strength", type=float, default=0.5, help="Fuerza del movimiento (0.0-1.0)")
@click.option("--steps", "-s", type=int, default=50, help="Pasos de inferencia")
@click.option("--seed", type=int, help="Semilla")
@click.option("--fps", type=int, default=24, help="Frames por segundo")
@click.option("--resolution", "-r", type=str, default="256,256", help="Resolución")
@click.option("--frames", "-f", type=int, default=16, help="Número de frames")
def image2video(image_path, output, motion_strength, steps, seed, fps, resolution, frames):
    """Anima imagen estática."""
    try:
        from PIL import Image
        import torchvision.transforms as transforms
        
        height, width = map(int, resolution.split(","))
        config = ImageToVideoConfig(
            video_length=frames,
            resolution=(height, width),
            fps=fps,
            motion_strength=motion_strength
        )
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Cargando imagen...", total=None)
                image = Image.open(image_path)
                transform = transforms.Compose([
                    transforms.Resize((height, width)),
                    transforms.ToTensor()
                ])
                image_tensor = transform(image).unsqueeze(0)
                
                progress.update(task, description="Creando modelo...")
                model = ImageToVideoModule(config)
                model.eval()
                
                progress.update(task, description="Animando imagen...")
                with torch.no_grad():
                    video, metadata = model.animate_image(
                        image_tensor,
                        num_inference_steps=steps,
                        motion_strength=motion_strength,
                        seed=seed
                    )
                
                progress.update(task, description="Guardando video...")
                save_video_opencv(video, output, fps=fps)
        else:
            click.echo("Cargando imagen...")
            image = Image.open(image_path)
            transform = transforms.Compose([
                transforms.Resize((height, width)),
                transforms.ToTensor()
            ])
            image_tensor = transform(image).unsqueeze(0)
            
            click.echo("Creando modelo...")
            model = ImageToVideoModule(config)
            model.eval()
            
            click.echo("Animando imagen...")
            with torch.no_grad():
                video, metadata = model.animate_image(
                    image_tensor,
                    num_inference_steps=steps,
                    motion_strength=motion_strength,
                    seed=seed
                )
            
            click.echo("Guardando video...")
            save_video_opencv(video, output, fps=fps)
        
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[green]✓[/green] Video animado exitosamente\n"
                f"Archivo: {output}\n"
                f"Motion Strength: {motion_strength}",
                title="[bold green]Éxito[/bold green]"
            ))
        else:
            click.echo(f"✓ Video animado: {output}")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)


@sora_cli.command()
@click.option("--hidden-dim", type=int, default=512, help="Dimensión hidden")
@click.option("--frames", "-f", type=int, default=16, help="Número de frames")
@click.option("--resolution", "-r", type=str, default="256,256", help="Resolución")
@click.option("--runs", type=int, default=10, help="Número de runs")
def benchmark(hidden_dim, frames, resolution, runs):
    """Benchmark de generación de video."""
    try:
        height, width = map(int, resolution.split(","))
        config = TextToVideoConfig(
            hidden_dim=hidden_dim,
            video_length=frames,
            resolution=(height, width)
        )
        
        model = TextToVideoModule(config)
        model.eval()
        
        if RICH_AVAILABLE:
            console.print("[yellow]Ejecutando benchmark...[/yellow]")
        
        results = benchmark_video_generation(
            model,
            input_shape=(1, frames, 3, height, width),
            num_runs=runs
        )
        
        if RICH_AVAILABLE:
            table = Table(title="Benchmark Results")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            
            table.add_row("Mean Time", f"{results['mean_time_ms']:.2f} ms")
            table.add_row("Std Time", f"{results['std_time_ms']:.2f} ms")
            table.add_row("Min Time", f"{results['min_time_ms']:.2f} ms")
            table.add_row("Max Time", f"{results['max_time_ms']:.2f} ms")
            table.add_row("FPS", f"{results['fps']:.2f}")
            table.add_row("Total Frames", str(results['total_frames']))
            
            console.print(table)
        else:
            click.echo("Benchmark Results:")
            click.echo(f"  Mean Time: {results['mean_time_ms']:.2f} ms")
            click.echo(f"  FPS: {results['fps']:.2f}")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)


@sora_cli.command()
@click.option("--hidden-dim", type=int, default=512, help="Dimensión hidden")
@click.option("--frames", "-f", type=int, default=16, help="Número de frames")
def model_info(hidden_dim, frames):
    """Muestra información del modelo."""
    try:
        config = TextToVideoConfig(hidden_dim=hidden_dim, video_length=frames)
        model = TextToVideoModule(config)
        
        info = model.get_model_info()
        size_info = estimate_model_size(model)
        
        if RICH_AVAILABLE:
            table = Table(title="Model Information")
            table.add_column("Propiedad", style="cyan")
            table.add_column("Valor", style="green")
            
            table.add_row("Total Parameters", f"{info['total_parameters']:,}")
            table.add_row("Trainable Parameters", f"{info['trainable_parameters']:,}")
            table.add_row("Model Size", f"{size_info['total_size_mb']:.2f} MB")
            table.add_row("Hidden Dim", str(config.hidden_dim))
            table.add_row("Video Length", str(config.video_length))
            table.add_row("Resolution", str(config.resolution))
            
            console.print(table)
        else:
            click.echo(f"Total Parameters: {info['total_parameters']:,}")
            click.echo(f"Model Size: {size_info['total_size_mb']:.2f} MB")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)


@sora_cli.command()
@click.option("--host", default="0.0.0.0", help="Host")
@click.option("--port", type=int, default=8000, help="Port")
@click.option("--models-dir", type=click.Path(), help="Directorio para modelos")
def serve(host, port, models_dir):
    """Inicia el servidor API."""
    try:
        from sora.api_server import SoraAPIServer
        
        models_path = Path(models_dir) if models_dir else None
        server = SoraAPIServer(models_dir=models_path)
        
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[bold green]Sora API Server[/bold green]\n"
                f"Host: {host}\n"
                f"Port: {port}\n"
                f"Docs: http://{host}:{port}/docs",
                title="Server"
            ))
        
        server.run(host=host, port=port)
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    if CLICK_AVAILABLE:
        sora_cli()
    else:
        print("Error: Click no está instalado. Instala con: pip install click rich")


