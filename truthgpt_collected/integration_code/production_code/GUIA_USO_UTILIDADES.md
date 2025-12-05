# 📖 Guía de Uso de Utilidades

**Versión**: 2.0.0  
**Fecha**: 2025-01-27

---

## 📋 Introducción

Esta guía proporciona ejemplos prácticos de cómo usar las utilidades reutilizables creadas para mejorar la calidad y consistencia del código.

---

## 🎨 Decoradores

### `@handle_route_errors`

Manejo consistente de errores en rutas API.

#### Uso Básico
```python
from api.decorators import handle_route_errors
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/store")
@handle_route_errors("store_episode", lambda s: s.is_available(), "memory")
async def store_episode(
    request: MemoryStoreRequest,
    req: Request,
    service: MemoryService = Depends(get_memory_service)
):
    # Tu código aquí - sin manejo de errores manual
    return service.store(request.episode)
```

#### Sin Decorador (Antes)
```python
@router.post("/store")
async def store_episode(request, req, service):
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Service not available")
        # ... código ...
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### `@validate_request`

Validación de requests antes de ejecutar la ruta.

#### Uso
```python
from api.decorators import validate_request

def validate_message(request: ChatRequest) -> tuple[bool, Optional[str]]:
    if not request.message.strip():
        return False, "Message cannot be empty"
    if len(request.message) > 10000:
        return False, "Message too long (max 10000 characters)"
    return True, None

@router.post("/chat")
@validate_request(validate_message)
async def chat(request: ChatRequest):
    # Request ya está validado
    return service.chat(request.message)
```

### `@log_request`

Logging de requests y responses.

#### Uso
```python
from api.decorators import log_request

@router.post("/process")
@log_request(log_request_body=True, log_response=False)
async def process(request: Request, data: ProcessRequest):
    # Request y response serán logueados automáticamente
    return process_data(data)
```

---

## 🛠️ Helpers

### Request Helpers

#### `get_request_id()`
```python
from api.helpers import get_request_id

request_id = get_request_id(req)
logger.info(f"Processing request", request_id=request_id)
```

#### `log_operation()`
```python
from api.helpers import log_operation

log_operation("convert_document", req, level="info", format="pdf")
```

### File Helpers

#### `validate_file_size()`
```python
from api.helpers import validate_file_size
from pathlib import Path

file_path = Path("document.pdf")
validate_file_size(file_path, max_size_mb=100)  # Raises HTTPException if too large
```

#### `generate_filename()`
```python
from api.helpers import generate_filename

# Con nombre base
filename = generate_filename("document", "pdf")  # "document.pdf"

# Sin nombre base (usa timestamp)
filename = generate_filename(extension="pdf")  # "file_20250127_143022.pdf"
```

#### `detect_file_type()`
```python
from api.helpers import detect_file_type
from pathlib import Path

file_path = Path("data.json")
file_type = detect_file_type(file_path)  # "json"
```

### Format Helpers

#### `normalize_format()`
```python
from api.helpers import normalize_format

format = normalize_format("word")  # "docx"
format = normalize_format("excel")  # "xlsx"
format = normalize_format("pdf")  # "pdf"
```

#### `validate_format()`
```python
from api.helpers import validate_format

# Valida y normaliza
format = validate_format("word", ["pdf", "docx", "xlsx"])  # "docx"
# Raises HTTPException if invalid
```

#### `get_media_type()`
```python
from api.helpers import get_media_type

media_type = get_media_type("pdf")  # "application/pdf"
media_type = get_media_type("docx")  # "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
```

---

## 📤 Response Utils

### `create_success_response()`
```python
from api.response_utils import create_success_response

# Respuesta simple
return create_success_response(
    data={"episodes": episodes},
    message="Episodes retrieved successfully",
    req=req
)

