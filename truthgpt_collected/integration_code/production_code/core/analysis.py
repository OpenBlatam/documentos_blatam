#!/usr/bin/env python3
"""
Analysis Utilities for Paper Modules
=====================================

Utilidades para análisis y visualización de módulos.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class LayerAnalysis:
    """Análisis de una capa."""
    name: str
    layer_type: str
    input_shape: Optional[Tuple[int, ...]] = None
    output_shape: Optional[Tuple[int, ...]] = None
    parameters: int = 0
    trainable: bool = True
    memory_mb: float = 0.0


@dataclass
class ModuleAnalysis:
    """Análisis completo de un módulo."""
    module_name: str
    total_parameters: int
    trainable_parameters: int
    layers: List[LayerAnalysis] = field(default_factory=list)
    memory_total_mb: float = 0.0
    layer_count: int = 0
    architecture_summary: Dict[str, Any] = field(default_factory=dict)


class ModuleAnalyzer:
    """Analizador de módulos."""
    
    def __init__(self):
        """Inicializa el analizador."""
        pass
    
    def analyze_module(self, module: BasePaperModule) -> ModuleAnalysis:
        """
        Analiza un módulo completo.
        
        Args:
            module: Módulo a analizar
        
        Returns:
            ModuleAnalysis con información detallada
        
        Raises:
            ValueError: Si module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        layers = []
        total_params = 0
        trainable_params = 0
        total_memory = 0.0
        
        layer_types = defaultdict(int)
        
        for name, layer in module.named_modules():
            if name == '':
                continue
            
            layer_type = type(layer).__name__
            layer_types[layer_type] += 1
            
            params = sum(p.numel() for p in layer.parameters())
            trainable = any(p.requires_grad for p in layer.parameters())
            memory_mb = sum(p.numel() * p.element_size() for p in layer.parameters()) / 1024**2
            
            total_params += params
            if trainable:
                trainable_params += params
            total_memory += memory_mb
            
            layers.append(LayerAnalysis(
                name=name,
                layer_type=layer_type,
                parameters=params,
                trainable=trainable,
                memory_mb=memory_mb
            ))
        
        return ModuleAnalysis(
            module_name=module.__class__.__name__,
            total_parameters=total_params,
            trainable_parameters=trainable_params,
            layers=layers,
            memory_total_mb=total_memory,
            layer_count=len(layers),
            architecture_summary={
                'layer_types': dict(layer_types),
                'total_layers': len(layers)
            }
        )
    
    def compare_architectures(
        self,
        modules: List[BasePaperModule]
    ) -> Dict[str, Any]:
        """
        Compara arquitecturas de múltiples módulos.
        
        Args:
            modules: Lista de módulos
        
        Returns:
            Diccionario con comparación
        """
        analyses = [self.analyze_module(m) for m in modules]
        
        return {
            'modules': [
                {
                    'name': a.module_name,
                    'parameters': a.total_parameters,
                    'trainable': a.trainable_parameters,
                    'memory_mb': a.memory_total_mb,
                    'layers': a.layer_count,
                    'layer_types': a.architecture_summary['layer_types']
                }
                for a in analyses
            ],
            'comparison': {
                'largest': max(analyses, key=lambda a: a.total_parameters).module_name,
                'smallest': min(analyses, key=lambda a: a.total_parameters).module_name,
                'most_layers': max(analyses, key=lambda a: a.layer_count).module_name,
                'least_layers': min(analyses, key=lambda a: a.layer_count).module_name
            }
        }
    
    def find_bottlenecks(self, module: BasePaperModule) -> List[LayerAnalysis]:
        """
        Encuentra cuellos de botella en un módulo.
        
        Args:
            module: Módulo a analizar
        
        Returns:
            Lista de capas que son cuellos de botella
        """
        analysis = self.analyze_module(module)
        
        if not analysis.layers:
            return []
        
        avg_params = sum(l.parameters for l in analysis.layers) / len(analysis.layers)
        threshold = avg_params * 2
        
        bottlenecks = [
            layer for layer in analysis.layers
            if layer.parameters > threshold
        ]
        
        return sorted(bottlenecks, key=lambda l: l.parameters, reverse=True)


