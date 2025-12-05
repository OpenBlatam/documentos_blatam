#!/usr/bin/env python3
"""
API REST para Chat Conversacional - Similar a ChatGPT
======================================================

API FastAPI completa para el sistema de chat con:
- Endpoints RESTful
- Manejo de sesiones
- Streaming de respuestas (opcional)
- Autenticación básica
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import os
import json

try:
    from fastapi import FastAPI, HTTPException, status, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .chat_engine import ChatEngine, Message, Conversation
from .chat_streaming import StreamingChatEngine
from .utils import setup_logger
from .api_utils import create_fastapi_app
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)


# Modelos Pydantic para requests/responses
if FASTAPI_AVAILABLE:
    class ChatRequest(BaseModel):
        """Request para enviar un mensaje."""
        message: str = Field(..., description="Mensaje del usuario")
        conversation_id: Optional[str] = Field(None, description="ID de conversación existente")
        user_id: Optional[str] = Field(None, description="ID del usuario")
        temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperatura para generación")
        max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Máximo de tokens en respuesta")
    
    class ChatResponse(BaseModel):
        """Response con la respuesta del chat."""
        response: str = Field(..., description="Respuesta del asistente")
        conversation_id: str = Field(..., description="ID de la conversación")
        timestamp: str = Field(..., description="Timestamp de la respuesta")
        metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")
    
    class ConversationInfo(BaseModel):
        """Información de una conversación."""
        conversation_id: str
        user_id: Optional[str]
        message_count: int
        created_at: str
        updated_at: str
    
    class CreateConversationRequest(BaseModel):
        """Request para crear una conversación."""
        user_id: Optional[str] = Field(None, description="ID del usuario")
        system_prompt: Optional[str] = Field(None, description="Prompt del sistema personalizado")


class ChatAPI:
    """API REST para el sistema de chat."""
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        enable_streaming: bool = False,
        enable_auth: bool = False
    ):
        """
        Inicializa la API de chat.
        
        Args:
            provider: Proveedor LLM ("openai", "anthropic", "local")
            model: Nombre del modelo
            api_key: API key
            system_prompt: Prompt del sistema por defecto
            enable_streaming: Habilitar streaming de respuestas
            enable_auth: Habilitar autenticación básica
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI no está instalado. Instala con: pip install fastapi uvicorn")
        
        self.app = create_fastapi_app(
            title="ChatGPT-like API",
            version="1.0.0",
            enable_cors=True
        )
        
        # Usar StreamingChatEngine si está disponible
        try:
            self.chat_engine = StreamingChatEngine(
                provider=provider,
                model=model,
                api_key=api_key,
                system_prompt=system_prompt
            )
        except Exception as e:
            logger.warning("No se pudo inicializar StreamingChatEngine, usando ChatEngine normal", error=str(e))
            self.chat_engine = ChatEngine(
                provider=provider,
                model=model,
                api_key=api_key,
                system_prompt=system_prompt
            )
        
        self.enable_streaming = enable_streaming
        self.enable_auth = enable_auth
        
        # Montar archivos estáticos si existe el directorio
        static_dir = Path(__file__).parent.parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        self._setup_routes()
        
        logger.info("ChatAPI inicializada", provider=provider, model=model)
    
    def _setup_routes(self):
        """Configura las rutas de la API."""
        
        @self.app.get("/")
        async def root():
            """Endpoint raíz - Redirige a la interfaz web."""
            static_dir = Path(__file__).parent.parent / "static"
            chat_html = static_dir / "chat.html"
            if chat_html.exists():
                return FileResponse(str(chat_html))
            return {
                "name": "ChatGPT-like API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "chat": "/api/v1/chat",
                    "conversations": "/api/v1/conversations",
                    "health": "/health",
                    "ui": "/static/chat.html"
                }
            }
        
        @self.app.get("/ui")
        async def ui():
            """Interfaz web del chat."""
            static_dir = Path(__file__).parent.parent / "static"
            chat_html = static_dir / "chat.html"
            if chat_html.exists():
                return FileResponse(str(chat_html))
            raise HTTPException(status_code=404, detail="Interfaz web no encontrada")
        
        @self.app.get("/health")
        async def health():
            """Health check."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "provider": self.chat_engine.provider,
                "model": self.chat_engine.model
            }
        
        @self.app.post("/api/v1/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            """
            Endpoint principal para enviar mensajes y recibir respuestas.
            
            Similar a la API de ChatGPT, procesa mensajes y mantiene el historial.
            """
            try:
                result = self.chat_engine.chat(
                    message=request.message,
                    conversation_id=request.conversation_id,
                    user_id=request.user_id,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                return ChatResponse(**result)
            
            except Exception as e:
                logger.error("Error en endpoint chat", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error procesando mensaje: {str(e)}"
                )
        
        @self.app.post("/api/v1/chat/stream")
        async def chat_stream(request: ChatRequest):
            """
            Endpoint para streaming de respuestas en tiempo real.
            
            Similar a ChatGPT, envía chunks de la respuesta conforme se generan.
            """
            if not isinstance(self.chat_engine, StreamingChatEngine):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Streaming no está disponible con este proveedor"
                )
            
            async def generate():
                try:
                    async for chunk in self.chat_engine.chat_stream(
                        message=request.message,
                        conversation_id=request.conversation_id,
                        user_id=request.user_id,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    ):
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    logger.error("Error en streaming", error=str(e))
                    error_chunk = {
                        "chunk": "",
                        "done": True,
                        "error": str(e)
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        @self.app.post("/api/v1/conversations", response_model=Dict[str, str])
        async def create_conversation(request: CreateConversationRequest):
            """Crea una nueva conversación."""
            try:
                conversation_id = self.chat_engine.create_conversation(
                    user_id=request.user_id,
                    system_prompt=request.system_prompt
                )
                
                return {
                    "conversation_id": conversation_id,
                    "status": "created"
                }
            
            except Exception as e:
                logger.error("Error creando conversación", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creando conversación: {str(e)}"
                )
        
        @self.app.get("/api/v1/conversations", response_model=List[ConversationInfo])
        async def list_conversations(user_id: Optional[str] = None):
            """Lista todas las conversaciones."""
            try:
                conversations = self.chat_engine.list_conversations(user_id=user_id)
                return [ConversationInfo(**conv) for conv in conversations]
            
            except Exception as e:
                logger.error("Error listando conversaciones", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error listando conversaciones: {str(e)}"
                )
        
        @self.app.get("/api/v1/conversations/{conversation_id}")
        async def get_conversation(conversation_id: str):
            """Obtiene una conversación específica."""
            try:
                conversation = self.chat_engine.get_conversation(conversation_id)
                
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Conversación {conversation_id} no encontrada"
                    )
                
                return conversation.to_dict()
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Error obteniendo conversación", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error obteniendo conversación: {str(e)}"
                )
        
        @self.app.delete("/api/v1/conversations/{conversation_id}")
        async def delete_conversation(conversation_id: str):
            """Elimina una conversación."""
            try:
                deleted = self.chat_engine.delete_conversation(conversation_id)
                
                if not deleted:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Conversación {conversation_id} no encontrada"
                    )
                
                return {
                    "conversation_id": conversation_id,
                    "status": "deleted"
                }
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Error eliminando conversación", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error eliminando conversación: {str(e)}"
                )
        
        @self.app.get("/api/v1/conversations/{conversation_id}/messages")
        async def get_messages(conversation_id: str):
            """Obtiene todos los mensajes de una conversación."""
            try:
                conversation = self.chat_engine.get_conversation(conversation_id)
                
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Conversación {conversation_id} no encontrada"
                    )
                
                return {
                    "conversation_id": conversation_id,
                    "messages": [msg.to_dict() for msg in conversation.messages]
                }
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Error obteniendo mensajes", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error obteniendo mensajes: {str(e)}"
                )


def create_chat_app(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> FastAPI:
    """
    Crea y retorna una aplicación FastAPI configurada para chat.
    
    Args:
        provider: Proveedor LLM ("openai", "anthropic", "local")
        model: Nombre del modelo
        api_key: API key (opcional, puede usar OPENAI_API_KEY o ANTHROPIC_API_KEY)
        system_prompt: Prompt del sistema
    
    Returns:
        Aplicación FastAPI configurada
    """
    # Obtener API key de variables de entorno si no se proporciona
    if api_key is None:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Obtener modelo por defecto si no se proporciona
    if model is None:
        if provider == "openai":
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        elif provider == "anthropic":
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    chat_api = ChatAPI(
        provider=provider,
        model=model,
        api_key=api_key,
        system_prompt=system_prompt
    )
    
    return chat_api.app


if __name__ == "__main__":
    import uvicorn
    
    # Crear app
    app = create_chat_app(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("LLM_MODEL"),
        system_prompt=os.getenv("SYSTEM_PROMPT")
    )
    
    # Ejecutar servidor
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )

