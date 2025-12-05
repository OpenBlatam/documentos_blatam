#!/usr/bin/env python3
"""
Checkpointing Utilities for Paper Modules
=========================================

Utilidades avanzadas para checkpointing y serialización de modelos.
"""

import torch
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
import time
import hashlib
import json

from .paper_base import BasePaperModule, BasePaperConfig
from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


@dataclass
class CheckpointMetadata:
    """Metadatos de un checkpoint."""
    checkpoint_path: str
    timestamp: float
    epoch: Optional[int] = None
    step: Optional[int] = None
    loss: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    model_info: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    size_mb: float = 0.0


class CheckpointManager:
    """Gestor de checkpoints con versionado y gestión automática."""
    
    def __init__(
        self,
        checkpoint_dir: Union[str, Path],
        max_checkpoints: int = 5,
        keep_best: bool = True,
        metric_name: str = 'loss',
        mode: str = 'min'
    ):
        """
        Inicializa el gestor de checkpoints.
        
        Args:
            checkpoint_dir: Directorio donde guardar checkpoints
            max_checkpoints: Número máximo de checkpoints a mantener
            keep_best: Si True, siempre mantiene el mejor checkpoint
            metric_name: Nombre de la métrica para determinar el mejor
            mode: 'min' o 'max' para determinar el mejor
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = max_checkpoints
        self.keep_best = keep_best
        self.metric_name = metric_name
        self.mode = mode
        
        self.checkpoints: List[CheckpointMetadata] = []
        self.best_metric: Optional[float] = None
        self.best_checkpoint: Optional[str] = None
        
        self._load_checkpoint_index()
    
    def _load_checkpoint_index(self):
        """Carga el índice de checkpoints existentes."""
        index_path = self.checkpoint_dir / 'checkpoint_index.json'
        if index_path.exists():
            def _load_index():
                with open(index_path, 'r') as f:
                    data = json.load(f)
                    return {
                        'checkpoints': [
                            CheckpointMetadata(**ckpt) for ckpt in data.get('checkpoints', [])
                        ],
                        'best_metric': data.get('best_metric'),
                        'best_checkpoint': data.get('best_checkpoint')
                    }
            
            result, error = safe_execute(_load_index, default_value=None, log_errors=False)
            if result:
                self.checkpoints = result['checkpoints']
                self.best_metric = result['best_metric']
                self.best_checkpoint = result['best_checkpoint']
            elif error:
                logger.warning("Error cargando índice de checkpoints", error=str(error))
    
    def _save_checkpoint_index(self):
        """Guarda el índice de checkpoints."""
        index_path = self.checkpoint_dir / 'checkpoint_index.json'
        
        def _save_index():
            data = {
                'checkpoints': [
                    {
                        'checkpoint_path': ckpt.checkpoint_path,
                        'timestamp': ckpt.timestamp,
                        'epoch': ckpt.epoch,
                        'step': ckpt.step,
                        'loss': ckpt.loss,
                        'metrics': ckpt.metrics,
                        'model_info': ckpt.model_info,
                        'checksum': ckpt.checksum,
                        'size_mb': ckpt.size_mb
                    }
                    for ckpt in self.checkpoints
                ],
                'best_metric': self.best_metric,
                'best_checkpoint': self.best_checkpoint
            }
            with open(index_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        result, error = safe_execute(_save_index, default_value=None, log_errors=False)
        if error:
            logger.warning("Error guardando índice de checkpoints", error=str(error))
    
    def _compute_checksum(self, path: Path) -> str:
        """Calcula checksum de un archivo."""
        def _compute():
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        
        result, error = safe_execute(_compute, default_value='', log_errors=False)
        if error:
            logger.warning("Error calculando checksum", path=str(path), error=str(error))
            return ''
        return result
    
    def save_checkpoint(
        self,
        module: BasePaperModule,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        loss: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> str:
        """
        Guarda un checkpoint.
        
        Args:
            module: Módulo a guardar
            epoch: Época actual
            step: Paso actual
            loss: Pérdida actual
            metrics: Métricas adicionales
            name: Nombre del checkpoint (opcional)
        
        Returns:
            Ruta del checkpoint guardado
        
        Raises:
            ValueError: Si el módulo es None o inválido
        """
        if module is None:
            raise ValueError("module no puede ser None")
        
        if name is None:
            timestamp = int(time.time())
            name = f"checkpoint_{timestamp}"
        
        checkpoint_path = self.checkpoint_dir / f"{name}.pt"
        
        model_info = module.get_model_info()
        
        checkpoint_data = {
            'model_state_dict': module.state_dict(),
            'config': module.config.to_dict(),
            'model_class': module.__class__.__name__,
            'epoch': epoch,
            'step': step,
            'loss': loss,
            'metrics': metrics or {},
            'model_info': model_info,
            'timestamp': time.time()
        }
        
        torch.save(checkpoint_data, checkpoint_path)
        
        size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
        checksum = self._compute_checksum(checkpoint_path)
        
        metadata = CheckpointMetadata(
            checkpoint_path=str(checkpoint_path),
            timestamp=time.time(),
            epoch=epoch,
            step=step,
            loss=loss,
            metrics=metrics or {},
            model_info=model_info,
            checksum=checksum,
            size_mb=size_mb
        )
        
        self.checkpoints.append(metadata)
        
        if metrics and self.metric_name in metrics:
            metric_value = metrics[self.metric_name]
            is_best = False
            
            if self.best_metric is None:
                is_best = True
            elif self.mode == 'min' and metric_value < self.best_metric:
                is_best = True
            elif self.mode == 'max' and metric_value > self.best_metric:
                is_best = True
            
            if is_best:
                self.best_metric = metric_value
                self.best_checkpoint = str(checkpoint_path)
                logger.info("Nuevo mejor checkpoint", metric=self.metric_name, value=metric_value)
        
        self._cleanup_old_checkpoints()
        self._save_checkpoint_index()
        
        logger.info(
            "Checkpoint guardado",
            path=str(checkpoint_path),
            size_mb=size_mb,
            epoch=epoch,
            step=step
        )
        
        return str(checkpoint_path)
    
    def _cleanup_old_checkpoints(self):
        """Elimina checkpoints antiguos manteniendo los mejores."""
        if len(self.checkpoints) <= self.max_checkpoints:
            return
        
        checkpoints_to_keep = []
        
        if self.keep_best and self.best_checkpoint:
            best_ckpt = next(
                (ckpt for ckpt in self.checkpoints if ckpt.checkpoint_path == self.best_checkpoint),
                None
            )
            if best_ckpt:
                checkpoints_to_keep.append(best_ckpt)
        
        remaining = [ckpt for ckpt in self.checkpoints if ckpt not in checkpoints_to_keep]
        remaining.sort(key=lambda x: x.timestamp, reverse=True)
        
        checkpoints_to_keep.extend(remaining[:self.max_checkpoints - len(checkpoints_to_keep)])
        
        checkpoints_to_remove = [ckpt for ckpt in self.checkpoints if ckpt not in checkpoints_to_keep]
        
        for ckpt in checkpoints_to_remove:
            def _remove_checkpoint():
                Path(ckpt.checkpoint_path).unlink()
            
            result, error = safe_execute(_remove_checkpoint, default_value=None, log_errors=False)
            if result is not None:
                logger.debug("Checkpoint eliminado", path=ckpt.checkpoint_path)
            elif error:
                logger.warning("Error eliminando checkpoint", path=ckpt.checkpoint_path, error=str(error))
        
        self.checkpoints = checkpoints_to_keep
    
    def load_checkpoint(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        module_class: Optional[type] = None,
        config: Optional[BasePaperConfig] = None,
        load_best: bool = False
    ) -> Dict[str, Any]:
        """
        Carga un checkpoint.
        
        Args:
            checkpoint_path: Ruta del checkpoint (opcional si load_best=True)
            module_class: Clase del módulo (opcional)
            config: Configuración (opcional)
            load_best: Si True, carga el mejor checkpoint
        
        Returns:
            Diccionario con datos del checkpoint
        
        Raises:
            ValueError: Si no hay checkpoints disponibles
            FileNotFoundError: Si el checkpoint no existe
        """
        if load_best and self.best_checkpoint:
            checkpoint_path = self.best_checkpoint
        elif checkpoint_path is None:
            if self.checkpoints:
                checkpoint_path = self.checkpoints[-1].checkpoint_path
            else:
                raise ValueError("No hay checkpoints disponibles")
        
        checkpoint_path = Path(checkpoint_path)
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint no encontrado: {checkpoint_path}")
        
        checkpoint_data = torch.load(checkpoint_path, map_location='cpu')
        
        if self.checkpoints:
            ckpt_meta = next(
                (ckpt for ckpt in self.checkpoints if ckpt.checkpoint_path == str(checkpoint_path)),
                None
            )
            if ckpt_meta:
                current_checksum = self._compute_checksum(checkpoint_path)
                if current_checksum != ckpt_meta.checksum:
                    logger.warning("Checksum no coincide", path=str(checkpoint_path))
        
        logger.info("Checkpoint cargado", path=str(checkpoint_path))
        
        return checkpoint_data
    
    def list_checkpoints(self) -> List[CheckpointMetadata]:
        """Lista todos los checkpoints disponibles."""
        return sorted(self.checkpoints, key=lambda x: x.timestamp, reverse=True)
    
    def get_best_checkpoint(self) -> Optional[str]:
        """Obtiene la ruta del mejor checkpoint."""
        return self.best_checkpoint


def save_checkpoint(
    module: BasePaperModule,
    path: Union[str, Path],
    epoch: Optional[int] = None,
    step: Optional[int] = None,
    loss: Optional[float] = None,
    metrics: Optional[Dict[str, Any]] = None
) -> str:
    """
    Guarda un checkpoint simple.
    
    Args:
        module: Módulo a guardar
        path: Ruta donde guardar
        epoch: Época actual
        step: Paso actual
        loss: Pérdida actual
        metrics: Métricas adicionales
    
    Returns:
        Ruta del checkpoint guardado
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    checkpoint_data = {
        'model_state_dict': module.state_dict(),
        'config': module.config.to_dict(),
        'model_class': module.__class__.__name__,
        'epoch': epoch,
        'step': step,
        'loss': loss,
        'metrics': metrics or {},
        'model_info': module.get_model_info(),
        'timestamp': time.time()
    }
    
    torch.save(checkpoint_data, path)
    logger.info("Checkpoint guardado", path=str(path))
    
    return str(path)


def load_checkpoint(
    path: Union[str, Path],
    module_class: Optional[type] = None,
    config: Optional[BasePaperConfig] = None,
    device: str = 'cpu'
) -> Dict[str, Any]:
    """
    Carga un checkpoint simple.
    
    Args:
        path: Ruta del checkpoint
        module_class: Clase del módulo (opcional)
        config: Configuración (opcional)
        device: Dispositivo donde cargar
    
    Returns:
        Diccionario con datos del checkpoint
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint no encontrado: {path}")
    
    checkpoint_data = torch.load(path, map_location=device)
    logger.info("Checkpoint cargado", path=str(path))
    
    return checkpoint_data

