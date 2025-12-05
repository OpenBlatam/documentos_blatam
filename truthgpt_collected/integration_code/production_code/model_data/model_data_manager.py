#!/usr/bin/env python3
"""
Model Data Manager
===================

Gestor principal que coordina la recolección, conexión y exportación
de datos de modelos.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import time

from .data_collector import ModelDataCollector, ModelData
from .info_connector import InfoConnector
from .data_aggregator import DataAggregator, AggregatedData
from .data_exporter import DataExporter
from .experiment_integration import ExperimentIntegration
from .data_persistence import DataPersistence
from .parallel_processor import ParallelProcessor
from .constants import (
    SUPPORTED_EXPORT_FORMATS,
    DEFAULT_EXPORT_FORMAT,
    DEFAULT_TOP_K_MODELS,
    MIN_WORKERS,
    MAX_WORKERS_LIMIT
)

from core.paper_base import BasePaperModule
from core.paper_registry import PaperRegistry, get_registry
from core.utils import setup_logger
from core.error_handling import safe_execute, ValidationError

logger = setup_logger(__name__)


class ModelDataManager:
    """
    Gestor principal para datos de modelos.
    
    Coordina:
    - Recolección de datos de modelos
    - Conexión a fuentes de información
    - Agregación y análisis
    - Exportación a diferentes formatos
    """
    
    def __init__(
        self,
        registry: Optional[PaperRegistry] = None,
        base_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        include_benchmarks: bool = True,
        enable_persistence: bool = True,
        enable_experiment_tracking: bool = False,
        enable_parallel: bool = True,
        max_workers: Optional[int] = None
    ):
        """
        Inicializa el gestor.
        
        Args:
            registry: Registry de papers (opcional)
            base_dir: Directorio base
            output_dir: Directorio de salida para exports
            include_benchmarks: Si True, incluye benchmarks
            enable_persistence: Si True, habilita persistencia en BD
            enable_experiment_tracking: Si True, habilita experiment tracking
            enable_parallel: Si True, habilita procesamiento paralelo
            max_workers: Número máximo de workers para procesamiento paralelo
        
        Raises:
            ValidationError: Si max_workers está fuera del rango válido
        """
        if max_workers is not None:
            if not isinstance(max_workers, int) or max_workers < MIN_WORKERS:
                raise ValidationError(f"max_workers debe ser >= {MIN_WORKERS}, recibido: {max_workers}")
            if max_workers > MAX_WORKERS_LIMIT:
                raise ValidationError(f"max_workers debe ser <= {MAX_WORKERS_LIMIT}, recibido: {max_workers}")
        self.info_connector = InfoConnector(registry=registry, base_dir=base_dir)
        self.data_collector = ModelDataCollector(include_benchmarks=include_benchmarks)
        self.data_aggregator = DataAggregator(info_connector=self.info_connector)
        self.data_exporter = DataExporter(output_dir=output_dir)
        
        # Nuevas funcionalidades
        self.persistence = DataPersistence() if enable_persistence else None
        self.experiment_tracking = ExperimentIntegration() if enable_experiment_tracking else None
        self.parallel_processor = ParallelProcessor(max_workers=max_workers) if enable_parallel else None
        
        self.base_dir = base_dir or Path(__file__).parent.parent
        self._collected_data: List[ModelData] = []
        self.enable_persistence = enable_persistence
        self.enable_experiment_tracking = enable_experiment_tracking
        self.enable_parallel = enable_parallel
    
    def collect_from_registry(
        self,
        paper_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        run_benchmarks: bool = True,
        limit: Optional[int] = None
    ) -> List[ModelData]:
        """
        Recolecta datos de modelos desde el registry.
        
        Args:
            paper_ids: IDs específicos de papers (opcional)
            category: Filtrar por categoría (opcional)
            run_benchmarks: Si True, ejecuta benchmarks
            limit: Límite de modelos a procesar (opcional)
        
        Returns:
            Lista de ModelData recolectados
        """
        logger.info(
            "Recolectando datos desde registry",
            paper_ids=paper_ids,
            category=category,
            limit=limit
        )
        
        collected = []
        
        # Obtener papers del registry
        if paper_ids:
            papers = [
                self.info_connector.registry.get_paper_info(pid)
                for pid in paper_ids
            ]
            papers = [p for p in papers if p is not None]
        else:
            papers = self.info_connector.registry.list_papers(
                category=category,
                enabled_only=True
            )
        
        if limit:
            papers = papers[:limit]
        
        # Cargar y recolectar datos
        for paper_info in papers:
            def _collect_paper_data():
                # Cargar modelo
                model = self.info_connector.registry.load_paper(
                    paper_info.paper_id,
                    force_reload=False
                )
                
                if model is None:
                    logger.warning("No se pudo cargar modelo", paper_id=paper_info.paper_id)
                    return None
                
                # Recolectar datos
                data = self.data_collector.collect_model_data(
                    model,
                    paper_id=paper_info.paper_id,
                    category=paper_info.category,
                    run_benchmarks=run_benchmarks
                )
                
                # Persistir si está habilitado
                if self.enable_persistence and self.persistence:
                    try:
                        self.persistence.save_model_data(data)
                    except Exception as e:
                        logger.warning(
                            "Error al persistir datos",
                            paper_id=paper_info.paper_id,
                            error=str(e)
                        )
                
                # Registrar en experiment tracking si está habilitado
                if self.enable_experiment_tracking and self.experiment_tracking:
                    try:
                        self.experiment_tracking.log_model_data(data)
                    except Exception as e:
                        logger.warning(
                            "Error al registrar en experiment tracking",
                            paper_id=paper_info.paper_id,
                            error=str(e)
                        )
                
                logger.info(
                    "Datos recolectados",
                    paper_id=paper_info.paper_id,
                    model_name=data.model_name
                )
                
                return data
            
            result, error = safe_execute(_collect_paper_data, default_value=None, log_errors=False)
            
            if error:
                logger.error(
                    "Error al recolectar datos",
                    paper_id=paper_info.paper_id,
                    error=str(error)
                )
            elif result:
                collected.append(result)
        
        self._collected_data.extend(collected)
        return collected
    
    def collect_from_models(
        self,
        models: List[BasePaperModule],
        paper_ids: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        run_benchmarks: bool = True,
        use_parallel: Optional[bool] = None
    ) -> List[ModelData]:
        """
        Recolecta datos de una lista de modelos.
        
        Args:
            models: Lista de modelos
            paper_ids: IDs de papers (opcional)
            categories: Categorías (opcional)
            run_benchmarks: Si True, ejecuta benchmarks
            use_parallel: Si True, usa procesamiento paralelo (opcional, usa default si None)
        
        Returns:
            Lista de ModelData recolectados
        """
        logger.info("Recolectando datos de modelos", total_models=len(models))
        
        use_parallel = use_parallel if use_parallel is not None else self.enable_parallel
        
        if use_parallel and self.parallel_processor:
            collected = self.parallel_processor.collect_models_parallel(
                models,
                paper_ids=paper_ids,
                categories=categories,
                run_benchmarks=run_benchmarks
            )
        else:
            collected = self.data_collector.collect_batch(
                models,
                paper_ids=paper_ids,
                categories=categories,
                run_benchmarks=run_benchmarks
            )
        
        # Persistir y registrar
        for data in collected:
            if self.enable_persistence and self.persistence:
                try:
                    self.persistence.save_model_data(data)
                except Exception as e:
                    logger.warning("Error al persistir datos", model_name=data.model_name, error=str(e))
            
            if self.enable_experiment_tracking and self.experiment_tracking:
                try:
                    self.experiment_tracking.log_model_data(data)
                except Exception as e:
                    logger.warning("Error al registrar en experiment tracking", model_name=data.model_name, error=str(e))
        
        self._collected_data.extend(collected)
        return collected
    
    def get_best_models_info(
        self,
        category: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K_MODELS
    ) -> List[Dict[str, Any]]:
        """
        Obtiene información de los mejores modelos.
        
        Args:
            category: Filtrar por categoría (opcional)
            top_k: Número de modelos a retornar
        
        Returns:
            Lista de información de mejores modelos
        
        Raises:
            ValidationError: Si top_k es inválido
        """
        if not isinstance(top_k, int) or top_k < 1:
            raise ValidationError(f"top_k debe ser un entero positivo, recibido: {top_k}")
        
        return self.info_connector.get_best_papers(
            category=category,
            top_k=top_k
        )
    
    def get_registry_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene información del registry.
        
        Args:
            force_refresh: Si True, fuerza actualización
        
        Returns:
            Diccionario con información del registry
        """
        return self.info_connector.get_registry_info(force_refresh=force_refresh)
    
    def aggregate_collected_data(
        self,
        include_benchmarks: bool = True,
        include_metrics: bool = True
    ) -> AggregatedData:
        """
        Agrega los datos recolectados.
        
        Args:
            include_benchmarks: Si True, incluye estadísticas de benchmarks
            include_metrics: Si True, incluye estadísticas de métricas
        
        Returns:
            AggregatedData con datos agregados
        """
        if not self._collected_data:
            logger.warning("No hay datos recolectados para agregar")
            return AggregatedData(total_models=0)
        
        return self.data_aggregator.aggregate(
            self._collected_data,
            include_benchmarks=include_benchmarks,
            include_metrics=include_metrics
        )
    
    def export_all(
        self,
        format: str = DEFAULT_EXPORT_FORMAT,
        filename: Optional[str] = None,
        include_aggregated: bool = True
    ) -> Dict[str, Path]:
        """
        Exporta todos los datos recolectados.
        
        Args:
            format: Formato de exportación ('json', 'csv', 'html', 'markdown')
            filename: Nombre del archivo (opcional)
            include_aggregated: Si True, incluye datos agregados
        
        Returns:
            Diccionario con rutas de archivos exportados
        
        Raises:
            ValidationError: Si el formato no es soportado
        """
        if format not in SUPPORTED_EXPORT_FORMATS:
            raise ValidationError(
                f"Formato '{format}' no soportado. Formatos válidos: {', '.join(SUPPORTED_EXPORT_FORMATS)}"
            )
        exported = {}
        
        if not self._collected_data:
            logger.warning("No hay datos para exportar")
            return exported
        
        # Exportar datos individuales
        if format == 'json':
            filename = filename or f'model_data_{int(time.time())}.json'
            exported['individual'] = self.data_exporter.export_json(
                self._collected_data,
                filename
            )
        elif format == 'csv':
            filename = filename or f'model_data_{int(time.time())}.csv'
            exported['individual'] = self.data_exporter.export_csv(
                self._collected_data,
                filename
            )
        
        # Exportar datos agregados
        if include_aggregated:
            aggregated = self.aggregate_collected_data()
            
            if format == 'json':
                filename = filename or f'aggregated_data_{int(time.time())}.json'
                exported['aggregated'] = self.data_exporter.export_json(
                    aggregated,
                    filename
                )
            elif format == 'html':
                filename = filename or f'model_data_report_{int(time.time())}.html'
                exported['report'] = self.data_exporter.export_html_report(
                    aggregated,
                    info_connector=self.info_connector,
                    filename=filename
                )
            elif format == 'markdown':
                filename = filename or f'model_data_report_{int(time.time())}.md'
                exported['report'] = self.data_exporter.export_markdown_report(
                    aggregated,
                    info_connector=self.info_connector,
                    filename=filename
                )
        
        return exported
    
    def get_full_report(
        self,
        paper_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        run_benchmarks: bool = True,
        export_format: str = 'html'
    ) -> Dict[str, Any]:
        """
        Genera un reporte completo.
        
        Args:
            paper_ids: IDs específicos de papers (opcional)
            category: Filtrar por categoría (opcional)
            run_benchmarks: Si True, ejecuta benchmarks
            export_format: Formato de exportación
        
        Returns:
            Diccionario con información del reporte y rutas exportadas
        
        Raises:
            ValidationError: Si el formato de exportación no es válido
        """
        if export_format not in SUPPORTED_EXPORT_FORMATS:
            raise ValidationError(
                f"Formato de exportación '{export_format}' no soportado. "
                f"Formatos válidos: {', '.join(SUPPORTED_EXPORT_FORMATS)}"
            )
        logger.info("Generando reporte completo")
        
        # Recolectar datos
        collected = self.collect_from_registry(
            paper_ids=paper_ids,
            category=category,
            run_benchmarks=run_benchmarks
        )
        
        # Agregar datos
        aggregated = self.aggregate_collected_data()
        
        # Obtener información del registry
        registry_info = self.get_registry_info()
        
        # Exportar
        exported = self.export_all(format=export_format, include_aggregated=True)
        
        return {
            'collected_models': len(collected),
            'aggregated_data': aggregated,
            'registry_info': registry_info,
            'exported_files': exported,
            'timestamp': time.time()
        }
    
    def clear_collected_data(self):
        """Limpia los datos recolectados."""
        self._collected_data.clear()
        logger.info("Datos recolectados limpiados")
    
    def get_collected_data(self) -> List[ModelData]:
        """Obtiene los datos recolectados."""
        return self._collected_data.copy()
    
    def get_model_history(
        self,
        paper_id: Optional[str] = None,
        model_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de un modelo desde la base de datos.
        
        Args:
            paper_id: Filtrar por paper_id
            model_name: Filtrar por model_name
            limit: Límite de resultados
        
        Returns:
            Lista de registros históricos
        """
        if not self.persistence:
            logger.warning("Persistencia no habilitada")
            return []
        
        return self.persistence.get_model_history(
            paper_id=paper_id,
            model_name=model_name,
            limit=limit
        )
    
    def compare_model_over_time(
        self,
        paper_id: str,
        metric: str = 'total_parameters'
    ) -> List[Dict[str, Any]]:
        """
        Compara un modelo a lo largo del tiempo.
        
        Args:
            paper_id: ID del paper
            metric: Métrica a comparar
        
        Returns:
            Lista de valores de la métrica a lo largo del tiempo
        """
        if not self.persistence:
            logger.warning("Persistencia no habilitada")
            return []
        
        return self.persistence.compare_models_over_time(paper_id=paper_id, metric=metric)
    
    def get_persistence_statistics(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos.
        
        Args:
            category: Filtrar por categoría (opcional)
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.persistence:
            logger.warning("Persistencia no habilitada")
            return {}
        
        return self.persistence.get_statistics(category=category)
    
    def finish_experiment_tracking(self):
        """Finaliza el experiment tracking."""
        if self.experiment_tracking:
            self.experiment_tracking.finish()

