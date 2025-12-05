#!/usr/bin/env python3
"""
Sistema de Almacenamiento para la API Multimodal.

Maneja el almacenamiento de archivos generados (videos, imágenes, audio).
"""

from typing import Optional, Dict, Any
from pathlib import Path
import shutil
import uuid
from datetime import datetime
import hashlib

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class StorageManager:
    """Gestor de almacenamiento de archivos."""
    
    def __init__(
        self,
        base_path: str = "./storage",
        url_prefix: str = "/storage"
    ):
        """
        Inicializa el gestor de almacenamiento.
        
        Args:
            base_path: Ruta base para almacenamiento
            url_prefix: Prefijo para URLs
        """
        self.base_path = Path(base_path)
        self.url_prefix = url_prefix
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Crear subdirectorios
        (self.base_path / "videos").mkdir(exist_ok=True)
        (self.base_path / "images").mkdir(exist_ok=True)
        (self.base_path / "audio").mkdir(exist_ok=True)
        (self.base_path / "3d").mkdir(exist_ok=True)
        (self.base_path / "temp").mkdir(exist_ok=True)
    
    def save_file(
        self,
        file_path: Path,
        modality: str,
        task_id: Optional[str] = None,
        extension: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Guarda un archivo generado.
        
        Args:
            file_path: Ruta del archivo a guardar
            modality: Modalidad (video, image, audio, 3d)
            task_id: ID de la tarea (opcional)
            extension: Extensión del archivo (opcional)
        
        Returns:
            Información del archivo guardado
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Determinar extensión
        if not extension:
            extension = file_path.suffix or ".bin"
        
        # Generar nombre único
        if task_id:
            filename = f"{task_id}{extension}"
        else:
            filename = f"{uuid.uuid4()}{extension}"
        
        # Ruta de destino
        modality_dir = self.base_path / modality
        destination = modality_dir / filename
        
        # Copiar archivo
        shutil.copy2(file_path, destination)
        
        # Generar URL
        url = f"{self.url_prefix}/{modality}/{filename}"
        
        # Calcular hash
        file_hash = self._calculate_hash(destination)
        
        # Obtener tamaño
        size = destination.stat().st_size
        
        logger.info(f"Archivo guardado: {destination} ({size} bytes)")
        
        return {
            "path": str(destination),
            "url": url,
            "filename": filename,
            "size": size,
            "hash": file_hash,
            "modality": modality,
            "saved_at": datetime.now().isoformat()
        }
    
    def get_file(self, modality: str, filename: str) -> Optional[Path]:
        """
        Obtiene la ruta de un archivo.
        
        Args:
            modality: Modalidad
            filename: Nombre del archivo
        
        Returns:
            Path del archivo o None
        """
        file_path = self.base_path / modality / filename
        
        if file_path.exists():
            return file_path
        
        return None
    
    def delete_file(self, modality: str, filename: str) -> bool:
        """
        Elimina un archivo.
        
        Args:
            modality: Modalidad
            filename: Nombre del archivo
        
        Returns:
            True si se eliminó correctamente
        """
        file_path = self.base_path / modality / filename
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Archivo eliminado: {file_path}")
            return True
        
        return False
    
    def cleanup_old_files(self, days: int = 7) -> int:
        """
        Limpia archivos antiguos.
        
        Args:
            days: Días de antigüedad para eliminar
        
        Returns:
            Número de archivos eliminados
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        for modality_dir in [self.base_path / m for m in ["videos", "images", "audio", "3d"]]:
            if not modality_dir.exists():
                continue
            
            for file_path in modality_dir.iterdir():
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        file_path.unlink()
                        deleted += 1
        
        logger.info(f"Eliminados {deleted} archivos antiguos")
        return deleted
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de almacenamiento.
        
        Returns:
            Estadísticas
        """
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_modality": {}
        }
        
        for modality in ["videos", "images", "audio", "3d"]:
            modality_dir = self.base_path / modality
            if not modality_dir.exists():
                continue
            
            files = list(modality_dir.iterdir())
            size = sum(f.stat().st_size for f in files if f.is_file())
            
            stats["by_modality"][modality] = {
                "count": len([f for f in files if f.is_file()]),
                "size": size
            }
            
            stats["total_files"] += stats["by_modality"][modality]["count"]
            stats["total_size"] += size
        
        return stats
    
    def _calculate_hash(self, file_path: Path) -> str:
        """
        Calcula hash SHA256 de un archivo.
        
        Args:
            file_path: Ruta del archivo
        
        Returns:
            Hash hexadecimal
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()


