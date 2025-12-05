#!/usr/bin/env python3
"""
Sistema de Streaming para Resultados de Generación.

Permite streaming de resultados parciales durante la generación.
"""

from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
import json
import asyncio

try:
    from fastapi import Response
    from fastapi.responses import StreamingResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class StreamingManager:
    """Gestor de streaming de resultados."""
    
    def __init__(self):
        """Inicializa el gestor de streaming."""
        self.active_streams: Dict[str, Dict[str, Any]] = {}
    
    def create_stream(self, task_id: str) -> AsyncIterator[str]:
        """
        Crea un stream para una tarea.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            AsyncIterator de eventos
        """
        async def stream_generator():
            """Generador de eventos de stream."""
            try:
                # Enviar evento inicial
                yield self._format_event("stream_started", {
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Simular progreso (en producción, esto vendría del generador)
                # Por ahora, solo placeholder
                while task_id in self.active_streams:
                    await asyncio.sleep(1)
                    # En producción, verificar progreso real
                    yield self._format_event("progress", {
                        "task_id": task_id,
                        "progress": 0.0
                    })
            
            except Exception as e:
                yield self._format_event("error", {
                    "task_id": task_id,
                    "error": str(e)
                })
            finally:
                self.active_streams.pop(task_id, None)
        
        self.active_streams[task_id] = {
            "created_at": datetime.now(),
            "status": "active"
        }
        
        return stream_generator()
    
    def _format_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Formatea un evento para streaming.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        
        Returns:
            String formateado (SSE format)
        """
        event_data = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        return f"data: {json.dumps(event_data)}\n\n"
    
    def close_stream(self, task_id: str):
        """
        Cierra un stream.
        
        Args:
            task_id: ID de la tarea
        """
        if task_id in self.active_streams:
            del self.active_streams[task_id]
            logger.info(f"Stream cerrado: {task_id}")
    
    def get_active_streams(self) -> List[str]:
        """
        Obtiene lista de streams activos.
        
        Returns:
            Lista de task IDs
        """
        return list(self.active_streams.keys())


def create_streaming_response(task_id: str) -> StreamingResponse:
    """
    Crea una respuesta de streaming para una tarea.
    
    Args:
        task_id: ID de la tarea
    
    Returns:
        StreamingResponse
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI no está disponible")
    
    from .streaming import StreamingManager
    
    manager = StreamingManager()
    stream = manager.create_stream(task_id)
    
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

