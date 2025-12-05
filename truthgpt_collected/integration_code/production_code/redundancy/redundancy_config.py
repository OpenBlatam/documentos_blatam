#!/usr/bin/env python3
"""
Configuración Avanzada para Redundancy
======================================

Sistema de configuración con perfiles predefinidos y gestión dinámica.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class PerformanceProfile(Enum):
    """Perfiles de rendimiento predefinidos."""
    SPEED = "speed"
    BALANCED = "balanced"
    QUALITY = "quality"
    MEMORY_EFFICIENT = "memory_efficient"
    ACCURACY = "accuracy"


class RedundancyConfigProfile:
    """
    Perfiles de configuración predefinidos para diferentes casos de uso.
    """
    
    PROFILES: Dict[PerformanceProfile, Dict[str, Any]] = {
        PerformanceProfile.SPEED: {
            'similarity_threshold': 0.90,
            'redundancy_detection_method': 'dot',
            'use_hierarchical_clustering': False,
            'max_cluster_size': 50,
            'bulk_processing_batch_size': 2000,
            'enable_caching': True,
            'cache_size': 10000,
            'enable_adaptive_threshold': False
        },
        PerformanceProfile.BALANCED: {
            'similarity_threshold': 0.85,
            'redundancy_detection_method': 'cosine',
            'use_hierarchical_clustering': True,
            'max_cluster_size': 100,
            'bulk_processing_batch_size': 1000,
            'enable_caching': True,
            'cache_size': 5000,
            'enable_adaptive_threshold': True,
            'min_reduction_rate': 0.1
        },
        PerformanceProfile.QUALITY: {
            'similarity_threshold': 0.80,
            'redundancy_detection_method': 'semantic',
            'use_hierarchical_clustering': True,
            'max_cluster_size': 200,
            'bulk_processing_batch_size': 500,
            'enable_caching': True,
            'cache_size': 3000,
            'enable_adaptive_threshold': True,
            'min_reduction_rate': 0.15
        },
        PerformanceProfile.MEMORY_EFFICIENT: {
            'similarity_threshold': 0.88,
            'redundancy_detection_method': 'cosine',
            'use_hierarchical_clustering': False,
            'max_cluster_size': 50,
            'bulk_processing_batch_size': 500,
            'enable_caching': False,
            'cache_size': 1000,
            'enable_adaptive_threshold': False
        },
        PerformanceProfile.ACCURACY: {
            'similarity_threshold': 0.75,
            'redundancy_detection_method': 'semantic',
            'use_hierarchical_clustering': True,
            'max_cluster_size': 300,
            'bulk_processing_batch_size': 300,
            'enable_caching': True,
            'cache_size': 2000,
            'enable_adaptive_threshold': True,
            'min_reduction_rate': 0.2
        }
    }
    
    @classmethod
    def get_profile(cls, profile: PerformanceProfile) -> Dict[str, Any]:
        """
        Obtiene configuración para un perfil.
        
        Args:
            profile: Perfil de rendimiento
        
        Returns:
            Diccionario con configuración
        """
        if profile not in cls.PROFILES:
            raise ValueError(f"Perfil no válido: {profile}. Válidos: {list(cls.PROFILES.keys())}")
        
        return cls.PROFILES[profile].copy()
    
    @classmethod
    def list_profiles(cls) -> List[str]:
        """Lista todos los perfiles disponibles."""
        return [p.value for p in cls.PROFILES.keys()]
    
    @classmethod
    def merge_profiles(
        cls,
        base_profile: PerformanceProfile,
        overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combina un perfil base con overrides.
        
        Args:
            base_profile: Perfil base
            overrides: Valores a sobrescribir
        
        Returns:
            Configuración combinada
        """
        config = cls.get_profile(base_profile)
        config.update(overrides)
        return config


