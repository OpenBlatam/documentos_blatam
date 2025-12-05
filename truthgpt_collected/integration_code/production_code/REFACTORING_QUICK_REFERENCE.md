# 🔄 Refactoring Quick Reference

**Quick action items for refactoring the production_code directory.**

---

## 🚨 Critical Issues (Fix First)

### 1. Duplicate `api_utils.py` Files
- **Root**: `api_utils.py` (268 lines) - Tensor validation
- **Core**: `core/api_utils.py` (231 lines) - HTTP/web utilities  
- **API**: `api/api_utils.py` (180 lines) - Route validation

**Action**: Migrate root `api_utils.py` → `api/api_utils.py`, then remove root file.

**Files to update:**
- `api_unified.py:38` - Change `from api_utils import` → `from api.api_utils import`
- `tests/test_api_utils.py:13` - Update import

---

### 2. Duplicate Config Managers
- **Root**: `config_manager.py` (521 lines)
- **Core**: `core/config_manager.py` (exists)

**Action**: Compare both files, consolidate into `core/config_manager.py`, update all imports.

**Files using root config_manager:**
- `infrastructure/providers/pipeline_provider.py:10`
- `application/service_container.py:16`
- `cli_unified.py:15`
- `examples/example_config.py:9`

---

### 3. API Entry Points Confusion
- **Old**: `api_unified.py` (1237 lines) - Doesn't use new `api/routes/` structure
- **New**: `application.py` (122 lines) - Uses layered architecture
- **Wrapper**: `api_server.py` (53 lines) - Uses `application.py`

**Action**: Migrate `api_unified.py` endpoints to `api/routes/`, deprecate `api_unified.py`.

---

### 4. Directory Naming Conflict
- **Issue**: `code/` conflicts with Python built-in `code` module
- **Action**: Rename `code/` → `code_modules/`

---

## 📋 File Duplication Analysis

### Auth Files (Different - Keep Both)
- `api/auth.py` - Simple OptionalAuth (176 lines)
- `api_auth.py` - Full APIKeyManager (313 lines)
- **Decision**: Keep both, but move `api_auth.py` → `api/auth_advanced.py` or consolidate

### Middleware Files (Overlapping - Consolidate)
- `api/middleware.py` - RequestID, Logging, ErrorHandling (110 lines)
- `api_middleware.py` - Logging, ErrorHandling, Monitoring (158 lines)
- **Decision**: Merge `api_middleware.py` functionality into `api/middleware.py`, remove root file

---

## 🔧 Import Standardization

### Current (Incorrect)
```python
from api_utils import validate_episode_data
from config_manager import ConfigManager
from api_auth import APIKeyManager
```

### Target (Correct)
```python
from api.api_utils import validate_episode_data
from core.config_manager import ConfigManager
from api.auth_advanced import APIKeyManager  # or consolidate
```

---

## 📁 Recommended File Moves

### To `api/` (Presentation Layer)
- `api_auth.py` → `api/auth_advanced.py` (or merge with `api/auth.py`)
- `api_middleware.py` → Merge into `api/middleware.py`

### To `services/` (Application Layer)
- Keep `integration_pipeline.py` at root (or move to `services/`)
- Keep `monitoring_system.py` at root (or move to `services/`)

### Keep at Root
- `api_server.py` - Entry point
- `application.py` - App factory
- `cli.py`, `cli_unified.py` - CLI entry points
- `chat_server.py` - Chat entry point

---

## ✅ Quick Wins (Can Do Immediately)

1. **Rename `code/` directory**
   ```bash
   mv code code_modules
   # Update all imports
   ```

2. **Update imports in `api_unified.py`**
   ```python
   # Line 38: Change
   from api_utils import ... 
   # To
   from api.api_utils import ...
   ```

3. **Merge middleware files**
   - Copy unique functionality from `api_middleware.py` to `api/middleware.py`
   - Remove `api_middleware.py`
   - Update imports

4. **Standardize config_manager imports**
   - Check if `core/config_manager.py` has all functionality
   - Update all root imports to `core.config_manager`

---

## 🎯 Priority Order

1. **Phase 1**: Fix import paths (low risk, high impact)
2. **Phase 2**: Consolidate duplicate files (medium risk)
3. **Phase 3**: Migrate API structure (higher risk, needs testing)
4. **Phase 4**: Directory reorganization (low risk)
5. **Phase 5**: Architecture verification (validation)

---

## 📝 Testing Checklist

After each change:
- [ ] Run `python -m pytest tests/`
- [ ] Check imports: `python -c "import <module>"`
- [ ] Run linter: `ruff check .`
- [ ] Verify no circular imports
- [ ] Test API endpoints (if changed)

---

## 🔗 Related Documents

- `REFACTORING_PLAN.md` - Detailed refactoring plan
- `ARCHITECTURE.md` - Layered architecture
- `docs/architecture/layers.md` - Layer rules



