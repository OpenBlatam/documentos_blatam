#!/usr/bin/env python3
"""
Endpoints de la API de Generación Multimodal.

Define todos los endpoints disponibles para generación.
"""

from typing import Optional
from datetime import datetime
import uuid

try:
    from fastapi import APIRouter, HTTPException, status, Depends, Request
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import (
    GenerationRequest,
    GenerationResponse,
    TaskStatus,
    BatchGenerationRequest,
    BatchGenerationResponse
)
from .utils.validators import validate_prompt, validate_parameters
from .error_handling import error_handler, ErrorCategory, APIError

try:
    from core.error_handling import safe_execute
    from core.utils import async_safe_execute
except ImportError:
    def safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            if log_errors:
                logger.error(f"Error en {func.__name__}: {e}")
            return default_value, e
    
    async def async_safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result, None
        except Exception as e:
            if log_errors:
                logger.error(f"Error en {func.__name__}: {e}")
            return default_value, e

# Referencia al deduplication manager (se inyectará desde el servidor)
deduplication_manager_ref = None
analytics_ref = None

router = APIRouter()


# Almacenamiento temporal de tareas (en producción usar Redis/DB)
# Esto se inyectará desde el servidor
tasks_storage = {}
task_queue_ref = None  # Se establecerá desde el servidor


@router.post("/generate", response_model=GenerationResponse)
async def generate(
    request: GenerationRequest,
    api_request: Request = None
):
    """
    Endpoint unificado para generación multimodal.
    
    Soporta todas las modalidades:
    - video: Text-to-Video, Image-to-Video, Video-to-Video
    - image: Text-to-Image, Image-to-Image, Image Upscale
    - audio: Text-to-Audio, Text-to-Music, Audio-to-Audio
    - 3d: Text-to-3D, Image-to-3D
    - multimodal: Contenido que combina múltiples modalidades
    """
    def _process_generation():
        # Validar prompt
        validate_prompt(request.prompt)
        
        # Validar parámetros
        validated_params = validate_parameters(
            request.parameters,
            request.modality.value
        )
        
        # Verificar duplicados
        if deduplication_manager_ref:
            is_duplicate, existing_task_id = deduplication_manager_ref.check_duplicate(
                request.prompt,
                request.modality.value,
                validated_params
            )
            
            if is_duplicate and existing_task_id:
                # Retornar tarea existente
                logger.info(f"Request duplicado detectado, retornando tarea existente: {existing_task_id}")
                if existing_task_id in tasks_storage:
                    existing_task = tasks_storage[existing_task_id]
                    return GenerationResponse(
                        task_id=existing_task_id,
                        status=existing_task["status"],
                        created_at=existing_task["created_at"],
                        result=existing_task.get("result"),
                        error=existing_task.get("error"),
                        progress=existing_task.get("progress"),
                        metadata={"duplicate": True, "original_task_id": existing_task_id}
                    )
        
        # Generar ID de tarea
        task_id = str(uuid.uuid4())
        
        # Crear entrada de tarea
        task_entry = {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "request": request.model_dump(),
            "validated_parameters": validated_params,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "progress": 0.0,
            "result": None,
            "error": None
        }
        
        # Almacenar tarea
        tasks_storage[task_id] = task_entry
        
        # Enviar a cola de procesamiento
        if task_queue_ref:
            task_queue_ref.add_task(
                modality=request.modality.value,
                generation_type=request.generation_type.value if request.generation_type else "text_to_video",
                prompt=request.prompt,
                parameters=request.parameters,
                priority=request.priority,
                callback_url=request.callback_url
            )
        
        # Registrar en deduplication manager
        if deduplication_manager_ref:
            deduplication_manager_ref.register_task(
                request.prompt,
                request.modality.value,
                validated_params,
                task_id
            )
        
        logger.info(
            f"Tarea creada: {task_id}",
            modality=request.modality.value,
            generation_type=request.generation_type
        )
        
        return GenerationResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=task_entry["created_at"],
            progress=0.0
        )
    
    result, error = safe_execute(_process_generation, default_value=None, log_errors=False)
    
    if error:
        logger.error(f"Error creando tarea: {error}")
        api_error = error_handler.handle_error(error, context={"endpoint": "generate"})
        raise error_handler.create_http_exception(api_error)
    
    return result


