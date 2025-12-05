# Import Standards

**Date**: 2025-01-27  
**Status**: ✅ Enforced

---

## Overview

This document defines the standard import paths for the production_code codebase. All imports should follow these conventions to maintain consistency and avoid import conflicts.

---

## ✅ Correct Import Patterns

### API Utilities
```python
# ✅ CORRECT
from api.api_utils import validate_episode_data, validate_query_data

# ❌ INCORRECT (deprecated)
from api_utils import validate_episode_data
```

### Configuration Management
```python
# ✅ CORRECT
from core.config_manager import ConfigManager, ModuleType, get_config_manager

# ❌ INCORRECT (deprecated)
from config_manager import ConfigManager
```

### Core Utilities
```python
# ✅ CORRECT
from core.utils import setup_logger
from core.api_utils import create_fastapi_app
from core.error_handling import safe_execute

# ❌ INCORRECT
from utils import setup_logger  # If utils is at root
```

### Services
```python
# ✅ CORRECT
from services import MemoryService, PipelineService
from services.memory_service import MemoryService

# ❌ INCORRECT
from memory_service import MemoryService  # If at root
```

### API Components
```python
# ✅ CORRECT
from api.routes import api_router, root_router
from api.routes.memory import router as memory_router
from api.dependencies import get_memory_service
from api.middleware import RequestIDMiddleware
from api.auth import OptionalAuth

# ❌ INCORRECT
from api_middleware import LoggingMiddleware
from api_auth import APIKeyManager
```

### Application Factory
```python
# ✅ CORRECT
from application import create_app, get_app
from application.service_container import ServiceContainer

# ❌ INCORRECT (deprecated)
from api_unified import app, create_api_app
```

### Domain Modules
```python
# ✅ CORRECT
from memory import create_memory_system
from redundancy import create_redundancy_suppressor
from core.paper_base import BasePaperModule

# ❌ INCORRECT
from memory_module import MemorySystem  # If renamed
```

### Infrastructure
```python
# ✅ CORRECT
from infrastructure.providers import build_integrated_pipeline
from infrastructure.providers.pipeline_provider import build_integrated_pipeline

# ❌ INCORRECT
from providers import build_integrated_pipeline  # If at root
```

---

## Import Organization

### Standard Import Order

1. **Standard Library**
   ```python
   import os
   import sys
   from pathlib import Path
   from typing import Dict, List, Optional
   ```

2. **Third-Party Libraries**
   ```python
   from fastapi import FastAPI, HTTPException
   import torch
   from pydantic import BaseModel
   ```

3. **Local Application Imports (by layer)**
   ```python
   # Presentation Layer
   from api.api_utils import validate_episode_data
   from api.routes import api_router
   
   # Application Layer
   from services import MemoryService
   
   # Domain Layer
   from core.utils import setup_logger
   from memory import create_memory_system
   
   # Infrastructure Layer
   from infrastructure.providers import build_integrated_pipeline
   ```

---

## Deprecated Imports

The following import patterns are **deprecated** and should be replaced:

| Deprecated | Replacement |
|------------|-------------|
| `from api_utils import ...` | `from api.api_utils import ...` |
| `from config_manager import ...` | `from core.config_manager import ...` |
| `from api_unified import app` | `from application import create_app` |
| `from api_middleware import ...` | `from api.middleware import ...` |
| `from api_auth import ...` | `from api.auth import ...` or `from api.auth_advanced import ...` |

---

## Layer-Specific Import Rules

### Presentation Layer (`api/`, `api_*.py`, `cli*.py`)

**Can Import From:**
- ✅ `api/` - Other API components
- ✅ `services/` - Application services
- ✅ `core/` - Core utilities
- ✅ `application/` - Application factory

**Cannot Import From:**
- ❌ Domain modules directly (`memory/`, `redundancy/`, etc.)
- ❌ Infrastructure details

