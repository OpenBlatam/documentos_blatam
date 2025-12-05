#!/usr/bin/env python3
"""
Utilidades para API
===================

⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.

Please use `api.api_utils` instead:
    from api.api_utils import validate_episode_data, validate_query_data, ...

This file is kept for backward compatibility only.
All functionality has been migrated to `api/api_utils.py`.
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "api_utils (root) is deprecated. Use 'api.api_utils' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from api.api_utils for backward compatibility
try:
    from api.api_utils import (
        # Constants
        DEFAULT_TENSOR_DTYPE,
        DEFAULT_TENSOR_DEVICE,
        MAX_TENSOR_ELEMENTS,
        # Core validation functions
        validate_tensor_shape,
        tensor_to_list,
        # Specific validators
        validate_episode_data,
        validate_query_data,
        validate_items_data,
        validate_k_value,
        validate_priority,
        validate_similarity_threshold,
        # Range validators
        validate_float_range,
        validate_int_range,
        # Response utilities
        format_response,
        paginate_results,
    )
except ImportError as e:
    # If api.api_utils is not available, raise a clear error
    raise ImportError(
        "api.api_utils is not available. "
        "Please ensure the api package is properly installed. "
        f"Original error: {e}"
    ) from e

__all__ = [
    # Constants
    "DEFAULT_TENSOR_DTYPE",
    "DEFAULT_TENSOR_DEVICE",
    "MAX_TENSOR_ELEMENTS",
    # Core validation functions
    "validate_tensor_shape",
    "tensor_to_list",
    # Specific validators
    "validate_episode_data",
    "validate_query_data",
    "validate_items_data",
    "validate_k_value",
    "validate_priority",
    "validate_similarity_threshold",
    # Range validators
    "validate_float_range",
    "validate_int_range",
    # Response utilities
    "format_response",
    "paginate_results",
]
