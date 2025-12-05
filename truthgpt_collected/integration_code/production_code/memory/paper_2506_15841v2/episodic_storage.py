#!/usr/bin/env python3
"""
Almacenamiento de Memoria Episódica
====================================

Módulo que maneja el almacenamiento y gestión de memoria episódica.
"""

import time
from typing import Dict, List, Optional, Any, Set
from collections import deque, defaultdict
import torch

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class EpisodicStorage:
    """Gestiona el almacenamiento de memoria episódica."""
    
    def __init__(self, max_size: int, enable_prioritization: bool = True):
        self.max_size = max_size
        self.episodic_memory = deque(maxlen=max_size)
        self.episode_access_counts = defaultdict(int)
        self.episode_tags: Dict[int, Set[str]] = defaultdict(set)
        self.episode_priorities: Optional[Dict[int, float]] = {} if enable_prioritization else None
    
    def store(
        self, 
        episode: torch.Tensor, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Almacena un episodio.
        
        Returns:
            Índice del episodio almacenado
        """
        def _store():
            episode_item = {
                'episode': episode.detach().cpu() if episode.is_cuda else episode.detach(),
                'metadata': metadata or {},
                'timestamp': time.time(),
                'access_count': 0
            }
            self.episodic_memory.append(episode_item)
            idx = len(self.episodic_memory) - 1
            return idx
        
        result, error = safe_execute(_store, default_value=-1, log_errors=True)
        if error:
            logger.error("Error almacenando episodio", error=str(error))
        return result
    
    def store_with_tags(
        self,
        episode: torch.Tensor,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: float = 1.0
    ) -> int:
        """Almacena un episodio con tags y prioridad."""
        idx = self.store(episode, metadata)
        
        if idx >= 0:
            if tags:
                self.episode_tags[idx].update(tags)
            if self.episode_priorities is not None:
                self.episode_priorities[idx] = priority
        
        return idx
    
    def get(self, idx: int) -> Optional[Dict[str, Any]]:
        """Obtiene un episodio por índice."""
        if 0 <= idx < len(self.episodic_memory):
            return self.episodic_memory[idx]
        return None
    
    def get_all_episodes(self) -> List[torch.Tensor]:
        """Obtiene todos los episodios como lista de tensores."""
        return [item['episode'] for item in self.episodic_memory]
    
    def update_access_count(self, idx: int):
        """Actualiza el contador de accesos de un episodio."""
        if 0 <= idx < len(self.episodic_memory):
            self.episode_access_counts[idx] += 1
            self.episodic_memory[idx]['access_count'] = self.episode_access_counts[idx]
    
    def get_by_tags(self, tags: List[str]) -> List[int]:
        """Obtiene índices de episodios que tienen los tags especificados."""
        tagged_indices = [
            idx
            for idx, episode_tags in self.episode_tags.items()
            if any(tag in episode_tags for tag in tags)
        ]
        return tagged_indices
    
    def get_by_priority(self, min_priority: float = 0.5) -> List[int]:
        """Obtiene índices de episodios con prioridad mínima."""
        if self.episode_priorities is None:
            return list(range(len(self.episodic_memory)))
        
        return [
            idx for idx, priority in self.episode_priorities.items()
            if priority >= min_priority
        ]
    
    def update_priority(self, idx: int, priority: float) -> bool:
        """Actualiza la prioridad de un episodio."""
        if self.episode_priorities is None:
            return False
        if not (0 <= idx < len(self.episodic_memory)):
            return False
        if priority < 0:
            return False
        
        self.episode_priorities[idx] = priority
        return True
    
    def size(self) -> int:
        """Retorna el tamaño actual de la memoria."""
        return len(self.episodic_memory)
    
    def clear(self):
        """Limpia toda la memoria episódica."""
        self.episodic_memory.clear()
        self.episode_access_counts.clear()
        self.episode_tags.clear()
        if self.episode_priorities is not None:
            self.episode_priorities.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria episódica."""
        return {
            'size': len(self.episodic_memory),
            'max_size': self.max_size,
            'utilization': len(self.episodic_memory) / self.max_size if self.max_size > 0 else 0.0,
            'total_accesses': sum(self.episode_access_counts.values()),
            'tagged_episodes': len(self.episode_tags),
            'prioritized_episodes': len(self.episode_priorities) if self.episode_priorities else 0
        }

