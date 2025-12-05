#!/usr/bin/env python3
"""
Data Exporter
=============

Exporta datos de modelos a diferentes formatos:
- JSON
- CSV
- HTML (reportes)
- Markdown
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
import csv
from datetime import datetime

from .data_collector import ModelData
from .data_aggregator import AggregatedData
from .info_connector import InfoConnector
from .constants import EXPORTS_DIR, SUPPORTED_EXPORT_FORMATS, DEFAULT_EXPORT_FORMAT
from core.optional_dependencies import PANDAS_AVAILABLE, get_pandas
from core.utils import setup_logger
from core.error_handling import ValidationError

logger = setup_logger(__name__)


class DataExporter:
    """
    Exportador de datos de modelos.
    
    Soporta múltiples formatos:
    - JSON
    - CSV
    - HTML
    - Markdown
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa el exportador.
        
        Args:
            output_dir: Directorio de salida (opcional)
        
        Raises:
            IOError: Si no se puede crear el directorio de salida
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / EXPORTS_DIR
        
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Error creando directorio de exportación", path=str(self.output_dir), error=str(e))
            raise IOError(f"No se pudo crear el directorio de exportación: {e}") from e
    
    def export_json(
        self,
        data: Union[ModelData, List[ModelData], AggregatedData, Dict[str, Any]],
        filename: str,
        pretty: bool = True
    ) -> Path:
        """
        Exporta datos a JSON.
        
        Args:
            data: Datos a exportar
            filename: Nombre del archivo
            pretty: Si True, formatea el JSON
        
        Returns:
            Ruta del archivo exportado
        
        Raises:
            IOError: Si hay un error al escribir el archivo
        """
        if not filename:
            raise ValidationError("filename no puede estar vacío")
        
        filepath = self.output_dir / filename
        if not filename.endswith('.json'):
            filepath = filepath.with_suffix('.json')
        
        # Convertir a dict
        if isinstance(data, ModelData):
            data_dict = data.to_dict()
        elif isinstance(data, AggregatedData):
            data_dict = self._aggregated_to_dict(data)
        elif isinstance(data, list):
            data_dict = [d.to_dict() if isinstance(d, ModelData) else d for d in data]
        else:
            data_dict = data
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data_dict, f, indent=2, default=str, ensure_ascii=False)
                else:
                    json.dump(data_dict, f, default=str, ensure_ascii=False)
        except (IOError, OSError, json.JSONEncodeError) as e:
            logger.error("Error exportando a JSON", filepath=str(filepath), error=str(e))
            raise IOError(f"Error al exportar a JSON: {e}") from e
        
        logger.info("Datos exportados a JSON", filepath=str(filepath))
        return filepath
    
    def export_csv(
        self,
        model_data_list: List[ModelData],
        filename: str
    ) -> Path:
        """
        Exporta datos de modelos a CSV.
        
        Args:
            model_data_list: Lista de ModelData
            filename: Nombre del archivo
        
        Returns:
            Ruta del archivo exportado
        """
        filepath = self.output_dir / filename
        if not filename.endswith('.csv'):
            filepath = filepath.with_suffix('.csv')
        
        rows = []
        for data in model_data_list:
            row = {
                'model_name': data.model_name,
                'paper_id': data.paper_id or '',
                'category': data.category or '',
                'total_parameters': data.parameters.get('total_parameters', 0),
                'trainable_parameters': data.parameters.get('trainable_parameters', 0),
                'forward_count': data.metrics.get('forward_count', 0),
                'device': data.metadata.get('device', 'unknown'),
                'collected_at': datetime.fromtimestamp(data.collected_at).isoformat()
            }
            rows.append(row)
        
        if PANDAS_AVAILABLE:
            pd = get_pandas()
            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False)
        else:
            # Fallback sin pandas
            if rows:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
        
        logger.info("Datos exportados a CSV", filepath=str(filepath))
        return filepath
    
    def export_html_report(
        self,
        aggregated_data: AggregatedData,
        info_connector: Optional[InfoConnector] = None,
        filename: str = 'model_data_report.html'
    ) -> Path:
        """
        Exporta un reporte HTML con datos agregados.
        
        Args:
            aggregated_data: Datos agregados
            info_connector: Conector a información (opcional)
            filename: Nombre del archivo
        
        Returns:
            Ruta del archivo exportado
        """
        filepath = self.output_dir / filename
        
        html = self._generate_html_report(aggregated_data, info_connector)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info("Reporte HTML exportado", filepath=str(filepath))
        return filepath
    
    def export_markdown_report(
        self,
        aggregated_data: AggregatedData,
        info_connector: Optional[InfoConnector] = None,
        filename: str = 'model_data_report.md'
    ) -> Path:
        """
        Exporta un reporte Markdown con datos agregados.
        
        Args:
            aggregated_data: Datos agregados
            info_connector: Conector a información (opcional)
            filename: Nombre del archivo
        
        Returns:
            Ruta del archivo exportado
        """
        filepath = self.output_dir / filename
        
        md = self._generate_markdown_report(aggregated_data, info_connector)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)
        
        logger.info("Reporte Markdown exportado", filepath=str(filepath))
        return filepath
    
    def _aggregated_to_dict(self, aggregated: AggregatedData) -> Dict[str, Any]:
        """Convierte AggregatedData a diccionario."""
        return {
            'total_models': aggregated.total_models,
            'categories': aggregated.categories,
            'total_parameters': aggregated.total_parameters,
            'benchmark_stats': aggregated.benchmark_stats,
            'metrics_summary': aggregated.metrics_summary,
            'best_models': aggregated.best_models,
            'aggregated_at': aggregated.aggregated_at
        }
    
    def _generate_html_report(
        self,
        aggregated_data: AggregatedData,
        info_connector: Optional[InfoConnector]
    ) -> str:
        """Genera reporte HTML."""
        timestamp = datetime.fromtimestamp(aggregated_data.aggregated_at).strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Model Data Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .stats {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Model Data Report</h1>
    <p><strong>Generated:</strong> {timestamp}</p>
    
    <h2>Summary</h2>
    <div class="stats">
        <p><strong>Total Models:</strong> {aggregated_data.total_models}</p>
        <p><strong>Categories:</strong> {len(aggregated_data.categories)}</p>
    </div>
    
    <h2>Categories</h2>
    <table>
        <tr><th>Category</th><th>Count</th></tr>
"""
        
        for category, count in aggregated_data.categories.items():
            html += f"        <tr><td>{category}</td><td>{count}</td></tr>\n"
        
        html += """    </table>
    
    <h2>Best Models</h2>
    <table>
        <tr><th>Model Name</th><th>Paper ID</th><th>Category</th><th>Score</th></tr>
"""
        
        for model in aggregated_data.best_models:
            html += f"        <tr><td>{model['model_name']}</td><td>{model.get('paper_id', 'N/A')}</td><td>{model.get('category', 'N/A')}</td><td>{model['score']:.2f}</td></tr>\n"
        
        html += """    </table>
</body>
</html>"""
        
        return html
    
    def _generate_markdown_report(
        self,
        aggregated_data: AggregatedData,
        info_connector: Optional[InfoConnector]
    ) -> str:
        """Genera reporte Markdown."""
        timestamp = datetime.fromtimestamp(aggregated_data.aggregated_at).strftime('%Y-%m-%d %H:%M:%S')
        
        md = f"""# Model Data Report

**Generated:** {timestamp}

## Summary

- **Total Models:** {aggregated_data.total_models}
- **Categories:** {len(aggregated_data.categories)}

## Categories

| Category | Count |
|----------|-------|
"""
        
        for category, count in aggregated_data.categories.items():
            md += f"| {category} | {count} |\n"
        
        md += "\n## Best Models\n\n"
        md += "| Model Name | Paper ID | Category | Score |\n"
        md += "|------------|---------|----------|-------|\n"
        
        for model in aggregated_data.best_models:
            md += f"| {model['model_name']} | {model.get('paper_id', 'N/A')} | {model.get('category', 'N/A')} | {model['score']:.2f} |\n"
        
        # Parámetros
        if aggregated_data.total_parameters:
            md += "\n## Parameters Summary\n\n"
            params = aggregated_data.total_parameters
            if 'total_parameters' in params:
                stats = params['total_parameters']
                md += f"- **Total Parameters:** {stats.get('sum', 0):,}\n"
                md += f"- **Mean:** {stats.get('mean', 0):,.0f}\n"
                md += f"- **Median:** {stats.get('median', 0):,.0f}\n"
                md += f"- **Range:** {stats.get('min', 0):,} - {stats.get('max', 0):,}\n"
        
        # Benchmarks
        if aggregated_data.benchmark_stats:
            md += "\n## Benchmark Statistics\n\n"
            for metric, stats in aggregated_data.benchmark_stats.items():
                md += f"### {metric}\n"
                md += f"- **Mean:** {stats.get('mean', 0):.4f}\n"
                md += f"- **Median:** {stats.get('median', 0):.4f}\n"
                md += f"- **Range:** {stats.get('min', 0):.4f} - {stats.get('max', 0):.4f}\n\n"
        
        return md


