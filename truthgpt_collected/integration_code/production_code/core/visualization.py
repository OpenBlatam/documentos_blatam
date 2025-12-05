#!/usr/bin/env python3
"""
Visualization Utilities for Paper Modules
=========================================

Utilidades para visualización y reportes de módulos.
"""

import torch
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


def generate_module_report(
    module: BasePaperModule,
    output_path: Optional[Union[str, Path]] = None,
    format: str = 'markdown'
) -> str:
    """
    Genera un reporte completo de un módulo.
    
    Args:
        module: Módulo a reportar
        output_path: Ruta donde guardar (opcional)
        format: Formato del reporte ('markdown', 'json', 'html')
    
    Returns:
        Contenido del reporte
    
    Raises:
        ValueError: Si module es None o format no es válido
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if format not in ('markdown', 'json', 'html'):
        raise ValueError(f"format debe ser 'markdown', 'json' o 'html', recibido: {format}")
    
    info = module.get_model_info()
    cache_stats = module.get_cache_stats()
    
    if format == 'markdown':
        report = f"""# Module Report: {info['model_name']}

## Configuration
```json
{json.dumps(info['config'], indent=2)}
```

## Parameters
- **Total Parameters**: {info['total_parameters']:,}
- **Trainable Parameters**: {info['trainable_parameters']:,}
- **Non-trainable Parameters**: {info['non_trainable_parameters']:,}

## Device & Type
- **Device**: {info['device']}
- **Dtype**: {info['dtype']}

## Usage Statistics
- **Forward Count**: {info['forward_count']}
- **Cache Size**: {cache_stats['cache_size']}/{cache_stats['max_cache_size']}
- **Cache Enabled**: {cache_stats['cache_enabled']}

## Metrics
```json
{json.dumps(module.get_metrics(), indent=2, default=str)}
```
"""
    elif format == 'json':
        report_data = {
            'model_info': info,
            'cache_stats': cache_stats,
            'metrics': module.get_metrics()
        }
        report = json.dumps(report_data, indent=2, default=str)
    else:
        report = str(info)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        def _write_report():
            output_path.write_text(report, encoding='utf-8')
        
        result, error = safe_execute(_write_report, default_value=None, log_errors=True)
        if result is not None:
            logger.info("Reporte generado", path=str(output_path))
        elif error:
            logger.error("Error guardando reporte", path=str(output_path), error=str(error))
    
    return report


def generate_comparison_report(
    modules: List[BasePaperModule],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Genera un reporte de comparación de múltiples módulos.
    
    Args:
        modules: Lista de módulos
        output_path: Ruta donde guardar (opcional)
    
    Returns:
        Contenido del reporte
    
    Raises:
        ValueError: Si modules está vacío o contiene None
    """
    if not modules:
        raise ValueError("modules no puede estar vacío")
    
    if any(m is None for m in modules):
        raise ValueError("modules no puede contener None")
    
    reports = []
    for module in modules:
        info = module.get_model_info()
        reports.append({
            'name': info['model_name'],
            'parameters': info['total_parameters'],
            'trainable': info['trainable_parameters'],
            'device': info['device'],
            'dtype': info['dtype'],
            'forward_count': info['forward_count']
        })
    
    report = "# Module Comparison Report\n\n"
    report += "| Module | Parameters | Trainable | Device | Dtype | Forward Count |\n"
    report += "|--------|------------|-----------|--------|-------|---------------|\n"
    
    for r in reports:
        report += f"| {r['name']} | {r['parameters']:,} | {r['trainable']:,} | {r['device']} | {r['dtype']} | {r['forward_count']} |\n"
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        def _write_comparison_report():
            output_path.write_text(report, encoding='utf-8')
        
        result, error = safe_execute(_write_comparison_report, default_value=None, log_errors=True)
        if result is not None:
            logger.info("Reporte de comparación generado", path=str(output_path))
        elif error:
            logger.error("Error guardando reporte de comparación", path=str(output_path), error=str(error))
    
    return report


def visualize_architecture(
    module: BasePaperModule,
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Genera una visualización de la arquitectura del módulo.
    
    Args:
        module: Módulo
        output_path: Ruta donde guardar (opcional)
    
    Returns:
        Representación de la arquitectura
    
    Raises:
        ValueError: Si module es None
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    lines = [f"Architecture: {module.__class__.__name__}", "=" * 60, ""]
    
    for name, layer in module.named_modules():
        if name == '':
            continue
        
        layer_type = type(layer).__name__
        params = sum(p.numel() for p in layer.parameters())
        
        lines.append(f"{name}: {layer_type} ({params:,} params)")
    
    architecture_str = "\n".join(lines)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(architecture_str, encoding='utf-8')
        logger.info("Arquitectura guardada", path=str(output_path))
    
    return architecture_str

