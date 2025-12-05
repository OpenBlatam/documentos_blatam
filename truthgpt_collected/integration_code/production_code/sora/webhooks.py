#!/usr/bin/env python3
"""
Webhooks - Sistema de Notificaciones
=====================================

Sistema de webhooks para notificar eventos de generación de video.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

from core.utils import setup_logger

logger = setup_logger(__name__)


class WebhookEvent(Enum):
    """Tipos de eventos de webhook."""
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    VIDEO_GENERATED = "video.generated"
    BATCH_COMPLETED = "batch.completed"


@dataclass
class Webhook:
    """Configuración de webhook."""
    url: str
    events: List[WebhookEvent]
    secret: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    enabled: bool = True


class WebhookManager:
    """
    Gestor de webhooks para notificaciones.
    
    Permite registrar webhooks y enviar notificaciones
    cuando ocurren eventos relevantes.
    """
    
    def __init__(self):
        """Inicializa el gestor de webhooks."""
        self.webhooks: Dict[str, Webhook] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea una sesión HTTP."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def register(self, webhook_id: str, webhook: Webhook):
        """
        Registra un webhook.
        
        Args:
            webhook_id: ID único del webhook
            webhook: Configuración del webhook
        """
        self.webhooks[webhook_id] = webhook
        logger.info(f"Webhook registrado: {webhook_id} -> {webhook.url}")
    
    async def unregister(self, webhook_id: str):
        """
        Desregistra un webhook.
        
        Args:
            webhook_id: ID del webhook
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info(f"Webhook desregistrado: {webhook_id}")
    
    async def send(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        webhook_id: Optional[str] = None
    ):
        """
        Envía notificación de evento.
        
        Args:
            event: Tipo de evento
            data: Datos del evento
            webhook_id: ID específico de webhook (opcional)
        """
        webhooks_to_notify = []
        
        if webhook_id:
            if webhook_id in self.webhooks:
                webhooks_to_notify.append(self.webhooks[webhook_id])
        else:
            for webhook in self.webhooks.values():
                if webhook.enabled and event in webhook.events:
                    webhooks_to_notify.append(webhook)
        
        if not webhooks_to_notify:
            return
        
        payload = {
            "event": event.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        tasks = []
        for webhook in webhooks_to_notify:
            task = self._send_to_webhook(webhook, payload)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_webhook(
        self,
        webhook: Webhook,
        payload: Dict[str, Any]
    ):
        """
        Envía payload a un webhook específico.
        
        Args:
            webhook: Configuración del webhook
            payload: Payload a enviar
        """
        session = await self._get_session()
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Sora-Webhook/1.6.0"
        }
        
        if webhook.secret:
            import hmac
            import hashlib
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook.secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Sora-Signature"] = f"sha256={signature}"
        
        for attempt in range(webhook.retry_count):
            try:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=webhook.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook enviado exitosamente: {webhook.url}")
                        return
                    else:
                        logger.warning(
                            f"Webhook retornó status {response.status}: {webhook.url}"
                        )
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout enviando webhook: {webhook.url}")
            except Exception as e:
                logger.error(f"Error enviando webhook: {e}")
            
            if attempt < webhook.retry_count - 1:
                await asyncio.sleep(webhook.retry_delay * (attempt + 1))
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        Lista todos los webhooks registrados.
        
        Returns:
            Lista de webhooks
        """
        return [
            {
                "webhook_id": webhook_id,
                "url": webhook.url,
                "events": [e.value for e in webhook.events],
                "enabled": webhook.enabled
            }
            for webhook_id, webhook in self.webhooks.items()
        ]
    
    async def close(self):
        """Cierra la sesión HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()


