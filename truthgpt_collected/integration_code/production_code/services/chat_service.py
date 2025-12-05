#!/usr/bin/env python3
"""
Chat Service
============

Business logic for chat operations.
"""

from typing import Dict, Optional, Any, TYPE_CHECKING
from core.utils import setup_logger
from core.error_handling import safe_execute

if TYPE_CHECKING:
    from integration_pipeline import IntegratedPipeline

logger = setup_logger(__name__)


class ChatService:
    """Service for chat operations."""
    
    def __init__(self, pipeline: "IntegratedPipeline") -> None:
        """
        Initialize chat service.
        
        Args:
            pipeline: IntegratedPipeline instance with chat module
        
        Raises:
            ValueError: If pipeline is None
        """
        if pipeline is None:
            raise ValueError("Pipeline cannot be None")
        self.pipeline = pipeline
    
    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat message.
        
        Args:
            message: User message
            conversation_id: Optional conversation ID
        
        Returns:
            Dictionary with response and metadata
        
        Raises:
            ValueError: If chat module is unavailable, message is empty, or message is too long
            RuntimeError: If processing fails
        """
        if not self.is_available():
            raise ValueError("Chat module not available")
        
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        if len(message) > 10000:
            raise ValueError("Message too long (max 10000 characters)")
        
        return safe_execute(
            lambda: self.pipeline.chat_with_memory(
                message,
                conversation_id=conversation_id
            ),
            error_message="Error processing chat"
        )
    
    def is_available(self) -> bool:
        """Check if chat module is available."""
        return (
            self.pipeline is not None
            and self.pipeline.enable_chat
            and self.pipeline.chat_engine is not None
        )


