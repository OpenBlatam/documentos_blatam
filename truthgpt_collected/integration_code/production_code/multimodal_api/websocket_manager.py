#!/usr/bin/env python3
"""
WebSocket Manager para Updates en Tiempo Real.

Permite a los clientes recibir actualizaciones en tiempo real sobre el estado
de las tareas de generación.
"""

from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gestor de conexiones WebSocket."""
    
    def __init__(self):
        """Inicializa el gestor de conexiones."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: Optional[str] = None):
        """
        Conecta un cliente WebSocket.
        
        Args:
            websocket: Conexión WebSocket
            task_id: ID de tarea específica (opcional)
        """
        await websocket.accept()
        
        if task_id:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = set()
            self.active_connections[task_id].add(websocket)
        else:
            # Conexión general
            if "general" not in self.active_connections:
                self.active_connections["general"] = set()
            self.active_connections["general"].add(websocket)
        
        self.connection_metadata[websocket] = {
            "task_id": task_id,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        
        logger.info(f"Conexión WebSocket establecida: {task_id or 'general'}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Desconecta un cliente WebSocket.
        
        Args:
            websocket: Conexión WebSocket
        """
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            task_id = metadata.get("task_id") or "general"
            if task_id in self.active_connections:
                self.active_connections[task_id].discard(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
            del self.connection_metadata[websocket]
        
        logger.info(f"Conexión WebSocket cerrada")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Envía un mensaje a una conexión específica.
        
        Args:
            message: Mensaje a enviar
            websocket: Conexión WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error enviando mensaje WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        """
        Envía un mensaje a todos los clientes suscritos a una tarea.
        
        Args:
            task_id: ID de la tarea
            message: Mensaje a enviar
        """
        if task_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error en broadcast: {e}")
                disconnected.add(connection)
        
        # Limpiar conexiones desconectadas
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Envía un mensaje a todas las conexiones.
        
        Args:
            message: Mensaje a enviar
        """
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)
        
        disconnected = set()
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error en broadcast general: {e}")
                disconnected.add(connection)
        
        # Limpiar conexiones desconectadas
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_connection_count(self, task_id: Optional[str] = None) -> int:
        """
        Obtiene el número de conexiones activas.
        
        Args:
            task_id: ID de tarea específica (opcional)
        
        Returns:
            Número de conexiones
        """
        if task_id:
            return len(self.active_connections.get(task_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Instancia global
connection_manager = ConnectionManager()


