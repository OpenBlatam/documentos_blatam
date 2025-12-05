#!/usr/bin/env python3
"""
Motor de Chat Conversacional - Similar a ChatGPT
================================================

Sistema completo de chat conversacional con:
- Manejo de historial de conversación
- Contexto persistente
- Integración con LLMs (OpenAI, Anthropic, modelos locales)
- Gestión de sesiones
- Calidad de respuestas mejorada
- Factory functions para creación fácil
- Funciones de utilidad para verificar disponibilidad

Ejemplo:
    >>> engine = create_chat_engine(provider="openai", model="gpt-4")
    >>> response = engine.chat("Hola, ¿cómo estás?")
"""

__version__ = '2.0.0'

from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
from collections import deque

try:
    from .llm_utils import LLMClient
    LLM_UTILS_AVAILABLE = True
except ImportError:
    LLM_UTILS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute, retry, RetryStrategy

try:
    from .chat_enhancements import (
        TokenCounter,
        ResponseCache,
        ResponseQualityAnalyzer,
        ResponsePostProcessor,
        RateLimiter
    )
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False

logger = setup_logger(__name__)


@dataclass
class Message:
    """Representa un mensaje en la conversación."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a diccionario."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Crea un mensaje desde un diccionario."""
        timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            metadata=data.get("metadata", {})
        )


@dataclass
class Conversation:
    """Representa una conversación completa."""
    conversation_id: str
    user_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message):
        """Añade un mensaje a la conversación."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_messages_for_llm(self, max_tokens: int = 4000, token_counter: Optional[Any] = None) -> List[Dict[str, str]]:
        """
        Obtiene mensajes formateados para el LLM, respetando límite de tokens.
        
        Args:
            max_tokens: Máximo de tokens aproximados a incluir
            token_counter: Instancia de TokenCounter para conteo preciso (opcional)
        
        Returns:
            Lista de mensajes formateados
        """
        # Incluir mensaje del sistema si existe
        formatted = []
        system_message = None
        
        for msg in self.messages:
            if msg.role == "system":
                system_message = {"role": "system", "content": msg.content}
            else:
                formatted.append({"role": msg.role, "content": msg.content})
        
        # Contar tokens (preciso si hay token_counter, aproximado si no)
        if token_counter:
            count_func = token_counter.count_messages_tokens
        else:
            # Fallback: aproximación
            def count_func(msgs):
                total = 0
                for msg in msgs:
                    total += 4  # Overhead
                    total += len(msg.get("content", "")) // 4
                return total
        
        # Si excede, mantener solo los más recientes
        all_messages = ([system_message] if system_message else []) + formatted
        total_tokens = count_func(all_messages)
        
        if total_tokens > max_tokens:
            # Mantener system message y los últimos mensajes
            result = []
            if system_message:
                result.append(system_message)
            
            # Incluir mensajes desde el final hasta alcanzar el límite
            current_tokens = count_func([system_message]) if system_message else 0
            for msg in reversed(formatted):
                msg_tokens = count_func([msg])
                if current_tokens + msg_tokens <= max_tokens:
                    result.insert(1 if system_message else 0, msg)
                    current_tokens += msg_tokens
                else:
                    break
            
            return result
        
        if system_message:
            formatted.insert(0, system_message)
        
        return formatted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la conversación a diccionario."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Crea una conversación desde un diccionario."""
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        return cls(
            conversation_id=data["conversation_id"],
            user_id=data.get("user_id"),
            messages=[Message.from_dict(msg) for msg in data.get("messages", [])],
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )


