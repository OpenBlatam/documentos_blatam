"""
Factories for building integrated pipelines with the concrete modules provided
by the repository (memory, redundancy, chat, Sora, etc.).
"""

from __future__ import annotations

from typing import Optional

from core.config_manager import PipelineConfig
from core.utils import setup_logger
from integration_pipeline import IntegratedPipeline, create_integrated_pipeline

logger = setup_logger(__name__)


def build_integrated_pipeline(configuration: PipelineConfig) -> Optional[IntegratedPipeline]:
    """
    Create an `IntegratedPipeline` instance from a `PipelineConfig`.

    The provider ensures that the application layer does not need to import
    concrete implementations directly; it simply consumes the resulting object
    through the `PipelineService`.
    """

    kwargs = {
        "enable_memory": configuration.enable_memory,
        "enable_redundancy": configuration.enable_redundancy,
        "enable_video": configuration.enable_video,
        "enable_chat": configuration.enable_chat,
        "use_config_manager": False,  # Configs already resolved upstream.
    }

    if configuration.memory_config is not None:
        kwargs["memory_config"] = configuration.memory_config
    if configuration.redundancy_config is not None:
        kwargs["redundancy_config"] = configuration.redundancy_config
    if configuration.sora_config is not None:
        kwargs["video_config"] = configuration.sora_config
    if configuration.chat_config is not None:
        kwargs["chat_config"] = configuration.chat_config

    pipeline = create_integrated_pipeline(**kwargs)

    if pipeline is None:
        logger.error("Failed to build IntegratedPipeline with config %s", configuration)

    return pipeline


