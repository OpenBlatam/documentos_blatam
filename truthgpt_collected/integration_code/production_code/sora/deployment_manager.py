#!/usr/bin/env python3
"""
Deployment Manager - Orquestador de despliegues Sora
=====================================================

Gestiona la creación de generadores, monitoreo, webhooks y
configuración de producción para despliegues listos para producción.
"""

from typing import Optional, Dict, Any, Callable
from pathlib import Path
import time

try:
    from core.error_handling import safe_execute
except ImportError:
    safe_execute = None

from core.utils import setup_logger

from .sora_base import VideoGenerationConfig
from .text_to_video import TextToVideoConfig, TextToVideoModule
from .sora_integration import (
    create_sora_with_memory,
    create_sora_with_redundancy,
    create_sora_integrated,
    create_sora_with_best_techniques
)
from . import (
    SoraMonitor,
    WebhookManager,
    WebhookEvent,
    ProductionConfig,
    create_production_environment,
    create_video_generator
)

logger = setup_logger(__name__)


class SoraDeploymentManager:
    """
    Administra despliegues de Sora listos para producción.

    Características:
    - Configuración centralizada de producción
    - Selección de variantes (base, memoria, redundancia, integrada, best techniques)
    - Monitoreo automático de métricas
    - Webhooks para eventos clave
    - Logging estructurado de eventos
    """

    def __init__(
        self,
        generator_type: str = "text_to_video",
        variant: str = "base",
        production_config: Optional[ProductionConfig] = None,
        video_config_kwargs: Optional[Dict[str, Any]] = None,
        webhook_urls: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el deployment manager.

        Args:
            generator_type: Tipo de generador (text_to_video, image_to_video, video_to_video, base)
            variant: Variante (base, memory, redundancy, integrated, best)
            production_config: Configuración de producción
            video_config_kwargs: Configuración del modelo de video
            webhook_urls: Diccionario {webhook_id: {"url": str, "events": [WebhookEvent]}}
        """
        self.generator_type = generator_type
        self.variant = variant
        self.video_config_kwargs = video_config_kwargs or {}

        if production_config is None:
            production_config = ProductionConfig()
        self.production_config = production_config
        self.production_env = create_production_environment(self.production_config)

        self.monitor = SoraMonitor() if SoraMonitor else None
        self.webhook_manager = WebhookManager() if WebhookManager else None
        self._register_default_webhooks(webhook_urls or {})

        self.generator = self._create_generator()

    def _register_default_webhooks(self, webhook_configs: Dict[str, Any]):
        if not self.webhook_manager or not WebhookEvent:
            return
        for webhook_id, cfg in webhook_configs.items():
            try:
                events = cfg.get("events", [WebhookEvent.VIDEO_GENERATED])
                self.webhook_manager.register(
                    webhook_id,
                    cfg.get("webhook_obj") or type("AutoWebhook", (), {})()  # placeholder
                )
            except Exception as e:
                logger.warning(f"No se pudo registrar webhook {webhook_id}: {e}")

    def _create_generator(self):
        """
        Crea el generador según la variante indicada.
        """
        if self.variant == "memory":
            config = TextToVideoConfig(**self.video_config_kwargs)
            return create_sora_with_memory(config)
        if self.variant == "redundancy":
            config = TextToVideoConfig(**self.video_config_kwargs)
            return create_sora_with_redundancy(config)
        if self.variant == "integrated":
            config = TextToVideoConfig(**self.video_config_kwargs)
            return create_sora_integrated(config)
        if self.variant == "best":
            config = TextToVideoConfig(**self.video_config_kwargs)
            return create_sora_with_best_techniques(config)

        # Variante base usando factory estándar
        generator = create_video_generator(
            generator_type=self.generator_type,
            **self.video_config_kwargs
        )
        if generator is None:
            raise ValueError("No se pudo crear el generador base")
        return generator

    def _safe_call(self, func: Callable, default=None):
        if safe_execute:
            result, error = safe_execute(func, default_value=default, log_errors=True)
            return result, error
        try:
            return func(), None
        except Exception as e:
            logger.error(f"Error en SoraDeploymentManager: {e}", exc_info=True)
            return default, e

    def generate_from_text(
        self,
        prompt: str,
        num_inference_steps: int = 20,
        seed: Optional[int] = None,
        **kwargs
    ):
        """
        Genera video desde texto con monitoreo y logging.
        """
        start_time = time.time()
        metadata = {}

        def _generate():
            if hasattr(self.generator, "generate_from_text"):
                return self.generator.generate_from_text(
                    prompt,
                    num_inference_steps=num_inference_steps,
                    seed=seed,
                    **kwargs
                )
            raise AttributeError("El generador no soporta generate_from_text")

        result, error = self._safe_call(_generate, default=(None, {}))
        video, metadata = result if error is None else (None, {})

        duration = time.time() - start_time
        self._log_generation(prompt, duration, metadata, error)
        self._record_metrics(duration, metadata, error)
        self._notify_webhooks(prompt, metadata, error)

        return video, metadata

    def _log_generation(self, prompt, duration, metadata, error):
        prod_logger = self.production_env.get('logger')
        if not prod_logger:
            return
        event_type = "video_generation"
        event_metadata = {
            'prompt_preview': prompt[:60],
            'duration': duration,
            'metadata': metadata,
            'variant': self.variant,
            'generator_type': self.generator_type,
            'error': str(error) if error else None
        }
        level = "ERROR" if error else "INFO"
        prod_logger.log_event(event_type, "Video generado", event_metadata, level=level)

    def _record_metrics(self, duration, metadata, error):
        if not self.monitor:
            return
        metrics = {
            'generation_time': duration,
            'success': 0.0 if error else 1.0,
            'variant': self.variant == "base"
        }
        if metadata.get('quality_score'):
            metrics['quality_score'] = metadata['quality_score']
        self.monitor.record_metrics(metrics)

    def _notify_webhooks(self, prompt, metadata, error):
        if not self.webhook_manager or not WebhookEvent:
            return
        event = WebhookEvent.TASK_FAILED if error else WebhookEvent.VIDEO_GENERATED
        data = {
            'prompt_preview': prompt[:100],
            'metadata': metadata,
            'error': str(error) if error else None,
            'variant': self.variant
        }
        self.webhook_manager.send(event, data)

    def health_check(self):
        """
        Ejecuta health checks del entorno.
        """
        health_checker = self.production_env.get('health_checker')
        if health_checker:
            return health_checker.check_all()
        return {'overall_health': 'unknown', 'checks': {}}

    def get_logs(self, **filters):
        """
        Obtiene logs filtrados.
        """
        prod_logger = self.production_env.get('logger')
        if not prod_logger:
            return []
        return prod_logger.get_logs(**filters)

    def get_monitor_metrics(self, last_n: Optional[int] = None):
        """
        Obtiene métricas del monitor.
        """
        if not self.monitor:
            return []
        return self.monitor.get_metrics(last_n=last_n)