# Con metadata
return create_success_response(
    data=result,
    metadata={"processing_time": 0.5, "items_processed": 100},
    req=req
)
```

### `create_paginated_response()`
```python
from api.response_utils import create_paginated_response

return create_paginated_response(
    items=results,
    page=page,
    page_size=page_size,
    total=total_count,
    req=req,
    metadata={"query": search_query}
)
```

### `create_list_response()`
```python
from api.response_utils import create_list_response

return create_list_response(
    items=items_list,
    req=req,
    metadata={"source": "database"}
)
```

### `create_stats_response()`
```python
from api.response_utils import create_stats_response

stats = {
    "total_processed": 1500,
    "average_time": 0.5,
    "success_rate": 0.98
}

return create_stats_response(stats, req=req)
```

### `create_error_response()`
```python
from api.response_utils import create_error_response

# Error simple
return create_error_response(
    error="Invalid input data",
    code="INVALID_INPUT",
    status_code=400,
    req=req
)

# Error con detalles
return create_error_response(
    error="Validation failed",
    code="VALIDATION_ERROR",
    status_code=400,
    req=req,
    details={"field": "email", "reason": "Invalid format"}
)
```

---

## ✅ Validation Helpers

### `validate_not_empty()`
```python
from api.validation_helpers import validate_not_empty

# Valida que no esté vacío
message = validate_not_empty(request.message, name="message")

# Permite whitespace
text = validate_not_empty(request.text, name="text", allow_whitespace=True)
```

### `validate_string_length()`
```python
from api.validation_helpers import validate_string_length

# Valida longitud
message = validate_string_length(
    request.message,
    min_length=1,
    max_length=10000,
    name="message"
)
```

### `validate_list_length()`
```python
from api.validation_helpers import validate_list_length

# Valida longitud de lista
items = validate_list_length(
    request.items,
    min_length=1,
    max_length=1000,
    name="items"
)
```

### `validate_file_exists()`
```python
from api.validation_helpers import validate_file_exists
from pathlib import Path

# Valida que archivo exista
file_path = validate_file_exists("document.pdf")
# Raises HTTPException 404 if not found
```

### `validate_dict_keys()`
```python
from api.validation_helpers import validate_dict_keys

# Valida que dict tenga keys requeridas
config = validate_dict_keys(
    request.config,
    required_keys=["host", "port", "database"],
    name="config"
)
```

### `validate_one_of()`
```python
from api.validation_helpers import validate_one_of

# Valida que valor esté en lista permitida
format = validate_one_of(
    request.format,
    ["pdf", "docx", "xlsx"],
    name="format"
)
```

---

## 🔄 Ejemplos de Migración

### Ejemplo 1: Ruta Simple

#### Antes
```python
@router.post("/process")
async def process(request: ProcessRequest, req: Request):
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="Data cannot be empty")
        
        result = service.process(request.data)
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "request_id": getattr(req.state, 'request_id', None)
        }
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

#### Después
```python
from api.decorators import handle_route_errors
from api.response_utils import create_success_response
from api.validation_helpers import validate_not_empty

@router.post("/process")
@handle_route_errors("process", lambda s: s.is_available(), "service")
async def process(request: ProcessRequest, req: Request, service: Service):
    validate_not_empty(request.data, name="data")
    result = service.process(request.data)
    return create_success_response(result, req=req)
```

### Ejemplo 2: Ruta con Validación Compleja

#### Antes
```python
@router.post("/convert")
async def convert(request: ConvertRequest, req: Request):
    try:
        # Validaciones manuales
        if not request.message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        if len(request.message) > 10000:
            raise HTTPException(status_code=400, detail="Message too long")
        
        format = request.format.lower()
        if format == "word":
            format = "docx"
        if format not in ["pdf", "docx", "xlsx"]:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        result = converter.convert(request.message, format)
        
        return {
            "success": True,
            "data": result,
            "request_id": getattr(req.state, 'request_id', None)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

#### Después
```python
from api.decorators import handle_route_errors
from api.helpers import validate_format
from api.validation_helpers import validate_string_length
from api.response_utils import create_success_response

