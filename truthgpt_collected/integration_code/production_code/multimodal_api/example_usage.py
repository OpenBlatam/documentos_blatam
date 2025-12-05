#!/usr/bin/env python3
"""
Ejemplo de uso de la API de Generación Multimodal.

Muestra cómo usar la API para diferentes tipos de generación.
"""

import asyncio
import requests
from typing import Dict, Any

# URL base de la API (ajustar según configuración)
API_BASE_URL = "http://localhost:8000/api/v1"


def generate_video(prompt: str, duration: int = 5) -> Dict[str, Any]:
    """
    Genera un video desde texto.
    
    Args:
        prompt: Descripción del video
        duration: Duración en segundos
    
    Returns:
        Respuesta de la API
    """
    response = requests.post(
        f"{API_BASE_URL}/generate",
        json={
            "modality": "video",
            "generation_type": "text_to_video",
            "prompt": prompt,
            "parameters": {
                "duration": duration,
                "resolution": "512x512",
                "fps": 24,
                "style": "realistic"
            },
            "priority": 5
        }
    )
    response.raise_for_status()
    return response.json()


def generate_image(prompt: str, style: str = "realistic") -> Dict[str, Any]:
    """
    Genera una imagen desde texto.
    
    Args:
        prompt: Descripción de la imagen
        style: Estilo de la imagen
    
    Returns:
        Respuesta de la API
    """
    response = requests.post(
        f"{API_BASE_URL}/generate",
        json={
            "modality": "image",
            "generation_type": "text_to_image",
            "prompt": prompt,
            "parameters": {
                "resolution": "1024x1024",
                "style": style,
                "quality": "high"
            }
        }
    )
    response.raise_for_status()
    return response.json()


def generate_audio(prompt: str, audio_type: str = "music") -> Dict[str, Any]:
    """
    Genera audio desde texto.
    
    Args:
        prompt: Descripción del audio
        audio_type: Tipo de audio (music, speech, sound_effect)
    
    Returns:
        Respuesta de la API
    """
    response = requests.post(
        f"{API_BASE_URL}/generate",
        json={
            "modality": "audio",
            "generation_type": "text_to_music" if audio_type == "music" else "text_to_audio",
            "prompt": prompt,
            "parameters": {
                "duration": 30,
                "style": "ambient",
                "tempo": "medium"
            }
        }
    )
    response.raise_for_status()
    return response.json()


def check_task_status(task_id: str) -> Dict[str, Any]:
    """
    Verifica el estado de una tarea.
    
    Args:
        task_id: ID de la tarea
    
    Returns:
        Estado de la tarea
    """
    response = requests.get(f"{API_BASE_URL}/task/{task_id}")
    response.raise_for_status()
    return response.json()


def generate_batch(requests_list: list) -> Dict[str, Any]:
    """
    Genera múltiples contenidos en batch.
    
    Args:
        requests_list: Lista de requests de generación
    
    Returns:
        Respuesta del batch
    """
    response = requests.post(
        f"{API_BASE_URL}/generate/batch",
        json={
            "requests": requests_list
        }
    )
    response.raise_for_status()
    return response.json()


def main():
    """Ejemplo de uso completo."""
    print("=== Ejemplo de uso de la API Multimodal ===\n")
    
    # Ejemplo 1: Generar video
    print("1. Generando video...")
    video_task = generate_video(
        "A beautiful sunset over the ocean with waves crashing on the shore",
        duration=10
    )
    print(f"   Tarea creada: {video_task['task_id']}")
    print(f"   Estado: {video_task['status']}\n")
    
    # Ejemplo 2: Generar imagen
    print("2. Generando imagen...")
    image_task = generate_image(
        "A futuristic cityscape at night with neon lights",
        style="cyberpunk"
    )
    print(f"   Tarea creada: {image_task['task_id']}")
    print(f"   Estado: {image_task['status']}\n")
    
    # Ejemplo 3: Generar audio
    print("3. Generando audio...")
    audio_task = generate_audio(
        "Peaceful ambient music for meditation",
        audio_type="music"
    )
    print(f"   Tarea creada: {audio_task['task_id']}")
    print(f"   Estado: {audio_task['status']}\n")
    
    # Ejemplo 4: Verificar estado
    print("4. Verificando estado de tarea...")
    status = check_task_status(video_task['task_id'])
    print(f"   Estado: {status['status']}")
    print(f"   Progreso: {status.get('progress', 0)}%\n")
    
    # Ejemplo 5: Generación en batch
    print("5. Generando batch...")
    batch_requests = [
        {
            "modality": "image",
            "prompt": "A cat playing with a ball",
            "parameters": {"resolution": "512x512"}
        },
        {
            "modality": "image",
            "prompt": "A dog running in a park",
            "parameters": {"resolution": "512x512"}
        }
    ]
    batch_result = generate_batch(batch_requests)
    print(f"   Batch ID: {batch_result['batch_id']}")
    print(f"   Total tareas: {batch_result['total_tasks']}\n")
    
    print("=== Ejemplos completados ===")


if __name__ == "__main__":
    main()


