#!/usr/bin/env python3
"""
Procesador de Batch Optimizado.

Optimiza el procesamiento de múltiples requests en batch.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuración de batch processing."""
    max_batch_size: int = 100
    batch_timeout_seconds: int = 5
    enable_deduplication: bool = True
    enable_prioritization: bool = True
    enable_parallel_processing: bool = True


class BatchProcessor:
    """Procesador optimizado de batches."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """
        Inicializa el procesador de batch.
        
        Args:
            config: Configuración
        """
        self.config = config or BatchConfig()
        self.pending_batch: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self.last_batch_time = datetime.now()
    
    async def add_to_batch(
        self,
        request: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Agrega un request a un batch y procesa si está lleno.
        
        Args:
            request: Request a agregar
            timeout: Timeout opcional
        
        Returns:
            Batch procesado o None si se agregó al batch pendiente
        """
        timeout = timeout or self.config.batch_timeout_seconds
        
        async with self.batch_lock:
            self.pending_batch.append(request)
            
            # Verificar si debemos procesar
            should_process = (
                len(self.pending_batch) >= self.config.max_batch_size or
                (datetime.now() - self.last_batch_time).total_seconds() >= timeout
            )
            
            if should_process:
                batch = self.pending_batch.copy()
                self.pending_batch.clear()
                self.last_batch_time = datetime.now()
                return batch
        
        return None
    
    def optimize_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimiza un batch antes de procesar.
        
        Args:
            batch: Batch a optimizar
        
        Returns:
            Batch optimizado
        """
        if not batch:
            return batch
        
        optimized = batch.copy()
        
        # Deduplicación
        if self.config.enable_deduplication:
            optimized = self._deduplicate_batch(optimized)
        
        # Priorización
        if self.config.enable_prioritization:
            optimized = self._prioritize_batch(optimized)
        
        # Agrupación por modalidad
        optimized = self._group_by_modality(optimized)
        
        return optimized
    
    def _deduplicate_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Elimina duplicados del batch.
        
        Args:
            batch: Batch original
        
        Returns:
            Batch sin duplicados
        """
        seen = set()
        unique = []
        
        for item in batch:
            # Crear clave única
            key = (
                item.get("prompt", ""),
                item.get("modality", ""),
                str(sorted(item.get("parameters", {}).items()))
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        if len(unique) < len(batch):
            logger.info(f"Deduplicación: {len(batch)} -> {len(unique)} requests")
        
        return unique
    
    def _prioritize_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioriza requests en el batch.
        
        Args:
            batch: Batch original
        
        Returns:
            Batch priorizado
        """
        return sorted(
            batch,
            key=lambda x: x.get("priority", 5),
            reverse=False  # Menor número = mayor prioridad
        )
    
    def _group_by_modality(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Agrupa requests por modalidad para procesamiento eficiente.
        
        Args:
            batch: Batch original
        
        Returns:
            Batch agrupado
        """
        # Por ahora, solo retornar ordenado
        # En el futuro, se podría agrupar para procesamiento paralelo
        return batch
    
    async def process_batch_parallel(
        self,
        batch: List[Dict[str, Any]],
        processor_func: callable,
        max_concurrent: int = 5
    ) -> List[Any]:
        """
        Procesa un batch en paralelo.
        
        Args:
            batch: Batch a procesar
            processor_func: Función procesadora
            max_concurrent: Máximo de procesamientos concurrentes
        
        Returns:
            Resultados del procesamiento
        """
        if not self.config.enable_parallel_processing:
            # Procesamiento secuencial
            results = []
            for item in batch:
                result = await processor_func(item)
                results.append(result)
            return results
        
        # Procesamiento paralelo con semáforo
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await processor_func(item)
        
        tasks = [process_with_semaphore(item) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar excepciones
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error procesando item {i}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results


