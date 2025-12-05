#!/usr/bin/env python3
"""
API REST Unificada
==================

⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.

Please use `application.py` instead:
    from application import create_app
    app = create_app()

Or use `api_server.py` as the entry point:
    python api_server.py

This file is kept for backward compatibility only.
All endpoints have been migrated to the new `api/routes/` structure.
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "api_unified.py is deprecated. Use 'application.create_app()' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from application for backward compatibility
try:
    from application import create_app, get_app
    
    # Create app instance for backward compatibility
    app = create_app()
    
    # Also export create_api_app as alias for create_app
    def create_api_app(*args, **kwargs):
        """Deprecated: Use create_app from application instead."""
        warnings.warn(
            "create_api_app() is deprecated. Use create_app() from application instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return create_app(*args, **kwargs)
    
    __all__ = ['app', 'create_app', 'create_api_app', 'get_app']
    
except ImportError as e:
    # If application is not available, raise a clear error
    raise ImportError(
        "application module is not available. "
        "Please ensure the application package is properly installed. "
        f"Original error: {e}"
    ) from e

__version__ = '2.0.0'
