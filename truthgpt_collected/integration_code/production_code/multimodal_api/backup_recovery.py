#!/usr/bin/env python3
"""
Sistema de Backup y Recovery para la API Multimodal.

Permite hacer backup y restaurar el estado del sistema.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadatos de un backup."""
    backup_id: str
    timestamp: datetime
    version: str
    components: List[str]
    size_bytes: int
    description: Optional[str] = None


class BackupManager:
    """Gestor de backups."""
    
    def __init__(self, backup_dir: str = "./backups"):
        """
        Inicializa el gestor de backups.
        
        Args:
            backup_dir: Directorio para backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backups: Dict[str, BackupMetadata] = {}
        self._load_backup_index()
    
    def _load_backup_index(self):
        """Carga el índice de backups."""
        index_file = self.backup_dir / "backup_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    for backup_id, metadata in data.items():
                        self.backups[backup_id] = BackupMetadata(**metadata)
            except Exception as e:
                logger.warning(f"Error cargando índice de backups: {e}")
    
    def _save_backup_index(self):
        """Guarda el índice de backups."""
        index_file = self.backup_dir / "backup_index.json"
        try:
            data = {
                backup_id: {
                    **asdict(metadata),
                    "timestamp": metadata.timestamp.isoformat()
                }
                for backup_id, metadata in self.backups.items()
            }
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando índice de backups: {e}")
    
    def create_backup(
        self,
        components: Dict[str, Any],
        description: Optional[str] = None
    ) -> str:
        """
        Crea un backup.
        
        Args:
            components: Componentes a respaldar
            description: Descripción del backup
        
        Returns:
            ID del backup
        """
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_file = self.backup_dir / f"{backup_id}.json"
        
        try:
            # Serializar componentes
            serialized = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "components": {}
            }
            
            total_size = 0
            component_names = []
            
            for name, data in components.items():
                # Serializar datos
                if hasattr(data, '__dict__'):
                    serialized_data = asdict(data) if hasattr(data, '__dict__') else str(data)
                elif isinstance(data, dict):
                    serialized_data = data
                else:
                    serialized_data = str(data)
                
                serialized["components"][name] = serialized_data
                component_names.append(name)
                total_size += len(json.dumps(serialized_data))
            
            # Guardar backup
            with open(backup_file, 'w') as f:
                json.dump(serialized, f, indent=2)
            
            # Crear metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.now(),
                version="1.0.0",
                components=component_names,
                size_bytes=total_size,
                description=description
            )
            
            self.backups[backup_id] = metadata
            self._save_backup_index()
            
            logger.info(f"Backup creado: {backup_id}")
            return backup_id
        
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            raise
    
    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Restaura un backup.
        
        Args:
            backup_id: ID del backup
        
        Returns:
            Componentes restaurados
        """
        if backup_id not in self.backups:
            raise ValueError(f"Backup {backup_id} no encontrado")
        
        backup_file = self.backup_dir / f"{backup_id}.json"
        if not backup_file.exists():
            raise FileNotFoundError(f"Archivo de backup {backup_id} no encontrado")
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            logger.info(f"Restaurando backup: {backup_id}")
            return backup_data.get("components", {})
        
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Lista todos los backups.
        
        Returns:
            Lista de backups
        """
        return [
            {
                **asdict(metadata),
                "timestamp": metadata.timestamp.isoformat()
            }
            for metadata in self.backups.values()
        ]
    
    def delete_backup(self, backup_id: str):
        """
        Elimina un backup.
        
        Args:
            backup_id: ID del backup
        """
        if backup_id not in self.backups:
            raise ValueError(f"Backup {backup_id} no encontrado")
        
        backup_file = self.backup_dir / f"{backup_id}.json"
        if backup_file.exists():
            backup_file.unlink()
        
        del self.backups[backup_id]
        self._save_backup_index()
        
        logger.info(f"Backup eliminado: {backup_id}")
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un backup.
        
        Args:
            backup_id: ID del backup
        
        Returns:
            Información del backup o None
        """
        if backup_id not in self.backups:
            return None
        
        metadata = self.backups[backup_id]
        return {
            **asdict(metadata),
            "timestamp": metadata.timestamp.isoformat()
        }

