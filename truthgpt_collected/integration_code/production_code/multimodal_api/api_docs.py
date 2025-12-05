#!/usr/bin/env python3
"""
Mejoras en la Documentación OpenAPI de la API.

Agrega ejemplos, descripciones detalladas y esquemas mejorados.
"""

from typing import Dict, Any

# Ejemplos de requests para la documentación
GENERATION_REQUEST_EXAMPLES = {
    "video": {
        "summary": "Generar video desde texto",
        "value": {
            "modality": "video",
            "generation_type": "text_to_video",
            "prompt": "A beautiful sunset over the ocean with waves crashing on the shore",
            "parameters": {
                "duration": 10,
                "resolution": "512x512",
                "fps": 24,
                "style": "realistic",
                "diffusion_steps": 50
            },
            "priority": 5
        }
    },
    "image": {
        "summary": "Generar imagen desde texto",
        "value": {
            "modality": "image",
            "generation_type": "text_to_image",
            "prompt": "A futuristic cityscape at night with neon lights",
            "parameters": {
                "resolution": "1024x1024",
                "style": "cyberpunk",
                "quality": "high"
            }
        }
    },
    "audio": {
        "summary": "Generar música desde texto",
        "value": {
            "modality": "audio",
            "generation_type": "text_to_music",
            "prompt": "Peaceful ambient music for meditation",
            "parameters": {
                "duration": 60,
                "genre": "ambient",
                "tempo": "slow"
            }
        }
    }
}

RESPONSE_EXAMPLES = {
    "task_created": {
        "summary": "Tarea creada exitosamente",
        "value": {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "pending",
            "created_at": "2024-01-15T10:30:00",
            "progress": 0.0,
            "result": None,
            "error": None
        }
    },
    "task_processing": {
        "summary": "Tarea en procesamiento",
        "value": {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "processing",
            "created_at": "2024-01-15T10:30:00",
            "progress": 45.5,
            "result": None,
            "error": None,
            "estimated_completion": "2024-01-15T10:35:00"
        }
    },
    "task_completed": {
        "summary": "Tarea completada",
        "value": {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00",
            "progress": 100.0,
            "result": {
                "url": "https://api.example.com/storage/videos/video.mp4",
                "metadata": {
                    "duration": 10,
                    "resolution": "512x512",
                    "fps": 24
                }
            },
            "error": None
        }
    }
}

# Tags para organización de endpoints
API_TAGS = [
    {
        "name": "generation",
        "description": "Endpoints para generación de contenido multimodal",
        "externalDocs": {
            "description": "Documentación completa",
            "url": "https://docs.example.com/generation"
        }
    },
    {
        "name": "tasks",
        "description": "Gestión de tareas de generación",
    },
    {
        "name": "monitoring",
        "description": "Métricas y monitoreo del sistema",
    },
    {
        "name": "webhooks",
        "description": "Configuración de webhooks",
    }
]

# Descripciones de parámetros comunes
PARAMETER_DESCRIPTIONS = {
    "modality": "Modalidad de generación: video, image, audio, 3d, o multimodal",
    "generation_type": "Tipo específico de generación (opcional, se infiere de modality si no se especifica)",
    "prompt": "Descripción del contenido a generar (1-5000 caracteres)",
    "parameters": "Parámetros específicos de generación según la modalidad",
    "priority": "Prioridad de la tarea (1=alta, 10=baja). Tareas de alta prioridad tienen más límite de rate limiting.",
    "callback_url": "URL opcional para recibir notificaciones cuando la tarea termine",
    "task_id": "ID único de la tarea",
    "status": "Estado de la tarea: pending, processing, completed, failed, cancelled",
    "limit": "Número máximo de resultados a retornar (paginación)",
    "offset": "Número de resultados a saltar (paginación)"
}