@router.post("/convert")
@handle_route_errors("convert", lambda s: s.is_available(), "converter")
async def convert(request: ConvertRequest, req: Request, converter: Converter):
    validate_string_length(request.message, max_length=10000, name="message")
    format = validate_format(request.format, ["pdf", "docx", "xlsx"])
    result = converter.convert(request.message, format)
    return create_success_response(result, req=req)
```

### Ejemplo 3: Ruta con Paginación

#### Antes
```python
@router.get("/items")
async def get_items(page: int = 1, page_size: int = 100, req: Request = None):
    try:
        items = service.get_all_items()
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            "success": True,
            "data": items[start:end],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            },
            "request_id": getattr(req.state, 'request_id', None) if req else None
        }
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

#### Después
```python
from api.decorators import handle_route_errors
from api.response_utils import create_paginated_response

@router.get("/items")
@handle_route_errors("get_items", lambda s: s.is_available(), "service")
async def get_items(
    page: int = 1,
    page_size: int = 100,
    req: Request = None,
    service: Service = Depends(get_service)
):
    items = service.get_all_items()
    return create_paginated_response(
        items=items,
        page=page,
        page_size=page_size,
        req=req
    )
```

---

## 💡 Mejores Prácticas

### 1. Usar Decoradores para Manejo de Errores
✅ **Hacer**:
```python
@handle_route_errors("operation_name", lambda s: s.is_available(), "service")
async def my_route(...):
    # Código sin try/except
```

❌ **Evitar**:
```python
async def my_route(...):
    try:
        # ... código ...
    except Exception as e:
        # Manejo manual
```

### 2. Usar Response Utils para Respuestas
✅ **Hacer**:
```python
return create_success_response(data, req=req)
```

❌ **Evitar**:
```python
return {
    "success": True,
    "data": data,
    "timestamp": datetime.now().isoformat(),
    "request_id": getattr(req.state, 'request_id', None)
}
```

### 3. Usar Validation Helpers
✅ **Hacer**:
```python
validate_string_length(message, max_length=10000, name="message")
```

❌ **Evitar**:
```python
if len(message) > 10000:
    raise HTTPException(status_code=400, detail="Message too long")
```

### 4. Combinar Utilidades
✅ **Hacer**:
```python
@handle_route_errors("convert", lambda s: s.is_available(), "converter")
@validate_request(validate_message)
async def convert(...):
    format = validate_format(request.format, ["pdf", "docx"])
    result = converter.convert(request.data, format)
    return create_success_response(result, req=req)
```

---

## 📚 Referencia Rápida

### Importaciones Comunes
```python
# Decoradores
from api.decorators import handle_route_errors, validate_request, log_request

# Helpers
from api.helpers import (
    get_request_id, validate_file_size, generate_filename,
    normalize_format, validate_format, get_media_type
)

# Response Utils
from api.response_utils import (
    create_success_response, create_error_response,
    create_paginated_response, create_list_response, create_stats_response
)

# Validation Helpers
from api.validation_helpers import (
    validate_not_empty, validate_string_length, validate_list_length,
    validate_file_exists, validate_dict_keys, validate_one_of
)
```

---

## ✅ Checklist de Migración

Al migrar una ruta existente:

- [ ] Reemplazar manejo de errores manual con `@handle_route_errors`
- [ ] Reemplazar validaciones manuales con validation helpers
- [ ] Reemplazar construcción de respuestas con response utils
- [ ] Usar `get_request_id()` en lugar de `getattr(req.state, 'request_id', None)`
- [ ] Agregar docstrings completos
- [ ] Verificar que no hay errores de linter
- [ ] Probar que la funcionalidad sigue igual

---

**Versión**: 2.0.0  
**Última actualización**: 2025-01-27



