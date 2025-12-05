#!/usr/bin/env python3
"""
Async Queue - Sistema de Colas Asíncronas
==========================================

Sistema de colas para procesamiento asíncrono de generación de videos.
"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import threading

from core.utils import setup_logger

logger = setup_logger(__name__)


class TaskStatus(Enum):
    """Estados de una tarea."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoGenerationTask:
    """Tarea de generación de video."""
    task_id: str
    task_type: str  # "text_to_video", "image_to_video", etc.
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0  # Mayor = más prioridad
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class AsyncVideoQueue:
    """
    Cola asíncrona para procesamiento de videos.
    
    Permite encolar tareas de generación de video y procesarlas
    de forma asíncrona con workers.
    """
    
    def __init__(
        self,
        max_workers: int = 2,
        max_queue_size: int = 100
    ):
        """
        Inicializa la cola asíncrona.
        
        Args:
            max_workers: Número máximo de workers
            max_queue_size: Tamaño máximo de la cola
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.tasks: Dict[str, VideoGenerationTask] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.lock = threading.Lock()
        
        self.processors: Dict[str, Callable] = {}
    
    def register_processor(
        self,
        task_type: str,
        processor: Callable
    ):
        """
        Registra un procesador para un tipo de tarea.
        
        Args:
            task_type: Tipo de tarea
            processor: Función procesadora (async)
        """
        self.processors[task_type] = processor
    
    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """
        Encola una tarea.
        
        Args:
            task_type: Tipo de tarea
            payload: Datos de la tarea
            priority: Prioridad (mayor = más prioridad)
        
        Returns:
            ID de la tarea
        """
        task_id = str(uuid.uuid4())
        
        task = VideoGenerationTask(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority
        )
        
        with self.lock:
            self.tasks[task_id] = task
        
        try:
            await self.queue.put((priority, task))
            logger.info(f"Tarea encolada: {task_id} ({task_type})")
        except asyncio.QueueFull:
            raise RuntimeError(f"Cola llena (max_size={self.max_queue_size})")
        
        return task_id
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de una tarea.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Estado de la tarea o None
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            return {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'status': task.status.value,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'result': task.result,
                'error': task.error,
                'retry_count': task.retry_count
            }
    
    async def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el resultado de una tarea completada.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Resultado o None
        """
        status = await self.get_status(task_id)
        if status and status['status'] == TaskStatus.COMPLETED.value:
            return status.get('result')
        return None
    
    async def cancel(self, task_id: str) -> bool:
        """
        Cancela una tarea pendiente.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            True si se canceló, False si no se pudo
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
        
        return False
    
    async def _worker(self, worker_id: int):
        """Worker que procesa tareas de la cola."""
        logger.info(f"Worker {worker_id} iniciado")
        
        while self.running:
            try:
                # Obtener tarea de la cola
                try:
                    priority, task = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Actualizar estado
                with self.lock:
                    task.status = TaskStatus.PROCESSING
                    task.started_at = datetime.now()
                
                # Procesar tarea
                processor = self.processors.get(task.task_type)
                if not processor:
                    error_msg = f"No hay procesador registrado para {task.task_type}"
                    logger.error(error_msg)
                    with self.lock:
                        task.status = TaskStatus.FAILED
                        task.error = error_msg
                        task.completed_at = datetime.now()
                    continue
                
                try:
                    result = await processor(task.payload)
                    
                    with self.lock:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        task.completed_at = datetime.now()
                    
                    logger.info(f"Tarea {task.task_id} completada")
                
                except Exception as e:
                    logger.error(f"Error procesando tarea {task.task_id}: {e}")
                    
                    with self.lock:
                        task.retry_count += 1
                        
                        if task.retry_count < task.max_retries:
                            task.status = TaskStatus.PENDING
                            await self.queue.put((task.priority, task))
                            logger.info(f"Reintentando tarea {task.task_id} ({task.retry_count}/{task.max_retries})")
                        else:
                            task.status = TaskStatus.FAILED
                            task.error = str(e)
                            task.completed_at = datetime.now()
                
                finally:
                    self.queue.task_done()
            
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelado")
                break
            except Exception as e:
                logger.error(f"Error en worker {worker_id}: {e}")
                await asyncio.sleep(1)
    
    def start(self):
        """Inicia los workers."""
        if self.running:
            logger.warning("Workers ya están ejecutándose")
            return
        
        self.running = True
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Iniciados {self.max_workers} workers")
    
    async def start_async(self):
        """Inicia los workers de forma asíncrona."""
        if self.running:
            return
        
        self.running = True
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Iniciados {self.max_workers} workers")
    
    async def stop(self, timeout: float = 30.0):
        """
        Detiene los workers.
        
        Args:
            timeout: Tiempo máximo de espera
        """
        if not self.running:
            return
        
        self.running = False
        
        # Cancelar workers
        for worker in self.workers:
            worker.cancel()
        
        # Esperar a que terminen
        await asyncio.wait_for(
            asyncio.gather(*self.workers, return_exceptions=True),
            timeout=timeout
        )
        
        self.workers.clear()
        logger.info("Workers detenidos")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la cola.
        
        Returns:
            Estadísticas
        """
        with self.lock:
            tasks_by_status = {}
            for status in TaskStatus:
                tasks_by_status[status.value] = sum(
                    1 for t in self.tasks.values() if t.status == status
                )
            
            return {
                'queue_size': self.queue.qsize(),
                'max_queue_size': self.max_queue_size,
                'max_workers': self.max_workers,
                'active_workers': len([w for w in self.workers if not w.done()]),
                'total_tasks': len(self.tasks),
                'tasks_by_status': tasks_by_status
            }


