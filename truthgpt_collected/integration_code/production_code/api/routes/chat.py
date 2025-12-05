#!/usr/bin/env python3
"""
Chat Routes
===========

API routes for chat operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional

from api.dependencies import get_chat_service
from api.models import ChatResponse
from api.rate_limiting import rate_limit_dependency
from api.auth import verify_api_key_optional
from services import ChatService
from core.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat."""
    message: str = Field(..., description="Mensaje del usuario")
    conversation_id: Optional[str] = Field(None, description="ID de conversación")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    req: Request,
    service: ChatService = Depends(get_chat_service),
    _rate_limit: None = Depends(rate_limit_dependency(limit=50, window_seconds=60, endpoint_name="/chat")),
    _auth: Optional[str] = Depends(lambda r: verify_api_key_optional(r, False))
) -> ChatResponse:
    """
    Process chat message with integrated memory system.
    
    Handles chat requests with optional conversation context. The chat service
    integrates with the memory system to provide context-aware responses.
    Messages are validated for length and content before processing.
    
    Args:
        request: Chat request containing:
            - message: String message from user (required, max 10000 characters)
            - conversation_id: Optional string ID for conversation continuity
        req: FastAPI request object for accessing request state
        service: ChatService instance injected via dependency injection
        _rate_limit: Rate limiting dependency (50 requests per 60 seconds)
        _auth: Optional API key for authentication (if enabled)
    
    Returns:
        ChatResponse containing:
            - response: String response from chat service
            - conversation_id: String ID for conversation tracking
            - metadata: Optional dictionary with additional response metadata
            - request_id: Request ID for tracking
    
    Raises:
        HTTPException:
            - 400: If validation fails (empty message, message too long)
            - 429: If rate limit exceeded (50 requests per 60 seconds)
            - 503: If chat service is unavailable
            - 500: If unexpected error occurs during processing
    
    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/v1/chat",
        ...     json={
        ...         "message": "Hello, how are you?",
        ...         "conversation_id": "conv-123"
        ...     }
        ... )
        >>> response.json()["response"]
        "I'm doing well, thank you!"
    """
    try:
        if not service.is_available():
            raise HTTPException(status_code=503, detail="Chat module not available")
        
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(request.message) > 10000:
            raise HTTPException(status_code=400, detail="Message too long (max 10000 characters)")
        
        response_data = service.chat(
            request.message,
            conversation_id=request.conversation_id
        )
        
        # Handle different response formats
        if isinstance(response_data, dict):
            response_text = response_data.get("response", response_data.get("message", str(response_data)))
            conversation_id = response_data.get("conversation_id", request.conversation_id)
            metadata = {k: v for k, v in response_data.items() if k not in ["response", "message", "conversation_id"]}
        else:
            response_text = str(response_data)
            conversation_id = request.conversation_id
            metadata = None
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            metadata=metadata,
            request_id=getattr(req.state, 'request_id', None)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors - return 400 with clear message
        logger.warning(f"Validation error in chat: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error(
            f"Unexpected error processing chat: {e}",
            exc_info=True,
            request_id=getattr(req.state, 'request_id', None)
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing chat"
        )


