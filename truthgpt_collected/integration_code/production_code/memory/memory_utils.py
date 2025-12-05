#!/usr/bin/env python3
"""
Utilidades para Sistemas de Memoria
====================================

Funciones de utilidad para trabajar con sistemas de memoria.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import numpy as np
from pathlib import Path
import json
import time

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


def create_episode_from_text(
    text: str,
    memory_dim: int = 512,
    method: str = "hash"
) -> torch.Tensor:
    """
    Crea un episodio (embedding) desde texto.
    
    Args:
        text: Texto a convertir
        memory_dim: Dimensión del embedding
        method: Método de conversión ("hash", "random", "zeros")
    
    Returns:
        Tensor del episodio
    """
    if method == "hash":
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        embedding = torch.zeros(memory_dim)
        for i, byte_val in enumerate(hash_bytes[:memory_dim]):
            embedding[i] = (byte_val - 128) / 128.0
        
        return embedding
    
    elif method == "random":
        return torch.randn(memory_dim)
    
    elif method == "zeros":
        return torch.zeros(memory_dim)
    
    else:
        raise ValueError(f"Método no soportado: {method}")


def batch_store_episodes(
    memory_system,
    episodes: List[torch.Tensor],
    metadata_list: Optional[List[Dict]] = None,
    tags_list: Optional[List[List[str]]] = None
) -> int:
    """
    Almacena múltiples episodios en batch.
    
    Args:
        memory_system: Sistema de memoria
        episodes: Lista de episodios
        metadata_list: Lista de metadata (opcional)
        tags_list: Lista de tags (opcional)
    
    Returns:
        Número de episodios almacenados exitosamente
    """
    stored = 0
    
    for i, episode in enumerate(episodes):
        metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
        tags = tags_list[i] if tags_list and i < len(tags_list) else None
        
        if hasattr(memory_system, 'store_episode_with_tags') and tags:
            result = memory_system.store_episode_with_tags(
                episode,
                metadata=metadata,
                tags=tags
            )
        else:
            result = memory_system.store_episode(episode, metadata=metadata)
        
        if result:
            stored += 1
    
    logger.info(f"Almacenados {stored}/{len(episodes)} episodios en batch")
    return stored


def compare_episodes(
    episode1: torch.Tensor,
    episode2: torch.Tensor,
    method: str = "cosine"
) -> float:
    """
    Compara dos episodios y retorna similitud.
    
    Args:
        episode1: Primer episodio
        episode2: Segundo episodio
        method: Método de comparación ("cosine", "euclidean", "dot")
    
    Returns:
        Score de similitud
    """
    if method == "cosine":
        # Similitud coseno
        dot_product = torch.dot(episode1, episode2)
        norm1 = torch.norm(episode1)
        norm2 = torch.norm(episode2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return (dot_product / (norm1 * norm2)).item()
    
    elif method == "euclidean":
        # Distancia euclidiana (invertida para similitud)
        distance = torch.norm(episode1 - episode2).item()
        return 1.0 / (1.0 + distance)
    
    elif method == "dot":
        # Producto punto
        return torch.dot(episode1, episode2).item()
    
    else:
        raise ValueError(f"Método no soportado: {method}")


def find_similar_episodes(
    memory_system,
    query: torch.Tensor,
    threshold: float = 0.7,
    max_results: int = 10
) -> List[Tuple[int, float]]:
    """
    Encuentra episodios similares a un query.
    
    Args:
        memory_system: Sistema de memoria
        query: Query tensor
        threshold: Umbral de similitud mínima
        max_results: Máximo de resultados
    
    Returns:
        Lista de tuplas (índice, similitud)
    """
    if not hasattr(memory_system, 'episodic_memory'):
        return []
    
    similarities = []
    
    for idx, item in enumerate(memory_system.episodic_memory):
        episode = item['episode']
        if isinstance(episode, torch.Tensor):
            similarity = compare_episodes(query, episode, method="cosine")
            if similarity >= threshold:
                similarities.append((idx, similarity))
    
    # Ordenar por similitud
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:max_results]


def export_memory_to_dict(
    memory_system,
    include_metadata: bool = True,
    include_tags: bool = True
) -> Dict[str, Any]:
    """
    Exporta memoria a diccionario.
    
    Args:
        memory_system: Sistema de memoria
        include_metadata: Si True, incluye metadata
        include_tags: Si True, incluye tags
    
    Returns:
        Diccionario con la memoria exportada
    """
    export_data = {
        'export_timestamp': time.time(),
        'episodic_memory': [],
        'semantic_memory': {},
        'stats': memory_system.get_episodic_stats() if hasattr(memory_system, 'get_episodic_stats') else {}
    }
    
    # Exportar memoria episódica
    if hasattr(memory_system, 'episodic_memory'):
        for idx, item in enumerate(memory_system.episodic_memory):
            episode_data = {
                'index': idx,
                'episode': item['episode'].cpu().tolist() if isinstance(item['episode'], torch.Tensor) else item['episode'],
                'timestamp': item.get('timestamp', time.time())
            }
            
            if include_metadata:
                episode_data['metadata'] = item.get('metadata', {})
            
            if include_tags and hasattr(memory_system, 'episode_tags') and idx in memory_system.episode_tags:
                episode_data['tags'] = list(memory_system.episode_tags[idx])
            
            export_data['episodic_memory'].append(episode_data)
    
    # Exportar memoria semántica
    if hasattr(memory_system, 'semantic_memory'):
        for key, value in memory_system.semantic_memory.items():
            export_data['semantic_memory'][key] = {
                'episode': value['episode'].cpu().tolist() if isinstance(value['episode'], torch.Tensor) else value['episode'],
                'metadata': value.get('metadata', {}) if include_metadata else {}
            }
    
    return export_data


def import_memory_from_dict(
    memory_system,
    import_data: Dict[str, Any],
    clear_existing: bool = False
) -> int:
    """
    Importa memoria desde diccionario.
    
    Args:
        memory_system: Sistema de memoria
        import_data: Datos a importar
        clear_existing: Si True, limpia memoria existente
    
    Returns:
        Número de episodios importados
    """
    if clear_existing and hasattr(memory_system, 'episodic_memory'):
        memory_system.episodic_memory.clear()
    
    imported = 0
    
    # Importar memoria episódica
    for item in import_data.get('episodic_memory', []):
        def _import_episode():
            episode = torch.tensor(item['episode'])
            metadata = item.get('metadata', {})
            
            if hasattr(memory_system, 'store_episode_with_tags') and 'tags' in item:
                memory_system.store_episode_with_tags(
                    episode,
                    metadata=metadata,
                    tags=item['tags']
                )
            else:
                memory_system.store_episode(episode, metadata=metadata)
            
            return True
        
        result, error = safe_execute(_import_episode, default_value=False, log_errors=False)
        if result:
            imported += 1
        elif error:
            logger.warning("Error importando episodio", error=str(error))
    
    logger.info(f"Importados {imported} episodios")
    return imported


def merge_memory_systems(
    source_memory: Any,
    target_memory: Any,
    merge_strategy: str = "append"
) -> int:
    """
    Fusiona dos sistemas de memoria.
    
    Args:
        source_memory: Memoria fuente
        target_memory: Memoria destino
        merge_strategy: Estrategia ("append", "replace", "merge")
    
    Returns:
        Número de episodios fusionados
    """
    if not (hasattr(source_memory, 'episodic_memory') and 
            hasattr(target_memory, 'episodic_memory')):
        return 0
    
    merged = 0
    
    if merge_strategy == "append":
        for item in source_memory.episodic_memory:
            target_memory.store_episode(
                item['episode'],
                metadata=item.get('metadata', {})
            )
            merged += 1
    
    elif merge_strategy == "replace":
        target_memory.episodic_memory.clear()
        for item in source_memory.episodic_memory:
            target_memory.store_episode(
                item['episode'],
                metadata=item.get('metadata', {})
            )
            merged += 1
    
    elif merge_strategy == "merge":
        # Merge inteligente: evitar duplicados
        source_episodes = {hash(item['episode'].cpu().numpy().tobytes()): item 
                          for item in source_memory.episodic_memory}
        target_episodes = {hash(item['episode'].cpu().numpy().tobytes()): item 
                          for item in target_memory.episodic_memory}
        
        for hash_val, item in source_episodes.items():
            if hash_val not in target_episodes:
                target_memory.store_episode(
                    item['episode'],
                    metadata=item.get('metadata', {})
                )
                merged += 1
    
    logger.info(f"Fusionados {merged} episodios usando estrategia '{merge_strategy}'")
    return merged


def get_memory_health_report(memory_system) -> Dict[str, Any]:
    """
    Genera reporte de salud del sistema de memoria.
    
    Args:
        memory_system: Sistema de memoria
    
    Returns:
        Diccionario con reporte de salud
    """
    report = {
        'timestamp': time.time(),
        'status': 'healthy',
        'warnings': [],
        'recommendations': []
    }
    
    if not hasattr(memory_system, 'episodic_memory'):
        report['status'] = 'error'
        report['warnings'].append('Sistema de memoria no tiene episodic_memory')
        return report
    
    # Verificar utilización
    if hasattr(memory_system, 'config'):
        utilization = len(memory_system.episodic_memory) / memory_system.config.max_memory_size
        report['utilization'] = utilization
        
        if utilization > 0.9:
            report['warnings'].append('Memoria casi llena (>90%)')
            report['recommendations'].append('Considerar consolidación o compresión')
        elif utilization > 0.7:
            report['warnings'].append('Memoria bastante llena (>70%)')
    
    # Verificar caché
    if hasattr(memory_system, 'retrieval_cache') and memory_system.retrieval_cache:
        cache_size = len(memory_system.retrieval_cache)
        if hasattr(memory_system, 'config') and hasattr(memory_system.config, 'cache_size'):
            cache_utilization = cache_size / memory_system.config.cache_size
            report['cache_utilization'] = cache_utilization
            
            if cache_utilization > 0.9:
                report['warnings'].append('Caché casi lleno')
                report['recommendations'].append('Limpiar caché')
    
    # Verificar hit rate
    if hasattr(memory_system, 'cache_hits') and hasattr(memory_system, 'cache_misses'):
        total = memory_system.cache_hits + memory_system.cache_misses
        if total > 0:
            hit_rate = memory_system.cache_hits / total
            report['cache_hit_rate'] = hit_rate
            
            if hit_rate < 0.3:
                report['warnings'].append('Cache hit rate bajo (<30%)')
                report['recommendations'].append('Revisar estrategia de caché')
    
    # Actualizar status
    if report['warnings']:
        report['status'] = 'warning'
    
    return report

