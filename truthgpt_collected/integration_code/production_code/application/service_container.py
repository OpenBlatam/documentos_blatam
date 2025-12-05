"""
Centralized service container for the application layer.

Presentation adapters (FastAPI, CLI, tests) use this container to resolve
services via dependency injection without importing infrastructure details.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from core.config_manager import (
    ChatConfig,
    ConfigManager,
    MemoryConfig,
    ModuleType,
    PipelineConfig,
    RedundancyConfig,
    SoraConfig,
    get_config_manager,
)
from core.utils import setup_logger
from infrastructure.providers import (
    build_integrated_pipeline,
    build_system_monitor,
)
from services import (
    ChatService,
    ConfigService,
    MemoryService,
    MonitoringService,
    PipelineService,
    RedundancyService,
)

logger = setup_logger(__name__)

T = TypeVar("T")
Factory = Callable[[], Any]


@dataclass(frozen=True)
class PresentationConfig:
    enable_dashboard: bool = True
    enable_docs: bool = True
    allowed_origins: tuple[str, ...] = ("*",)
    rate_limiting_enabled: bool = True


@dataclass(frozen=True)
class ApplicationConfig:
    pipeline: PipelineConfig
    safe_execute_attempts: int = 3
    quotas_per_minute: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class DomainConfig:
    memory: MemoryConfig
    redundancy: RedundancyConfig
    chat: ChatConfig
    sora: SoraConfig


@dataclass(frozen=True)
class InfrastructureConfig:
    monitoring_enabled: bool = True
    persistence_path: Optional[str] = None


@dataclass(frozen=True)
class LayeredConfig:
    presentation: PresentationConfig
    application: ApplicationConfig
    domain: DomainConfig
    infrastructure: InfrastructureConfig


class ServiceContainer:
    """
    Simple DI container that wires configuration, providers and services.
    """

    def __init__(
        self,
        *,
        config_path: Optional[Union[str, Path]] = None,
        presentation_overrides: Optional[Dict[str, Any]] = None,
        monitoring_enabled: Optional[bool] = None,
    ) -> None:
        self._lock = RLock()
        self.config_manager = get_config_manager(config_path)
        self._layered_config: Optional[LayeredConfig] = None
        self._presentation_overrides = presentation_overrides or {}
        self._monitoring_override = monitoring_enabled
        self._instances: Dict[str, Any] = {"config_manager": self.config_manager}
        self._errors: Dict[str, str] = {}

    # ------------------------------------------------------------------ #
    # Lifecycle helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_env(
        cls,
        *,
        config_path: Optional[Union[str, Path]] = None,
        presentation_overrides: Optional[Dict[str, Any]] = None,
        monitoring_enabled: Optional[bool] = None,
    ) -> "ServiceContainer":
        return cls(
            config_path=config_path,
            presentation_overrides=presentation_overrides,
            monitoring_enabled=monitoring_enabled,
        )

    async def startup(self) -> None:
        """Warm-up critical services without blocking the event loop."""

        await asyncio.to_thread(self._warmup_resources)

    async def shutdown(self) -> None:
        """Gracefully tear down long-lived resources."""

        pipeline = self._instances.get("pipeline")
        if pipeline and hasattr(pipeline, "shutdown"):
            await asyncio.to_thread(pipeline.shutdown)

    def _warmup_resources(self) -> None:
        self.get_layered_config()
        try:
            self.get_pipeline()
        except Exception as exc:  # pragma: no cover - warm-up logging
            logger.warning("Pipeline warm-up failed: %s", exc)

    # ------------------------------------------------------------------ #
    # Layered configuration
    # ------------------------------------------------------------------ #
    def get_layered_config(self) -> LayeredConfig:
        if self._layered_config is None:
            with self._lock:
                if self._layered_config is None:
                    self._layered_config = self._build_layered_config()
        return self._layered_config

    def _build_layered_config(self) -> LayeredConfig:
        memory_cfg = self._coerce_dataclass(ModuleType.MEMORY, MemoryConfig)
        redundancy_cfg = self._coerce_dataclass(ModuleType.REDUNDANCY, RedundancyConfig)
        chat_cfg = self._coerce_dataclass(ModuleType.CHAT, ChatConfig)
        sora_cfg = self._coerce_dataclass(ModuleType.SORA, SoraConfig)
        pipeline_cfg = self._coerce_dataclass(ModuleType.PIPELINE, PipelineConfig)

        presentation_cfg = replace(
            PresentationConfig(),
            **self._presentation_overrides,
        )

        infrastructure_cfg = InfrastructureConfig(
            monitoring_enabled=self._monitoring_override
            if self._monitoring_override is not None
            else True,
            persistence_path=memory_cfg.persistence_path,
        )

        application_cfg = ApplicationConfig(pipeline=pipeline_cfg)
        domain_cfg = DomainConfig(
            memory=memory_cfg,
            redundancy=redundancy_cfg,
            chat=chat_cfg,
            sora=sora_cfg,
        )

        return LayeredConfig(
            presentation=presentation_cfg,
            application=application_cfg,
            domain=domain_cfg,
            infrastructure=infrastructure_cfg,
        )

    def _coerce_dataclass(self, module_type: ModuleType, cls: Type[T]) -> T:
        """Convert dictionary configs to their dataclass counterpart."""

        raw = self.config_manager.get_config(module_type)
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, dict):
            return cls(**raw)
        if hasattr(raw, "__dict__"):
            return cls(**raw.__dict__)  # type: ignore[arg-type]
        return cls()

    # ------------------------------------------------------------------ #
    # Service resolution helpers
    # ------------------------------------------------------------------ #
    def get_pipeline(self):
        return self._get_or_create("pipeline", self._build_pipeline)

    def get_pipeline_service(self) -> PipelineService:
        return self._get_or_create(
            "pipeline_service", lambda: PipelineService(self.get_pipeline())
        )

    def get_memory_service(self) -> MemoryService:
        return self._get_or_create(
            "memory_service", lambda: MemoryService(self.get_pipeline())
        )

    def get_redundancy_service(self) -> RedundancyService:
        return self._get_or_create(
            "redundancy_service", lambda: RedundancyService(self.get_pipeline())
        )

    def get_chat_service(self) -> ChatService:
        return self._get_or_create(
            "chat_service", lambda: ChatService(self.get_pipeline())
        )

    def get_config_service(self) -> ConfigService:
        return self._get_or_create(
            "config_service", lambda: ConfigService(self.config_manager)
        )

    def get_monitoring_service(self) -> Optional[MonitoringService]:
        layered = self.get_layered_config()
        if not layered.infrastructure.monitoring_enabled:
            return None

        monitor = self._get_or_create("monitor", build_system_monitor)
        if monitor is None:
            return None

        return self._get_or_create(
            "monitoring_service", lambda: MonitoringService(monitor)
        )

    # ------------------------------------------------------------------ #
    # Diagnostics
    # ------------------------------------------------------------------ #
    def describe_resources(self) -> Dict[str, Dict[str, Any]]:
        resources = {
            "pipeline": self._resource_snapshot("pipeline"),
            "config_manager": self._resource_snapshot("config_manager"),
        }
        if self.get_layered_config().infrastructure.monitoring_enabled:
            resources["monitor"] = self._resource_snapshot("monitor")
        return resources

    def _resource_snapshot(self, key: str) -> Dict[str, Any]:
        return {
            "initialized": key in self._instances and self._instances[key] is not None,
            "error": self._errors.get(key),
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _get_or_create(self, key: str, factory: Factory):
        if key in self._instances:
            return self._instances[key]

        with self._lock:
            if key in self._instances:
                return self._instances[key]

            try:
                instance = factory()
            except Exception as exc:
                self._errors[key] = str(exc)
                raise
            else:
                self._instances[key] = instance
                self._errors.pop(key, None)
                return instance

    def _build_pipeline(self):
        pipeline_config = self.get_layered_config().application.pipeline
        pipeline = build_integrated_pipeline(pipeline_config)

        if pipeline is None:
            raise RuntimeError("Integrated pipeline could not be created")

        return pipeline


