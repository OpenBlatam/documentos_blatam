#!/usr/bin/env python3
"""
Visualizations
==============

Visualizaciones mejoradas para datos de modelos.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import time

from .data_collector import ModelData
from .data_aggregator import AggregatedData
from .constants import VISUALIZATIONS_DIR
from .dependencies import (
    MATPLOTLIB_AVAILABLE,
    PLOTLY_AVAILABLE,
    get_matplotlib,
    get_plotly
)
from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)


class ModelDataVisualizer:
    """
    Visualizador de datos de modelos.
    
    Crea visualizaciones interactivas y estáticas de:
    - Comparación de modelos
    - Benchmarks
    - Métricas temporales
    - Distribuciones
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa el visualizador.
        
        Args:
            output_dir: Directorio de salida para gráficos
        
        Raises:
            IOError: Si no se puede crear el directorio de salida
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / VISUALIZATIONS_DIR
        
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Error creando directorio de visualizaciones", path=str(self.output_dir), error=str(e))
            raise IOError(f"No se pudo crear el directorio de visualizaciones: {e}") from e
    
    def plot_model_comparison(
        self,
        model_data_list: List[ModelData],
        metric: str = 'total_parameters',
        save_path: Optional[Path] = None,
        interactive: bool = True
    ) -> Optional[Path]:
        """
        Crea gráfico de comparación de modelos.
        
        Args:
            model_data_list: Lista de ModelData
            metric: Métrica a comparar
            save_path: Ruta donde guardar (opcional)
            interactive: Si True, usa plotly (interactivo)
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not MATPLOTLIB_AVAILABLE and not PLOTLY_AVAILABLE:
            logger.warning("No hay librerías de visualización disponibles")
            return None
        
        # Extraer datos
        model_names = []
        values = []
        
        for data in model_data_list:
            model_names.append(data.model_name)
            
            if metric == 'total_parameters':
                values.append(data.parameters.get('total_parameters', 0))
            elif metric == 'trainable_parameters':
                values.append(data.parameters.get('trainable_parameters', 0))
            elif metric == 'forward_count':
                values.append(data.metrics.get('forward_count', 0))
            else:
                values.append(0)
        
        if interactive and PLOTLY_AVAILABLE:
            go = get_plotly().graph_objects
            fig = go.Figure(data=[
                go.Bar(x=model_names, y=values, text=values, textposition='auto')
            ])
            fig.update_layout(
                title=f'Comparación de Modelos - {metric}',
                xaxis_title='Modelo',
                yaxis_title=metric,
                template='plotly_white'
            )
            
            if save_path is None:
                save_path = self.output_dir / f'model_comparison_{metric}_{int(time.time())}.html'
            
            fig.write_html(str(save_path))
            logger.info("Gráfico interactivo guardado", path=str(save_path))
            return save_path
        
        elif MATPLOTLIB_AVAILABLE:
            plt = get_matplotlib().pyplot
            plt.figure(figsize=(12, 6))
            plt.bar(model_names, values)
            plt.title(f'Comparación de Modelos - {metric}')
            plt.xlabel('Modelo')
            plt.ylabel(metric)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            if save_path is None:
                save_path = self.output_dir / f'model_comparison_{metric}_{int(time.time())}.png'
            
            plt.savefig(str(save_path), dpi=300, bbox_inches='tight')
            plt.close()
            logger.info("Gráfico guardado", path=str(save_path))
            return save_path
        
        return None
    
    def plot_benchmark_comparison(
        self,
        model_data_list: List[ModelData],
        benchmark_metric: str = 'throughput',
        save_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Compara benchmarks de múltiples modelos.
        
        Args:
            model_data_list: Lista de ModelData
            benchmark_metric: Métrica de benchmark a comparar
            save_path: Ruta donde guardar (opcional)
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly no disponible para gráfico interactivo")
            return None
        
        go = get_plotly().graph_objects
        fig = go.Figure()
        
        for data in model_data_list:
            if not data.benchmarks:
                continue
            
            batch_sizes = [b.get('batch_size', 0) for b in data.benchmarks]
            values = [b.get(benchmark_metric, 0) or 0 for b in data.benchmarks]
            
            fig.add_trace(go.Scatter(
                x=batch_sizes,
                y=values,
                mode='lines+markers',
                name=data.model_name
            ))
        
        fig.update_layout(
            title=f'Comparación de Benchmarks - {benchmark_metric}',
            xaxis_title='Batch Size',
            yaxis_title=benchmark_metric,
            template='plotly_white',
            hovermode='x unified'
        )
        
        if save_path is None:
            save_path = self.output_dir / f'benchmark_comparison_{benchmark_metric}_{int(time.time())}.html'
        
        fig.write_html(str(save_path))
        logger.info("Gráfico de benchmarks guardado", path=str(save_path))
        return save_path
    
    def plot_temporal_analysis(
        self,
        history_data: List[Dict[str, Any]],
        metric: str = 'total_parameters',
        save_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Visualiza análisis temporal de un modelo.
        
        Args:
            history_data: Lista de registros históricos
            metric: Métrica a visualizar
            save_path: Ruta donde guardar (opcional)
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly no disponible")
            return None
        
        go = get_plotly().graph_objects
        timestamps = [h['timestamp'] for h in history_data]
        values = [h['value'] for h in history_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=values,
            mode='lines+markers',
            name=metric,
            line=dict(width=2)
        ))
        
        fig.update_layout(
            title=f'Análisis Temporal - {metric}',
            xaxis_title='Timestamp',
            yaxis_title=metric,
            template='plotly_white',
            hovermode='x unified'
        )
        
        if save_path is None:
            save_path = self.output_dir / f'temporal_analysis_{metric}_{int(time.time())}.html'
        
        fig.write_html(str(save_path))
        logger.info("Gráfico temporal guardado", path=str(save_path))
        return save_path
    
    def plot_category_distribution(
        self,
        aggregated_data: AggregatedData,
        save_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Visualiza distribución por categorías.
        
        Args:
            aggregated_data: Datos agregados
            save_path: Ruta donde guardar (opcional)
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly no disponible")
            return None
        
        go = get_plotly().graph_objects
        categories = list(aggregated_data.categories.keys())
        counts = list(aggregated_data.categories.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=counts,
            hole=0.3
        )])
        
        fig.update_layout(
            title='Distribución de Modelos por Categoría',
            template='plotly_white'
        )
        
        if save_path is None:
            save_path = self.output_dir / f'category_distribution_{int(time.time())}.html'
        
        fig.write_html(str(save_path))
        logger.info("Gráfico de distribución guardado", path=str(save_path))
        return save_path
    
    def create_dashboard(
        self,
        aggregated_data: AggregatedData,
        model_data_list: List[ModelData],
        save_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Crea un dashboard completo con múltiples visualizaciones.
        
        Args:
            aggregated_data: Datos agregados
            model_data_list: Lista de ModelData
            save_path: Ruta donde guardar (opcional)
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly no disponible para dashboard")
            return None
        
        plotly = get_plotly()
        go = plotly.graph_objects
        make_subplots = plotly.subplots.make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Distribución por Categoría',
                'Comparación de Parámetros',
                'Top Modelos',
                'Resumen'
            ),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # 1. Distribución por categoría
        categories = list(aggregated_data.categories.keys())
        counts = list(aggregated_data.categories.values())
        fig.add_trace(
            go.Pie(labels=categories, values=counts, name="Categorías"),
            row=1, col=1
        )
        
        # 2. Comparación de parámetros
        model_names = [d.model_name for d in model_data_list[:10]]
        total_params = [d.parameters.get('total_parameters', 0) for d in model_data_list[:10]]
        fig.add_trace(
            go.Bar(x=model_names, y=total_params, name="Parámetros"),
            row=1, col=2
        )
        
        # 3. Top modelos
        top_models = aggregated_data.best_models[:5]
        top_names = [m['model_name'] for m in top_models]
        top_scores = [m['score'] for m in top_models]
        fig.add_trace(
            go.Bar(x=top_names, y=top_scores, name="Score"),
            row=2, col=1
        )
        
        # 4. Tabla de resumen
        summary_data = [
            ['Total Modelos', str(aggregated_data.total_models)],
            ['Categorías', str(len(aggregated_data.categories))],
        ]
        fig.add_trace(
            go.Table(
                header=dict(values=['Métrica', 'Valor']),
                cells=dict(values=list(zip(*summary_data)))
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="Dashboard de Modelos",
            height=800,
            template='plotly_white'
        )
        
        if save_path is None:
            save_path = self.output_dir / f'dashboard_{int(time.time())}.html'
        
        fig.write_html(str(save_path))
        logger.info("Dashboard guardado", path=str(save_path))
        return save_path