@dataclass
class RedundancyConfigManager:
    """
    Gestor de configuración avanzado para redundancia.
    """
    
    current_config: Dict[str, Any] = field(default_factory=dict)
    config_history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 10
    
    def __post_init__(self):
        """Inicializa el gestor."""
        if not self.current_config:
            self.current_config = RedundancyConfigProfile.get_profile(
                PerformanceProfile.BALANCED
            )
    
    def load_profile(self, profile: PerformanceProfile) -> Dict[str, Any]:
        """
        Carga un perfil de configuración.
        
        Args:
            profile: Perfil a cargar
        
        Returns:
            Configuración cargada
        """
        def _load():
            config = RedundancyConfigProfile.get_profile(profile)
            self._save_to_history()
            self.current_config = config
            logger.info(f"Perfil cargado: {profile.value}")
            return config
        
        result, error = safe_execute(_load, default_value=self.current_config, log_errors=True)
        return result
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza la configuración actual.
        
        Args:
            updates: Valores a actualizar
        
        Returns:
            Configuración actualizada
        """
        def _update():
            self._save_to_history()
            self.current_config.update(updates)
            logger.info(f"Configuración actualizada: {list(updates.keys())}")
            return self.current_config.copy()
        
        result, error = safe_execute(_update, default_value=self.current_config, log_errors=True)
        return result
    
    def reset_to_default(self) -> Dict[str, Any]:
        """
        Resetea a configuración por defecto.
        
        Returns:
            Configuración por defecto
        """
        return self.load_profile(PerformanceProfile.BALANCED)
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual."""
        return self.current_config.copy()
    
    def _save_to_history(self):
        """Guarda configuración actual en historial."""
        if len(self.config_history) >= self.max_history:
            self.config_history.pop(0)
        self.config_history.append(self.current_config.copy())
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtiene historial de configuraciones."""
        return self.config_history.copy()
    
    def restore_from_history(self, index: int = -1) -> Dict[str, Any]:
        """
        Restaura configuración desde historial.
        
        Args:
            index: Índice en historial (-1 = última)
        
        Returns:
            Configuración restaurada
        """
        if not self.config_history:
            logger.warning("No hay historial disponible")
            return self.current_config
        
        if abs(index) > len(self.config_history):
            raise ValueError(f"Índice inválido: {index}")
        
        config = self.config_history[index].copy()
        self._save_to_history()
        self.current_config = config
        logger.info(f"Configuración restaurada desde historial (índice {index})")
        return config
    
    def compare_configs(
        self,
        config1: Dict[str, Any],
        config2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compara dos configuraciones.
        
        Args:
            config1: Primera configuración
            config2: Segunda configuración
        
        Returns:
            Diccionario con diferencias
        """
        def _compare():
            all_keys = set(config1.keys()) | set(config2.keys())
            differences = {}
            
            for key in all_keys:
                val1 = config1.get(key)
                val2 = config2.get(key)
                
                if val1 != val2:
                    differences[key] = {
                        'config1': val1,
                        'config2': val2
                    }
            
            return {
                'differences': differences,
                'total_differences': len(differences),
                'identical': len(differences) == 0
            }
        
        result, error = safe_execute(_compare, default_value={'differences': {}, 'total_differences': 0, 'identical': True}, log_errors=True)
        return result


def create_config_from_profile(
    profile: PerformanceProfile,
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea configuración desde un perfil.
    
    Args:
        profile: Perfil de rendimiento
        overrides: Valores a sobrescribir
    
    Returns:
        Configuración completa
    """
    if overrides:
        return RedundancyConfigProfile.merge_profiles(profile, overrides)
    return RedundancyConfigProfile.get_profile(profile)


def get_recommended_profile(
    use_case: str,
    data_size: int,
    memory_constraint: bool = False
) -> PerformanceProfile:
    """
    Recomienda un perfil según el caso de uso.
    
    Args:
        use_case: Caso de uso ("speed", "quality", "balanced", etc.)
        data_size: Tamaño de datos
        memory_constraint: Si hay restricciones de memoria
    
    Returns:
        Perfil recomendado
    """
    if memory_constraint:
        return PerformanceProfile.MEMORY_EFFICIENT
    
    use_case_lower = use_case.lower()
    
    if use_case_lower in ["speed", "fast", "quick"]:
        return PerformanceProfile.SPEED
    elif use_case_lower in ["quality", "accuracy", "precision"]:
        return PerformanceProfile.ACCURACY
    elif use_case_lower in ["balanced", "default", "general"]:
        return PerformanceProfile.BALANCED
    else:
        return PerformanceProfile.BALANCED