**Example:**
```python
# ✅ CORRECT
from api.api_utils import validate_episode_data
from services import MemoryService
from core.utils import setup_logger

# ❌ INCORRECT
from memory.paper_2506_15841v2 import MemoryModule  # Too deep
```

### Application Layer (`services/`, `integration_pipeline.py`)

**Can Import From:**
- ✅ `core/` - Core utilities
- ✅ Domain modules (`memory/`, `redundancy/`, etc.)
- ✅ `infrastructure/providers/` - Infrastructure factories

**Cannot Import From:**
- ❌ `api/` - Presentation layer
- ❌ FastAPI/Flask directly (use services)

**Example:**
```python
# ✅ CORRECT
from core.utils import setup_logger
from memory import create_memory_system
from infrastructure.providers import build_integrated_pipeline

# ❌ INCORRECT
from api.routes import api_router  # Presentation layer
from fastapi import FastAPI  # Should use services
```

### Domain Layer (`core/`, `memory/`, `redundancy/`, etc.)

**Can Import From:**
- ✅ `core/` - Core utilities
- ✅ Other domain modules
- ✅ Standard library
- ✅ Third-party libraries (torch, numpy, etc.)

**Cannot Import From:**
- ❌ `api/` - Presentation layer
- ❌ `services/` - Application layer
- ❌ FastAPI/Flask - Framework dependencies

**Example:**
```python
# ✅ CORRECT
from core.paper_base import BasePaperModule
from core.utils import setup_logger
import torch

# ❌ INCORRECT
from api.api_utils import validate_episode_data  # Presentation layer
from services import MemoryService  # Application layer
from fastapi import HTTPException  # Framework dependency
```

### Infrastructure Layer (`infrastructure/`)

**Can Import From:**
- ✅ Domain modules
- ✅ `core/` - Core utilities
- ✅ External libraries (FastAPI, databases, etc.)

**Example:**
```python
# ✅ CORRECT
from core.config_manager import ConfigManager
from memory import create_memory_system
from fastapi import FastAPI
```

---

## Common Import Patterns

### Conditional Imports with Availability Flags
```python
try:
    from some_module import SomeClass
    SOME_MODULE_AVAILABLE = True
except ImportError:
    SomeClass = None
    SOME_MODULE_AVAILABLE = False
```

### Type Checking Imports
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI
    from services import MemoryService
```

### Relative Imports (within same package)
```python
# Within api/routes/
from .memory import router as memory_router
from ..dependencies import get_memory_service
```

---

## Verification

### Check for Deprecated Imports
```bash
# Find root-level imports
grep -r "from (api_utils|config_manager|api_auth|api_middleware) import" --include="*.py"

# Should return no results (except in deprecated compatibility shims)
```

### Lint Check
```bash
# Run linter to check imports
ruff check . --select F401  # Unused imports
mypy . --check-untyped-defs  # Type checking
```

---

## Migration Checklist

When updating imports:

- [ ] Replace root-level imports with module paths
- [ ] Verify imports follow layer rules
- [ ] Check for circular dependencies
- [ ] Update tests to use new import paths
- [ ] Run linter to verify no errors
- [ ] Test that code still works

---

## Examples

### Before (Deprecated)
```python
from api_utils import validate_episode_data
from config_manager import ConfigManager
from api_unified import app
```

### After (Correct)
```python
from api.api_utils import validate_episode_data
from core.config_manager import ConfigManager
from application import create_app

app = create_app()
```

---

## Notes

- **Backward Compatibility**: Some deprecated imports are maintained in compatibility shims (e.g., `api_utils.py`, `api_unified.py`) but emit deprecation warnings.
- **Documentation**: Documentation files (`.md`) may show examples with deprecated imports for historical reference, but code should use correct imports.
- **Tests**: Test files should use the same import standards as production code.

---

**Last Updated**: 2025-01-27  
**Status**: ✅ Enforced



