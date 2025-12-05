#!/usr/bin/env python3
"""
Streaming de Respuestas para Chat
==================================

Implementa streaming de respuestas en tiempo real similar a ChatGPT.
"""

from typing import AsyncGenerator, Dict, Any, Optional, List
import json
import asyncio

try:
    from openai import AsyncOpenAI
    OPENAI_ASYNC_AVAILABLE = True
except ImportError:
    OPENAI_ASYNC_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_ASYNC_AVAILABLE = True
except ImportError:
    ANTHROPIC_ASYNC_AVAILABLE = False

from .utils import setup_logger
from .chat_engine import ChatEngine, Conversation, Message

logger = setup_logger(__name__)


class StreamingChatEngine(ChatEngine):
    """Extensión de ChatEngine con soporte para streaming."""
    
    def __init__(self, *args, **kwargs):
        """Inicializa el motor de chat con streaming."""
        super().__init__(*args, **kwargs)
        
        # Clientes asíncronos para streaming
        self.async_client = None
        if self.provider == "openai" and OPENAI_ASYNC_AVAILABLE:
            try:
                self.async_client = AsyncOpenAI(api_key=kwargs.get('api_key'))
            except Exception as e:
                logger.warning("No se pudo inicializar cliente async OpenAI", error=str(e))
        elif self.provider == "anthropic" and ANTHROPIC_ASYNC_AVAILABLE:
            try:
                self.async_client = AsyncAnthropic(api_key=kwargs.get('api_key'))
            except Exception as e:
                logger.warning("No se pudo inicializar cliente async Anthropic", error=str(e))
    
    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Genera respuesta en streaming.
        
        Args:
            message: Mensaje del usuario
            conversation_id: ID de conversación
            user_id: ID del usuario
            **kwargs: Parámetros adicionales
        
        Yields:
            Diccionarios con chunks de la respuesta
        """
        # Crear o obtener conversación
        if conversation_id is None or conversation_id not in self.conversations:
            conversation_id = self.create_conversation(user_id=user_id)
        
        conversation = self.conversations[conversation_id]
        
        # Añadir mensaje del usuario
        user_message = Message(role="user", content=message)
        conversation.add_message(user_message)
        
        # Obtener mensajes formateados
        messages = conversation.get_messages_for_llm(
            self.max_history_tokens,
            token_counter=self.token_counter
        )
        
        full_response = ""
        
        try:
            if self.provider == "openai" and self.async_client:
                async for chunk in self._stream_openai(messages, **kwargs):
                    if chunk:
                        full_response += chunk
                        yield {
                            "chunk": chunk,
                            "conversation_id": conversation_id,
                            "done": False
                        }
            
            elif self.provider == "anthropic" and self.async_client:
                async for chunk in self._stream_anthropic(messages, **kwargs):
                    if chunk:
                        full_response += chunk
                        yield {
                            "chunk": chunk,
                            "conversation_id": conversation_id,
                            "done": False
                        }
            
            else:
                # Fallback: generar respuesta normal y simular streaming
                response = await asyncio.to_thread(
                    self._generate_llm_response,
                    conversation,
                    **kwargs
                )
                
                # Simular streaming palabra por palabra
                words = response.split()
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    full_response += chunk
                    yield {
                        "chunk": chunk,
                        "conversation_id": conversation_id,
                        "done": False
                    }
                    await asyncio.sleep(0.05)  # Pequeña pausa para efecto visual
            
            # Añadir respuesta completa a la conversación
            assistant_message = Message(
                role="assistant",
                content=full_response,
                metadata={
                    "provider": self.provider,
                    "model": self.model,
                    "streamed": True
                }
            )
            conversation.add_message(assistant_message)
            
            # Último chunk indicando finalización
            yield {
                "chunk": "",
                "conversation_id": conversation_id,
                "done": True,
                "full_response": full_response
            }
        
        except Exception as e:
            logger.error("Error en streaming", error=str(e))
            error_response = f"Error: {str(e)}"
            yield {
                "chunk": error_response,
                "conversation_id": conversation_id,
                "done": True,
                "error": str(e)
            }
    
    async def _stream_openai(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream de OpenAI."""
        if not self.async_client:
            return
        
        stream = await self.async_client.chat.completions.create(
            model=kwargs.get('model', self.model or 'gpt-3.5-turbo'),
            messages=messages,
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_anthropic(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream de Anthropic."""
        if not self.async_client:
            return
        
        # Filtrar mensaje del sistema para Anthropic
        anthropic_messages = [msg for msg in messages if msg["role"] != "system"]
        system_msg = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
        
        async with self.async_client.messages.stream(
            model=kwargs.get('model', self.model or 'claude-3-opus-20240229'),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            system=system_msg if system_msg else self.default_system_prompt,
            messages=anthropic_messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

