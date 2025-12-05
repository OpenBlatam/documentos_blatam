#!/usr/bin/env python3
"""
Analytics y Visualización del Sistema de Memoria
=================================================

Proporciona análisis avanzados, visualizaciones y métricas
del sistema de memoria.
"""

from typing import Dict, List, Tuple, Optional, Any
import torch
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import time

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from core.utils import setup_logger

logger = setup_logger(__name__)


class MemoryAnalytics:
    """Analytics avanzados para el sistema de memoria."""
    
    def __init__(self, memory_system):
        """
        Inicializa analytics.
        
        Args:
            memory_system: Instancia de Paper2506_15841v2_MemorySystem
        """
        self.memory_system = memory_system
        logger.info("MemoryAnalytics inicializado")
    
    def analyze_access_patterns(self) -> Dict[str, Any]:
        """
        Analiza patrones de acceso a la memoria.
        
        Returns:
            Diccionario con análisis de patrones
        """
        access_counts = self.memory_system.episode_access_counts
        
        if not access_counts:
            return {
                'total_accesses': 0,
                'unique_episodes_accessed': 0,
                'most_accessed': [],
                'least_accessed': [],
                'access_distribution': {}
            }
        
        total = sum(access_counts.values())
        unique = len(access_counts)
        
        # Episodios más accedidos
        most_accessed = sorted(
            access_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Episodios menos accedidos
        least_accessed = sorted(
            access_counts.items(),
            key=lambda x: x[1]
        )[:10]
        
        # Distribución de accesos
        access_values = list(access_counts.values())
        distribution = {
            'mean': np.mean(access_values),
            'median': np.median(access_values),
            'std': np.std(access_values),
            'min': np.min(access_values),
            'max': np.max(access_values)
        }
        
        return {
            'total_accesses': total,
            'unique_episodes_accessed': unique,
            'most_accessed': most_accessed,
            'least_accessed': least_accessed,
            'access_distribution': distribution,
            'access_rate': total / unique if unique > 0 else 0.0
        }
    
    def analyze_temporal_patterns(self) -> Dict[str, Any]:
        """
        Analiza patrones temporales de almacenamiento.
        
        Returns:
            Diccionario con análisis temporal
        """
        if not self.memory_system.episodic_memory:
            return {'episodes_by_time': {}, 'storage_rate': 0.0}
        
        # Agrupar por períodos de tiempo
        now = time.time()
        time_buckets = defaultdict(int)
        
        for item in self.memory_system.episodic_memory:
            timestamp = item.get('timestamp', now)
            age_hours = (now - timestamp) / 3600
            
            if age_hours < 1:
                bucket = 'last_hour'
            elif age_hours < 24:
                bucket = 'last_day'
            elif age_hours < 168:  # 7 days
                bucket = 'last_week'
            elif age_hours < 720:  # 30 days
                bucket = 'last_month'
            else:
                bucket = 'older'
            
            time_buckets[bucket] += 1
        
        # Calcular tasa de almacenamiento
        if len(self.memory_system.episodic_memory) > 0:
            oldest_timestamp = min(
                item.get('timestamp', now) 
                for item in self.memory_system.episodic_memory
            )
            time_span_hours = (now - oldest_timestamp) / 3600
            storage_rate = len(self.memory_system.episodic_memory) / max(time_span_hours, 1)
        else:
            storage_rate = 0.0
        
        return {
            'episodes_by_time': dict(time_buckets),
            'storage_rate': storage_rate,
            'total_episodes': len(self.memory_system.episodic_memory)
        }
    
    def analyze_similarity_clusters(self, n_clusters: int = 5) -> Dict[str, Any]:
        """
        Analiza clusters de similitud entre episodios.
        
        Args:
            n_clusters: Número de clusters a encontrar
        
        Returns:
            Diccionario con análisis de clusters
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'sklearn no disponible'}
        
        if len(self.memory_system.episodic_memory) < n_clusters:
            return {'error': f'No hay suficientes episodios (necesita {n_clusters})'}
        
        # Extraer embeddings de episodios
        episodes = torch.stack([
            item['episode'] for item in self.memory_system.episodic_memory
        ]).cpu().numpy()
        
        # Reducir dimensionalidad si es necesario
        if episodes.shape[1] > 50:
            pca = PCA(n_components=50)
            episodes_reduced = pca.fit_transform(episodes)
        else:
            episodes_reduced = episodes
        
        # Clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(episodes_reduced)
        
        # Calcular silhouette score
        silhouette = silhouette_score(episodes_reduced, cluster_labels)
        
        # Análisis por cluster
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_indices = np.where(cluster_labels == i)[0]
            cluster_analysis[f'cluster_{i}'] = {
                'size': len(cluster_indices),
                'indices': cluster_indices.tolist(),
                'center': kmeans.cluster_centers_[i].tolist()
            }
        
        return {
            'n_clusters': n_clusters,
            'silhouette_score': float(silhouette),
            'clusters': cluster_analysis,
            'cluster_labels': cluster_labels.tolist()
        }
    
    def analyze_tag_distribution(self) -> Dict[str, Any]:
        """
        Analiza distribución de tags.
        
        Returns:
            Diccionario con análisis de tags
        """
        if not hasattr(self.memory_system, 'episode_tags'):
            return {'error': 'Sistema de tags no disponible'}
        
        # Contar tags
        all_tags = []
        for tags in self.memory_system.episode_tags.values():
            all_tags.extend(tags)
        
        tag_counts = Counter(all_tags)
        
        # Episodios por tag
        episodes_by_tag = defaultdict(list)
        for idx, tags in self.memory_system.episode_tags.items():
            for tag in tags:
                episodes_by_tag[tag].append(idx)
        
        return {
            'total_unique_tags': len(tag_counts),
            'most_common_tags': tag_counts.most_common(10),
            'tag_distribution': dict(tag_counts),
            'episodes_by_tag': {k: len(v) for k, v in episodes_by_tag.items()}
        }
    
    def analyze_priority_distribution(self) -> Dict[str, Any]:
        """
        Analiza distribución de prioridades.
        
        Returns:
            Diccionario con análisis de prioridades
        """
        if not hasattr(self.memory_system, 'episode_priorities') or self.memory_system.episode_priorities is None:
            return {'error': 'Sistema de prioridades no disponible'}
        
        priorities = list(self.memory_system.episode_priorities.values())
        
        if not priorities:
            return {'total_prioritized': 0}
        
        return {
            'total_prioritized': len(priorities),
            'mean_priority': float(np.mean(priorities)),
            'median_priority': float(np.median(priorities)),
            'std_priority': float(np.std(priorities)),
            'min_priority': float(np.min(priorities)),
            'max_priority': float(np.max(priorities)),
            'high_priority_count': sum(1 for p in priorities if p >= 0.7),
            'medium_priority_count': sum(1 for p in priorities if 0.3 <= p < 0.7),
            'low_priority_count': sum(1 for p in priorities if p < 0.3)
        }
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo de analytics.
        
        Returns:
            Diccionario con todos los análisis
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'basic_stats': self.memory_system.get_episodic_stats(),
            'access_patterns': self.analyze_access_patterns(),
            'temporal_patterns': self.analyze_temporal_patterns(),
            'tag_distribution': self.analyze_tag_distribution(),
            'priority_distribution': self.analyze_priority_distribution(),
            'similarity_clusters': self.analyze_similarity_clusters() if SKLEARN_AVAILABLE else {'sklearn_not_available': True}
        }
    
    def visualize_memory_distribution(self, save_path: Optional[str] = None):
        """
        Visualiza distribución de memoria.
        
        Args:
            save_path: Ruta para guardar la visualización
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualización no disponible (matplotlib/seaborn)")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Distribución de accesos
        access_counts = list(self.memory_system.episode_access_counts.values())
        if access_counts:
            axes[0, 0].hist(access_counts, bins=20, edgecolor='black')
            axes[0, 0].set_title('Distribución de Accesos a Episodios')
            axes[0, 0].set_xlabel('Número de Accesos')
            axes[0, 0].set_ylabel('Frecuencia')
        
        # 2. Distribución temporal
        temporal = self.analyze_temporal_patterns()
        if temporal.get('episodes_by_time'):
            time_buckets = temporal['episodes_by_time']
            axes[0, 1].bar(time_buckets.keys(), time_buckets.values())
            axes[0, 1].set_title('Episodios por Período de Tiempo')
            axes[0, 1].set_xlabel('Período')
            axes[0, 1].set_ylabel('Número de Episodios')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. Distribución de tags
        tag_analysis = self.analyze_tag_distribution()
        if 'most_common_tags' in tag_analysis and tag_analysis['most_common_tags']:
            tags, counts = zip(*tag_analysis['most_common_tags'][:10])
            axes[1, 0].barh(tags, counts)
            axes[1, 0].set_title('Top 10 Tags Más Comunes')
            axes[1, 0].set_xlabel('Frecuencia')
        
        # 4. Distribución de prioridades
        priority_analysis = self.analyze_priority_distribution()
        if 'mean_priority' in priority_analysis:
            priorities = list(self.memory_system.episode_priorities.values()) if self.memory_system.episode_priorities else []
            if priorities:
                axes[1, 1].hist(priorities, bins=20, edgecolor='black')
                axes[1, 1].set_title('Distribución de Prioridades')
                axes[1, 1].set_xlabel('Prioridad')
                axes[1, 1].set_ylabel('Frecuencia')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Visualización guardada en {save_path}")
        else:
            plt.show()
        
        plt.close()


class MemoryOptimizer:
    """Optimizador del sistema de memoria."""
    
    def __init__(self, memory_system):
        """
        Inicializa optimizador.
        
        Args:
            memory_system: Instancia de Paper2506_15841v2_MemorySystem
        """
        self.memory_system = memory_system
        logger.info("MemoryOptimizer inicializado")
    
    def optimize_memory_layout(self) -> Dict[str, Any]:
        """
        Optimiza el layout de memoria para mejor rendimiento.
        
        Returns:
            Diccionario con resultados de optimización
        """
        optimizations = []
        
        # 1. Consolidar episodios frecuentemente accedidos
        if len(self.memory_system.episodic_memory) > 100:
            consolidated = self.memory_system.consolidate_to_semantic()
            optimizations.append({
                'type': 'consolidation',
                'episodes_consolidated': consolidated
            })
        
        # 2. Comprimir episodios antiguos
        if self.memory_system.config.enable_compression:
            compressed = self.memory_system.compress_memory()
            optimizations.append({
                'type': 'compression',
                'episodes_compressed': compressed
            })
        
        # 3. Limpiar caché si está muy lleno
        if (self.memory_system.retrieval_cache and 
            len(self.memory_system.retrieval_cache) > self.memory_system.config.cache_size * 0.9):
            old_size = len(self.memory_system.retrieval_cache)
            self.memory_system.clear_cache()
            optimizations.append({
                'type': 'cache_clear',
                'cache_entries_removed': old_size
            })
        
        return {
            'optimizations_applied': len(optimizations),
            'details': optimizations,
            'memory_utilization_after': len(self.memory_system.episodic_memory) / self.memory_system.config.max_memory_size
        }
    
    def recommend_episodes_for_consolidation(self, top_k: int = 10) -> List[int]:
        """
        Recomienda episodios para consolidación.
        
        Args:
            top_k: Número de episodios a recomendar
        
        Returns:
            Lista de índices de episodios recomendados
        """
        # Episodios más accedidos que aún no están consolidados
        access_counts = self.memory_system.episode_access_counts
        
        # Filtrar episodios que ya están en memoria semántica
        semantic_keys = set(self.memory_system.semantic_memory.keys())
        
        candidates = []
        for idx, count in access_counts.items():
            if idx < len(self.memory_system.episodic_memory):
                # Verificar si ya está consolidado
                episode_item = self.memory_system.episodic_memory[idx]
                if 'consolidated' not in episode_item.get('metadata', {}):
                    candidates.append((idx, count))
        
        # Ordenar por acceso y retornar top_k
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in candidates[:top_k]]
    
    def suggest_cache_size(self) -> int:
        """
        Sugiere tamaño óptimo de caché basado en uso.
        
        Returns:
            Tamaño sugerido de caché
        """
        if not self.memory_system.retrieval_cache:
            return self.memory_system.config.cache_size
        
        total_requests = self.memory_system.cache_hits + self.memory_system.cache_misses
        
        if total_requests == 0:
            return self.memory_system.config.cache_size
        
        hit_rate = self.memory_system.cache_hits / total_requests
        
        # Si hit rate es alto, aumentar caché
        # Si hit rate es bajo, reducir caché
        current_size = len(self.memory_system.retrieval_cache)
        
        if hit_rate > 0.8:
            suggested = int(current_size * 1.2)
        elif hit_rate < 0.3:
            suggested = int(current_size * 0.8)
        else:
            suggested = current_size
        
        return max(100, min(suggested, self.memory_system.config.max_memory_size // 10))


class MemoryExporter:
    """Exportador/Importador de memoria."""
    
    def __init__(self, memory_system):
        """
        Inicializa exportador.
        
        Args:
            memory_system: Instancia de Paper2506_15841v2_MemorySystem
        """
        self.memory_system = memory_system
        logger.info("MemoryExporter inicializado")
    
    def export_to_json(self, filepath: str, include_metadata: bool = True) -> bool:
        """
        Exporta memoria a JSON.
        
        Args:
            filepath: Ruta del archivo
            include_metadata: Si True, incluye metadata completa
        
        Returns:
            True si se exportó exitosamente
        """
        try:
            import json
            
            export_data = {
                'version': '1.0',
                'export_timestamp': datetime.now().isoformat(),
                'config': {
                    'memory_dim': self.memory_system.config.memory_dim,
                    'max_memory_size': self.memory_system.config.max_memory_size
                },
                'episodic_memory': [],
                'semantic_memory': {},
                'stats': self.memory_system.get_episodic_stats()
            }
            
            # Exportar memoria episódica
            for idx, item in enumerate(self.memory_system.episodic_memory):
                episode_data = {
                    'index': idx,
                    'episode': item['episode'].cpu().tolist() if isinstance(item['episode'], torch.Tensor) else item['episode'],
                    'timestamp': item.get('timestamp', time.time())
                }
                
                if include_metadata:
                    episode_data['metadata'] = item.get('metadata', {})
                    if hasattr(self.memory_system, 'episode_tags') and idx in self.memory_system.episode_tags:
                        episode_data['tags'] = list(self.memory_system.episode_tags[idx])
                    if (hasattr(self.memory_system, 'episode_priorities') and 
                        self.memory_system.episode_priorities and 
                        idx in self.memory_system.episode_priorities):
                        episode_data['priority'] = self.memory_system.episode_priorities[idx]
                
                export_data['episodic_memory'].append(episode_data)
            
            # Exportar memoria semántica
            for key, value in self.memory_system.semantic_memory.items():
                export_data['semantic_memory'][key] = {
                    'episode': value['episode'].cpu().tolist() if isinstance(value['episode'], torch.Tensor) else value['episode'],
                    'metadata': value.get('metadata', {}),
                    'consolidation_time': value.get('consolidation_time', time.time())
                }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Memoria exportada a {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error exportando memoria: {e}")
            return False
    
    def import_from_json(self, filepath: str) -> bool:
        """
        Importa memoria desde JSON.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si se importó exitosamente
        """
        try:
            import json
            
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            # Limpiar memoria existente
            self.memory_system.episodic_memory.clear()
            self.memory_system.semantic_memory.clear()
            
            # Importar memoria episódica
            for item in import_data.get('episodic_memory', []):
                episode = torch.tensor(item['episode'])
                metadata = item.get('metadata', {})
                
                self.memory_system.episodic_memory.append({
                    'episode': episode,
                    'metadata': metadata,
                    'timestamp': item.get('timestamp', time.time())
                })
                
                # Restaurar tags y prioridades
                idx = len(self.memory_system.episodic_memory) - 1
                if 'tags' in item:
                    if not hasattr(self.memory_system, 'episode_tags'):
                        self.memory_system.episode_tags = defaultdict(set)
                    self.memory_system.episode_tags[idx] = set(item['tags'])
                
                if 'priority' in item:
                    if not hasattr(self.memory_system, 'episode_priorities'):
                        self.memory_system.episode_priorities = {}
                    self.memory_system.episode_priorities[idx] = item['priority']
            
            # Importar memoria semántica
            for key, value in import_data.get('semantic_memory', {}).items():
                self.memory_system.semantic_memory[key] = {
                    'episode': torch.tensor(value['episode']),
                    'metadata': value.get('metadata', {}),
                    'consolidation_time': value.get('consolidation_time', time.time())
                }
            
            logger.info(f"Memoria importada desde {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error importando memoria: {e}")
            return False


