#!/usr/bin/env python3
"""
Sistema de Deduplicación Inteligente para la API Multimodal.

Detecta y elimina requests duplicados o similares usando técnicas de redundancy suppression.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json

try:
    from redundancy.paper_2510_00071 import (
        Paper2510_00071_RedundancySuppressor,
        Paper2510_00071Config
    )
    REDUNDANCY_AVAILABLE = True
except ImportError:
    try:
        # Intentar importación alternativa
        from redundancy import (
            Paper2510_00071_RedundancySuppressor,
            Paper2510_00071Config
        )
        REDUNDANCY_AVAILABLE = True
    except ImportError:
        REDUNDANCY_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class RequestSignature:
    """Firma de un request para deduplicación."""
    prompt_hash: str
    modality: str
    parameters_hash: str
    timestamp: datetime
    task_id: Optional[str] = None


class DeduplicationManager:
    """Gestor de deduplicación de requests."""
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,
        time_window_seconds: int = 3600,
        enable_semantic_dedup: bool = True
    ):
        """
        Inicializa el gestor de deduplicación.
        
        Args:
            similarity_threshold: Umbral de similitud (0.0-1.0)
            time_window_seconds: Ventana de tiempo para considerar duplicados
            enable_semantic_dedup: Si usar deduplicación semántica
        """
        self.similarity_threshold = similarity_threshold
        self.time_window_seconds = time_window_seconds
        self.enable_semantic_dedup = enable_semantic_dedup
        
        # Cache de requests recientes
        self.recent_requests: Dict[str, RequestSignature] = {}
        
        # Redundancy suppressor (si está disponible)
        self.redundancy_suppressor = None
        if REDUNDANCY_AVAILABLE and enable_semantic_dedup:
            try:
                config = Paper2510_00071Config(
                    similarity_threshold=similarity_threshold,
                    redundancy_detection_method="cosine"
                )
                self.redundancy_suppressor = Paper2510_00071_RedundancySuppressor(config)
                logger.info("Redundancy suppressor inicializado")
            except Exception as e:
                logger.warning(f"No se pudo inicializar redundancy suppressor: {e}")
        
        self.stats = {
            "total_requests": 0,
            "duplicates_detected": 0,
            "duplicates_prevented": 0,
            "cache_hits": 0
        }
    
    def _hash_prompt(self, prompt: str) -> str:
        """
        Genera hash de un prompt.
        
        Args:
            prompt: Prompt a hashear
        
        Returns:
            Hash hexadecimal
        """
        # Normalizar prompt
        normalized = prompt.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def _hash_parameters(self, parameters: Dict[str, Any]) -> str:
        """
        Genera hash de parámetros.
        
        Args:
            parameters: Parámetros a hashear
        
        Returns:
            Hash hexadecimal
        """
        # Ordenar y serializar
        sorted_params = json.dumps(parameters, sort_keys=True)
        return hashlib.sha256(sorted_params.encode()).hexdigest()
    
    def _create_signature(
        self,
        prompt: str,
        modality: str,
        parameters: Dict[str, Any]
    ) -> RequestSignature:
        """
        Crea una firma de request.
        
        Args:
            prompt: Prompt
            modality: Modalidad
            parameters: Parámetros
        
        Returns:
            Firma del request
        """
        return RequestSignature(
            prompt_hash=self._hash_prompt(prompt),
            modality=modality,
            parameters_hash=self._hash_parameters(parameters),
            timestamp=datetime.now()
        )
    
    def check_duplicate(
        self,
        prompt: str,
        modality: str,
        parameters: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un request es duplicado.
        
        Args:
            prompt: Prompt del request
            modality: Modalidad
            parameters: Parámetros
        
        Returns:
            (es_duplicado, task_id_existente)
        """
        self.stats["total_requests"] += 1
        
        signature = self._create_signature(prompt, modality, parameters)
        signature_key = f"{signature.prompt_hash}:{signature.modality}:{signature.parameters_hash}"
        
        # Limpiar requests antiguos
        cutoff = datetime.now() - timedelta(seconds=self.time_window_seconds)
        self.recent_requests = {
            k: v for k, v in self.recent_requests.items()
            if v.timestamp > cutoff
        }
        
        # Verificar duplicado exacto
        if signature_key in self.recent_requests:
            existing = self.recent_requests[signature_key]
            self.stats["duplicates_detected"] += 1
            self.stats["cache_hits"] += 1
            logger.info(f"Duplicado exacto detectado: {signature_key}")
            return True, existing.task_id
        
        # Verificar similitud semántica (si está habilitado)
        if self.enable_semantic_dedup and self.redundancy_suppressor:
            similar = self._check_semantic_similarity(signature, prompt)
            if similar:
                self.stats["duplicates_detected"] += 1
                return True, similar
        
        # No es duplicado, almacenar
        self.recent_requests[signature_key] = signature
        return False, None
    
    def _check_semantic_similarity(
        self,
        signature: RequestSignature,
        prompt: str
    ) -> Optional[str]:
        """
        Verifica similitud semántica con requests anteriores.
        
        Args:
            signature: Firma del request
            prompt: Prompt
        
        Returns:
            Task ID de request similar o None
        """
        # TODO: Implementar verificación semántica usando embeddings
        # Por ahora, solo verificación exacta
        return None
    
    def register_task(
        self,
        prompt: str,
        modality: str,
        parameters: Dict[str, Any],
        task_id: str
    ):
        """
        Registra una tarea completada para deduplicación futura.
        
        Args:
            prompt: Prompt
            modality: Modalidad
            parameters: Parámetros
            task_id: ID de la tarea
        """
        signature = self._create_signature(prompt, modality, parameters)
        signature_key = f"{signature.prompt_hash}:{signature.modality}:{signature.parameters_hash}"
        
        if signature_key in self.recent_requests:
            self.recent_requests[signature_key].task_id = task_id
        else:
            signature.task_id = task_id
            self.recent_requests[signature_key] = signature
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de deduplicación.
        
        Returns:
            Estadísticas
        """
        total = self.stats["total_requests"]
        duplicate_rate = (
            (self.stats["duplicates_detected"] / total * 100)
            if total > 0 else 0.0
        )
        
        return {
            **self.stats,
            "duplicate_rate": round(duplicate_rate, 2),
            "cache_size": len(self.recent_requests),
            "similarity_threshold": self.similarity_threshold,
            "time_window_seconds": self.time_window_seconds
        }
    
    def clear_cache(self):
        """Limpia el cache de requests."""
        self.recent_requests.clear()
        logger.info("Cache de deduplicación limpiado")

