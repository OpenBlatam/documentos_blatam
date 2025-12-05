#!/usr/bin/env python3
"""
Testing Utilities for Paper Modules
===================================

Utilidades para testing y validación de módulos.
"""

import torch
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from .paper_base import BasePaperModule, BasePaperConfig, ValidationError
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class TestResult:
    """Resultado de un test."""
    test_name: str
    passed: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModuleTester:
    """Tester para módulos de papers."""
    
    def __init__(self, device: str = "cpu"):
        """
        Inicializa el tester.
        
        Args:
            device: Dispositivo a usar
        """
        self.device = torch.device(device)
    
    def test_module(
        self,
        module: BasePaperModule,
        batch_size: int = 2,
        seq_len: int = 10,
        hidden_dim: Optional[int] = None
    ) -> List[TestResult]:
        """
        Ejecuta una suite de tests en un módulo.
        
        Args:
            module: Módulo a testear
            batch_size: Tamaño del batch
            seq_len: Longitud de secuencia
            hidden_dim: Dimensión hidden
        
        Returns:
            Lista de TestResult
        
        Raises:
            ValueError: Si los parámetros son inválidos o module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        if batch_size <= 0:
            raise ValueError(f"batch_size debe ser > 0, recibido: {batch_size}")
        
        if seq_len <= 0:
            raise ValueError(f"seq_len debe ser > 0, recibido: {seq_len}")
        
        if hidden_dim is None:
            hidden_dim = module.config.hidden_dim
        
        module.to(self.device)
        results = []
        
        tests = [
            ("test_forward_pass", self._test_forward_pass),
            ("test_output_shape", self._test_output_shape),
            ("test_gradient_flow", self._test_gradient_flow),
            ("test_nan_detection", self._test_nan_detection),
            ("test_inf_detection", self._test_inf_detection),
            ("test_device_consistency", self._test_device_consistency),
        ]
        
        hidden_states = torch.randn(
            batch_size,
            seq_len,
            hidden_dim,
            device=self.device,
            requires_grad=True
        )
        
        for test_name, test_func in tests:
            result, error = safe_execute(
                test_func,
                default_value=(False, {'error': 'Test execution failed'}),
                log_errors=False,
                module=module,
                hidden_states=hidden_states
            )
            
            if error:
                results.append(TestResult(
                    test_name=test_name,
                    passed=False,
                    error=str(error)
                ))
            else:
                passed, metadata = result
                results.append(TestResult(
                    test_name=test_name,
                    passed=passed,
                    metadata=metadata if metadata is not None else {}
                ))
        
        return results
    
    def _test_forward_pass(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test: Forward pass funciona."""
        try:
            output, metadata = module(hidden_states)
            return True, {
                'output_shape': list(output.shape),
                'has_metadata': metadata is not None
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def _test_output_shape(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test: Output shape es correcto."""
        try:
            output, _ = module(hidden_states)
            expected_shape = hidden_states.shape
            passed = output.shape == expected_shape
            return passed, {
                'expected': list(expected_shape),
                'actual': list(output.shape)
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def _test_gradient_flow(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test: Gradientes fluyen correctamente."""
        try:
            module.train()
            output, _ = module(hidden_states)
            loss = output.mean()
            loss.backward()
            
            has_grad = hidden_states.grad is not None
            grad_norm = hidden_states.grad.norm().item() if has_grad else 0.0
            
            return has_grad and grad_norm > 0, {
                'has_gradient': has_grad,
                'gradient_norm': grad_norm
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def _test_nan_detection(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test: No hay NaN en output."""
        try:
            output, _ = module(hidden_states)
            has_nan = torch.isnan(output).any().item()
            return not has_nan, {
                'has_nan': has_nan,
                'nan_count': torch.isnan(output).sum().item() if has_nan else 0
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def _test_inf_detection(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test: No hay Inf en output."""
        try:
            output, _ = module(hidden_states)
            has_inf = torch.isinf(output).any().item()
            return not has_inf, {
                'has_inf': has_inf,
                'inf_count': torch.isinf(output).sum().item() if has_inf else 0
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def _test_device_consistency(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> Tuple[bool, Dict[str, Any]]:
        """Test: Output está en el mismo device que input."""
        try:
            output, _ = module(hidden_states)
            same_device = output.device == hidden_states.device
            return same_device, {
                'input_device': str(hidden_states.device),
                'output_device': str(output.device)
            }
        except Exception as e:
            return False, {'error': str(e)}


def run_tests(
    module: BasePaperModule,
    device: str = "cpu",
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Ejecuta tests en un módulo y retorna resumen.
    
    Args:
        module: Módulo a testear
        device: Dispositivo
        **kwargs: Argumentos para test_module()
    
    Returns:
        Diccionario con resumen de tests
    
    Raises:
        ValueError: Si module es None
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    tester = ModuleTester(device=device)
    results = tester.test_module(module, **kwargs)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    return {
        'module_name': module.__class__.__name__,
        'total_tests': total,
        'passed': passed,
        'failed': total - passed,
        'pass_rate': passed / total if total > 0 else 0.0,
        'results': [
            {
                'test': r.test_name,
                'passed': r.passed,
                'error': r.error,
                'metadata': r.metadata
            }
            for r in results
        ]
    }

