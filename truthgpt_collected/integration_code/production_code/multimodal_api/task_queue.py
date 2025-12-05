#!/usr/bin/env python3
"""
Sistema de Cola de Tareas para Procesamiento Asíncrono.

Maneja la cola de tareas de generación de forma asíncrona.
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio
import uuid
import threading
from queue import Queue, PriorityQueue

try:
    from core.utils import setup_logger, async_safe_execute
    logger = setup_logger(__name__)
except ImportError:
    import logging
    import asyncio
    logger = logging.getLogger(__name__)
    
    async def async_safe_execute(func, default_value=None, log_errors=True, *args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result, None
        except Exception as e:
            if log_errors:
                logger.error(f"Error en {func.__name__}: {e}")
            return default_value, e

try:
    from .websocket_manager import connection_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    connection_manager = None


class TaskPriority(Enum):
    """Prioridades de tarea."""
    LOW = 10
    NORMAL = 5
    HIGH = 3
    URGENT = 1


@dataclass
class Task:
    """Representa una tarea de generación."""
    task_id: str
    modality: str
    generation_type: str
    prompt: str
    parameters: Dict[str, Any]
    priority: int
    callback_url: Optional[str] = None
    created_at: datetime = None
    status: str = "pending"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __lt__(self, other):
        """Comparación para PriorityQueue."""
        return self.priority < other.priority


class TaskQueue:
    """Cola de tareas con priorización."""
    
    def __init__(self, max_workers: int = 4):
        """
        Inicializa la cola de tareas.
        
        Args:
            max_workers: Número máximo de workers concurrentes
        """
        self.queue: PriorityQueue = PriorityQueue()
        self.tasks: Dict[str, Task] = {}
        self.max_workers = max_workers
        self.workers: list = []
        self.running = False
        self.lock = threading.Lock()
        self.processors: Dict[str, Callable] = {}
    
    def register_processor(
        self,
        modality: str,
        processor: Callable
    ):
        """
        Registra un procesador para una modalidad.
        
        Args:
            modality: Modalidad (video, image, audio, etc.)
            processor: Función que procesa la tarea
        """
        self.processors[modality] = processor
        logger.info(f"Procesador registrado para modalidad: {modality}")
    
    def add_task(
        self,
        modality: str,
        generation_type: str,
        prompt: str,
        parameters: Dict[str, Any],
        priority: int = 5,
        callback_url: Optional[str] = None
    ) -> str:
        """
        Agrega una tarea a la cola.
        
        Args:
            modality: Modalidad de generación
            generation_type: Tipo de generación
            prompt: Prompt de generación
            parameters: Parámetros
            priority: Prioridad (1-10, menor es más alta)
            callback_url: URL de callback opcional
        
        Returns:
            ID de la tarea
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            modality=modality,
            generation_type=generation_type,
            prompt=prompt,
            parameters=parameters,
            priority=priority,
            callback_url=callback_url
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.queue.put((priority, task))
        
        logger.info(f"Tarea agregada a la cola: {task_id} (prioridad: {priority})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Obtiene una tarea por ID.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Tarea o None
        """
        return self.tasks.get(task_id)
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        progress: Optional[float] = None
    ):
        """
        Actualiza el estado de una tarea.
        
        Args:
            task_id: ID de la tarea
            status: Nuevo estado
            result: Resultado (opcional)
            error: Error (opcional)
            progress: Progreso 0-100 (opcional)
        """
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                if result:
                    task.parameters["result"] = result
                if error:
                    task.parameters["error"] = error
                if progress is not None:
                    task.parameters["progress"] = progress
    
    async def _process_task(self, task: Task):
        """
        Procesa una tarea.
        
        Args:
            task: Tarea a procesar
        """
        try:
            from core.utils import async_safe_execute
            
            logger.info(f"Procesando tarea: {task.task_id}")
            self.update_task_status(task.task_id, "processing", progress=0.0)
            
            # Notificar inicio vía WebSocket
            if WEBSOCKET_AVAILABLE:
                await async_safe_execute(
                    connection_manager.broadcast_to_task,
                    default_value=None,
                    log_errors=False,
                    task_id=task.task_id,
                    message={
                        "type": "task_started",
                        "task_id": task.task_id,
                        "progress": 0.0,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Obtener procesador para la modalidad
            processor = self.processors.get(task.modality)
            if not processor:
                raise ValueError(f"No hay procesador para modalidad: {task.modality}")
            
            # Procesar de forma segura
            result, proc_error = await async_safe_execute(
                processor,
                default_value=None,
                log_errors=False,
                prompt=task.prompt,
                parameters=task.parameters
            )
            
            if proc_error:
                raise proc_error
            
            # Actualizar estado
            self.update_task_status(
                task.task_id,
                "completed",
                result=result,
                progress=100.0
            )
            
            # Notificar vía WebSocket
            if WEBSOCKET_AVAILABLE:
                await async_safe_execute(
                    connection_manager.broadcast_to_task,
                    default_value=None,
                    log_errors=False,
                    task_id=task.task_id,
                    message={
                        "type": "task_completed",
                        "task_id": task.task_id,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Enviar webhooks
            webhook_manager = getattr(self, '_webhook_manager', None)
            if webhook_manager:
                await async_safe_execute(
                    webhook_manager.send_webhook,
                    default_value={},
                    log_errors=False,
                    event="task.completed",
                    task_id=task.task_id,
                    data={"result": result}
                )
            
            # Callback si existe
            if task.callback_url:
                await async_safe_execute(
                    self._send_callback,
                    default_value=None,
                    log_errors=False,
                    url=task.callback_url,
                    task_id=task.task_id,
                    result=result
                )
            
            # Registrar en analytics
            try:
                analytics_ref = getattr(self, '_analytics_ref', None)
                if analytics_ref:
                    analytics_ref.record_task(
                        task_id=task.task_id,
                        modality=task.modality,
                        status="completed",
                        processing_time=None,  # Se puede calcular del tiempo total
                        error=None
                    )
            except Exception as e:
                logger.debug(f"No se pudo registrar tarea en analytics: {e}")
            
            logger.info(f"Tarea completada: {task.task_id}")
        
        except Exception as e:
            logger.error(f"Error procesando tarea {task.task_id}: {e}")
            self.update_task_status(
                task.task_id,
                "failed",
                error=str(e)
            )
            
            # Registrar en analytics
            try:
                analytics_ref = getattr(self, '_analytics_ref', None)
                if analytics_ref:
                    analytics_ref.record_task(
                        task_id=task.task_id,
                        modality=task.modality,
                        status="failed",
                        processing_time=None,
                        error=str(e)
                    )
            except Exception as e2:
                logger.debug(f"No se pudo registrar tarea fallida en analytics: {e2}")
            
            # Notificar vía WebSocket
            if WEBSOCKET_AVAILABLE:
                await async_safe_execute(
                    connection_manager.broadcast_to_task,
                    default_value=None,
                    log_errors=False,
                    task_id=task.task_id,
                    message={
                        "type": "task_failed",
                        "task_id": task.task_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    async def _worker(self, worker_id: int):
        """Worker que procesa tareas de la cola."""
        logger.info(f"Worker {worker_id} iniciado")
        
        while self.running:
            try:
                # Obtener tarea de la cola (con timeout)
                try:
                    # Usar get_nowait para evitar bloqueos
                    priority, task = self.queue.get_nowait()
                except:
                    # Si no hay tareas, esperar un poco
                    await asyncio.sleep(0.1)
                    continue
                
                # Procesar tarea
                await self._process_task(task)
                
                # Marcar tarea como completada
                self.queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelado")
                break
            except Exception as e:
                logger.error(f"Error en worker {worker_id}: {e}")
                await asyncio.sleep(1)  # Esperar antes de reintentar
    
    def start(self):
        """Inicia los workers."""
        if self.running:
            logger.warning("Workers ya están ejecutándose")
            return
        
        self.running = True
        
        # Crear workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Iniciados {self.max_workers} workers")
    
    async def start_async(self):
        """Inicia los workers de forma asíncrona."""
        if self.running:
            return
        
        self.running = True
        
        # Crear workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Iniciados {self.max_workers} workers")
    
    def stop(self):
        """Detiene los workers."""
        self.running = False
        
        # Esperar a que terminen los workers
        for worker in self.workers:
            worker.cancel()
        
        self.workers.clear()
        logger.info("Workers detenidos")
    
    async def _send_callback(self, url: str, task_id: str, result: Dict[str, Any]):
        """
        Envía callback a URL.
        
        Args:
            url: URL de callback
            task_id: ID de la tarea
            result: Resultado
        """
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(
                    url,
                    json={
                        "task_id": task_id,
                        "status": "completed",
                        "result": result
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            logger.info(f"Callback enviado para tarea: {task_id}")
        except Exception as e:
            logger.error(f"Error enviando callback: {e}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la cola.
        
        Returns:
            Estadísticas
        """
        with self.lock:
            pending = sum(1 for t in self.tasks.values() if t.status == "pending")
            processing = sum(1 for t in self.tasks.values() if t.status == "processing")
            completed = sum(1 for t in self.tasks.values() if t.status == "completed")
            failed = sum(1 for t in self.tasks.values() if t.status == "failed")
            
            return {
                "queue_size": self.queue.qsize(),
                "total_tasks": len(self.tasks),
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "workers": len(self.workers),
                "max_workers": self.max_workers
            }