def analyze_forward_pass(
    module: BasePaperModule,
    hidden_states: torch.Tensor,
    track_gradients: bool = False
) -> Dict[str, Any]:
    """
    Analiza un forward pass completo.
    
    Args:
        module: Módulo a analizar
        hidden_states: Input
        track_gradients: Si True, trackea gradientes
    
    Returns:
        Diccionario con análisis
    
    Raises:
        ValueError: Si los parámetros son inválidos
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if not isinstance(hidden_states, torch.Tensor):
        raise ValueError(f"hidden_states debe ser torch.Tensor, recibido: {type(hidden_states)}")
    
    module.eval()
    
    if track_gradients:
        module.train()
        hidden_states.requires_grad_(True)
    
    hooks = []
    activations = {}
    
    def hook_fn(name):
        def hook(module, input, output):
            if isinstance(output, torch.Tensor):
                activations[name] = {
                    'shape': list(output.shape),
                    'dtype': str(output.dtype),
                    'mean': output.mean().item(),
                    'std': output.std().item(),
                    'min': output.min().item(),
                    'max': output.max().item()
                }
        return hook
    
    for name, layer in module.named_modules():
        if name:
            hooks.append(layer.register_forward_hook(hook_fn(name)))
    
    try:
        with torch.set_grad_enabled(track_gradients):
            output, metadata = module(hidden_states)
        
        return {
            'input_shape': list(hidden_states.shape),
            'output_shape': list(output.shape),
            'activations': activations,
            'metadata': metadata,
            'num_activations': len(activations)
        }
    finally:
        for hook in hooks:
            hook.remove()


def compute_flops(
    module: BasePaperModule,
    input_shape: Tuple[int, ...] = (1, 128, 512)
) -> Dict[str, Any]:
    """
    Calcula FLOPs aproximados de un módulo.
    
    Args:
        module: Módulo
        input_shape: Shape del input
    
    Returns:
        Diccionario con FLOPs
    
    Raises:
        ValueError: Si los parámetros son inválidos
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if not isinstance(input_shape, tuple) or len(input_shape) < 2:
        raise ValueError(f"input_shape debe ser una tupla con al menos 2 elementos, recibido: {input_shape}")
    
    if any(s <= 0 for s in input_shape):
        raise ValueError(f"input_shape debe contener valores > 0, recibido: {input_shape}")
    
    def _check_thop():
        from thop import profile, clever_format
        return profile, clever_format
    
    thop_result, thop_error = safe_execute(_check_thop, default_value=None, log_errors=False)
    
    if thop_error or thop_result is None:
        logger.warning("thop no disponible, usando estimación aproximada")
        return _estimate_flops(module, input_shape)
    
    profile, clever_format = thop_result
    dummy_input = torch.randn(*input_shape)
    
    def _compute_flops():
        flops, params = profile(module, inputs=(dummy_input,), verbose=False)
        flops_formatted, params_formatted = clever_format([flops, params], "%.3f")
        return {
            'flops': flops,
            'flops_formatted': flops_formatted,
            'parameters': params,
            'parameters_formatted': params_formatted,
            'flops_per_parameter': flops / params if params > 0 else 0.0
        }
    
    result, error = safe_execute(_compute_flops, default_value=None, log_errors=False)
    if error or result is None:
        logger.warning("Error calculando FLOPs con thop", error=str(error) if error else "Unknown error")
        return _estimate_flops(module, input_shape)
    
    return result


def _estimate_flops(
    module: BasePaperModule,
    input_shape: Tuple[int, ...]
) -> Dict[str, Any]:
    """Estima FLOPs sin thop."""
    batch_size, seq_len, hidden_dim = input_shape
    
    total_params = sum(p.numel() for p in module.parameters())
    
    estimated_flops = batch_size * seq_len * total_params * 2
    
    return {
        'flops': estimated_flops,
        'flops_formatted': f"{estimated_flops / 1e9:.2f}G",
        'parameters': total_params,
        'parameters_formatted': f"{total_params / 1e6:.2f}M",
        'flops_per_parameter': 2.0,
        'estimated': True
    }

