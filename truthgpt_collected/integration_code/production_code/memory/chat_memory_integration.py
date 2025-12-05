#!/usr/bin/env python3
"""
Integración del Sistema de Memoria con Chat Engine
===================================================

Permite que el sistema de chat use memoria episódica para:
- Recordar conversaciones importantes
- Recuperar contexto relevante
- Mejorar respuestas con memoria a largo plazo
"""

from typing import Dict, Any, Optional, List
import torch
import numpy as np

try:
    from core.chat_engine import ChatEngine, Conversation, Message
    from memory.paper_2506_15841v2 import (
        Paper2506_15841v2_MemorySystem,
        Paper2506_15841v2Config
    )
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False

from core.utils import setup_logger

logger = setup_logger(__name__)


class ChatMemoryIntegration:
    """
    Integra el sistema de memoria con el chat engine.
    
    Permite que el chat:
    - Almacene conversaciones importantes en memoria episódica
    - Recupere contexto relevante de conversaciones pasadas
    - Use memoria semántica para mejorar respuestas
    """
    
    def __init__(
        self,
        chat_engine: ChatEngine,
        memory_config: Optional[Paper2506_15841v2Config] = None
    ):
        """
        Inicializa la integración.
        
        Args:
            chat_engine: Instancia de ChatEngine
            memory_config: Configuración del sistema de memoria
        """
        if not INTEGRATION_AVAILABLE:
            raise ImportError("Dependencias de integración no disponibles")
        
        self.chat_engine = chat_engine
        self.memory_config = memory_config or Paper2506_15841v2Config(
            memory_dim=512,
            enable_persistence=True,
            persistence_path="./memory_data"
        )
        
        self.memory_system = Paper2506_15841v2_MemorySystem(self.memory_config)
        
        # Embeddings para conversaciones (simplificado)
        self.conversation_embeddings = {}
        
        logger.info("ChatMemoryIntegration inicializada")
    
    def store_conversation_episode(
        self,
        conversation: Conversation,
        importance: float = 1.0,
        tags: List[str] = None
    ):
        """
        Almacena una conversación como episodio en memoria.
        
        Args:
            conversation: Conversación a almacenar
            importance: Importancia de la conversación (0-1)
            tags: Tags para categorización
        """
        try:
            # Crear embedding de la conversación
            # Simplificado: usar promedio de embeddings de mensajes
            conversation_text = " ".join([
                msg.content for msg in conversation.messages
                if msg.role in ["user", "assistant"]
            ])
            
            # Crear embedding simple (en producción usar modelo de embeddings)
            embedding = self._create_embedding(conversation_text)
            
            # Almacenar en memoria
            self.memory_system.store_episode_with_tags(
                episode=embedding,
                metadata={
                    'conversation_id': conversation.conversation_id,
                    'user_id': conversation.user_id,
                    'message_count': len(conversation.messages),
                    'created_at': conversation.created_at.isoformat()
                },
                tags=tags or [],
                priority=importance
            )
            
            # Guardar embedding de conversación
            self.conversation_embeddings[conversation.conversation_id] = embedding
            
            logger.info(
                "Conversación almacenada en memoria",
                conversation_id=conversation.conversation_id,
                importance=importance
            )
        
        except Exception as e:
            logger.error("Error almacenando conversación", error=str(e))
    
    def retrieve_relevant_context(
        self,
        current_message: str,
        conversation_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recupera contexto relevante de conversaciones pasadas.
        
        Args:
            current_message: Mensaje actual
            conversation_id: ID de conversación actual (opcional)
            k: Número de episodios a recuperar
        
        Returns:
            Lista de contextos relevantes
        """
        try:
            # Crear embedding del mensaje actual
            query_embedding = self._create_embedding(current_message)
            
            # Recuperar episodios relevantes
            retrieved, weights = self.memory_system.retrieve_episodes(
                query_embedding,
                k=k
            )
            
            # Obtener metadata de episodios recuperados
            contexts = []
            for i in range(min(k, retrieved.size(1))):
                # En producción, aquí se recuperaría la conversación completa
                # desde la metadata del episodio
                contexts.append({
                    'relevance': weights[0, i].item() if weights.dim() > 1 else weights[i].item(),
                    'episode_idx': i
                })
            
            return contexts
        
        except Exception as e:
            logger.error("Error recuperando contexto", error=str(e))
            return []
    
    def enhance_chat_with_memory(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        store_important: bool = True
    ) -> Dict[str, Any]:
        """
        Mejora el chat usando memoria.
        
        Args:
            message: Mensaje del usuario
            conversation_id: ID de conversación
            user_id: ID del usuario
            store_important: Si True, almacena conversaciones importantes
        
        Returns:
            Respuesta mejorada con contexto de memoria
        """
        # Obtener contexto relevante
        relevant_contexts = self.retrieve_relevant_context(
            message,
            conversation_id=conversation_id
        )
        
        # Generar respuesta normal
        response = self.chat_engine.chat(
            message=message,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        # Añadir información de memoria a metadata
        if relevant_contexts:
            response['metadata']['memory_contexts'] = len(relevant_contexts)
            response['metadata']['memory_relevance'] = max(
                ctx['relevance'] for ctx in relevant_contexts
            ) if relevant_contexts else 0.0
        
        # Almacenar conversación si es importante
        if store_important and conversation_id:
            conversation = self.chat_engine.get_conversation(conversation_id)
            if conversation and len(conversation.messages) > 4:
                # Determinar importancia (simplificado)
                importance = self._calculate_importance(conversation)
                if importance > 0.5:
                    self.store_conversation_episode(
                        conversation,
                        importance=importance,
                        tags=self._extract_tags(conversation)
                    )
        
        return response
    
    def _create_embedding(self, text: str) -> torch.Tensor:
        """
        Crea embedding de texto.
        
        En producción, usar modelo de embeddings real (sentence-transformers, etc.)
        """
        # Embedding simple basado en hash (placeholder)
        # En producción usar: sentence_transformers o similar
        import hashlib
        
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convertir a tensor del tamaño correcto
        embedding = torch.zeros(self.memory_config.memory_dim)
        for i, byte_val in enumerate(hash_bytes[:self.memory_config.memory_dim]):
            embedding[i] = (byte_val - 128) / 128.0
        
        return embedding
    
    def _calculate_importance(self, conversation: Conversation) -> float:
        """
        Calcula la importancia de una conversación.
        
        Args:
            conversation: Conversación a evaluar
        
        Returns:
            Score de importancia (0-1)
        """
        # Factores de importancia:
        # - Longitud de conversación
        # - Número de mensajes
        # - Palabras clave importantes
        
        message_count = len(conversation.messages)
        length_score = min(message_count / 10.0, 1.0)
        
        # Detectar palabras clave importantes
        important_keywords = ['importante', 'recordar', 'guardar', 'clave', 'crítico']
        text = " ".join([msg.content.lower() for msg in conversation.messages])
        keyword_score = sum(1 for keyword in important_keywords if keyword in text) / len(important_keywords)
        
        importance = (length_score * 0.6 + keyword_score * 0.4)
        return min(importance, 1.0)
    
    def _extract_tags(self, conversation: Conversation) -> List[str]:
        """Extrae tags de una conversación."""
        tags = []
        
        # Tags basados en contenido (simplificado)
        text = " ".join([msg.content.lower() for msg in conversation.messages])
        
        if any(word in text for word in ['código', 'programación', 'python', 'javascript']):
            tags.append('programming')
        
        if any(word in text for word in ['pregunta', 'ayuda', 'cómo']):
            tags.append('question')
        
        if any(word in text for word in ['error', 'problema', 'bug']):
            tags.append('troubleshooting')
        
        return tags
    
    def save_memory(self):
        """Guarda la memoria en disco."""
        if self.memory_system.config.enable_persistence:
            self.memory_system.save_persisted_memory()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de memoria."""
        return self.memory_system.get_episodic_stats()


