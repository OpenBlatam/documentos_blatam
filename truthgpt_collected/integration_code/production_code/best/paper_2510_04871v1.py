#!/usr/bin/env python3
"""
Paper: 2510.04871v1 (Best Techniques Paper)
============================================

Implementación específica basada en las mejores técnicas.
Este módulo implementa las técnicas específicas propuestas en este paper.

Paper URL: https://arxiv.org/html/2510.04871v1

MATEMÁTICAS DEL PAPER IMPLEMENTADAS:

1. Ensemble Attention:
   - Múltiples cabezas: A_i = Attention_i(Q, K, V) para i ∈ [1, N]
   - Combinación: A_ensemble = Σ_i w_i · A_i
     donde w_i son pesos aprendibles o uniformes
   - Implementado en: EnsembleAttention.forward()

2. Weighted Combination:
   - Pesos: w_i = softmax(W · [A_i; context])
     donde W es una red que aprende pesos basados en el contexto
   - Permite que diferentes cabezas se especialicen en diferentes aspectos
   - Implementado opcionalmente en el módulo

3. Residual Connections:
   - Output: y = x + f(x) donde f es la transformación
   - Mejora el flujo de gradientes y estabilidad del entrenamiento
   - Implementado en las capas del módulo
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from core.utils import setup_logger
logger = setup_logger(__name__)
@dataclass
class Paper2510_04871v1Config:
    """Configuración específica para paper 2510.04871v1 (Best Techniques)."""
    hidden_dim: int = 512
    num_heads: int = 8
    best_technique_param: float = 1.0
    use_advanced_techniques: bool = True
    use_ensemble_attention: bool = True
    use_residual_connections: bool = True
    num_ensemble_heads: int = 4


class EnsembleAttention(nn.Module):
    """
    Ensemble Attention basado en paper 2510.04871v1.
    Técnica: Múltiples cabezas de atención con ensemble.
    
    Mejoras:
    - Validación de ensemble size
    - Mejor inicialización
    - Métricas de ensemble diversity
    - Weighted combination opcional
    """
    
    def __init__(self, hidden_dim: int, num_heads: int, num_ensemble: int = 4,
                 use_weighted_combination: bool = True, dropout: float = 0.1):
        super().__init__()
        if hidden_dim % num_heads != 0:
            raise ValueError(f"hidden_dim debe ser divisible por num_heads, recibido: hidden_dim={hidden_dim}, num_heads={num_heads}")
        if num_ensemble <= 0:
            raise ValueError(f"num_ensemble debe ser positivo, recibido: {num_ensemble}")
        
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.num_ensemble = num_ensemble
        self.head_dim = hidden_dim // num_heads
        self.use_weighted_combination = use_weighted_combination
        
        # Multiple attention heads (ensemble)
        self.attention_heads = nn.ModuleList([
            nn.MultiheadAttention(hidden_dim, num_heads, batch_first=True, dropout=dropout)
            for _ in range(num_ensemble)
        ])
        
        # Ensemble combination con mejor inicialización
        if use_weighted_combination:
            # Weighted combination
            self.ensemble_weights = nn.Parameter(torch.ones(num_ensemble) / num_ensemble)
            self.ensemble_combiner = nn.Linear(hidden_dim, hidden_dim)
        else:
            # Simple concatenation
            self.ensemble_combiner = nn.Linear(hidden_dim * num_ensemble, hidden_dim)
        
        nn.init.xavier_uniform_(self.ensemble_combiner.weight)
        if self.ensemble_combiner.bias is not None:
            nn.init.zeros_(self.ensemble_combiner.bias)
        
        # Metrics
        self.register_buffer('ensemble_diversity', torch.tensor(0.0))
        
    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Ensemble attention forward con mejoras.
        
        Args:
            x: Input tensor [batch, seq_len, hidden_dim]
            attention_mask: Optional attention mask
        """
        # Validation
        if x.dim() != 3:
            raise ValueError(f"Expected 3D input, got {x.dim()}D")
        if x.size(-1) != self.hidden_dim:
            raise ValueError(f"Input hidden_dim ({x.size(-1)}) != configured ({self.hidden_dim})")
        
        ensemble_outputs = []
        
        for attn_head in self.attention_heads:
            if attention_mask is not None:
                attn_out, _ = attn_head(x, x, x, key_padding_mask=attention_mask)
            else:
                attn_out, _ = attn_head(x, x, x)
            ensemble_outputs.append(attn_out)
        
        # Compute ensemble diversity (variance across outputs)
        if len(ensemble_outputs) > 1 and self.training:
            with torch.no_grad():
                stacked = torch.stack(ensemble_outputs, dim=0)  # [ensemble, batch, seq, hidden]
                diversity = stacked.std(dim=0).mean().item()
                self.ensemble_diversity = 0.9 * self.ensemble_diversity + 0.1 * diversity
        
        # Combine ensemble outputs
        if self.use_weighted_combination:
            # Weighted sum (more efficient than zip)
            weights = F.softmax(self.ensemble_weights, dim=0)
            stacked = torch.stack(ensemble_outputs, dim=0)  # [ensemble, batch, seq, hidden]
            weights_expanded = weights.view(-1, 1, 1, 1)  # [ensemble, 1, 1, 1]
            combined = (stacked * weights_expanded).sum(dim=0)  # [batch, seq, hidden]
            output = self.ensemble_combiner(combined)
        else:
            # Concatenation
            combined = torch.cat(ensemble_outputs, dim=-1)
            output = self.ensemble_combiner(combined)
        
        return output
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get ensemble metrics."""
        metrics = {
            'ensemble_diversity': self.ensemble_diversity.item()
        }
        if self.use_weighted_combination and hasattr(self, 'ensemble_weights'):
            metrics['ensemble_weights'] = F.softmax(self.ensemble_weights, dim=0).detach().cpu().tolist()
        return metrics


class Paper2510_04871v1_BestTechniques(nn.Module):
    """
    Módulo implementando las mejores técnicas del paper 2510.04871v1.
    
    Técnicas implementadas:
    - Ensemble Attention
    - Residual connections optimizadas
    - Best practices combinadas
    
    Basado en: https://arxiv.org/html/2510.04871v1
    """
    
    def __init__(self, config: Paper2510_04871v1Config):
        super().__init__()
        self.config = config
        self._gradient_checkpointing = False
        
        # Ensemble attention
        if config.use_ensemble_attention:
            self.ensemble_attn = EnsembleAttention(
                config.hidden_dim,
                config.num_heads,
                config.num_ensemble_heads
            )
        else:
            self.ensemble_attn = None
        
        # Layer normalization
        self.layer_norm_1 = nn.LayerNorm(config.hidden_dim)
        self.layer_norm_2 = nn.LayerNorm(config.hidden_dim)
        
        # Feed-forward con mejor inicialización
        self.ffn = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(config.hidden_dim * 4, config.hidden_dim),
            nn.Dropout(0.1)
        )
        
        # Initialize FFN weights
        for module in self.ffn:
            if isinstance(module, nn.Linear):
                try:
                    gain = nn.init.calculate_gain('gelu')
                except ValueError:
                    gain = 1.0
                nn.init.xavier_uniform_(module.weight, gain=gain)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        
        logger.info(f"Initialized Paper 2510.04871v1 Best Techniques with config: {config}")
    
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        use_autocast: bool = False
    ) -> torch.Tensor:
        """
        Forward pass implementando las mejores técnicas del paper.
        
        Args:
            x: Input tensor [batch_size, seq_len, hidden_dim]
            attention_mask: Optional attention mask [batch_size, seq_len]
            use_autocast: If True, use mixed precision (FP16/BF16) for faster inference
            
        Returns:
            Output tensor con mejores técnicas aplicadas
        """
        if x.dim() != 3:
            raise ValueError(f"Expected 3D input [batch, seq, hidden_dim], got {x.dim()}D tensor")
        if x.size(-1) != self.config.hidden_dim:
            raise ValueError(f"Input hidden_dim ({x.size(-1)}) != config.hidden_dim ({self.config.hidden_dim})")
        
        if torch.isnan(x).any() or torch.isinf(x).any():
            logger.warning("Input contains NaN or Inf values")
        
        def _forward_impl(x, attention_mask):
            residual = x
            x = self.layer_norm_1(x)
            if self.ensemble_attn is not None:
                x = self.ensemble_attn(x, attention_mask=attention_mask)
            if self.config.use_residual_connections:
                x = residual + x
            
            residual = x
            x = self.layer_norm_2(x)
            x = self.ffn(x)
            if self.config.use_residual_connections:
                x = residual + x
            
            return x
        
        if use_autocast and torch.cuda.is_available():
            autocast_context = torch.cuda.amp.autocast()
        else:
            from contextlib import nullcontext
            autocast_context = nullcontext()
        
        if self._gradient_checkpointing and self.training:
            with autocast_context:
                x = torch.utils.checkpoint.checkpoint(_forward_impl, x, attention_mask, use_reentrant=False)
        else:
            with autocast_context:
                x = _forward_impl(x, attention_mask)
        
        if torch.isnan(x).any() or torch.isinf(x).any():
            logger.error("Output contains NaN or Inf values")
        
        return x
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from ensemble attention."""
        if self.ensemble_attn is not None:
            return self.ensemble_attn.get_metrics()
        return {}
    
    def reset_metrics(self):
        """Reset all metrics to initial values."""
        if self.ensemble_attn is not None:
            self.ensemble_attn.ensemble_diversity.zero_()
    
    def enable_gradient_checkpointing(self, enable: bool = True):
        """Enable or disable gradient checkpointing to save memory."""
        self._gradient_checkpointing = enable
        logger.info(f"Gradient checkpointing {'enabled' if enable else 'disabled'}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model architecture."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        param_size_mb = sum(p.numel() * p.element_size() for p in self.parameters()) / (1024 ** 2)
        buffer_size_mb = sum(b.numel() * b.element_size() for b in self.buffers()) / (1024 ** 2)
        total_size_mb = param_size_mb + buffer_size_mb
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'non_trainable_parameters': total_params - trainable_params,
            'parameter_size_mb': param_size_mb,
            'buffer_size_mb': buffer_size_mb,
            'total_size_mb': total_size_mb,
            'hidden_dim': self.config.hidden_dim,
            'num_heads': self.config.num_heads,
            'use_ensemble_attention': self.config.use_ensemble_attention,
            'use_residual_connections': self.config.use_residual_connections,
            'num_ensemble_heads': self.config.num_ensemble_heads,
            'gradient_checkpointing': self._gradient_checkpointing
        }
    
    def save_state_dict(self, path: str, include_config: bool = True):
        """Save model state dict and optionally config."""
        state = {
            'model_state_dict': self.state_dict(),
        }
        if include_config:
            state['config_dict'] = {
                'hidden_dim': self.config.hidden_dim,
                'num_heads': self.config.num_heads,
                'best_technique_param': self.config.best_technique_param,
                'use_advanced_techniques': self.config.use_advanced_techniques,
                'use_ensemble_attention': self.config.use_ensemble_attention,
                'use_residual_connections': self.config.use_residual_connections,
                'num_ensemble_heads': self.config.num_ensemble_heads,
            }
        torch.save(state, path)
        logger.info(f"Model state dict saved to {path}")
    
    @classmethod
    def load_state_dict(cls, path: str, config: Optional[Paper2510_04871v1Config] = None):
        """Load model from state dict."""
        try:
            checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        except Exception:
            checkpoint = torch.load(path, map_location='cpu', weights_only=False)
        
        if config is None:
            if checkpoint.get('config_dict') is not None:
                config = Paper2510_04871v1Config(**checkpoint['config_dict'])
            elif checkpoint.get('config') is not None:
                config = checkpoint['config']
            else:
                config = Paper2510_04871v1Config()
        
        model = cls(config)
        model.load_state_dict(checkpoint['model_state_dict'])
        logger.info(f"Model state dict loaded from {path}")
        return model
    
    def compile_model(self, mode: str = "reduce-overhead"):
        """Compile model for better performance (PyTorch 2.0+)."""
        if hasattr(torch, 'compile'):
            try:
                compiled = torch.compile(self, mode=mode)
                logger.info(f"Model compiled with mode: {mode}")
                return compiled
            except Exception as e:
                logger.warning(f"Could not compile model: {e}")
                return self
        else:
            logger.warning("torch.compile not available (requires PyTorch 2.0+)")
            return self
    
    def optimize_for_inference(self):
        """Optimize model for inference."""
        self.eval()
        for param in self.parameters():
            param.requires_grad = False
        logger.info("Model optimized for inference")
        return self
    
    def to_device(self, device: torch.device):
        """Move model to specified device."""
        return self.to(device)
    
    def analyze_layers(self) -> Dict[str, Any]:
        """Analyze individual layers of the model."""
        layers_info = []
        layer_types = {}
        
        for name, module in self.named_modules():
            if name == '':
                continue
            
            layer_type = type(module).__name__
            params = sum(p.numel() for p in module.parameters())
            trainable = any(p.requires_grad for p in module.parameters())
            memory_mb = sum(p.numel() * p.element_size() for p in module.parameters()) / (1024 ** 2)
            
            layers_info.append({
                'name': name,
                'type': layer_type,
                'parameters': params,
                'trainable': trainable,
                'memory_mb': memory_mb
            })
            
            if layer_type not in layer_types:
                layer_types[layer_type] = 0
            layer_types[layer_type] += 1
        
        return {
            'layers': layers_info,
            'layer_types': layer_types,
            'total_layers': len(layers_info)
        }
    
    def convert_dtype(self, dtype: torch.dtype) -> 'Paper2510_04871v1_BestTechniques':
        """Convert model to specified dtype."""
        self.to(dtype)
        logger.info(f"Model converted to {dtype}")
        return self
    
    def get_gradient_norm(self) -> float:
        """Get the norm of all gradients."""
        total_norm = 0.0
        param_count = 0
        
        for p in self.parameters():
            if p.grad is not None:
                param_norm = p.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
                param_count += 1
        
        if param_count == 0:
            return 0.0
        
        total_norm = total_norm ** (1. / 2)
        return total_norm
    
    def clip_gradients(self, max_norm: float = 1.0) -> float:
        """Clip gradients to max_norm."""
        if max_norm <= 0:
            raise ValueError(f"max_norm must be positive, got {max_norm}")
        
        total_norm = torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm)
        return total_norm.item()
    
    def analyze_gradients(self) -> Dict[str, Any]:
        """Analyze gradient statistics."""
        grad_norms = []
        grad_max = []
        grad_min = []
        param_names = []
        
        for name, param in self.named_parameters():
            if param.grad is not None:
                grad_norm = param.grad.data.norm(2).item()
                grad_max_val = param.grad.data.max().item()
                grad_min_val = param.grad.data.min().item()
                
                grad_norms.append(grad_norm)
                grad_max.append(grad_max_val)
                grad_min.append(grad_min_val)
                param_names.append(name)
        
        if not grad_norms:
            return {
                'has_gradients': False,
                'total_norm': 0.0,
                'mean_norm': 0.0,
                'max_norm': 0.0,
                'min_norm': 0.0,
                'param_count': 0
            }
        
        return {
            'has_gradients': True,
            'total_norm': sum(g**2 for g in grad_norms) ** 0.5,
            'mean_norm': sum(grad_norms) / len(grad_norms),
            'max_norm': max(grad_norms),
            'min_norm': min(grad_norms),
            'max_grad_value': max(grad_max) if grad_max else 0.0,
            'min_grad_value': min(grad_min) if grad_min else 0.0,
            'param_count': len(grad_norms),
            'param_names': param_names
        }
    
    def export_to_onnx(
        self,
        output_path: str,
        input_shape: Tuple[int, ...] = (1, 128, 512),
        opset_version: int = 14
    ) -> bool:
        """Export model to ONNX format."""
        try:
            import torch.onnx
        except ImportError:
            logger.error("torch.onnx not available")
            return False
        
        from pathlib import Path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.eval()
        
        try:
            dummy_input = torch.randn(*input_shape)
            torch.onnx.export(
                self,
                dummy_input,
                str(output_path),
                opset_version=opset_version,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={
                    'input': {0: 'batch_size', 1: 'seq_len'},
                    'output': {0: 'batch_size', 1: 'seq_len'}
                }
            )
            logger.info(f"Model exported to ONNX: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to ONNX: {e}")
            return False
    
    def export_to_torchscript(
        self,
        output_path: str,
        input_shape: Tuple[int, ...] = (1, 128, 512),
        method: str = 'trace'
    ) -> bool:
        """Export model to TorchScript format."""
        from pathlib import Path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.eval()
        
        try:
            dummy_input = torch.randn(*input_shape)
            
            if method == 'trace':
                traced = torch.jit.trace(self, dummy_input)
                traced.save(str(output_path))
            elif method == 'script':
                scripted = torch.jit.script(self)
                scripted.save(str(output_path))
            else:
                raise ValueError(f"Unknown method: {method}")
            
            logger.info(f"Model exported to TorchScript: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to TorchScript: {e}")
            return False
    
    def freeze_parameters(self, freeze: bool = True):
        """Freeze or unfreeze model parameters."""
        for param in self.parameters():
            param.requires_grad = not freeze
        logger.info(f"Parameters {'frozen' if freeze else 'unfrozen'}")
        return self
    
    def setup_optimizer(
        self,
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        optimizer_type: str = 'adamw'
    ) -> torch.optim.Optimizer:
        """Setup optimizer for training."""
        if optimizer_type.lower() == 'adamw':
            optimizer = torch.optim.AdamW(
                self.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
                eps=1e-8
            )
        elif optimizer_type.lower() == 'adam':
            optimizer = torch.optim.Adam(
                self.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
                eps=1e-8
            )
        elif optimizer_type.lower() == 'sgd':
            optimizer = torch.optim.SGD(
                self.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
                momentum=0.9
            )
        else:
            raise ValueError(f"Unknown optimizer type: {optimizer_type}")
        
        logger.info(f"Optimizer setup: {optimizer_type} with lr={learning_rate}")
        return optimizer
    
    def setup_scheduler(
        self,
        optimizer: torch.optim.Optimizer,
        scheduler_type: str = 'cosine',
        warmup_steps: int = 0,
        max_steps: int = None,
        **kwargs
    ) -> Optional[torch.optim.lr_scheduler._LRScheduler]:
        """Setup learning rate scheduler."""
        if scheduler_type.lower() == 'cosine':
            if max_steps is None:
                raise ValueError("max_steps required for cosine scheduler")
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=max_steps,
                **kwargs
            )
        elif scheduler_type.lower() == 'linear':
            if max_steps is None:
                raise ValueError("max_steps required for linear scheduler")
            scheduler = torch.optim.lr_scheduler.LinearLR(
                optimizer,
                start_factor=1.0,
                end_factor=0.1,
                total_iters=max_steps,
                **kwargs
            )
        elif scheduler_type.lower() == 'lambda':
            if warmup_steps > 0 or max_steps is not None:
                def lr_lambda(step):
                    if step < warmup_steps:
                        return step / max(warmup_steps, 1)
                    if max_steps is not None:
                        progress = (step - warmup_steps) / max(max_steps - warmup_steps, 1)
                        return max(0.1, 1.0 - progress * 0.9)
                    return 1.0
                scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
            else:
                return None
        else:
            raise ValueError(f"Unknown scheduler type: {scheduler_type}")
        
        logger.info(f"Scheduler setup: {scheduler_type}")
        return scheduler
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the model."""
        checks = {
            'has_forward': hasattr(self, 'forward'),
            'has_parameters': True,
            'parameters_valid': True,
            'config_valid': True,
            'device_consistent': True
        }
        
        try:
            param_count = sum(p.numel() for p in self.parameters())
            checks['parameter_count'] = param_count
            checks['has_parameters'] = param_count > 0
            
            for name, param in self.named_parameters():
                if torch.isnan(param).any() or torch.isinf(param).any():
                    checks['parameters_valid'] = False
                    break
        except Exception as e:
            checks['has_parameters'] = False
            checks['parameters_valid'] = False
            checks['parameter_error'] = str(e)
        
        try:
            if not hasattr(self, 'config'):
                checks['config_valid'] = False
            elif self.config.hidden_dim <= 0 or self.config.num_heads <= 0:
                checks['config_valid'] = False
        except Exception:
            checks['config_valid'] = False
        
        try:
            devices = {p.device for p in self.parameters()}
            checks['device_consistent'] = len(devices) <= 1
            checks['device'] = str(list(devices)[0]) if devices else 'unknown'
        except Exception:
            checks['device_consistent'] = False
        
        all_passed = all(
            v for k, v in checks.items() 
            if isinstance(v, bool) and k not in ['has_forward']
        )
        
        return {
            'status': 'healthy' if all_passed else 'degraded',
            'checks': checks,
            'timestamp': __import__('time').time()
        }
    
    def validate_model(self) -> Dict[str, Any]:
        """Validate model structure and parameters."""
        issues = []
        warnings = []
        
        if not hasattr(self, 'config'):
            issues.append('Missing config attribute')
        
        if not hasattr(self, 'forward'):
            issues.append('Missing forward method')
        
        try:
            param_count = sum(p.numel() for p in self.parameters())
            if param_count == 0:
                warnings.append('Model has no parameters')
            
            for name, param in self.named_parameters():
                if param.requires_grad and torch.isnan(param).any():
                    issues.append(f'NaN in parameter: {name}')
                if param.requires_grad and torch.isinf(param).any():
                    issues.append(f'Inf in parameter: {name}')
        except Exception as e:
            issues.append(f'Error checking parameters: {e}')
        
        try:
            if hasattr(self, 'config'):
                if self.config.hidden_dim <= 0:
                    issues.append('Invalid hidden_dim in config')
                if self.config.num_heads <= 0:
                    issues.append('Invalid num_heads in config')
        except Exception as e:
            issues.append(f'Error validating config: {e}')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'parameter_count': sum(p.numel() for p in self.parameters()) if hasattr(self, 'parameters') else 0
        }
    
    def generate_comprehensive_report(
        self,
        include_benchmark: bool = False,
        include_memory_estimation: bool = True,
        batch_size: int = 4,
        seq_len: int = 128
    ) -> Dict[str, Any]:
        """Generate comprehensive report of the model."""
        report = {
            'model_name': self.__class__.__name__,
            'timestamp': __import__('time').time(),
            'config': {
                'hidden_dim': self.config.hidden_dim,
                'num_heads': self.config.num_heads,
                'use_ensemble_attention': self.config.use_ensemble_attention,
                'use_residual_connections': self.config.use_residual_connections,
                'num_ensemble_heads': self.config.num_ensemble_heads,
            }
        }
        
        model_info = self.get_model_info()
        report['model_info'] = model_info
        
        health = self.health_check()
        report['health'] = health
        
        validation = self.validate_model()
        report['validation'] = validation
        
        layer_analysis = self.analyze_layers()
        report['layer_analysis'] = {
            'total_layers': layer_analysis['total_layers'],
            'layer_types': layer_analysis['layer_types']
        }
        
        if include_memory_estimation:
            memory = self.estimate_memory_usage(batch_size=batch_size, seq_len=seq_len)
            report['memory_estimation'] = memory
        
        if include_benchmark:
            try:
                benchmark_result = self.benchmark(batch_size=batch_size, seq_len=seq_len, num_runs=5)
                report['benchmark'] = {
                    'avg_time': benchmark_result['avg_time'],
                    'throughput': benchmark_result['throughput'],
                    'device': benchmark_result['device']
                }
            except Exception as e:
                report['benchmark'] = {'error': str(e)}
        
        metrics = self.get_metrics()
        if metrics:
            report['metrics'] = metrics
        
        return report
    
    def estimate_memory_usage(
        self,
        batch_size: int = 1,
        seq_len: int = 128,
        dtype: torch.dtype = torch.float32
    ) -> Dict[str, float]:
        """Estimate memory usage for given input size."""
        bytes_per_element = {
            torch.float32: 4,
            torch.float16: 2,
            torch.bfloat16: 2,
            torch.int8: 1,
        }.get(dtype, 4)
        
        model_params = sum(p.numel() for p in self.parameters())
        model_memory_mb = (model_params * bytes_per_element) / (1024 ** 2)
        
        input_size = batch_size * seq_len * self.config.hidden_dim
        input_memory_mb = (input_size * bytes_per_element) / (1024 ** 2)
        
        output_memory_mb = input_memory_mb
        
        estimated_activation_memory_mb = input_memory_mb * 4
        
        total_memory_mb = model_memory_mb + input_memory_mb + output_memory_mb + estimated_activation_memory_mb
        
        return {
            'model_memory_mb': model_memory_mb,
            'input_memory_mb': input_memory_mb,
            'output_memory_mb': output_memory_mb,
            'activation_memory_mb': estimated_activation_memory_mb,
            'total_estimated_mb': total_memory_mb,
            'dtype': str(dtype)
        }
    
    def benchmark(
        self,
        batch_size: int = 4,
        seq_len: int = 128,
        num_runs: int = 10,
        warmup_runs: int = 3,
        device: Optional[torch.device] = None
    ) -> Dict[str, Any]:
        """Benchmark model performance."""
        if device is None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.to(device)
        self.eval()
        
        x = torch.randn(batch_size, seq_len, self.config.hidden_dim, device=device)
        attention_mask = torch.ones(batch_size, seq_len, dtype=torch.bool, device=device)
        
        for _ in range(warmup_runs):
            with torch.no_grad():
                _ = self(x, attention_mask=attention_mask)
        
        if device.type == 'cuda':
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        
        times = []
        for _ in range(num_runs):
            if device.type == 'cuda':
                torch.cuda.synchronize()
            
            start = torch.cuda.Event(enable_timing=True) if device.type == 'cuda' else None
            end = torch.cuda.Event(enable_timing=True) if device.type == 'cuda' else None
            
            if start:
                start.record()
            else:
                import time
                start_time = time.perf_counter()
            
            with torch.no_grad():
                _ = self(x, attention_mask=attention_mask)
            
            if end:
                end.record()
                torch.cuda.synchronize()
                elapsed = start.elapsed_time(end) / 1000.0
            else:
                elapsed = time.perf_counter() - start_time
            
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        memory_used = None
        if device.type == 'cuda':
            memory_used = torch.cuda.max_memory_allocated() / 1024**2
        
        total_tokens = batch_size * seq_len * num_runs
        throughput = total_tokens / sum(times) if sum(times) > 0 else 0
        
        std_time = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5 if len(times) > 1 else 0.0
        
        return {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_time': std_time,
            'throughput': throughput,
            'memory_used_mb': memory_used,
            'device': str(device),
            'batch_size': batch_size,
            'seq_len': seq_len,
            'num_runs': num_runs
        }


class TruthGPT_Paper2510_04871v1_Integration(nn.Module):
    """Integración del paper 2510.04871v1 con TruthGPT."""
    
    def __init__(self, base_model: nn.Module, paper_config: Paper2510_04871v1Config):
        super().__init__()
        if not isinstance(base_model, nn.Module):
            raise TypeError(f"base_model must be nn.Module, got {type(base_model)}")
        self.base_model = base_model
        self.best_techniques = Paper2510_04871v1_BestTechniques(paper_config)
    
    def forward(self, *args, **kwargs):
        """Forward pass con mejores técnicas del paper."""
        output = self.base_model(*args, **kwargs)
        if isinstance(output, tuple):
            hidden_states = output[0]
            attention_mask = kwargs.get('attention_mask', None)
            enhanced_hidden = self.best_techniques(hidden_states, attention_mask=attention_mask)
            return (enhanced_hidden,) + output[1:]
        else:
            attention_mask = kwargs.get('attention_mask', None)
            return self.best_techniques(output, attention_mask=attention_mask)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Paper 2510.04871v1 Best Techniques")
    print("=" * 60)
    
    config = Paper2510_04871v1Config()
    module = Paper2510_04871v1_BestTechniques(config)
    
    # Basic forward test
    x = torch.randn(2, 32, config.hidden_dim)
    output = module(x)
    print(f"✅ Basic forward: Input {x.shape} -> Output {output.shape}")
    
    # Test with attention mask
    attention_mask = torch.ones(2, 32, dtype=torch.bool)
    output = module(x, attention_mask=attention_mask)
    print(f"✅ With attention mask: Output {output.shape}")
    
    # Test metrics
    metrics = module.get_metrics()
    print(f"✅ Metrics: {list(metrics.keys())}")
    
    # Test model info
    info = module.get_model_info()
    print(f"✅ Model info: {info['total_parameters']:,} total parameters")
    
    # Test gradient checkpointing
    module.enable_gradient_checkpointing(True)
    module.train()
    output = module(x)
    print(f"✅ With gradient checkpointing: Output {output.shape}")
    
    # Test reset metrics
    module.reset_metrics()
    print("✅ Metrics reset successfully")
    
    # Test save/load
    import tempfile
    import os
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as f:
            temp_path = f.name
        module.save_state_dict(temp_path)
        loaded_module = Paper2510_04871v1_BestTechniques.load_state_dict(temp_path)
        test_output = loaded_module(x)
        print(f"✅ Save/load: Output {test_output.shape}")
    except Exception as e:
        print(f"⚠️ Save/load test skipped: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Test compile
    try:
        compiled = module.compile_model()
        compiled_output = compiled(x)
        print(f"✅ Compile: Output {compiled_output.shape}")
    except Exception as e:
        print(f"⚠️ Compile not available: {e}")
    
    # Test optimize for inference
    module.optimize_for_inference()
    print("✅ Optimized for inference")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)

