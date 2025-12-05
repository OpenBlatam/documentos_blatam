#!/usr/bin/env python3
"""
Visualización y Reportes para Redundancy
=========================================

Herramientas para visualizar métricas, clusters y estadísticas.
"""

from typing import Dict, List, Optional, Any, Tuple
import torch
import numpy as np
from pathlib import Path
import json
import time

from core.utils import setup_logger
from core.error_handling import safe_execute

logger = setup_logger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None


class RedundancyVisualizer:
    """
    Visualizador de métricas y estadísticas de redundancia.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Args:
            output_dir: Directorio para guardar visualizaciones
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_reduction_over_time(
        self,
        reduction_rates: List[float],
        timestamps: Optional[List[float]] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Grafica la tasa de reducción a lo largo del tiempo.
        
        Args:
            reduction_rates: Lista de tasas de reducción
            timestamps: Timestamps (opcional)
            save_path: Ruta para guardar el gráfico
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib no disponible, no se puede generar gráfico")
            return None
        
        def _plot():
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if timestamps:
                ax.plot(timestamps, reduction_rates, marker='o', linestyle='-')
            else:
                ax.plot(reduction_rates, marker='o', linestyle='-')
            
            ax.set_xlabel('Tiempo' if timestamps else 'Batch')
            ax.set_ylabel('Tasa de Reducción')
            ax.set_title('Tasa de Reducción a lo Largo del Tiempo')
            ax.grid(True, alpha=0.3)
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            elif self.output_dir:
                save_path = str(self.output_dir / f"reduction_over_time_{int(time.time())}.png")
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            else:
                save_path = f"/tmp/reduction_over_time_{int(time.time())}.png"
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            
            plt.close()
            return save_path
        
        result, error = safe_execute(_plot, default_value=None, log_errors=True)
        return result
    
    def plot_cluster_distribution(
        self,
        cluster_sizes: List[int],
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Grafica la distribución de tamaños de clusters.
        
        Args:
            cluster_sizes: Lista de tamaños de clusters
            save_path: Ruta para guardar el gráfico
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib no disponible, no se puede generar gráfico")
            return None
        
        def _plot():
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.hist(cluster_sizes, bins=20, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Tamaño de Cluster')
            ax.set_ylabel('Frecuencia')
            ax.set_title('Distribución de Tamaños de Clusters')
            ax.grid(True, alpha=0.3)
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            elif self.output_dir:
                save_path = str(self.output_dir / f"cluster_distribution_{int(time.time())}.png")
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            else:
                save_path = f"/tmp/cluster_distribution_{int(time.time())}.png"
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            
            plt.close()
            return save_path
        
        result, error = safe_execute(_plot, default_value=None, log_errors=True)
        return result
    
    def plot_similarity_matrix(
        self,
        similarity_matrix: torch.Tensor,
        save_path: Optional[str] = None,
        max_size: int = 100
    ) -> Optional[str]:
        """
        Visualiza la matriz de similitud.
        
        Args:
            similarity_matrix: Matriz de similitud
            save_path: Ruta para guardar el gráfico
            max_size: Tamaño máximo para visualizar
        
        Returns:
            Ruta del archivo guardado o None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib no disponible, no se puede generar gráfico")
            return None
        
        def _plot():
            matrix = similarity_matrix.cpu().numpy()
            
            if matrix.shape[0] > max_size:
                matrix = matrix[:max_size, :max_size]
            
            fig, ax = plt.subplots(figsize=(10, 10))
            im = ax.imshow(matrix, cmap='viridis', aspect='auto')
            ax.set_title('Matriz de Similitud')
            ax.set_xlabel('Índice')
            ax.set_ylabel('Índice')
            plt.colorbar(im, ax=ax)
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            elif self.output_dir:
                save_path = str(self.output_dir / f"similarity_matrix_{int(time.time())}.png")
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            else:
                save_path = f"/tmp/similarity_matrix_{int(time.time())}.png"
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
            
            plt.close()
            return save_path
        
        result, error = safe_execute(_plot, default_value=None, log_errors=True)
        return result
    
    def generate_comprehensive_report(
        self,
        suppressor: Any,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera un reporte completo con visualizaciones.
        
        Args:
            suppressor: Supresor de redundancia
            output_path: Ruta para guardar el reporte
        
        Returns:
            Diccionario con el reporte
        """
        def _generate():
            report = {
                'timestamp': time.time(),
                'metrics': suppressor.get_metrics() if hasattr(suppressor, 'get_metrics') else {},
                'visualizations': {}
            }
            
            if hasattr(suppressor, 'reduction_rates') and suppressor.reduction_rates:
                reduction_plot = self.plot_reduction_over_time(suppressor.reduction_rates)
                if reduction_plot:
                    report['visualizations']['reduction_over_time'] = reduction_plot
            
            if hasattr(suppressor, 'cluster_sizes') and suppressor.cluster_sizes:
                cluster_plot = self.plot_cluster_distribution(suppressor.cluster_sizes)
                if cluster_plot:
                    report['visualizations']['cluster_distribution'] = cluster_plot
            
            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            
            return report
        
        result, error = safe_execute(_generate, default_value={}, log_errors=True)
        return result


