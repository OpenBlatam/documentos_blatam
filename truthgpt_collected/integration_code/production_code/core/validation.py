#!/usr/bin/env python3
"""
Validation Utilities for Paper Modules
=======================================

Utilidades adicionales para validación y verificación.
"""

import torch
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass

from .paper_base import BasePaperModule, ValidationError
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class ValidationResult:
    """Resultado de una validación."""
    passed: bool
    message: str
    details: Dict[str, Any]


class ModuleValidator:
    """Validador de módulos."""
    
    def __init__(self):
        """Inicializa el validador."""
        self.validators: List[Callable] = []
    
    def register_validator(self, validator: Callable) -> None:
        """
        Registra un validador.
        
        Args:
            validator: Función que retorna ValidationResult
        
        Raises:
            ValueError: Si validator es None o no es callable
        """
        if validator is None:
            raise ValueError("validator no puede ser None")
        
        if not callable(validator):
            raise ValueError(f"validator debe ser callable, recibido: {type(validator)}")
        
        self.validators.append(validator)
        logger.debug("Validador registrado", validator=validator.__name__)
    
    def validate_module(self, module: BasePaperModule) -> List[ValidationResult]:
        """
        Ejecuta todos los validadores en un módulo.
        
        Args:
            module: Módulo a validar
        
        Returns:
            Lista de ValidationResult
        
        Raises:
            ValueError: Si module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        results = []
        
        for validator in self.validators:
            result, error = safe_execute(
                validator,
                default_value=ValidationResult(
                    passed=False,
                    message=f"Error ejecutando validador: {error}" if error else "Unknown error",
                    details={}
                ),
                log_errors=False,
                module=module
            )
            
            if error:
                results.append(ValidationResult(
                    passed=False,
                    message=f"Error en validador: {str(error)}",
                    details={'validator': validator.__name__}
                ))
            else:
                results.append(result)
        
        return results
    
    def validate_all(self, module: BasePaperModule) -> Dict[str, Any]:
        """
        Valida un módulo y retorna resumen.
        
        Args:
            module: Módulo a validar
        
        Returns:
            Diccionario con resumen de validación
        
        Raises:
            ValueError: Si module es None
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        results = self.validate_module(module)
        
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        return {
            'module_name': module.__class__.__name__,
            'total_validations': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total if total > 0 else 0.0,
            'results': [
                {
                    'passed': r.passed,
                    'message': r.message,
                    'details': r.details
                }
                for r in results
            ]
        }


def create_default_validators() -> ModuleValidator:
    """
    Crea validadores por defecto.
    
    Returns:
        ModuleValidator con validadores predefinidos
    """
    validator = ModuleValidator()
    
    def validate_parameters(module: BasePaperModule) -> ValidationResult:
        """Valida que el módulo tenga parámetros."""
        info = module.get_model_info()
        has_params = info['total_parameters'] > 0
        
        return ValidationResult(
            passed=has_params,
            message='Module has parameters' if has_params else 'Module has no parameters',
            details={'total_parameters': info['total_parameters']}
        )
    
    def validate_config(module: BasePaperModule) -> ValidationResult:
        """Valida la configuración del módulo."""
        try:
            module.config.validate()
            return ValidationResult(
                passed=True,
                message='Configuration is valid',
                details={'config': module.config.to_dict()}
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f'Configuration validation failed: {str(e)}',
                details={'error': str(e)}
            )
    
    def validate_forward_shape(module: BasePaperModule) -> ValidationResult:
        """Valida que el forward mantenga la forma."""
        try:
            hidden_states = torch.randn(2, 10, module.config.hidden_dim)
            output, _ = module(hidden_states)
            
            shape_match = output.shape == hidden_states.shape
            
            return ValidationResult(
                passed=shape_match,
                message='Output shape matches input' if shape_match else 'Output shape mismatch',
                details={
                    'input_shape': list(hidden_states.shape),
                    'output_shape': list(output.shape)
                }
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f'Forward validation failed: {str(e)}',
                details={'error': str(e)}
            )
    
    validator.register_validator(validate_parameters)
    validator.register_validator(validate_config)
    validator.register_validator(validate_forward_shape)
    
    return validator


