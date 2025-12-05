#!/usr/bin/env python3
"""
Sistema de Notificaciones para la API Multimodal.

Sistema completo de notificaciones con múltiples canales.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Canales de notificación."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


@dataclass
class Notification:
    """Notificación."""
    id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    timestamp: datetime
    sent: bool = False
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NotificationManager:
    """Gestor de notificaciones."""
    
    def __init__(self):
        """Inicializa el gestor de notificaciones."""
        self.notifications: Dict[str, Notification] = {}
        self.handlers: Dict[NotificationChannel, callable] = {}
        self.queue: List[Notification] = []
        self.running = False
    
    def register_handler(self, channel: NotificationChannel, handler: callable):
        """
        Registra un handler para un canal.
        
        Args:
            channel: Canal de notificación
            handler: Función handler
        """
        self.handlers[channel] = handler
        logger.info(f"Handler registrado para canal: {channel.value}")
    
    async def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Envía una notificación.
        
        Args:
            channel: Canal de notificación
            recipient: Destinatario
            subject: Asunto
            message: Mensaje
            metadata: Metadatos adicionales
        
        Returns:
            ID de notificación
        """
        notification_id = f"notif_{datetime.now().timestamp()}"
        
        notification = Notification(
            id=notification_id,
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.notifications[notification_id] = notification
        
        # Enviar de forma asíncrona
        if channel in self.handlers:
            try:
                handler = self.handlers[channel]
                if asyncio.iscoroutinefunction(handler):
                    await handler(notification)
                else:
                    handler(notification)
                
                notification.sent = True
                notification.sent_at = datetime.now()
                logger.info(f"Notificación enviada: {notification_id}")
            except Exception as e:
                notification.error = str(e)
                logger.error(f"Error enviando notificación {notification_id}: {e}")
        else:
            # Agregar a cola si no hay handler
            self.queue.append(notification)
            logger.warning(f"No hay handler para canal {channel.value}, agregado a cola")
        
        return notification_id
    
    async def send_task_notification(
        self,
        task_id: str,
        status: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Envía notificación sobre una tarea.
        
        Args:
            task_id: ID de tarea
            status: Estado
            recipient: Destinatario
            metadata: Metadatos adicionales
        """
        subject = f"Tarea {task_id} - {status}"
        message = f"La tarea {task_id} ha cambiado a estado: {status}"
        
        if metadata:
            message += f"\n\nDetalles: {metadata}"
        
        # Determinar canal (por defecto webhook)
        channel = NotificationChannel.WEBHOOK
        
        await self.send_notification(
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            metadata={"task_id": task_id, "status": status, **(metadata or {})}
        )
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """
        Obtiene una notificación.
        
        Args:
            notification_id: ID de notificación
        
        Returns:
            Notificación o None
        """
        return self.notifications.get(notification_id)
    
    def get_notifications(
        self,
        channel: Optional[NotificationChannel] = None,
        sent: Optional[bool] = None
    ) -> List[Notification]:
        """
        Obtiene notificaciones con filtros.
        
        Args:
            channel: Filtrar por canal
            sent: Filtrar por estado de envío
        
        Returns:
            Lista de notificaciones
        """
        notifications = list(self.notifications.values())
        
        if channel:
            notifications = [n for n in notifications if n.channel == channel]
        
        if sent is not None:
            notifications = [n for n in notifications if n.sent == sent]
        
        return notifications
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de notificaciones.
        
        Returns:
            Estadísticas
        """
        total = len(self.notifications)
        sent = sum(1 for n in self.notifications.values() if n.sent)
        failed = sum(1 for n in self.notifications.values() if n.error)
        
        by_channel = {}
        for notification in self.notifications.values():
            channel = notification.channel.value
            by_channel[channel] = by_channel.get(channel, 0) + 1
        
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "pending": total - sent - failed,
            "by_channel": by_channel,
            "queue_size": len(self.queue)
        }


