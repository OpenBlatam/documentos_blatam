#!/usr/bin/env python3
"""
Utilidades para Large Language Models (LLMs).

Incluye:
- Integración con OpenAI, Anthropic
- Vector databases
- RAG (Retrieval Augmented Generation)
- Prompt engineering
"""

from typing import Dict, Any, Optional, List, Union
import numpy as np

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from .utils import setup_logger

try:
    from .error_handling import safe_execute, retry, RetryStrategy
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    def safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            if log_errors:
                logger.error("Error en ejecución", error=str(e))
            return default_value, e
    
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class RetryStrategy:
        EXPONENTIAL_BACKOFF = "exponential_backoff"

logger = setup_logger(__name__)


class LLMClient:
    """Cliente unificado para LLMs."""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Inicializa cliente LLM.
        
        Args:
            provider: Proveedor ("openai", "anthropic")
            api_key: API key (opcional, puede usar variables de entorno)
        """
        self.provider = provider
        
        if provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai no está instalado")
            self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        
        elif provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic no está instalado")
            self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
        else:
            raise ValueError(f"Proveedor no soportado: {provider}")
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Genera texto usando el LLM.
        
        Args:
            prompt: Prompt de entrada
            **kwargs: Parámetros adicionales
        
        Returns:
            Texto generado o None
        """
        def _generate_openai():
            response = self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                **{k: v for k, v in kwargs.items() if k != 'model'}
            )
            return response.choices[0].message.content
        
        def _generate_anthropic():
            response = self.client.messages.create(
                model=kwargs.get('model', 'claude-3-opus-20240229'),
                max_tokens=kwargs.get('max_tokens', 1024),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        @retry(
            max_attempts=3,
            delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            exceptions=(Exception,)
        )
        def _generate_with_retry():
            if self.provider == "openai":
                return _generate_openai()
            elif self.provider == "anthropic":
                return _generate_anthropic()
            return None
        
        result, error = safe_execute(_generate_with_retry, default_value=None, log_errors=True)
        if error:
            logger.error("Error generando texto", provider=self.provider, error=str(error))
        return result


class VectorStore:
    """Almacén de vectores para RAG."""
    
    def __init__(self, backend: str = "chroma", **kwargs: Any) -> None:
        """
        Inicializa vector store.
        
        Args:
            backend: Backend ("chroma", "faiss")
            **kwargs: Configuración adicional
        """
        self.backend = backend
        
        if backend == "chroma":
            if not CHROMADB_AVAILABLE:
                raise ImportError("chromadb no está instalado")
            self.client = chromadb.Client()
            self.collection = self.client.create_collection(name=kwargs.get('collection_name', 'documents'))
        
        elif backend == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError("faiss no está instalado")
            self.dimension = kwargs.get('dimension', 384)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []
        else:
            raise ValueError(f"Backend no soportado: {backend}")
    
    def add_documents(self, documents: List[str], embeddings: Optional[np.ndarray] = None):
        """
        Añade documentos al vector store.
        
        Args:
            documents: Lista de documentos
            embeddings: Embeddings pre-calculados (opcional)
        """
        if self.backend == "chroma":
            if embeddings is None:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embeddings = model.encode(documents)
                else:
                    raise ValueError("Se requieren embeddings o sentence-transformers")
            
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                ids=[f"doc_{i}" for i in range(len(documents))]
            )
        
        elif self.backend == "faiss":
            if embeddings is None:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embeddings = model.encode(documents)
                else:
                    raise ValueError("Se requieren embeddings o sentence-transformers")
            
            self.index.add(embeddings.astype('float32'))
            self.documents.extend(documents)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca documentos similares.
        
        Args:
            query: Query de búsqueda
            top_k: Número de resultados
        
        Returns:
            Lista de documentos relevantes
        """
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            query_embedding = model.encode([query])
        else:
            raise ValueError("sentence-transformers requerido para búsqueda")
        
        if self.backend == "chroma":
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k
            )
            return [
                {'document': doc, 'distance': dist}
                for doc, dist in zip(results['documents'][0], results['distances'][0])
            ]
        
        elif self.backend == "faiss":
            distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
            return [
                {'document': self.documents[idx], 'distance': float(dist)}
                for dist, idx in zip(distances[0], indices[0])
            ]

