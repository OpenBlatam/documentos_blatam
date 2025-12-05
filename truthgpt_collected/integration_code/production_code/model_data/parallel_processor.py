#!/usr/bin/env python3
"""
Parallel Processor
=================

Procesamiento paralelo para recolección de datos de múltiples modelos.
"""

from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import time

from .data_collector import ModelDataCollector, ModelData
from .constants import MIN_WORKERS, MAX_WORKERS_LIMIT
from core.paper_base import BasePaperModule
from core.paper_registry import PaperInfo
from core.utils import setup_logger
from core.error_handling import safe_execute, ValidationError

logger = setup_logger(__name__)


class ParallelProcessor:
    """
    Procesador paralelo para recolección de datos.
    
    Permite procesar múltiples modelos en paralelo usando:
    - ThreadPoolExecutor (para I/O bound)
    - ProcessPoolExecutor (para CPU bound)
    """
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = False
    ):
        """
        Inicializa el procesador paralelo.
        
        Args:
            max_workers: Número máximo de workers (opcional)
            use_processes: Si True, usa procesos en lugar de threads
        
        Raises:
            ValidationError: Si max_workers está fuera del rango válido
        """
        if max_workers is not None:
            if not isinstance(max_workers, int) or max_workers < MIN_WORKERS:
                raise ValidationError(f"max_workers debe ser >= {MIN_WORKERS}, recibido: {max_workers}")
            if max_workers > MAX_WORKERS_LIMIT:
                raise ValidationError(f"max_workers debe ser <= {MAX_WORKERS_LIMIT}, recibido: {max_workers}")
        
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    def collect_models_parallel(
        self,
        models: List[BasePaperModule],
        paper_ids: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        run_benchmarks: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ModelData]:
        """
        Recolecta datos de múltiples modelos en paralelo.
        
        Args:
            models: Lista de modelos
            paper_ids: IDs de papers (opcional)
            categories: Categorías (opcional)
            run_benchmarks: Si True, ejecuta benchmarks
            progress_callback: Callback para progreso (opcional)
        
        Returns:
            Lista de ModelData recolectados
        """
        collector = ModelDataCollector(include_benchmarks=run_benchmarks)
        
        def collect_single(args):
            """Recolecta datos de un solo modelo."""
            model, paper_id, category = args
            
            def _collect():
                return collector.collect_model_data(
                    model,
                    paper_id=paper_id,
                    category=category,
                    run_benchmarks=run_benchmarks
                )
            
            result, error = safe_execute(_collect, default_value=None, log_errors=False)
            
            if error:
                logger.error("Error recolectando datos", error=str(error))
            
            return result
        
        # Preparar argumentos
        args_list = []
        for i, model in enumerate(models):
            paper_id = paper_ids[i] if paper_ids and i < len(paper_ids) else None
            category = categories[i] if categories and i < len(categories) else None
            args_list.append((model, paper_id, category))
        
        results = []
        total = len(args_list)
        
        with self.executor_class(max_workers=self.max_workers) as executor:
            # Enviar tareas
            future_to_args = {
                executor.submit(collect_single, args): args
                for args in args_list
            }
            
            # Procesar resultados
            completed = 0
            for future in as_completed(future_to_args):
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                
                def _get_result():
                    return future.result()
                
                result, error = safe_execute(_get_result, default_value=None, log_errors=False)
                
                if error:
                    logger.error("Error en tarea paralela", error=str(error))
                elif result:
                    results.append(result)
        
        logger.info("Procesamiento paralelo completado", total=total, successful=len(results))
        return results
    
    def process_papers_parallel(
        self,
        papers: List[PaperInfo],
        registry,
        run_benchmarks: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ModelData]:
        """
        Procesa múltiples papers en paralelo.
        
        Args:
            papers: Lista de PaperInfo
            registry: Registry de papers
            run_benchmarks: Si True, ejecuta benchmarks
            progress_callback: Callback para progreso (opcional)
        
        Returns:
            Lista de ModelData recolectados
        """
        def process_paper(paper_info: PaperInfo):
            """Procesa un paper."""
            def _process():
                # Cargar modelo
                model = registry.load_paper(paper_info.paper_id, force_reload=False)
                if model is None:
                    return None
                
                # Recolectar datos
                collector = ModelDataCollector(include_benchmarks=run_benchmarks)
                return collector.collect_model_data(
                    model,
                    paper_id=paper_info.paper_id,
                    category=paper_info.category,
                    run_benchmarks=run_benchmarks
                )
            
            result, error = safe_execute(_process, default_value=None, log_errors=False)
            
            if error:
                logger.error("Error procesando paper", paper_id=paper_info.paper_id, error=str(error))
            
            return result
        
        results = []
        total = len(papers)
        
        with self.executor_class(max_workers=self.max_workers) as executor:
            future_to_paper = {
                executor.submit(process_paper, paper): paper
                for paper in papers
            }
            
            completed = 0
            for future in as_completed(future_to_paper):
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                
                def _get_result():
                    return future.result()
                
                result, error = safe_execute(_get_result, default_value=None, log_errors=False)
                
                if error:
                    logger.error("Error en tarea paralela", error=str(error))
                elif result:
                    results.append(result)
        
        logger.info("Procesamiento de papers completado", total=total, successful=len(results))
        return results


