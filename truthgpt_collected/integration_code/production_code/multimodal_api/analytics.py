#!/usr/bin/env python3
"""
Sistema de Analytics Avanzado para la API Multimodal.

Proporciona análisis detallado de uso, rendimiento y tendencias.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Estadísticas de uso."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    by_modality: Dict[str, int] = field(default_factory=dict)
    by_generation_type: Dict[str, int] = field(default_factory=dict)
    avg_processing_time: float = 0.0
    peak_hour: Optional[str] = None
    peak_day: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento."""
    avg_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    throughput: float = 0.0  # requests per second
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    queue_wait_time: float = 0.0


class AnalyticsEngine:
    """Motor de analytics avanzado."""
    
    def __init__(self, retention_days: int = 30):
        """
        Inicializa el motor de analytics.
        
        Args:
            retention_days: Días de retención de datos
        """
        self.retention_days = retention_days
        self.request_history: List[Dict[str, Any]] = []
        self.task_history: List[Dict[str, Any]] = []
        self.hourly_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.daily_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def record_request(
        self,
        modality: str,
        generation_type: str,
        success: bool,
        response_time: float,
        user_id: Optional[str] = None
    ):
        """
        Registra un request.
        
        Args:
            modality: Modalidad
            generation_type: Tipo de generación
            success: Si fue exitoso
            response_time: Tiempo de respuesta
            user_id: ID de usuario (opcional)
        """
        record = {
            "timestamp": datetime.now(),
            "modality": modality,
            "generation_type": generation_type,
            "success": success,
            "response_time": response_time,
            "user_id": user_id
        }
        
        self.request_history.append(record)
        
        # Actualizar estadísticas por hora
        hour_key = record["timestamp"].strftime("%Y-%m-%d %H:00")
        if hour_key not in self.hourly_stats:
            self.hourly_stats[hour_key] = {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "response_times": []
            }
        
        self.hourly_stats[hour_key]["requests"] += 1
        if success:
            self.hourly_stats[hour_key]["successful"] += 1
        else:
            self.hourly_stats[hour_key]["failed"] += 1
        self.hourly_stats[hour_key]["response_times"].append(response_time)
        
        # Actualizar estadísticas diarias
        day_key = record["timestamp"].strftime("%Y-%m-%d")
        if day_key not in self.daily_stats:
            self.daily_stats[day_key] = {
                "requests": 0,
                "successful": 0,
                "failed": 0
            }
        
        self.daily_stats[day_key]["requests"] += 1
        if success:
            self.daily_stats[day_key]["successful"] += 1
        else:
            self.daily_stats[day_key]["failed"] += 1
        
        # Limpiar datos antiguos
        self._cleanup_old_data()
    
    def record_task(
        self,
        task_id: str,
        modality: str,
        status: str,
        processing_time: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Registra una tarea.
        
        Args:
            task_id: ID de tarea
            modality: Modalidad
            status: Estado final
            processing_time: Tiempo de procesamiento
            error: Error si hubo
        """
        record = {
            "task_id": task_id,
            "timestamp": datetime.now(),
            "modality": modality,
            "status": status,
            "processing_time": processing_time,
            "error": error
        }
        
        self.task_history.append(record)
        self._cleanup_old_data()
    
    def _cleanup_old_data(self):
        """Limpia datos antiguos."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        self.request_history = [
            r for r in self.request_history
            if r["timestamp"] > cutoff
        ]
        
        self.task_history = [
            t for t in self.task_history
            if t["timestamp"] > cutoff
        ]
        
        # Limpiar estadísticas por hora
        hour_cutoff = cutoff.strftime("%Y-%m-%d %H:00")
        self.hourly_stats = {
            k: v for k, v in self.hourly_stats.items()
            if k > hour_cutoff
        }
        
        # Limpiar estadísticas diarias
        day_cutoff = cutoff.strftime("%Y-%m-%d")
        self.daily_stats = {
            k: v for k, v in self.daily_stats.items()
            if k > day_cutoff
        }
    
    def get_usage_stats(self, days: int = 7) -> UsageStats:
        """
        Obtiene estadísticas de uso.
        
        Args:
            days: Número de días a analizar
        
        Returns:
            Estadísticas de uso
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_requests = [
            r for r in self.request_history
            if r["timestamp"] > cutoff
        ]
        
        recent_tasks = [
            t for t in self.task_history
            if t["timestamp"] > cutoff
        ]
        
        stats = UsageStats(
            total_requests=len(recent_requests),
            successful_requests=sum(1 for r in recent_requests if r["success"]),
            failed_requests=sum(1 for r in recent_requests if not r["success"]),
            total_tasks=len(recent_tasks),
            completed_tasks=sum(1 for t in recent_tasks if t["status"] == "completed"),
            failed_tasks=sum(1 for t in recent_tasks if t["status"] == "failed")
        )
        
        # Por modalidad
        for request in recent_requests:
            modality = request["modality"]
            stats.by_modality[modality] = stats.by_modality.get(modality, 0) + 1
        
        # Por tipo de generación
        for request in recent_requests:
            gen_type = request["generation_type"]
            stats.by_generation_type[gen_type] = stats.by_generation_type.get(gen_type, 0) + 1
        
        # Tiempo promedio de procesamiento
        processing_times = [
            t["processing_time"] for t in recent_tasks
            if t["processing_time"] is not None
        ]
        if processing_times:
            stats.avg_processing_time = statistics.mean(processing_times)
        
        # Hora pico
        if self.hourly_stats:
            peak_hour = max(
                self.hourly_stats.items(),
                key=lambda x: x[1]["requests"]
            )
            stats.peak_hour = peak_hour[0]
        
        # Día pico
        if self.daily_stats:
            peak_day = max(
                self.daily_stats.items(),
                key=lambda x: x[1]["requests"]
            )
            stats.peak_day = peak_day[0]
        
        return stats
    
    def get_performance_metrics(self, days: int = 7) -> PerformanceMetrics:
        """
        Obtiene métricas de rendimiento.
        
        Args:
            days: Número de días a analizar
        
        Returns:
            Métricas de rendimiento
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_requests = [
            r for r in self.request_history
            if r["timestamp"] > cutoff
        ]
        
        if not recent_requests:
            return PerformanceMetrics()
        
        response_times = [r["response_time"] for r in recent_requests]
        response_times.sort()
        
        metrics = PerformanceMetrics(
            avg_response_time=statistics.mean(response_times),
            p50_response_time=statistics.median(response_times),
            p95_response_time=response_times[int(len(response_times) * 0.95)] if response_times else 0.0,
            p99_response_time=response_times[int(len(response_times) * 0.99)] if response_times else 0.0,
            error_rate=sum(1 for r in recent_requests if not r["success"]) / len(recent_requests)
        )
        
        # Throughput (requests per second)
        if recent_requests:
            time_span = (recent_requests[-1]["timestamp"] - recent_requests[0]["timestamp"]).total_seconds()
            if time_span > 0:
                metrics.throughput = len(recent_requests) / time_span
        
        return metrics
    
    def get_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Obtiene tendencias.
        
        Args:
            days: Número de días a analizar
        
        Returns:
            Tendencias
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Tendencias diarias
        daily_trends = []
        for i in range(days):
            day = datetime.now() - timedelta(days=i)
            day_key = day.strftime("%Y-%m-%d")
            stats = self.daily_stats.get(day_key, {"requests": 0, "successful": 0, "failed": 0})
            daily_trends.append({
                "date": day_key,
                "requests": stats["requests"],
                "successful": stats["successful"],
                "failed": stats["failed"]
            })
        
        daily_trends.reverse()
        
        return {
            "daily_trends": daily_trends,
            "growth_rate": self._calculate_growth_rate(days)
        }
    
    def _calculate_growth_rate(self, days: int) -> float:
        """
        Calcula tasa de crecimiento.
        
        Args:
            days: Días a analizar
        
        Returns:
            Tasa de crecimiento
        """
        if days < 2:
            return 0.0
        
        first_half = self.get_usage_stats(days // 2)
        second_half = self.get_usage_stats(days)
        
        if first_half.total_requests == 0:
            return 0.0
        
        growth = (second_half.total_requests - first_half.total_requests) / first_half.total_requests
        return growth * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen completo de analytics.
        
        Returns:
            Resumen
        """
        usage = self.get_usage_stats()
        performance = self.get_performance_metrics()
        trends = self.get_trends()
        
        return {
            "usage": {
                "total_requests": usage.total_requests,
                "successful_requests": usage.successful_requests,
                "failed_requests": usage.failed_requests,
                "total_tasks": usage.total_tasks,
                "completed_tasks": usage.completed_tasks,
                "failed_tasks": usage.failed_tasks,
                "by_modality": usage.by_modality,
                "by_generation_type": usage.by_generation_type,
                "avg_processing_time": usage.avg_processing_time,
                "peak_hour": usage.peak_hour,
                "peak_day": usage.peak_day
            },
            "performance": {
                "avg_response_time": performance.avg_response_time,
                "p50_response_time": performance.p50_response_time,
                "p95_response_time": performance.p95_response_time,
                "p99_response_time": performance.p99_response_time,
                "throughput": performance.throughput,
                "error_rate": performance.error_rate
            },
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }


