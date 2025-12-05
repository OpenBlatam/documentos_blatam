#!/usr/bin/env python3
"""
Modelos de datos para la API de Generación Multimodal.

Define los modelos Pydantic para requests y responses de la API.
"""

from typing import Optional, Dict, Any, List, Literal, Union
from enum import Enum
from datetime import datetime
import uuid

try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    from dataclasses import dataclass


class Modality(str, Enum):
    """Tipos de modalidades soportadas."""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    THREE_D = "3d"
    MULTIMODAL = "multimodal"


class GenerationType(str, Enum):
    """Tipos de generación específicos."""
    # Video
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    VIDEO_TO_VIDEO = "video_to_video"
    VIDEO_INPAINTING = "video_inpainting"
    
    # Image
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    IMAGE_UPSCALE = "image_upscale"
    IMAGE_INPAINTING = "image_inpainting"
    
    # Audio
    TEXT_TO_AUDIO = "text_to_audio"
    TEXT_TO_MUSIC = "text_to_music"
    AUDIO_TO_AUDIO = "audio_to_audio"
    VOICE_CLONING = "voice_cloning"
    
    # 3D
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    
    # Multimodal
    MULTIMODAL_CONTENT = "multimodal_content"


class TaskStatus(str, Enum):
    """Estados de una tarea de generación."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


if PYDANTIC_AVAILABLE:
    class GenerationRequest(BaseModel):
        """Request para generación multimodal."""
        
        modality: Modality = Field(
            ...,
            description="Modalidad de generación (video, image, audio, 3d, multimodal)"
        )
        
        generation_type: Optional[GenerationType] = Field(
            None,
            description="Tipo específico de generación"
        )
        
        prompt: str = Field(
            ...,
            min_length=1,
            max_length=5000,
            description="Descripción del contenido a generar"
        )
        
        parameters: Dict[str, Any] = Field(
            default_factory=dict,
            description="Parámetros específicos de generación"
        )
        
        priority: int = Field(
            default=5,
            ge=1,
            le=10,
            description="Prioridad de la tarea (1=alta, 10=baja)"
        )
        
        callback_url: Optional[str] = Field(
            None,
            description="URL para callback cuando la generación termine"
        )
        
        @field_validator('prompt')
        @classmethod
        def validate_prompt(cls, v: str) -> str:
            """Valida el prompt."""
            if not v or not v.strip():
                raise ValueError("El prompt no puede estar vacío")
            return v.strip()
        
        def to_dict(self) -> Dict[str, Any]:
            """Convierte a diccionario."""
            return self.model_dump(exclude_none=True)
    
    class GenerationResponse(BaseModel):
        """Response de generación."""
        
        task_id: str = Field(
            ...,
            description="ID único de la tarea"
        )
        
        status: TaskStatus = Field(
            ...,
            description="Estado actual de la tarea"
        )
        
        created_at: datetime = Field(
            default_factory=datetime.now,
            description="Fecha de creación"
        )
        
        result: Optional[Dict[str, Any]] = Field(
            None,
            description="Resultado de la generación (si está completa)"
        )
        
        error: Optional[str] = Field(
            None,
            description="Mensaje de error (si falló)"
        )
        
        progress: Optional[float] = Field(
            None,
            ge=0.0,
            le=100.0,
            description="Progreso de la generación (0-100)"
        )
        
        estimated_completion: Optional[datetime] = Field(
            None,
            description="Tiempo estimado de finalización"
        )
        
        metadata: Dict[str, Any] = Field(
            default_factory=dict,
            description="Metadatos adicionales"
        )
    
    class TaskStatusResponse(BaseModel):
        """Response para consultar estado de tarea."""
        
        task_id: str
        status: TaskStatus
        progress: Optional[float] = None
        result: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
        created_at: datetime
        updated_at: datetime
    
    class HealthResponse(BaseModel):
        """Response de health check."""
        
        status: str = "healthy"
        version: str
        uptime_seconds: float
        active_tasks: int
        queue_size: int
        cache_stats: Dict[str, Any]
        rate_limit_stats: Dict[str, Any]
    
    class BatchGenerationRequest(BaseModel):
        """Request para generación en batch."""
        
        requests: List[GenerationRequest] = Field(
            ...,
            min_length=1,
            max_length=100,
            description="Lista de requests de generación"
        )
        
        batch_id: Optional[str] = Field(
            None,
            description="ID opcional para el batch"
        )
        
        @field_validator('requests')
        @classmethod
        def validate_requests(cls, v: List[GenerationRequest]) -> List[GenerationRequest]:
            """Valida la lista de requests."""
            if not v:
                raise ValueError("Debe haber al menos un request")
            return v
    
    class BatchGenerationResponse(BaseModel):
        """Response de generación en batch."""
        
        batch_id: str
        task_ids: List[str]
        total_tasks: int
        created_at: datetime

else:
    # Fallback sin Pydantic
    from dataclasses import dataclass
    
    @dataclass
    class GenerationRequest:
        modality: str
        prompt: str
        parameters: Dict[str, Any] = None
        priority: int = 5
        callback_url: Optional[str] = None
    
    @dataclass
    class GenerationResponse:
        task_id: str
        status: str
        result: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
        progress: Optional[float] = None


