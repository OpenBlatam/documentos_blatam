#!/usr/bin/env python3
"""
Sistema de Reportes para la API Multimodal.

Genera reportes detallados del sistema.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class Report:
    """Reporte."""
    id: str
    title: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    data: Dict[str, Any]
    format: str = "json"  # json, csv, pdf


class ReportGenerator:
    """Generador de reportes."""
    
    def __init__(self):
        """Inicializa el generador de reportes."""
        self.reports: Dict[str, Report] = {}
    
    def generate_usage_report(
        self,
        analytics_engine,
        days: int = 7
    ) -> Report:
        """
        Genera reporte de uso.
        
        Args:
            analytics_engine: Instancia de AnalyticsEngine
            days: Días a analizar
        
        Returns:
            Reporte
        """
        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)
        
        usage_stats = analytics_engine.get_usage_stats(days)
        performance_metrics = analytics_engine.get_performance_metrics(days)
        trends = analytics_engine.get_trends(days)
        
        report_id = f"usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = Report(
            id=report_id,
            title=f"Reporte de Uso - {days} días",
            report_type="usage",
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            data={
                "usage": {
                    "total_requests": usage_stats.total_requests,
                    "successful_requests": usage_stats.successful_requests,
                    "failed_requests": usage_stats.failed_requests,
                    "by_modality": usage_stats.by_modality,
                    "by_generation_type": usage_stats.by_generation_type,
                    "avg_processing_time": usage_stats.avg_processing_time,
                    "peak_hour": usage_stats.peak_hour,
                    "peak_day": usage_stats.peak_day
                },
                "performance": {
                    "avg_response_time": performance_metrics.avg_response_time,
                    "p95_response_time": performance_metrics.p95_response_time,
                    "p99_response_time": performance_metrics.p99_response_time,
                    "throughput": performance_metrics.throughput,
                    "error_rate": performance_metrics.error_rate
                },
                "trends": trends
            }
        )
        
        self.reports[report_id] = report
        logger.info(f"Reporte de uso generado: {report_id}")
        
        return report
    
    def generate_security_report(
        self,
        security_manager,
        days: int = 7
    ) -> Report:
        """
        Genera reporte de seguridad.
        
        Args:
            security_manager: Instancia de SecurityManager
            days: Días a analizar
        
        Returns:
            Reporte
        """
        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)
        
        stats = security_manager.get_security_stats()
        
        report_id = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = Report(
            id=report_id,
            title=f"Reporte de Seguridad - {days} días",
            report_type="security",
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            data={
                "blocked_ips": stats.get("blocked_ips", 0),
                "failed_attempts": stats.get("failed_attempts", 0),
                "unique_identifiers": stats.get("unique_identifiers", 0)
            }
        )
        
        self.reports[report_id] = report
        logger.info(f"Reporte de seguridad generado: {report_id}")
        
        return report
    
    def generate_performance_report(
        self,
        performance_optimizer,
        days: int = 7
    ) -> Report:
        """
        Genera reporte de rendimiento.
        
        Args:
            performance_optimizer: Instancia de PerformanceOptimizer
            days: Días a analizar
        
        Returns:
            Reporte
        """
        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)
        
        stats = performance_optimizer.get_performance_stats()
        
        report_id = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = Report(
            id=report_id,
            title=f"Reporte de Rendimiento - {days} días",
            report_type="performance",
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            data=stats
        )
        
        self.reports[report_id] = report
        logger.info(f"Reporte de rendimiento generado: {report_id}")
        
        return report
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """
        Obtiene un reporte.
        
        Args:
            report_id: ID de reporte
        
        Returns:
            Reporte o None
        """
        return self.reports.get(report_id)
    
    def list_reports(
        self,
        report_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista reportes.
        
        Args:
            report_type: Filtrar por tipo
        
        Returns:
            Lista de reportes
        """
        reports = list(self.reports.values())
        
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        
        return [
            {
                "id": r.id,
                "title": r.title,
                "report_type": r.report_type,
                "generated_at": r.generated_at.isoformat(),
                "period_start": r.period_start.isoformat(),
                "period_end": r.period_end.isoformat(),
                "format": r.format
            }
            for r in sorted(reports, key=lambda x: x.generated_at, reverse=True)
        ]
    
    def export_report(self, report_id: str, format: str = "json") -> str:
        """
        Exporta un reporte.
        
        Args:
            report_id: ID de reporte
            format: Formato (json, csv)
        
        Returns:
            Contenido del reporte
        """
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Reporte {report_id} no encontrado")
        
        if format == "json":
            return json.dumps({
                "id": report.id,
                "title": report.title,
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "data": report.data
            }, indent=2)
        
        elif format == "csv":
            # Implementación básica de CSV
            lines = [f"{report.title}"]
            lines.append(f"Generado: {report.generated_at.isoformat()}")
            lines.append(f"Período: {report.period_start.isoformat()} - {report.period_end.isoformat()}")
            lines.append("")
            
            # Convertir datos a CSV básico
            for key, value in report.data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k},{v}")
                else:
                    lines.append(f"{key},{value}")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Formato no soportado: {format}")


