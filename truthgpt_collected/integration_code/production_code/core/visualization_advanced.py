#!/usr/bin/env python3
"""
Visualización Avanzada - Integración de Librerías
==================================================

Integración de librerías de visualización de requirements.txt.
"""

from typing import Dict, Any, Optional, List, Union
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Matplotlib
# ============================================================================

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ============================================================================
# Seaborn
# ============================================================================

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

# ============================================================================
# Plotly
# ============================================================================

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class AdvancedVisualizer:
    """Visualizador avanzado con múltiples backends."""
    
    def __init__(self, backend: str = "matplotlib"):
        """
        Inicializa el visualizador.
        
        Args:
            backend: Backend a usar ("matplotlib", "seaborn", "plotly")
        """
        self.backend = backend
        
        if backend == "seaborn" and SEABORN_AVAILABLE:
            sns.set_style("darkgrid")
            sns.set_palette("husl")
    
    def plot_line(
        self,
        x: List[float],
        y: List[float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        save_path: Optional[str] = None
    ) -> None:
        """
        Crea un gráfico de líneas.
        
        Args:
            x: Valores en x
            y: Valores en y
            title: Título del gráfico
            xlabel: Etiqueta del eje x
            ylabel: Etiqueta del eje y
            save_path: Ruta para guardar el gráfico
        """
        if self.backend == "plotly" and PLOTLY_AVAILABLE:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Data'))
            fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel)
            if save_path:
                fig.write_image(save_path)
            else:
                fig.show()
        elif MATPLOTLIB_AVAILABLE:
            plt.figure(figsize=(10, 6))
            plt.plot(x, y)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.grid(True)
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()
    
    def plot_bar(
        self,
        categories: List[str],
        values: List[float],
        title: str = "",
        save_path: Optional[str] = None
    ) -> None:
        """
        Crea un gráfico de barras.
        
        Args:
            categories: Categorías
            values: Valores
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        if self.backend == "plotly" and PLOTLY_AVAILABLE:
            fig = go.Figure(data=[go.Bar(x=categories, y=values)])
            fig.update_layout(title=title)
            if save_path:
                fig.write_image(save_path)
            else:
                fig.show()
        elif self.backend == "seaborn" and SEABORN_AVAILABLE:
            plt.figure(figsize=(10, 6))
            sns.barplot(x=categories, y=values)
            plt.title(title)
            plt.xticks(rotation=45)
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()
        elif MATPLOTLIB_AVAILABLE:
            plt.figure(figsize=(10, 6))
            plt.bar(categories, values)
            plt.title(title)
            plt.xticks(rotation=45)
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()
    
    def plot_heatmap(
        self,
        data: np.ndarray,
        title: str = "",
        save_path: Optional[str] = None
    ) -> None:
        """
        Crea un mapa de calor.
        
        Args:
            data: Matriz de datos
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        if self.backend == "plotly" and PLOTLY_AVAILABLE:
            fig = go.Figure(data=go.Heatmap(z=data))
            fig.update_layout(title=title)
            if save_path:
                fig.write_image(save_path)
            else:
                fig.show()
        elif self.backend == "seaborn" and SEABORN_AVAILABLE:
            plt.figure(figsize=(10, 8))
            sns.heatmap(data, annot=True, fmt='.2f', cmap='viridis')
            plt.title(title)
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()
        elif MATPLOTLIB_AVAILABLE:
            plt.figure(figsize=(10, 8))
            plt.imshow(data, cmap='viridis')
            plt.colorbar()
            plt.title(title)
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()
    
    def plot_distribution(
        self,
        data: List[float],
        title: str = "",
        save_path: Optional[str] = None
    ) -> None:
        """
        Crea un gráfico de distribución.
        
        Args:
            data: Datos a visualizar
            title: Título del gráfico
            save_path: Ruta para guardar
        """
        if self.backend == "plotly" and PLOTLY_AVAILABLE:
            fig = go.Figure(data=[go.Histogram(x=data)])
            fig.update_layout(title=title)
            if save_path:
                fig.write_image(save_path)
            else:
                fig.show()
        elif self.backend == "seaborn" and SEABORN_AVAILABLE:
            plt.figure(figsize=(10, 6))
            sns.histplot(data, kde=True)
            plt.title(title)
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()
        elif MATPLOTLIB_AVAILABLE:
            plt.figure(figsize=(10, 6))
            plt.hist(data, bins=30, edgecolor='black')
            plt.title(title)
            plt.xlabel('Value')
            plt.ylabel('Frequency')
            if save_path:
                plt.savefig(save_path)
            else:
                plt.show()
            plt.close()


def create_metrics_dashboard(metrics: Dict[str, List[float]], save_path: Optional[str] = None) -> None:
    """
    Crea un dashboard de métricas.
    
    Args:
        metrics: Diccionario de métricas {nombre: [valores]}
        save_path: Ruta para guardar
    """
    if PLOTLY_AVAILABLE:
        n_metrics = len(metrics)
        fig = make_subplots(
            rows=n_metrics,
            cols=1,
            subplot_titles=list(metrics.keys())
        )
        
        for i, (name, values) in enumerate(metrics.items(), 1):
            fig.add_trace(
                go.Scatter(y=values, name=name),
                row=i,
                col=1
            )
        
        fig.update_layout(height=300 * n_metrics, title_text="Metrics Dashboard")
        
        if save_path:
            fig.write_html(save_path)
        else:
            fig.show()
    elif MATPLOTLIB_AVAILABLE:
        n_metrics = len(metrics)
        fig, axes = plt.subplots(n_metrics, 1, figsize=(12, 4 * n_metrics))
        
        if n_metrics == 1:
            axes = [axes]
        
        for ax, (name, values) in zip(axes, metrics.items()):
            ax.plot(values)
            ax.set_title(name)
            ax.grid(True)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
        plt.close()