@router.post("/generate/batch", response_model=BatchGenerationResponse)
async def generate_batch(
    batch_request: BatchGenerationRequest
):
    """
    Endpoint para generación en batch.
    
    Permite enviar múltiples requests de generación en una sola llamada.
    """
    def _process_batch():
        batch_id = batch_request.batch_id or str(uuid.uuid4())
        task_ids = []
        
        for req in batch_request.requests:
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)
            
            task_entry = {
                "task_id": task_id,
                "batch_id": batch_id,
                "status": TaskStatus.PENDING,
                "request": req.model_dump(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "progress": 0.0,
                "result": None,
                "error": None
            }
            
            tasks_storage[task_id] = task_entry
        
        logger.info(
            f"Batch creado: {batch_id}",
            total_tasks=len(task_ids)
        )
        
        return BatchGenerationResponse(
            batch_id=batch_id,
            task_ids=task_ids,
            total_tasks=len(task_ids),
            created_at=datetime.now()
        )
    
    result, error = safe_execute(_process_batch, default_value=None, log_errors=False)
    
    if error:
        logger.error(f"Error creando batch: {error}")
        api_error = error_handler.handle_error(error, context={"endpoint": "generate_batch"})
        raise error_handler.create_http_exception(api_error)
    
    return result


@router.get("/task/{task_id}", response_model=GenerationResponse)
async def get_task(task_id: str):
    """
    Obtiene el estado y resultado de una tarea.
    
    Args:
        task_id: ID de la tarea
    """
    if task_id not in tasks_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea {task_id} no encontrada"
        )
    
    task = tasks_storage[task_id]
    
    return GenerationResponse(
        task_id=task_id,
        status=task["status"],
        created_at=task["created_at"],
        result=task.get("result"),
        error=task.get("error"),
        progress=task.get("progress"),
        estimated_completion=task.get("estimated_completion"),
        metadata=task.get("metadata", {})
    )


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancela una tarea pendiente o en procesamiento.
    
    Args:
        task_id: ID de la tarea
    """
    def _cancel_task():
        if task_id not in tasks_storage:
            api_error = APIError(
                category=ErrorCategory.NOT_FOUND,
                code="TASK_NOT_FOUND",
                message=f"Tarea {task_id} no encontrada",
                status_code=404
            )
            raise error_handler.create_http_exception(api_error)
        
        task = tasks_storage[task_id]
        
        if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            api_error = APIError(
                category=ErrorCategory.VALIDATION,
                code="TASK_ALREADY_FINALIZED",
                message=f"La tarea {task_id} ya está {task['status'].value}",
                status_code=400
            )
            raise error_handler.create_http_exception(api_error)
        
        task["status"] = TaskStatus.CANCELLED
        task["updated_at"] = datetime.now()
        
        logger.info(f"Tarea cancelada: {task_id}")
        
        return {"message": f"Tarea {task_id} cancelada exitosamente"}
    
    result, error = safe_execute(_cancel_task, default_value=None, log_errors=False)
    
    if error:
        if isinstance(error, HTTPException):
            raise error
        api_error = error_handler.handle_error(error, context={"endpoint": "cancel_task"})
        raise error_handler.create_http_exception(api_error)
    
    return result


@router.get("/tasks")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    modality: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Lista tareas con filtros opcionales.
    
    Args:
        status: Filtrar por estado
        modality: Filtrar por modalidad
        limit: Límite de resultados
        offset: Offset para paginación
    """
    filtered_tasks = list(tasks_storage.values())
    
    if status:
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
    
    if modality:
        filtered_tasks = [
            t for t in filtered_tasks
            if t.get("request", {}).get("modality") == modality
        ]
    
    # Ordenar por fecha de creación (más recientes primero)
    filtered_tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Paginación
    paginated = filtered_tasks[offset:offset + limit]
    
    return {
        "total": len(filtered_tasks),
        "limit": limit,
        "offset": offset,
        "tasks": [
            {
                "task_id": t["task_id"],
                "status": t["status"].value,
                "modality": t.get("request", {}).get("modality"),
                "created_at": t["created_at"].isoformat(),
                "progress": t.get("progress")
            }
            for t in paginated
        ]
    }


@router.get("/stats")
async def get_stats():
    """
    Obtiene estadísticas de la API.
    
    Returns:
        Estadísticas agregadas
    """
    def _get_stats():
        stats = {
            "tasks": {
                "total": len(tasks_storage),
                "by_status": {},
                "by_modality": {}
            }
        }
        
        # Estadísticas por estado
        for task in tasks_storage.values():
            status = task["status"].value if hasattr(task["status"], "value") else str(task["status"])
            stats["tasks"]["by_status"][status] = stats["tasks"]["by_status"].get(status, 0) + 1
            
            modality = task.get("request", {}).get("modality", "unknown")
            stats["tasks"]["by_modality"][modality] = stats["tasks"]["by_modality"].get(modality, 0) + 1
        
        # Estadísticas de cola
        if task_queue_ref:
            queue_stats, _ = safe_execute(
                task_queue_ref.get_queue_stats,
                default_value={},
                log_errors=False
            )
            stats["queue"] = queue_stats
        
        return stats
    
    result, error = safe_execute(_get_stats, default_value={}, log_errors=False)
    
    if error:
        api_error = error_handler.handle_error(error, context={"endpoint": "get_stats"})
        raise error_handler.create_http_exception(api_error)
    
    return result

