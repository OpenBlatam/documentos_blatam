#!/usr/bin/env python3
"""
Sistema de Webhooks para la API Multimodal.

Maneja envío de webhooks cuando las tareas cambian de estado.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
import aiohttp
import hashlib
import hmac
import json

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Eventos de webhook."""
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"


@dataclass
class Webhook:
    """Configuración de webhook."""
    url: str
    secret: Optional[str] = None
    events: List[WebhookEvent] = None
    timeout: int = 10
    retry_attempts: int = 3
    enabled: bool = True
    
    def __post_init__(self):
        if self.events is None:
            self.events = list(WebhookEvent)


class WebhookManager:
    """Gestor de webhooks."""
    
    def __init__(self):
        """Inicializa el gestor de webhooks."""
        self.webhooks: Dict[str, Webhook] = {}
        self.delivery_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def register_webhook(
        self,
        webhook_id: str,
        url: str,
        secret: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        timeout: int = 10
    ) -> str:
        """
        Registra un nuevo webhook.
        
        Args:
            webhook_id: ID único del webhook
            url: URL de destino
            secret: Secreto para firma (opcional)
            events: Eventos a escuchar (opcional)
            timeout: Timeout en segundos
        
        Returns:
            ID del webhook
        """
        webhook = Webhook(
            url=url,
            secret=secret,
            events=events or list(WebhookEvent),
            timeout=timeout
        )
        
        self.webhooks[webhook_id] = webhook
        self.delivery_history[webhook_id] = []
        
        logger.info(f"Webhook registrado: {webhook_id} -> {url}")
        return webhook_id
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Elimina un webhook.
        
        Args:
            webhook_id: ID del webhook
        
        Returns:
            True si se eliminó correctamente
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self.delivery_history.pop(webhook_id, None)
            logger.info(f"Webhook eliminado: {webhook_id}")
            return True
        return False
    
    async def send_webhook(
        self,
        event: WebhookEvent,
        task_id: str,
        data: Dict[str, Any],
        webhook_id: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Envía un webhook.
        
        Args:
            event: Tipo de evento
            task_id: ID de la tarea
            data: Datos del evento
            webhook_id: ID específico de webhook (opcional)
        
        Returns:
            Resultado del envío por webhook
        """
        results = {}
        
        # Filtrar webhooks que escuchan este evento
        webhooks_to_notify = []
        if webhook_id:
            if webhook_id in self.webhooks:
                webhook = self.webhooks[webhook_id]
                if event in webhook.events and webhook.enabled:
                    webhooks_to_notify.append((webhook_id, webhook))
        else:
            for wid, webhook in self.webhooks.items():
                if event in webhook.events and webhook.enabled:
                    webhooks_to_notify.append((wid, webhook))
        
        # Enviar a cada webhook
        for wid, webhook in webhooks_to_notify:
            success = await self._deliver_webhook(wid, webhook, event, task_id, data)
            results[wid] = success
        
        return results
    
    async def _deliver_webhook(
        self,
        webhook_id: str,
        webhook: Webhook,
        event: WebhookEvent,
        task_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Entrega un webhook específico.
        
        Args:
            webhook_id: ID del webhook
            webhook: Configuración del webhook
            event: Evento
            task_id: ID de la tarea
            data: Datos
        
        Returns:
            True si se entregó correctamente
        """
        payload = {
            "event": event.value,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Firmar payload si hay secreto
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            signature = self._sign_payload(payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature
        
        # Intentar entregar con reintentos
        for attempt in range(webhook.retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=webhook.timeout)
                    ) as response:
                        success = response.status in (200, 201, 202, 204)
                        
                        # Registrar en historial
                        self.delivery_history[webhook_id].append({
                            "event": event.value,
                            "task_id": task_id,
                            "attempt": attempt + 1,
                            "success": success,
                            "status_code": response.status,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        if success:
                            logger.info(
                                f"Webhook entregado: {webhook_id} "
                                f"(evento: {event.value}, tarea: {task_id})"
                            )
                            return True
                        else:
                            logger.warning(
                                f"Webhook falló: {webhook_id} "
                                f"(status: {response.status})"
                            )
            
            except asyncio.TimeoutError:
                logger.warning(
                    f"Webhook timeout: {webhook_id} (intento {attempt + 1})"
                )
            except Exception as e:
                logger.error(f"Error entregando webhook {webhook_id}: {e}")
            
            # Esperar antes de reintentar
            if attempt < webhook.retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
        
        return False
    
    def _sign_payload(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Firma un payload con HMAC.
        
        Args:
            payload: Payload a firmar
            secret: Secreto
        
        Returns:
            Firma hexadecimal
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """
        Verifica la firma de un webhook recibido.
        
        Args:
            payload: Payload recibido
            signature: Firma recibida
            secret: Secreto
        
        Returns:
            True si la firma es válida
        """
        expected_signature = self._sign_payload(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    def get_webhook_stats(self, webhook_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de webhooks.
        
        Args:
            webhook_id: ID específico (opcional)
        
        Returns:
            Estadísticas
        """
        if webhook_id:
            history = self.delivery_history.get(webhook_id, [])
            total = len(history)
            successful = sum(1 for h in history if h["success"])
            
            return {
                "webhook_id": webhook_id,
                "total_deliveries": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": (successful / total * 100) if total > 0 else 0.0
            }
        
        # Estadísticas globales
        all_history = []
        for history in self.delivery_history.values():
            all_history.extend(history)
        
        total = len(all_history)
        successful = sum(1 for h in all_history if h["success"])
        
        return {
            "total_webhooks": len(self.webhooks),
            "total_deliveries": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0.0
        }