class ChatEngine:
    """
    Motor de chat conversacional principal.
    
    Similar a ChatGPT, maneja conversaciones con historial,
    contexto y generación de respuestas de calidad.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_history_tokens: int = 4000,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_local_model: bool = False,
        local_model_path: Optional[str] = None
    ):
        """
        Inicializa el motor de chat.
        
        Args:
            provider: Proveedor LLM ("openai", "anthropic", "local")
            model: Nombre del modelo a usar
            api_key: API key (opcional, puede usar variables de entorno)
            system_prompt: Prompt del sistema por defecto
            max_history_tokens: Máximo de tokens en el historial
            temperature: Temperatura para generación
            max_tokens: Máximo de tokens en respuesta
            use_local_model: Si True, usa modelo local
            local_model_path: Ruta al modelo local
        """
        self.provider = provider
        self.model = model
        self.max_history_tokens = max_history_tokens
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_local_model = use_local_model
        
        # Prompt del sistema por defecto
        self.default_system_prompt = system_prompt or (
            "Eres un asistente de IA útil, inofensivo y honesto. "
            "Proporcionas respuestas claras, precisas y bien fundamentadas. "
            "Si no sabes algo, lo admites. Siempre intentas ser útil y respetuoso."
        )
        
        # Inicializar cliente LLM
        if use_local_model:
            self._init_local_model(local_model_path)
        elif LLM_UTILS_AVAILABLE:
            def _init_llm_client():
                return LLMClient(provider=provider, api_key=api_key)
            
            result, error = safe_execute(_init_llm_client, default_value=None, log_errors=False)
            if error:
                logger.warning("No se pudo inicializar LLM client", error=str(error))
            self.llm_client = result
        else:
            self.llm_client = None
        
        # Almacenamiento de conversaciones
        self.conversations: Dict[str, Conversation] = {}
        
        # Mejoras opcionales
        if ENHANCEMENTS_AVAILABLE:
            self.token_counter = TokenCounter(model=model or "gpt-3.5-turbo")
            self.response_cache = ResponseCache(max_size=100, ttl_seconds=3600)
            self.quality_analyzer = ResponseQualityAnalyzer()
            self.post_processor = ResponsePostProcessor()
            self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        else:
            self.token_counter = None
            self.response_cache = None
            self.quality_analyzer = None
            self.post_processor = None
            self.rate_limiter = None
        
        logger.info(
            "ChatEngine inicializado",
            provider=provider,
            model=model,
            use_local_model=use_local_model,
            enhancements_available=ENHANCEMENTS_AVAILABLE
        )
    
    def _init_local_model(self, model_path: Optional[str] = None):
        """Inicializa modelo local usando transformers."""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers no está instalado para modelos locales")
        
        def _load_local_model():
            model_name = model_path or "microsoft/DialoGPT-medium"
            logger.info("Cargando modelo local", model=model_name)
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            if torch.cuda.is_available():
                model = model.cuda()
            
            model.eval()
            
            pipeline_obj = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            return tokenizer, model, pipeline_obj
        
        result, error = safe_execute(_load_local_model, default_value=None, log_errors=True)
        if error:
            logger.error("Error cargando modelo local", error=str(error))
            raise RuntimeError(f"Error cargando modelo local: {error}") from error
        
        self.local_tokenizer, self.local_model, self.local_pipeline = result
        logger.info("Modelo local cargado exitosamente")
    
    def create_conversation(
        self,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Crea una nueva conversación.
        
        Args:
            user_id: ID del usuario (opcional)
            conversation_id: ID de conversación (opcional, se genera si no se proporciona)
            system_prompt: Prompt del sistema personalizado
        
        Returns:
            ID de la conversación
        """
        if conversation_id is None:
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        system_msg = system_prompt or self.default_system_prompt
        
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata={"system_prompt": system_msg}
        )
        
        # Añadir mensaje del sistema
        conversation.add_message(Message(
            role="system",
            content=system_msg
        ))
        
        self.conversations[conversation_id] = conversation
        
        logger.info("Conversación creada", conversation_id=conversation_id, user_id=user_id)
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Obtiene una conversación por ID."""
        return self.conversations.get(conversation_id)
    
    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        use_cache: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje y genera una respuesta.
        
        Args:
            message: Mensaje del usuario
            conversation_id: ID de conversación (se crea si no existe)
            user_id: ID del usuario
            use_cache: Si True, usa caché de respuestas
            **kwargs: Parámetros adicionales (temperature, max_tokens, etc.)
        
        Returns:
            Diccionario con la respuesta y metadata
        
        Raises:
            ValueError: Si el mensaje está vacío o es inválido
        """
        if not message or not isinstance(message, str) or not message.strip():
            raise ValueError("El mensaje no puede estar vacío")
        
        # Rate limiting
        if self.rate_limiter:
            identifier = user_id or conversation_id or "anonymous"
            allowed, error_msg = self.rate_limiter.is_allowed(identifier)
            if not allowed:
                return {
                    "response": f"Rate limit exceeded. {error_msg}",
                    "conversation_id": conversation_id or "unknown",
                    "timestamp": datetime.now().isoformat(),
                    "error": "rate_limit_exceeded"
                }
        
        # Crear o obtener conversación
        if conversation_id is None or conversation_id not in self.conversations:
            conversation_id = self.create_conversation(user_id=user_id)
        
        conversation = self.conversations[conversation_id]
        
        # Añadir mensaje del usuario
        user_message = Message(role="user", content=message)
        conversation.add_message(user_message)
        
        # Verificar caché
        cached_response = None
        if use_cache and self.response_cache:
            context = self._get_conversation_context(conversation)
            cached_response = self.response_cache.get(message, context)
        
        start_time = datetime.now()
        
        try:
            if cached_response:
                response_text = cached_response
                logger.info("Respuesta obtenida del caché", conversation_id=conversation_id)
            else:
                # Generar respuesta
                if self.use_local_model:
                    response_text = self._generate_local_response(conversation, **kwargs)
                elif self.llm_client:
                    response_text = self._generate_llm_response(conversation, **kwargs)
                else:
                    response_text = self._generate_fallback_response(message)
                
                # Post-procesar respuesta
                if self.post_processor:
                    response_text = self.post_processor.process(
                        response_text,
                        capitalize_first=True,
                        add_final_period=False
                    )
                
                # Guardar en caché
                if use_cache and self.response_cache:
                    context = self._get_conversation_context(conversation)
                    self.response_cache.set(message, response_text, context)
            
            # Analizar calidad
            quality_metrics = {}
            if self.quality_analyzer:
                quality_metrics = self.quality_analyzer.analyze(response_text)
            
            # Añadir respuesta del asistente
            generation_time = (datetime.now() - start_time).total_seconds()
            assistant_message = Message(
                role="assistant",
                content=response_text,
                metadata={
                    "generation_time": generation_time,
                    "provider": self.provider,
                    "model": self.model,
                    "cached": cached_response is not None,
                    "quality": quality_metrics
                }
            )
            conversation.add_message(assistant_message)
            
            return {
                "response": response_text,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": assistant_message.metadata
            }
        
        except Exception as e:
            logger.error("Error generando respuesta", error=str(e), conversation_id=conversation_id)
            error_response = f"Lo siento, ocurrió un error al generar la respuesta: {str(e)}"
            
            assistant_message = Message(
                role="assistant",
                content=error_response,
                metadata={"error": str(e)}
            )
            conversation.add_message(assistant_message)
            
            return {
                "response": error_response,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _get_conversation_context(self, conversation: Conversation) -> str:
        """Obtiene contexto de la conversación para el caché."""
        if not conversation.messages:
            return ""
        
        # Usar los últimos 3 mensajes como contexto
        recent_messages = conversation.messages[-3:]
        context_parts = [msg.content[:50] for msg in recent_messages if msg.role != "system"]
        return "|".join(context_parts)
    
    def _generate_llm_response(self, conversation: Conversation, **kwargs: Any) -> str:
        """Genera respuesta usando LLM externo."""
        if not self.llm_client:
            raise ValueError("LLM client no está disponible")
        
        # Obtener mensajes formateados con conteo preciso de tokens
        messages = conversation.get_messages_for_llm(
            self.max_history_tokens,
            token_counter=self.token_counter
        )
        
        # Construir prompt (para OpenAI/Anthropic)
        if self.provider == "openai":
            response = self.llm_client.client.chat.completions.create(
                model=kwargs.get('model', self.model or 'gpt-3.5-turbo'),
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens)
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            # Filtrar mensaje del sistema para Anthropic
            anthropic_messages = [msg for msg in messages if msg["role"] != "system"]
            system_msg = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            
            response = self.llm_client.client.messages.create(
                model=kwargs.get('model', self.model or 'claude-3-opus-20240229'),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                system=system_msg if system_msg else self.default_system_prompt,
                messages=anthropic_messages
            )
            return response.content[0].text
        
        else:
            # Usar método genérico
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            return self.llm_client.generate(prompt, **kwargs) or "No se pudo generar respuesta"
    
    def _generate_local_response(self, conversation: Conversation, **kwargs: Any) -> str:
        """Genera respuesta usando modelo local."""
        if not hasattr(self, 'local_pipeline'):
            raise ValueError("Modelo local no está disponible")
        
        # Obtener contexto de la conversación con conteo preciso
        messages = conversation.get_messages_for_llm(
            self.max_history_tokens,
            token_counter=self.token_counter
        )
        
        # Construir prompt
        prompt_parts = []
        for msg in messages[-5:]:  # Últimos 5 mensajes para contexto
            if msg["role"] == "user":
                prompt_parts.append(f"Usuario: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"Asistente: {msg['content']}")
        
        prompt = "\n".join(prompt_parts) + "\nAsistente:"
        
        # Generar respuesta
        result = self.local_pipeline(
            prompt,
            max_length=len(prompt.split()) + kwargs.get('max_tokens', self.max_tokens),
            temperature=kwargs.get('temperature', self.temperature),
            do_sample=True,
            pad_token_id=self.local_tokenizer.eos_token_id
        )
        
        generated_text = result[0]['generated_text']
        # Extraer solo la parte nueva
        response = generated_text[len(prompt):].strip()
        
        return response if response else "No pude generar una respuesta adecuada."
    
    def _generate_fallback_response(self, message: str) -> str:
        """Genera respuesta de fallback cuando no hay LLM disponible."""
        return (
            f"Recibí tu mensaje: '{message}'. "
            "Actualmente no tengo acceso a un modelo de lenguaje configurado. "
            "Por favor, configura un proveedor LLM (OpenAI, Anthropic) o un modelo local."
        )
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Elimina una conversación."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info("Conversación eliminada", conversation_id=conversation_id)
            return True
        return False
    
    def list_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todas las conversaciones, opcionalmente filtradas por usuario."""
        conversations = []
        for conv in self.conversations.values():
            if user_id is None or conv.user_id == user_id:
                conversations.append({
                    "conversation_id": conv.conversation_id,
                    "user_id": conv.user_id,
                    "message_count": len(conv.messages),
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat()
                })
        return conversations
    
    def save_conversation(self, conversation_id: str, filepath: str):
        """Guarda una conversación en un archivo JSON."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info("Conversación guardada", conversation_id=conversation_id, filepath=filepath)
    
    def load_conversation(self, filepath: str) -> str:
        """Carga una conversación desde un archivo JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conversation = Conversation.from_dict(data)
        self.conversations[conversation.conversation_id] = conversation
        
        logger.info("Conversación cargada", conversation_id=conversation.conversation_id, filepath=filepath)
        
        return conversation.conversation_id


def get_available_providers() -> Dict[str, bool]:
    """
    Obtiene el estado de disponibilidad de todos los proveedores LLM.
    
    Returns:
        Diccionario con el estado de disponibilidad de cada proveedor.
        
    Example:
        >>> providers = get_available_providers()
        >>> if providers['openai']:
        ...     print("OpenAI disponible")
    """
    return {
        'llm_utils': LLM_UTILS_AVAILABLE,
        'transformers': TRANSFORMERS_AVAILABLE,
        'enhancements': ENHANCEMENTS_AVAILABLE
    }


def recommend_chat_config(
    use_case: str = 'general',
    require_local: bool = False
) -> Dict[str, Any]:
    """
    Recomienda configuración de chat basada en caso de uso.
    
    Args:
        use_case: Caso de uso ('general', 'long_context', 'fast', 'quality')
        require_local: Si se requiere modelo local
    
    Returns:
        Diccionario con configuración recomendada.
        
    Raises:
        ValueError: Si use_case no es válido.
        
    Example:
        >>> config = recommend_chat_config(use_case='long_context')
        >>> engine = create_chat_engine(**config)
    """
    if use_case not in ['general', 'long_context', 'fast', 'quality']:
        raise ValueError(f"use_case debe ser 'general', 'long_context', 'fast' o 'quality', recibido: {use_case}")
    
    base_config = {
        'provider': 'openai' if LLM_UTILS_AVAILABLE and not require_local else 'local',
        'temperature': 0.7,
        'max_tokens': 2000
    }
    
    if use_case == 'long_context':
        base_config.update({
            'max_history_tokens': 8000,
            'max_tokens': 4000
        })
    elif use_case == 'fast':
        base_config.update({
            'temperature': 0.3,
            'max_tokens': 1000,
            'max_history_tokens': 2000
        })
    elif use_case == 'quality':
        base_config.update({
            'temperature': 0.9,
            'max_tokens': 3000,
            'max_history_tokens': 6000
        })
    else:  # general
        base_config.update({
            'max_history_tokens': 4000
        })
    
    return base_config


def create_chat_engine(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_history_tokens: int = 4000,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    use_local_model: bool = False,
    local_model_path: Optional[str] = None
) -> Optional[ChatEngine]:
    """
    Factory function para crear instancia de ChatEngine.
    
    Args:
        provider: Proveedor LLM ("openai", "anthropic", "local") (default: "openai")
        model: Nombre del modelo a usar (default: None, usa modelo por defecto del proveedor)
        api_key: API key (opcional, puede usar variables de entorno)
        system_prompt: Prompt del sistema por defecto (opcional)
        max_history_tokens: Máximo de tokens en el historial (default: 4000)
        temperature: Temperatura para generación (default: 0.7)
        max_tokens: Máximo de tokens en respuesta (default: 2000)
        use_local_model: Si True, usa modelo local (default: False)
        local_model_path: Ruta al modelo local (opcional)
    
    Returns:
        Instancia de ChatEngine o None si hay error.
        
    Raises:
        ValueError: Si los parámetros no son válidos.
        
    Example:
        >>> # Chat básico con OpenAI
        >>> engine = create_chat_engine(provider="openai", model="gpt-4")
        >>> 
        >>> # Chat con modelo local
        >>> engine = create_chat_engine(
        ...     use_local_model=True,
        ...     local_model_path="/path/to/model"
        ... )
        >>> 
        >>> # Chat con configuración personalizada
        >>> engine = create_chat_engine(
        ...     provider="anthropic",
        ...     temperature=0.9,
        ...     max_tokens=3000
        ... )
    """
    # Validación de entrada
    if not isinstance(provider, str) or not provider:
        raise ValueError(f"provider debe ser un string no vacío, recibido: {provider}")
    
    valid_providers = ["openai", "anthropic", "local"]
    if provider.lower() not in valid_providers:
        raise ValueError(f"provider debe ser uno de {valid_providers}, recibido: {provider}")
    
    if model is not None and not isinstance(model, str):
        raise ValueError(f"model debe ser str o None, recibido: {type(model).__name__}")
    
    if not isinstance(max_history_tokens, int) or max_history_tokens <= 0:
        raise ValueError(f"max_history_tokens debe ser un entero positivo, recibido: {max_history_tokens}")
    
    if not isinstance(temperature, (int, float)) or not (0.0 <= temperature <= 2.0):
        raise ValueError(f"temperature debe estar en [0.0, 2.0], recibido: {temperature}")
    
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError(f"max_tokens debe ser un entero positivo, recibido: {max_tokens}")
    
    if not isinstance(use_local_model, bool):
        raise ValueError(f"use_local_model debe ser bool, recibido: {type(use_local_model).__name__}")
    
    if use_local_model and local_model_path is not None and not isinstance(local_model_path, str):
        raise ValueError(f"local_model_path debe ser str o None, recibido: {type(local_model_path).__name__}")
    
    try:
        engine = ChatEngine(
            provider=provider,
            model=model,
            api_key=api_key,
            system_prompt=system_prompt,
            max_history_tokens=max_history_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
            use_local_model=use_local_model,
            local_model_path=local_model_path
        )
        
        logger.info(
            "ChatEngine creado exitosamente",
            provider=provider,
            model=model,
            use_local_model=use_local_model
        )
        
        return engine
    
    except Exception as e:
        logger.error(
            f"Error creando ChatEngine: {e}",
            exc_info=True,
            provider=provider,
            model=model,
            use_local_model=use_local_model
        )
        return None


# Exportar clases y funciones principales
__all__ = [
    'Message',
    'Conversation',
    'ChatEngine',
    'create_chat_engine',
    'get_available_providers',
    'recommend_chat_config',
    'LLM_UTILS_AVAILABLE',
    'TRANSFORMERS_AVAILABLE',
    'ENHANCEMENTS_AVAILABLE',
    '__version__'
]

