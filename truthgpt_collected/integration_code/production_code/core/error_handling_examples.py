#!/usr/bin/env python3
"""
Ejemplos de uso de las utilidades de manejo de errores.

Este archivo muestra cómo usar las nuevas utilidades de error handling.
"""

from .error_handling import retry, RetryStrategy, safe_execute, ErrorHandler
from .paper_base import BasePaperModule, BasePaperConfig, ValidationError, ConfigurationError


def example_retry_decorator():
    """Ejemplo de uso del decorador retry."""
    
    @retry(
        max_attempts=3,
        delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=(IOError, OSError)
    )
    def save_file_operation(path: str, data: str):
        """Operación que puede fallar y necesita reintentos."""
        with open(path, 'w') as f:
            f.write(data)
    
    try:
        save_file_operation("/tmp/test.txt", "data")
    except Exception as e:
        print(f"Error después de reintentos: {e}")


def example_safe_execute():
    """Ejemplo de uso de safe_execute."""
    
    def risky_operation(x: int, y: int) -> int:
        """Operación que puede fallar."""
        if x < 0:
            raise ValueError("x debe ser positivo")
        return x + y
    
    result, error = safe_execute(
        risky_operation,
        default_value=0,
        log_errors=True,
        x=-1,
        y=5
    )
    
    if error:
        print(f"Error capturado: {error}")
    else:
        print(f"Resultado: {result}")


def example_error_handler():
    """Ejemplo de uso de ErrorHandler."""
    
    handler = ErrorHandler()
    
    def handle_validation_error(exception: Exception, context: dict) -> str:
        """Manejador para ValidationError."""
        return f"Error de validación: {exception}"
    
    def handle_config_error(exception: Exception, context: dict) -> str:
        """Manejador para ConfigurationError."""
        return f"Error de configuración: {exception}"
    
    def default_handler(exception: Exception, context: dict) -> str:
        """Manejador por defecto."""
        return f"Error desconocido: {exception}"
    
    handler.register_handler(ValidationError, handle_validation_error)
    handler.register_handler(ConfigurationError, handle_config_error)
    handler.set_default_handler(default_handler)
    
    try:
        raise ValidationError("Valor inválido")
    except ValidationError as e:
        result = handler.handle(e, context={"operation": "validate"})
        print(f"Resultado del handler: {result}")


def example_retry_with_callback():
    """Ejemplo de retry con callback."""
    
    attempt_count = [0]
    
    def on_retry_callback(attempt: int, exception: Exception):
        """Callback llamado en cada reintento."""
        attempt_count[0] = attempt
        print(f"Reintento {attempt}: {exception}")
    
    @retry(
        max_attempts=3,
        delay=0.5,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        on_retry=on_retry_callback
    )
    def flaky_operation():
        """Operación que falla las primeras veces."""
        if attempt_count[0] < 2:
            raise RuntimeError("Operación fallida")
        return "Éxito"
    
    result = flaky_operation()
    print(f"Resultado final: {result}")


if __name__ == "__main__":
    print("=== Ejemplo 1: Retry Decorator ===")
    example_retry_decorator()
    
    print("\n=== Ejemplo 2: Safe Execute ===")
    example_safe_execute()
    
    print("\n=== Ejemplo 3: Error Handler ===")
    example_error_handler()
    
    print("\n=== Ejemplo 4: Retry con Callback ===")
    example_retry_with_callback()



