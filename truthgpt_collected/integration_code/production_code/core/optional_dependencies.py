#!/usr/bin/env python3
"""
Optional Dependencies Manager
=============================

Manejo centralizado de dependencias opcionales y lazy imports.
"""

from __future__ import annotations

from typing import Optional, Any, Dict, TYPE_CHECKING
import importlib

if TYPE_CHECKING:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly
    import torch
    import fastapi
    import uvicorn
    import langchain
    import numpy as np
    import PIL


class OptionalDependency:
    """Wrapper para dependencias opcionales con mensajes informativos."""

    def __init__(
        self,
        module_name: str,
        package_name: Optional[str] = None,
        install_hint: Optional[str] = None
    ):
        """
        Inicializa un wrapper de dependencia opcional.

        Args:
            module_name: Nombre del módulo a importar.
            package_name: Nombre del paquete en pip (si difiere del módulo).
            install_hint: Mensaje personalizado para instalar.
        """
        self.module_name = module_name
        self.package_name = package_name or module_name
        self.install_hint = install_hint or f"pip install {self.package_name}"
        self._module: Optional[Any] = None
        self._available = False
        self._check_availability()

    def _check_availability(self):
        """Verifica si la dependencia está disponible."""
        try:
            self._module = importlib.import_module(self.module_name)
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self) -> bool:
        """Indica si la dependencia está disponible."""
        return self._available

    def get(self):
        """
        Obtiene el módulo si está disponible.

        Raises:
            ImportError: Si la dependencia no está instalada.
        """
        if not self._available:
            raise ImportError(
                f"{self.module_name} no está disponible. "
                f"Instálalo con: {self.install_hint}"
            )
        return self._module

    def __bool__(self) -> bool:
        return self._available


DEPENDENCY_SPECS = {
    'torch': {'install_hint': "pip install torch>=2.0.0"},
    'pandas': {'install_hint': "pip install pandas>=2.0.0"},
    'matplotlib': {'install_hint': "pip install matplotlib>=3.7.0"},
    'seaborn': {'install_hint': "pip install seaborn>=0.12.0"},
    'plotly': {'install_hint': "pip install plotly>=5.17.0"},
    'fastapi': {'install_hint': "pip install fastapi>=0.104.0"},
    'uvicorn': {'install_hint': "pip install 'uvicorn[standard]'>=0.24.0"},
    'langchain': {'install_hint': "pip install langchain>=0.0.350"},
    'sklearn': {
        'module_name': 'sklearn',
        'package_name': 'scikit-learn',
        'install_hint': "pip install scikit-learn>=1.3.0"
    },
    'PIL': {
        'package_name': 'Pillow',
        'install_hint': "pip install Pillow>=10.0.0"
    },
    'numpy': {'install_hint': "pip install numpy>=1.24.0"},
}


_DEPENDENCIES: Dict[str, OptionalDependency] = {}

for name, spec in DEPENDENCY_SPECS.items():
    module_name = spec.get('module_name', name)
    _DEPENDENCIES[name] = OptionalDependency(
        module_name=module_name,
        package_name=spec.get('package_name'),
        install_hint=spec.get('install_hint')
    )


def _get_dependency(name: str) -> OptionalDependency:
    if name not in _DEPENDENCIES:
        raise ValueError(f"Dependencia desconocida: {name}")
    return _DEPENDENCIES[name]


def get_dependency_info() -> Dict[str, Dict[str, Any]]:
    """Obtiene información de todas las dependencias registradas."""
    return {
        name: {
            'module': dep.module_name,
            'package': dep.package_name,
            'available': dep.available,
            'install_hint': dep.install_hint
        }
        for name, dep in _DEPENDENCIES.items()
    }


def check_optional_dependencies() -> Dict[str, bool]:
    """Retorna disponibilidad resumida de las dependencias."""
    return {name: dep.available for name, dep in _DEPENDENCIES.items()}


def require_dependency(dependency_name: str):
    """
    Decorador para requerir una dependencia opcional antes de ejecutar la función.

    Example:
        @require_dependency('pandas')
        def export_to_excel(data):
            pd = get_pandas()
            ...
    """
    dependency = _get_dependency(dependency_name)

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not dependency.available:
                raise ImportError(
                    f"{func.__name__} requiere {dependency_name}. "
                    f"Instálalo con: {dependency.install_hint}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_pandas():
    return _get_dependency('pandas').get()


def get_matplotlib():
    return _get_dependency('matplotlib').get()


def get_seaborn():
    return _get_dependency('seaborn').get()


def get_plotly():
    return _get_dependency('plotly').get()


def get_torch():
    return _get_dependency('torch').get()


def get_fastapi():
    return _get_dependency('fastapi').get()


def get_uvicorn():
    return _get_dependency('uvicorn').get()


def get_langchain():
    return _get_dependency('langchain').get()


def get_sklearn():
    return _get_dependency('sklearn').get()


def get_pillow():
    return _get_dependency('PIL').get()


def get_numpy():
    return _get_dependency('numpy').get()


PANDAS_AVAILABLE = _DEPENDENCIES['pandas'].available
MATPLOTLIB_AVAILABLE = _DEPENDENCIES['matplotlib'].available
SEABORN_AVAILABLE = _DEPENDENCIES['seaborn'].available
PLOTLY_AVAILABLE = _DEPENDENCIES['plotly'].available
TORCH_AVAILABLE = _DEPENDENCIES['torch'].available
FASTAPI_AVAILABLE = _DEPENDENCIES['fastapi'].available
UVICORN_AVAILABLE = _DEPENDENCIES['uvicorn'].available
LANGCHAIN_AVAILABLE = _DEPENDENCIES['langchain'].available
SKLEARN_AVAILABLE = _DEPENDENCIES['sklearn'].available
PIL_AVAILABLE = _DEPENDENCIES['PIL'].available
NUMPY_AVAILABLE = _DEPENDENCIES['numpy'].available



