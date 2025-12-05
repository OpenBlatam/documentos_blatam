#!/usr/bin/env python3
"""
Gestor de Configuración Centralizado
=====================================

⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.

Please use `core.config_manager` instead:
    from core.config_manager import ConfigManager, ModuleType, get_config_manager

This file is kept for backward compatibility only.
All functionality has been migrated to `core/config_manager.py`.
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "config_manager (root) is deprecated. Use 'core.config_manager' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from core.config_manager for backward compatibility
try:
    from core.config_manager import (
        # Classes
        ConfigManager,
        ModuleType,
        MemoryConfig,
        RedundancyConfig,
        SoraConfig,
        ChatConfig,
        PipelineConfig,
        # Functions
        get_config_manager,
        create_from_config,
        get_available_modules,
        validate_module_config,
        # Constants
        PYDANTIC_AVAILABLE,
        __version__,
    )
    
    __all__ = [
        'ConfigManager',
        'ModuleType',
        'MemoryConfig',
        'RedundancyConfig',
        'SoraConfig',
        'ChatConfig',
        'PipelineConfig',
        'get_config_manager',
        'create_from_config',
        'get_available_modules',
        'validate_module_config',
        'PYDANTIC_AVAILABLE',
        '__version__',
    ]
    
except ImportError as e:
    # If core.config_manager is not available, raise a clear error
    raise ImportError(
        "core.config_manager is not available. "
        "Please ensure the core package is properly installed. "
        f"Original error: {e}"
    ) from e
