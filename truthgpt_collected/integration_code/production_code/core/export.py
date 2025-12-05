#!/usr/bin/env python3
"""
Export Utilities for Paper Modules
===================================

Utilidades para exportar modelos a diferentes formatos.
"""

import torch
from typing import Dict, Any, Optional, Union, Tuple, List
from pathlib import Path

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)


def export_to_onnx(
    module: BasePaperModule,
    output_path: Union[str, Path],
    input_shape: Tuple[int, ...] = (1, 128, 512),
    opset_version: int = 14,
    **kwargs: Any
) -> bool:
    """
    Exporta un módulo a formato ONNX.
    
    Args:
        module: Módulo a exportar
        output_path: Ruta de salida
        input_shape: Shape del input de ejemplo (batch, seq, hidden_dim)
        opset_version: Versión de opset de ONNX
        **kwargs: Argumentos adicionales para torch.onnx.export
    
    Returns:
        True si la exportación fue exitosa
    
    Raises:
        ValueError: Si input_shape es inválido o opset_version está fuera de rango
    """
    if not isinstance(input_shape, tuple) or len(input_shape) < 2:
        raise ValueError(f"input_shape debe ser una tupla con al menos 2 elementos, recibido: {input_shape}")
    
    if not (7 <= opset_version <= 18):
        raise ValueError(f"opset_version debe estar entre 7 y 18, recibido: {opset_version}")
    
    try:
        import torch.onnx
    except ImportError:
        logger.error("torch.onnx no disponible")
        return False
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    module.eval()
    
    def _export_onnx():
        dummy_input = torch.randn(*input_shape)
        torch.onnx.export(
            module,
            dummy_input,
            str(output_path),
            opset_version=opset_version,
            input_names=['hidden_states'],
            output_names=['output'],
            dynamic_axes={
                'hidden_states': {0: 'batch_size', 1: 'seq_len'},
                'output': {0: 'batch_size', 1: 'seq_len'}
            },
            **kwargs
        )
    
    @retry(
        max_attempts=2,
        delay=0.5,
        strategy=RetryStrategy.FIXED_DELAY,
        exceptions=(RuntimeError, IOError, OSError)
    )
    def _export_with_retry():
        _export_onnx()
    
    result, error = safe_execute(_export_with_retry, default_value=False, log_errors=True)
    if result:
        logger.info("Modelo exportado a ONNX", path=str(output_path))
    return result


def export_to_torchscript(
    module: BasePaperModule,
    output_path: Union[str, Path],
    input_shape: Tuple[int, ...] = (1, 128, 512),
    method: str = 'trace'
) -> bool:
    """
    Exporta un módulo a TorchScript.
    
    Args:
        module: Módulo a exportar
        output_path: Ruta de salida
        input_shape: Shape del input de ejemplo
        method: Método de exportación ('trace' o 'script')
    
    Returns:
        True si la exportación fue exitosa
    
    Raises:
        ValueError: Si method no es 'trace' o 'script', o si input_shape es inválido
    """
    if method not in ('trace', 'script'):
        raise ValueError(f"method debe ser 'trace' o 'script', recibido: {method}")
    
    if not isinstance(input_shape, tuple) or len(input_shape) < 2:
        raise ValueError(f"input_shape debe ser una tupla con al menos 2 elementos, recibido: {input_shape}")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    module.eval()
    
    def _export_torchscript():
        if method == 'trace':
            dummy_input = torch.randn(*input_shape)
            traced = torch.jit.trace(module, dummy_input)
            traced.save(str(output_path))
        elif method == 'script':
            scripted = torch.jit.script(module)
            scripted.save(str(output_path))
        else:
            raise ValueError(f"Método inválido: {method}")
    
    result, error = safe_execute(_export_torchscript, default_value=False, log_errors=True)
    if result:
        logger.info("Modelo exportado a TorchScript", path=str(output_path), method=method)
    elif error and isinstance(error, ValueError):
        logger.error("Método inválido", method=method)
    return result


def export_model_info(
    module: BasePaperModule,
    output_path: Union[str, Path],
    format: str = 'json'
) -> bool:
    """
    Exporta información del modelo a un archivo.
    
    Args:
        module: Módulo
        output_path: Ruta de salida
        format: Formato de salida ('json', 'yaml', 'txt')
    
    Returns:
        True si la exportación fue exitosa
    
    Raises:
        ValueError: Si format no es soportado o module es None
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if format not in ('json', 'yaml', 'txt'):
        raise ValueError(f"format debe ser 'json', 'yaml' o 'txt', recibido: {format}")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    info = module.get_model_info()
    
    def _export_info():
        if format == 'json':
            import json
            with open(output_path, 'w') as f:
                json.dump(info, f, indent=2)
        elif format == 'yaml':
            try:
                import yaml
                with open(output_path, 'w') as f:
                    yaml.dump(info, f, default_flow_style=False)
            except ImportError:
                logger.warning("yaml no disponible, usando json")
                import json
                with open(output_path, 'w') as f:
                    json.dump(info, f, indent=2)
        elif format == 'txt':
            with open(output_path, 'w') as f:
                f.write(f"Model: {info['model_name']}\n")
                f.write(f"Total Parameters: {info['total_parameters']:,}\n")
                f.write(f"Trainable Parameters: {info['trainable_parameters']:,}\n")
                f.write(f"Device: {info['device']}\n")
                f.write(f"Dtype: {info['dtype']}\n")
                f.write(f"\nConfig:\n{info['config']}\n")
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    result, error = safe_execute(_export_info, default_value=False, log_errors=True)
    if result:
        logger.info("Información del modelo exportada", path=str(output_path), format=format)
    elif error and isinstance(error, ValueError):
        logger.error("Formato no soportado", format=format)
    return result


def export_complete(
    module: BasePaperModule,
    base_path: Union[str, Path],
    input_shape: Tuple[int, ...] = (1, 128, 512),
    formats: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Exporta un módulo en múltiples formatos.
    
    Args:
        module: Módulo a exportar
        base_path: Ruta base para los archivos
        input_shape: Shape del input
        formats: Lista de formatos ('onnx', 'torchscript', 'info')
    
    Returns:
        Diccionario con resultados de cada exportación
    
    Raises:
        ValueError: Si module es None, formats contiene valores inválidos, o input_shape es inválido
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if not isinstance(input_shape, tuple) or len(input_shape) < 2:
        raise ValueError(f"input_shape debe ser una tupla con al menos 2 elementos, recibido: {input_shape}")
    
    valid_formats = {'onnx', 'torchscript', 'info'}
    if formats is None:
        formats = ['onnx', 'torchscript', 'info']
    else:
        invalid_formats = [f for f in formats if f not in valid_formats]
        if invalid_formats:
            raise ValueError(f"formatos inválidos: {invalid_formats}. Formatos válidos: {valid_formats}")
    
    base_path = Path(base_path)
    results = {}
    
    if 'onnx' in formats:
        onnx_path = base_path.with_suffix('.onnx')
        results['onnx'] = export_to_onnx(module, onnx_path, input_shape)
    
    if 'torchscript' in formats:
        ts_path = base_path.with_suffix('.pt')
        results['torchscript'] = export_to_torchscript(module, ts_path, input_shape)
    
    if 'info' in formats:
        info_path = base_path.with_suffix('.json')
        results['info'] = export_model_info(module, info_path)
    
    return results

