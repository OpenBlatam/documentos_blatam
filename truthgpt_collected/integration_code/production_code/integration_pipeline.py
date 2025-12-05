#!/usr/bin/env python3
"""
Pipeline de Integración General
================================

Sistema unificado que integra todos los módulos (memory, redundancy, sora, chat)
para crear un pipeline completo de procesamiento.

Este módulo proporciona:
- Factory function para crear pipelines integrados
- Integración de múltiples módulos (memory, redundancy, sora, chat)
- Funciones de utilidad para verificar disponibilidad
- Validación robusta de configuraciones

Ejemplo:
    >>> pipeline = create_integrated_pipeline(
    ...     enable_memory=True,
    ...     enable_redundancy=True
    ... )
    >>> output, metadata = pipeline.process_pipeline(data)
"""

__version__ = '2.0.0'

from typing import Dict, List, Tuple, Optional, Any, Union
import torch
import torch.nn as nn
from pathlib import Path
import time

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)

# Importar gestor de configuración opcional
try:
    from core.config_manager import get_config_manager, ModuleType
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Importar módulos opcionales
try:
    from memory import (
        Paper2506_15841v2_MemorySystem,
        Paper2506_15841v2Config,
        create_memory_system
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from redundancy import (
        Paper2510_00071_RedundancySuppressor,
        Paper2510_00071Config,
        create_redundancy_suppressor
    )
    REDUNDANCY_AVAILABLE = True
except ImportError:
    REDUNDANCY_AVAILABLE = False

try:
    from sora import (
        VideoGenerationModule,
        VideoGenerationConfig,
        create_sora_integrated
    )
    SORA_AVAILABLE = True
except ImportError:
    SORA_AVAILABLE = False

try:
    from core.chat_engine import ChatEngine
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False


class IntegratedPipeline:
    """
    Pipeline completo que integra todos los módulos.
    
    Características:
    - Memoria para contexto persistente
    - Redundancia para eficiencia
    - Generación de video
    - Chat con memoria
    """
    
    def __init__(
        self,
        memory_config: Optional[Any] = None,
        redundancy_config: Optional[Any] = None,
        video_config: Optional[Any] = None,
        chat_config: Optional[Dict] = None,
        enable_memory: bool = True,
        enable_redundancy: bool = True,
        enable_video: bool = False,
        enable_chat: bool = False
    ):
        """
        Inicializa pipeline integrado.
        
        Args:
            memory_config: Configuración de memoria
            redundancy_config: Configuración de redundancia
            video_config: Configuración de video
            chat_config: Configuración de chat
            enable_memory: Habilitar memoria
            enable_redundancy: Habilitar redundancia
            enable_video: Habilitar generación de video
            enable_chat: Habilitar chat
        """
        self.enable_memory = enable_memory and MEMORY_AVAILABLE
        self.enable_redundancy = enable_redundancy and REDUNDANCY_AVAILABLE
        self.enable_video = enable_video and SORA_AVAILABLE
        self.enable_chat = enable_chat and CHAT_AVAILABLE
        
        # Inicializar memoria
        if self.enable_memory:
            if memory_config is None:
                memory_config = Paper2506_15841v2Config(
                    memory_dim=512,
                    max_memory_size=10000,
                    enable_cache=True,
                    enable_persistence=True
                )
            self.memory_system = create_memory_system("2506_15841v2", **memory_config.__dict__ if hasattr(memory_config, '__dict__') else {})
        else:
            self.memory_system = None
        
        # Inicializar redundancia
        if self.enable_redundancy:
            if redundancy_config is None:
                redundancy_config = Paper2510_00071Config(
                    similarity_threshold=0.85,
                    enable_caching=True
                )
            self.redundancy_suppressor = create_redundancy_suppressor("2510_00071", **redundancy_config.__dict__ if hasattr(redundancy_config, '__dict__') else {})
        else:
            self.redundancy_suppressor = None
        
        # Inicializar video
        if self.enable_video:
            if video_config is None:
                video_config = VideoGenerationConfig(
                    hidden_dim=512,
                    video_length=16
                )
            self.video_module = create_sora_integrated(video_config, memory_config, redundancy_config)
        else:
            self.video_module = None
        
        # Inicializar chat
        if self.enable_chat:
            chat_kwargs = chat_config or {}
            self.chat_engine = ChatEngine(**chat_kwargs)
        else:
            self.chat_engine = None
        
        # Métricas
        self.processing_stats = {
            'total_processed': 0,
            'memory_operations': 0,
            'redundancy_operations': 0,
            'video_generations': 0,
            'chat_interactions': 0
        }
        
        logger.info(
            "Pipeline integrado inicializado",
            memory=self.enable_memory,
            redundancy=self.enable_redundancy,
            video=self.enable_video,
            chat=self.enable_chat
        )
    
    def process_with_memory(
        self,
        data: torch.Tensor,
        metadata: Optional[Dict] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa datos con memoria integrada.
        
        Args:
            data: Tensor de datos
            metadata: Metadata adicional
        
        Returns:
            Tuple (output, metadata)
        """
        if not self.enable_memory or not self.memory_system:
            return data, {'memory_used': False}
        
        with torch.no_grad():
            # Almacenar en memoria
            if data.dim() >= 2:
                query = data.view(data.size(0), -1).mean(dim=0)  # Promedio global
                self.memory_system.store_episode(query, metadata=metadata)
                self.processing_stats['memory_operations'] += 1
            
            # Recuperar contexto
            if data.dim() >= 2:
                query = data.view(data.size(0), -1).mean(dim=0)
                retrieved, weights = self.memory_system.retrieve_episodes(query, k=5)
                
                if retrieved.size(0) > 0 and retrieved.size(1) > 0:
                    # Integrar memoria
                    memory_contribution = (retrieved * weights.unsqueeze(-1)).sum(dim=1)
                    # Expandir a forma de data
                    while memory_contribution.dim() < data.dim():
                        memory_contribution = memory_contribution.unsqueeze(0)
                    
                    # Ajustar tamaño
                    if memory_contribution.shape[-1] == data.shape[-1]:
                        data = data + memory_contribution * 0.1
        
        return data, {
            'memory_used': True,
            'memory_episodes': len(self.memory_system.episodic_memory) if self.memory_system else 0
        }
    
    def process_with_redundancy(
        self,
        data: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa datos eliminando redundancias.
        
        Args:
            data: Tensor de datos [batch, ...]
        
        Returns:
            Tuple (output, metadata)
        """
        if not self.enable_redundancy or not self.redundancy_suppressor:
            return data, {'redundancy_used': False}
        
        # Aplanar para procesamiento
        original_shape = data.shape
        batch_size = data.size(0)
        
        if batch_size <= 1:
            return data, {'redundancy_used': False}
        
        with torch.no_grad():
            # Reshape a [batch, seq, features]
            flattened = data.view(batch_size, -1, data.numel() // batch_size)
            
            # Aplicar supresión de redundancia
            unique_data, stats = self.redundancy_suppressor.process_bulk(flattened)
            
            # Reshape de vuelta
            unique_data = unique_data.view(-1, *original_shape[1:])
        
        self.processing_stats['redundancy_operations'] += 1
        
        return unique_data, {
            'redundancy_used': True,
            'redundancy_stats': stats
        }
    
    def generate_video(
        self,
        prompt: Optional[str] = None,
        image: Optional[torch.Tensor] = None
    ) -> Tuple[Optional[torch.Tensor], Dict[str, Any]]:
        """
        Genera video usando el módulo Sora.
        
        Args:
            prompt: Prompt de texto (opcional)
            image: Imagen inicial (opcional)
        
        Returns:
            Tuple (video, metadata)
        """
        if not self.enable_video or not self.video_module:
            return None, {'video_generated': False}
        
        try:
            if prompt:
                video, metadata = self.video_module.generate_from_text(prompt)
            elif image is not None:
                video, metadata = self.video_module.generate_from_image(image)
            else:
                return None, {'error': 'Se requiere prompt o image'}
            
            self.processing_stats['video_generations'] += 1
            
            return video, {
                'video_generated': True,
                **metadata
            }
        except Exception as e:
            logger.error(f"Error generando video: {e}")
            return None, {'error': str(e)}
    
    def chat_with_memory(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat con memoria integrada.
        
        Args:
            message: Mensaje del usuario
            conversation_id: ID de conversación
        
        Returns:
            Diccionario con respuesta y metadata
        """
        if not self.enable_chat or not self.chat_engine:
            return {'error': 'Chat no disponible'}
        
        try:
            # Chat normal
            response = self.chat_engine.chat(message, conversation_id=conversation_id)
            
            # Almacenar en memoria si está disponible
            if self.enable_memory and self.memory_system:
                # Crear embedding del mensaje
                import hashlib
                message_hash = hashlib.sha256(message.encode()).digest()
                message_embedding = torch.as_tensor([b / 255.0 for b in message_hash[:512]], dtype=torch.float32)
                
                with torch.no_grad():
                    self.memory_system.store_episode(
                        message_embedding,
                        metadata={
                            'message': message,
                            'response': response,
                            'conversation_id': conversation_id
                        }
                    )
            
            self.processing_stats['chat_interactions'] += 1
            
            return {
                'response': response,
                'memory_used': self.enable_memory,
                'conversation_id': conversation_id
            }
        except Exception as e:
            logger.error(f"Error en chat: {e}")
            return {'error': str(e)}
    
    def process_pipeline(
        self,
        data: torch.Tensor,
        use_memory: bool = True,
        use_redundancy: bool = True
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Procesa datos a través del pipeline completo.
        
        Args:
            data: Tensor de datos
            use_memory: Usar memoria
            use_redundancy: Usar redundancia
        
        Returns:
            Tuple (output, metadata)
        """
        metadata = {}
        output = data
        
        # 1. Redundancia (primero para reducir datos)
        if use_redundancy:
            output, redundancy_metadata = self.process_with_redundancy(output)
            metadata.update(redundancy_metadata)
        
        # 2. Memoria (después para contexto)
        if use_memory:
            output, memory_metadata = self.process_with_memory(output)
            metadata.update(memory_metadata)
        
        self.processing_stats['total_processed'] += 1
        
        return output, metadata
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del pipeline.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            **self.processing_stats,
            'modules_enabled': {
                'memory': self.enable_memory,
                'redundancy': self.enable_redundancy,
                'video': self.enable_video,
                'chat': self.enable_chat
            }
        }
        
        # Estadísticas de memoria
        if self.enable_memory and self.memory_system:
            memory_stats = self.memory_system.get_episodic_stats()
            stats['memory_stats'] = memory_stats
        
        # Estadísticas de redundancia
        if self.enable_redundancy and self.redundancy_suppressor:
            redundancy_stats = self.redundancy_suppressor.get_metrics()
            stats['redundancy_stats'] = redundancy_stats
        
        return stats
    
    def save_pipeline_state(self, filepath: str) -> bool:
        """
        Guarda estado del pipeline.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            state = {
                'stats': self.processing_stats,
                'config': {
                    'memory_enabled': self.enable_memory,
                    'redundancy_enabled': self.enable_redundancy,
                    'video_enabled': self.enable_video,
                    'chat_enabled': self.enable_chat
                }
            }
            
            import json
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.info(f"Estado del pipeline guardado en {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error guardando estado: {e}")
            return False


def get_available_modules() -> Dict[str, bool]:
    """
    Obtiene el estado de disponibilidad de todos los módulos.
    
    Returns:
        Diccionario con el estado de disponibilidad de cada módulo.
        
    Example:
        >>> modules = get_available_modules()
        >>> if modules['memory']:
        ...     print("Módulo de memoria disponible")
    """
    return {
        'memory': MEMORY_AVAILABLE,
        'redundancy': REDUNDANCY_AVAILABLE,
        'sora': SORA_AVAILABLE,
        'chat': CHAT_AVAILABLE,
        'config_manager': CONFIG_MANAGER_AVAILABLE
    }


def recommend_pipeline_config(
    priority: str = 'balanced',
    use_memory: bool = True,
    use_redundancy: bool = True
) -> Dict[str, Any]:
    """
    Recomienda configuración de pipeline basada en prioridad.
    
    Args:
        priority: Prioridad deseada ('performance', 'memory', 'balanced')
        use_memory: Si se usará memoria
        use_redundancy: Si se usará redundancia
    
    Returns:
        Diccionario con configuración recomendada.
        
    Raises:
        ValueError: Si priority no es válido.
        
    Example:
        >>> config = recommend_pipeline_config(priority='performance')
        >>> pipeline = create_integrated_pipeline(**config)
    """
    if priority not in ['performance', 'memory', 'balanced']:
        raise ValueError(f"priority debe ser 'performance', 'memory' o 'balanced', recibido: {priority}")
    
    if priority == 'performance':
        return {
            'enable_memory': use_memory and MEMORY_AVAILABLE,
            'enable_redundancy': use_redundancy and REDUNDANCY_AVAILABLE,
            'enable_video': False,
            'enable_chat': False
        }
    elif priority == 'memory':
        return {
            'enable_memory': use_memory and MEMORY_AVAILABLE,
            'enable_redundancy': False,
            'enable_video': False,
            'enable_chat': False
        }
    else:  # balanced
        return {
            'enable_memory': use_memory and MEMORY_AVAILABLE,
            'enable_redundancy': use_redundancy and REDUNDANCY_AVAILABLE,
            'enable_video': False,
            'enable_chat': False
        }


def create_integrated_pipeline(
    enable_memory: bool = True,
    enable_redundancy: bool = True,
    enable_video: bool = False,
    enable_chat: bool = False,
    use_config_manager: bool = True,
    **config_kwargs
) -> Optional[IntegratedPipeline]:
    """
    Factory function para crear pipeline integrado.
    
    Args:
        enable_memory: Habilitar memoria (default: True)
        enable_redundancy: Habilitar redundancia (default: True)
        enable_video: Habilitar video (default: False)
        enable_chat: Habilitar chat (default: False)
        use_config_manager: Usar gestor de configuración si está disponible (default: True)
        **config_kwargs: Configuraciones adicionales (memory_config, redundancy_config, etc.)
    
    Returns:
        Instancia de IntegratedPipeline o None si hay error.
        
    Raises:
        ValueError: Si los parámetros booleanos no son válidos.
        
    Example:
        >>> # Pipeline básico con memoria y redundancia
        >>> pipeline = create_integrated_pipeline()
        >>> 
        >>> # Pipeline completo
        >>> pipeline = create_integrated_pipeline(
        ...     enable_memory=True,
        ...     enable_redundancy=True,
        ...     enable_video=True,
        ...     enable_chat=True
        ... )
        >>> 
        >>> # Con configuraciones personalizadas
        >>> from memory import Paper2506_15841v2Config
        >>> memory_config = Paper2506_15841v2Config(memory_dim=1024)
        >>> pipeline = create_integrated_pipeline(
        ...     memory_config=memory_config
        ... )
    """
    # Validación de entrada
    if not isinstance(enable_memory, bool):
        raise ValueError(f"enable_memory debe ser bool, recibido: {type(enable_memory).__name__}")
    if not isinstance(enable_redundancy, bool):
        raise ValueError(f"enable_redundancy debe ser bool, recibido: {type(enable_redundancy).__name__}")
    if not isinstance(enable_video, bool):
        raise ValueError(f"enable_video debe ser bool, recibido: {type(enable_video).__name__}")
    if not isinstance(enable_chat, bool):
        raise ValueError(f"enable_chat debe ser bool, recibido: {type(enable_chat).__name__}")
    if not isinstance(use_config_manager, bool):
        raise ValueError(f"use_config_manager debe ser bool, recibido: {type(use_config_manager).__name__}")
    
    try:
        # Usar gestor de configuración si está disponible y no se proporcionaron configs
        if use_config_manager and CONFIG_MANAGER_AVAILABLE and not any([
            'memory_config' in config_kwargs,
            'redundancy_config' in config_kwargs,
            'video_config' in config_kwargs,
            'chat_config' in config_kwargs
        ]):
            config_manager = get_config_manager()
            
            # Obtener configuraciones desde gestor
            if 'memory_config' not in config_kwargs:
                memory_config_dict = config_manager.get_config(ModuleType.MEMORY)
                if memory_config_dict:
                    from memory import Paper2506_15841v2Config
                    config_kwargs['memory_config'] = Paper2506_15841v2Config(**memory_config_dict)
            
            if 'redundancy_config' not in config_kwargs:
                redundancy_config_dict = config_manager.get_config(ModuleType.REDUNDANCY)
                if redundancy_config_dict:
                    from redundancy import Paper2510_00071Config
                    config_kwargs['redundancy_config'] = Paper2510_00071Config(**redundancy_config_dict)
        
        memory_config = config_kwargs.get('memory_config')
        redundancy_config = config_kwargs.get('redundancy_config')
        video_config = config_kwargs.get('video_config')
        chat_config = config_kwargs.get('chat_config')
        
        pipeline = IntegratedPipeline(
            memory_config=memory_config,
            redundancy_config=redundancy_config,
            video_config=video_config,
            chat_config=chat_config,
            enable_memory=enable_memory,
            enable_redundancy=enable_redundancy,
            enable_video=enable_video,
            enable_chat=enable_chat
        )
        
        logger.info(
            "Pipeline integrado creado exitosamente",
            memory=enable_memory and MEMORY_AVAILABLE,
            redundancy=enable_redundancy and REDUNDANCY_AVAILABLE,
            video=enable_video and SORA_AVAILABLE,
            chat=enable_chat and CHAT_AVAILABLE
        )
        
        return pipeline
    
    except Exception as e:
        logger.error(
            f"Error creando pipeline integrado: {e}",
            exc_info=True,
            enable_memory=enable_memory,
            enable_redundancy=enable_redundancy,
            enable_video=enable_video,
            enable_chat=enable_chat
        )
        return None


# Exportar funciones y clases principales
__all__ = [
    'IntegratedPipeline',
    'create_integrated_pipeline',
    'get_available_modules',
    'recommend_pipeline_config',
    'MEMORY_AVAILABLE',
    'REDUNDANCY_AVAILABLE',
    'SORA_AVAILABLE',
    'CHAT_AVAILABLE',
    'CONFIG_MANAGER_AVAILABLE',
    '__version__'
]

