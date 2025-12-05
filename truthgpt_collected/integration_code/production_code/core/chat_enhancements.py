#!/usr/bin/env python3
"""
Mejoras Avanzadas para el Sistema de Chat
==========================================

Incluye:
- Estimación precisa de tokens
- Caché de respuestas
- Análisis de calidad
- Post-procesamiento de respuestas
- Rate limiting
"""

from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import re

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


class TokenCounter:
    """Contador preciso de tokens usando tiktoken."""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Inicializa el contador de tokens.
        
        Args:
            model: Modelo para el cual contar tokens
        """
        self.model = model
        self.encoding = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                # Obtener encoding según el modelo
                if "gpt-4" in model or "gpt-3.5" in model:
                    self.encoding = tiktoken.encoding_for_model(model)
                else:
                    # Encoding por defecto
                    self.encoding = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                logger.warning("No se pudo inicializar tiktoken", error=str(e))
    
    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en un texto.
        
        Args:
            text: Texto a contar
        
        Returns:
            Número de tokens
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        
        # Fallback: aproximación (1 token ≈ 4 caracteres)
        return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Cuenta tokens en una lista de mensajes.
        
        Args:
            messages: Lista de mensajes formateados
        
        Returns:
            Número total de tokens
        """
        total = 0
        for msg in messages:
            # Cada mensaje tiene overhead de formato
            total += 4  # Overhead por mensaje
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
        return total


class ResponseCache:
    """Caché de respuestas para mejorar rendimiento."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Inicializa el caché.
        
        Args:
            max_size: Tamaño máximo del caché
            ttl_seconds: Tiempo de vida en segundos
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[str, datetime]] = {}
        self.access_times: Dict[str, datetime] = {}
    
    def _generate_key(self, message: str, context: Optional[str] = None) -> str:
        """Genera una clave única para el mensaje."""
        combined = f"{message}|{context or ''}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, message: str, context: Optional[str] = None) -> Optional[str]:
        """
        Obtiene una respuesta del caché.
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional (opcional)
        
        Returns:
            Respuesta en caché o None
        """
        key = self._generate_key(message, context)
        
        if key not in self.cache:
            return None
        
        response, timestamp = self.cache[key]
        
        # Verificar TTL
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None
        
        # Actualizar tiempo de acceso
        self.access_times[key] = datetime.now()
        return response
    
    def set(self, message: str, response: str, context: Optional[str] = None):
        """
        Guarda una respuesta en el caché.
        
        Args:
            message: Mensaje del usuario
            response: Respuesta a guardar
            context: Contexto adicional (opcional)
        """
        key = self._generate_key(message, context)
        
        # Si el caché está lleno, eliminar el menos usado
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Eliminar el más antiguo
            if self.access_times:
                oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
        
        self.cache[key] = (response, datetime.now())
        self.access_times[key] = datetime.now()
    
    def clear(self):
        """Limpia el caché."""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }


class ResponseQualityAnalyzer:
    """Analiza la calidad de las respuestas."""
    
    @staticmethod
    def analyze(response: str) -> Dict[str, Any]:
        """
        Analiza la calidad de una respuesta.
        
        Args:
            response: Respuesta a analizar
        
        Returns:
            Diccionario con métricas de calidad
        """
        metrics = {
            "length": len(response),
            "word_count": len(response.split()),
            "sentence_count": len(re.split(r'[.!?]+', response)),
            "has_code": bool(re.search(r'```|`[^`]+`', response)),
            "has_links": bool(re.search(r'http[s]?://', response)),
            "has_questions": bool(re.search(r'\?', response)),
            "readability_score": 0.0
        }
        
        # Calcular score de legibilidad simple (Flesch-like)
        if metrics["sentence_count"] > 0 and metrics["word_count"] > 0:
            avg_sentence_length = metrics["word_count"] / metrics["sentence_count"]
            avg_word_length = sum(len(word) for word in response.split()) / metrics["word_count"]
            
            # Score simple (0-100, más alto = más legible)
            metrics["readability_score"] = max(0, min(100, 
                206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 5)
            ))
        
        return metrics


class ResponsePostProcessor:
    """Post-procesa respuestas para mejorar calidad."""
    
    @staticmethod
    def process(response: str, **kwargs) -> str:
        """
        Post-procesa una respuesta.
        
        Args:
            response: Respuesta original
            **kwargs: Opciones de procesamiento
        
        Returns:
            Respuesta procesada
        """
        processed = response.strip()
        
        # Eliminar espacios múltiples
        processed = re.sub(r' +', ' ', processed)
        
        # Eliminar saltos de línea múltiples (excepto en código)
        if not kwargs.get("preserve_code_formatting", True):
            processed = re.sub(r'\n{3,}', '\n\n', processed)
        
        # Capitalizar primera letra si es necesario
        if kwargs.get("capitalize_first", True) and processed:
            processed = processed[0].upper() + processed[1:] if len(processed) > 1 else processed.upper()
        
        # Añadir punto final si falta
        if kwargs.get("add_final_period", False) and processed and processed[-1] not in '.!?':
            processed += '.'
        
        return processed
    
    @staticmethod
    def format_markdown(response: str) -> str:
        """
        Formatea markdown básico en la respuesta.
        
        Args:
            response: Respuesta con markdown
        
        Returns:
            Respuesta formateada
        """
        # Mejorar formato de código
        response = re.sub(r'```(\w+)?\n(.*?)```', r'```\1\n\2```', response, flags=re.DOTALL)
        
        # Mejorar formato de listas
        response = re.sub(r'^\* ', '- ', response, flags=re.MULTILINE)
        
        return response


class RateLimiter:
    """Rate limiter para prevenir abusos."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Inicializa el rate limiter.
        
        Args:
            max_requests: Máximo de requests por ventana
            window_seconds: Tamaño de la ventana en segundos
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un request está permitido.
        
        Args:
            identifier: Identificador único (user_id, IP, etc.)
        
        Returns:
            Tupla (allowed, error_message)
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Limpiar requests antiguos
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Verificar límite
        if len(self.requests[identifier]) >= self.max_requests:
            return False, f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds."
        
        # Registrar request
        self.requests[identifier].append(now)
        return True, None
    
    def get_remaining(self, identifier: str) -> int:
        """
        Obtiene requests restantes.
        
        Args:
            identifier: Identificador único
        
        Returns:
            Número de requests restantes
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))


class ConversationSummarizer:
    """Resume conversaciones largas para mantener contexto."""
    
    @staticmethod
    def summarize_messages(messages: List[Dict[str, str]], max_length: int = 200) -> str:
        """
        Resume una lista de mensajes.
        
        Args:
            messages: Lista de mensajes
            max_length: Longitud máxima del resumen
        
        Returns:
            Resumen de la conversación
        """
        if not messages:
            return ""
        
        summary_parts = []
        for msg in messages[:5]:  # Primeros 5 mensajes
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]  # Primeros 50 caracteres
            summary_parts.append(f"{role}: {content}...")
        
        summary = " | ".join(summary_parts)
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary


