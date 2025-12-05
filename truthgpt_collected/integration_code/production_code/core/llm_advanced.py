#!/usr/bin/env python3
"""
Utilidades Avanzadas para LLMs - Integración de Librerías
==========================================================

Integración de librerías de LLM, RAG, y prompt engineering de requirements.txt.
"""

from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# LangChain Integration
# ============================================================================

try:
    from langchain.llms import OpenAI as LangChainOpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Chroma, FAISS
    from langchain.chains import RetrievalQA, LLMChain
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    from langchain_community.llms import HuggingFacePipeline
    from langchain_community.embeddings import HuggingFaceEmbeddings
    LANGCHAIN_COMMUNITY_AVAILABLE = True
except ImportError:
    LANGCHAIN_COMMUNITY_AVAILABLE = False

# ============================================================================
# LlamaIndex Integration
# ============================================================================

try:
    from llama_index import (
        VectorStoreIndex,
        ServiceContext,
        StorageContext,
        load_index_from_storage,
        SimpleDirectoryReader
    )
    from llama_index.llms import OpenAI as LlamaIndexOpenAI
    from llama_index.embeddings import OpenAIEmbedding
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

# ============================================================================
# Tiktoken for Token Counting
# ============================================================================

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# ============================================================================
# Sentence Transformers
# ============================================================================

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# ============================================================================
# Vector Databases
# ============================================================================

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# ============================================================================
# FAISS for Similarity Search
# ============================================================================

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# ============================================================================
# Prompt Engineering
# ============================================================================

try:
    import guidance
    GUIDANCE_AVAILABLE = True
except ImportError:
    GUIDANCE_AVAILABLE = False

try:
    import outlines
    OUTLINES_AVAILABLE = True
except ImportError:
    OUTLINES_AVAILABLE = False


class AdvancedLLMClient:
    """Cliente avanzado para LLMs con múltiples backends."""
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        use_langchain: bool = False,
        **kwargs
    ):
        """
        Inicializa el cliente LLM avanzado.
        
        Args:
            provider: Proveedor ("openai", "anthropic", "huggingface")
            model: Nombre del modelo
            use_langchain: Si True, usa LangChain
            **kwargs: Argumentos adicionales
        """
        self.provider = provider
        self.model = model
        self.use_langchain = use_langchain and LANGCHAIN_AVAILABLE
        self.client = None
        
        if self.use_langchain:
            self._init_langchain(**kwargs)
        else:
            self._init_direct(**kwargs)
    
    def _init_langchain(self, **kwargs):
        """Inicializa cliente usando LangChain."""
        if self.provider == "openai":
            self.client = ChatOpenAI(
                model_name=self.model or "gpt-3.5-turbo",
                **kwargs
            )
        elif self.provider == "huggingface" and LANGCHAIN_COMMUNITY_AVAILABLE:
            self.client = HuggingFacePipeline.from_model_id(
                model_id=self.model or "gpt2",
                **kwargs
            )
    
    def _init_direct(self, **kwargs):
        """Inicializa cliente directo."""
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(**kwargs)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(**kwargs)
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """Genera texto usando el LLM."""
        if self.use_langchain and self.client:
            return self.client.predict(prompt, **kwargs)
        elif self.provider == "openai" and self.client:
            response = self.client.chat.completions.create(
                model=self.model or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        return None


class TokenCounter:
    """Contador de tokens usando tiktoken."""
    
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
                self.encoding = tiktoken.encoding_for_model(model)
            except Exception:
                self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en un texto.
        
        Args:
            text: Texto a contar
        
        Returns:
            Número de tokens
        """
        if not TIKTOKEN_AVAILABLE or not self.encoding:
            return len(text.split())
        
        return len(self.encoding.encode(text))
    
    def count_tokens_batch(self, texts: List[str]) -> List[int]:
        """
        Cuenta tokens en múltiples textos.
        
        Args:
            texts: Lista de textos
        
        Returns:
            Lista de conteos de tokens
        """
        return [self.count_tokens(text) for text in texts]


class AdvancedVectorStore:
    """Almacén de vectores avanzado con múltiples backends."""
    
    def __init__(
        self,
        backend: str = "chroma",
        embedding_model: Optional[str] = None,
        **kwargs
    ):
        """
        Inicializa el almacén de vectores.
        
        Args:
            backend: Backend a usar ("chroma", "pinecone", "weaviate", "qdrant", "faiss")
            embedding_model: Modelo de embeddings
            **kwargs: Argumentos adicionales
        """
        self.backend = backend
        self.store = None
        self.embeddings = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE and embedding_model:
            self.embeddings = SentenceTransformer(embedding_model)
        
        self._init_store(**kwargs)
    
    def _init_store(self, **kwargs):
        """Inicializa el almacén según el backend."""
        if self.backend == "chroma" and CHROMADB_AVAILABLE:
            self.store = chromadb.Client(**kwargs)
        elif self.backend == "pinecone" and PINECONE_AVAILABLE:
            api_key = kwargs.get("api_key")
            environment = kwargs.get("environment", "us-east-1-aws")
            self.store = Pinecone(api_key=api_key).Index(
                index_name=kwargs.get("index_name", "default")
            )
        elif self.backend == "weaviate" and WEAVIATE_AVAILABLE:
            self.store = weaviate.Client(**kwargs)
        elif self.backend == "qdrant" and QDRANT_AVAILABLE:
            self.store = QdrantClient(**kwargs)
        elif self.backend == "faiss" and FAISS_AVAILABLE:
            dimension = kwargs.get("dimension", 384)
            self.index = faiss.IndexFlatL2(dimension)
            self.vectors = []
            self.metadata = []
    
    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None):
        """Añade documentos al almacén."""
        if not self.embeddings:
            raise ValueError("Embeddings no inicializados")
        
        embeddings = self.embeddings.encode(documents)
        
        if self.backend == "faiss" and FAISS_AVAILABLE:
            embeddings_np = np.array(embeddings).astype('float32')
            self.index.add(embeddings_np)
            self.vectors.extend(embeddings)
            self.metadata.extend(metadatas or [{}] * len(documents))
        elif self.backend == "chroma" and CHROMADB_AVAILABLE:
            collection = self.store.get_or_create_collection("documents")
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
                ids=[f"doc_{i}" for i in range(len(documents))]
            )
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca documentos similares."""
        if not self.embeddings:
            raise ValueError("Embeddings no inicializados")
        
        query_embedding = self.embeddings.encode([query])[0]
        
        if self.backend == "faiss" and FAISS_AVAILABLE:
            query_np = np.array([query_embedding]).astype('float32')
            distances, indices = self.index.search(query_np, k)
            return [
                {
                    "document": self.metadata[i],
                    "distance": float(distances[0][j])
                }
                for j, i in enumerate(indices[0])
            ]
        elif self.backend == "chroma" and CHROMADB_AVAILABLE:
            collection = self.store.get_collection("documents")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            return results


class PromptEngineer:
    """Herramientas para prompt engineering."""
    
    def __init__(self, use_guidance: bool = False):
        """
        Inicializa el ingeniero de prompts.
        
        Args:
            use_guidance: Si True, usa guidance
        """
        self.use_guidance = use_guidance and GUIDANCE_AVAILABLE
    
    def create_prompt_template(self, template: str, **kwargs) -> Any:
        """
        Crea una plantilla de prompt.
        
        Args:
            template: Plantilla con placeholders
            **kwargs: Variables para la plantilla
        
        Returns:
            Prompt renderizado
        """
        if self.use_guidance and GUIDANCE_AVAILABLE:
            try:
                return guidance(template, **kwargs)
            except Exception:
                return template.format(**kwargs)
        else:
            return template.format(**kwargs)
    
    def optimize_prompt(self, prompt: str, iterations: int = 3) -> str:
        """
        Optimiza un prompt (placeholder para implementación futura).
        
        Args:
            prompt: Prompt a optimizar
            iterations: Número de iteraciones
        
        Returns:
            Prompt optimizado
        """
        return prompt

