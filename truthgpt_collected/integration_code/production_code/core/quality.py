#!/usr/bin/env python3
"""
Quality Assurance Utilities for Paper Modules
=============================================

Utilidades para asegurar calidad y detectar problemas en módulos.
"""

import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

from .paper_base import BasePaperModule
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class QualityIssue:
    """Problema de calidad detectado."""
    severity: str
    category: str
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class QualityReport:
    """Reporte de calidad de un módulo."""
    module_name: str
    issues: List[QualityIssue] = field(default_factory=list)
    warnings: List[QualityIssue] = field(default_factory=list)
    score: float = 1.0
    passed: bool = True


class QualityChecker:
    """Verificador de calidad para módulos."""
    
    def __init__(self):
        """Inicializa el verificador."""
        self.checks = [
            self._check_initialization,
            self._check_forward_pass,
            self._check_gradients,
            self._check_parameters,
            self._check_device_consistency,
            self._check_nan_inf,
            self._check_memory_efficiency
        ]
    
    def check_module(
        self,
        module: BasePaperModule,
        hidden_states: Optional[torch.Tensor] = None
    ) -> QualityReport:
        """
        Verifica la calidad de un módulo.
        
        Args:
            module: Módulo a verificar
            hidden_states: Input de ejemplo (opcional)
        
        Returns:
            QualityReport con resultados
        
        Raises:
            ValueError: Si module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        if hidden_states is not None and not isinstance(hidden_states, torch.Tensor):
            raise ValueError(f"hidden_states debe ser torch.Tensor o None, recibido: {type(hidden_states)}")
        
        report = QualityReport(module_name=module.__class__.__name__)
        
        if hidden_states is None:
            hidden_states = torch.randn(1, 32, module.config.hidden_dim)
        
        for check in self.checks:
            result, error = safe_execute(
                check,
                default_value=[],
                log_errors=False,
                module=module,
                hidden_states=hidden_states
            )
            
            if error:
                logger.warning("Error en check de calidad", check=check.__name__, error=str(error))
                continue
            
            issues = result if result else []
            for issue in issues:
                if issue.severity == 'error':
                    report.issues.append(issue)
                    report.passed = False
                else:
                    report.warnings.append(issue)
        
        report.score = self._calculate_score(report)
        
        return report
    
    def _check_initialization(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica la inicialización del módulo."""
        issues = []
        
        if not hasattr(module, 'config'):
            issues.append(QualityIssue(
                severity='error',
                category='initialization',
                message='Módulo no tiene atributo config',
                suggestion='Asegúrate de llamar super().__init__(config)'
            ))
        
        if not hasattr(module, 'forward'):
            issues.append(QualityIssue(
                severity='error',
                category='initialization',
                message='Módulo no tiene método forward',
                suggestion='Implementa el método forward'
            ))
        
        return issues
    
    def _check_forward_pass(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica el forward pass."""
        issues = []
        
        def _run_forward():
            module.eval()
            with torch.no_grad():
                return module(hidden_states)
        
        result, error = safe_execute(_run_forward, default_value=None, log_errors=False)
        
        if error:
            issues.append(QualityIssue(
                severity='error',
                category='forward_pass',
                message=f'Error en forward pass: {str(error)}',
                suggestion='Revisa la implementación del forward pass'
            ))
            return issues
        
        if result is None:
            return issues
        
        output, metadata = result
        
        if not isinstance(output, torch.Tensor):
            issues.append(QualityIssue(
                severity='error',
                category='forward_pass',
                message='Forward pass no retorna tensor',
                suggestion='Asegúrate de retornar (output, metadata)'
            ))
        
        if output.shape[0] != hidden_states.shape[0]:
            issues.append(QualityIssue(
                severity='error',
                category='forward_pass',
                message='Batch size no coincide',
                suggestion='Verifica que el forward pass preserve batch size'
            ))
        
        if not isinstance(metadata, dict):
            issues.append(QualityIssue(
                severity='warning',
                category='forward_pass',
                message='Metadata no es un diccionario',
                suggestion='Retorna un diccionario como metadata'
            ))
        
        return issues
    
    def _check_gradients(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica el flujo de gradientes."""
        issues = []
        
        def _run_gradient_check():
            module.train()
            hidden_states.requires_grad_(True)
            
            output, _ = module(hidden_states)
            loss = output.mean()
            loss.backward()
            
            has_grad = any(p.grad is not None for p in module.parameters() if p.requires_grad)
            
            grad_norms = [
                p.grad.norm().item()
                for p in module.parameters()
                if p.grad is not None
            ]
            
            return has_grad, grad_norms
        
        result, error = safe_execute(_run_gradient_check, default_value=(False, []), log_errors=False)
        
        if error:
            issues.append(QualityIssue(
                severity='warning',
                category='gradients',
                message=f'Error verificando gradientes: {str(error)}',
                suggestion='Revisa el flujo de gradientes'
            ))
            return issues
        
        has_grad, grad_norms = result
        
        if not has_grad:
            issues.append(QualityIssue(
                severity='warning',
                category='gradients',
                message='No se detectaron gradientes',
                suggestion='Verifica que los parámetros tengan requires_grad=True'
            ))
        
        if grad_norms:
            max_grad = max(grad_norms)
            if max_grad > 100.0:
                issues.append(QualityIssue(
                    severity='warning',
                    category='gradients',
                    message=f'Gradientes muy grandes: {max_grad:.2f}',
                    suggestion='Considera usar gradient clipping'
                ))
        
        return issues
    
    def _check_parameters(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica los parámetros del módulo."""
        issues = []
        
        total_params = sum(p.numel() for p in module.parameters())
        trainable_params = sum(p.numel() for p in module.parameters() if p.requires_grad)
        
        if total_params == 0:
            issues.append(QualityIssue(
                severity='error',
                category='parameters',
                message='Módulo no tiene parámetros',
                suggestion='Añade capas con parámetros al módulo'
            ))
        
        if trainable_params == 0:
            issues.append(QualityIssue(
                severity='warning',
                category='parameters',
                message='No hay parámetros entrenables',
                suggestion='Asegúrate de que algunos parámetros tengan requires_grad=True'
            ))
        
        return issues
    
    def _check_device_consistency(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica consistencia de dispositivos."""
        issues = []
        
        module_device = next(module.parameters()).device
        input_device = hidden_states.device
        
        if module_device != input_device:
            issues.append(QualityIssue(
                severity='warning',
                category='device',
                message=f'Dispositivo del módulo ({module_device}) != input ({input_device})',
                suggestion='Usa module.to(device) o hidden_states.to(device)'
            ))
        
        return issues
    
    def _check_nan_inf(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica NaN e Inf."""
        issues = []
        
        def _run_nan_inf_check():
            module.eval()
            with torch.no_grad():
                output, _ = module(hidden_states)
            return output
        
        result, error = safe_execute(_run_nan_inf_check, default_value=None, log_errors=False)
        
        if error or result is None:
            return issues
        
        output = result
        
        if torch.isnan(output).any():
            issues.append(QualityIssue(
                severity='error',
                category='numerical',
                message='NaN detectado en output',
                suggestion='Revisa operaciones matemáticas y normalizaciones'
            ))
        
        if torch.isinf(output).any():
            issues.append(QualityIssue(
                severity='error',
                category='numerical',
                message='Inf detectado en output',
                suggestion='Revisa operaciones que pueden causar overflow'
            ))
        
        return issues
    
    def _check_memory_efficiency(
        self,
        module: BasePaperModule,
        hidden_states: torch.Tensor
    ) -> List[QualityIssue]:
        """Verifica eficiencia de memoria."""
        issues = []
        
        total_params = sum(p.numel() for p in module.parameters())
        param_size_mb = total_params * 4 / (1024 * 1024)
        
        if param_size_mb > 1000:
            issues.append(QualityIssue(
                severity='warning',
                category='memory',
                message=f'Modelo muy grande: {param_size_mb:.2f} MB',
                suggestion='Considera usar técnicas de compresión o cuantización'
            ))
        
        return issues
    
    def _calculate_score(self, report: QualityReport) -> float:
        """Calcula score de calidad."""
        if not report.issues and not report.warnings:
            return 1.0
        
        error_penalty = len(report.issues) * 0.3
        warning_penalty = len(report.warnings) * 0.1
        
        score = max(0.0, 1.0 - error_penalty - warning_penalty)
        return score


def check_module_quality(
    module: BasePaperModule,
    hidden_states: Optional[torch.Tensor] = None
) -> QualityReport:
    """
    Verifica la calidad de un módulo.
    
    Args:
        module: Módulo a verificar
        hidden_states: Input de ejemplo (opcional)
    
    Returns:
        QualityReport con resultados
    
    Raises:
        ValueError: Si module es None
    """
    if module is None:
        raise ValueError("module no puede ser None")
    
    if hidden_states is not None and not isinstance(hidden_states, torch.Tensor):
        raise ValueError(f"hidden_states debe ser torch.Tensor o None, recibido: {type(hidden_states)}")
    
    checker = QualityChecker()
    return checker.check_module(module, hidden_states)
    """
    Verifica la calidad de un módulo.
    
    Args:
        module: Módulo a verificar
        hidden_states: Input de ejemplo
    
    Returns:
        QualityReport con resultados
    """
    checker = QualityChecker()
    return checker.check_module(module, hidden_states)

