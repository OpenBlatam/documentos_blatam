#!/usr/bin/env python3
"""
Sistema de Quotas y Límites Avanzados para la API Multimodal.

Gestión de quotas por usuario, plan, o recurso.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class QuotaType(str, Enum):
    """Tipos de quota."""
    REQUESTS_PER_DAY = "requests_per_day"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    STORAGE_GB = "storage_gb"
    TASKS_CONCURRENT = "tasks_concurrent"
    BANDWIDTH_GB = "bandwidth_gb"


@dataclass
class Quota:
    """Quota."""
    quota_type: QuotaType
    limit: float
    current: float = 0.0
    reset_at: Optional[datetime] = None
    period_seconds: Optional[int] = None


@dataclass
class QuotaPlan:
    """Plan de quotas."""
    plan_id: str
    name: str
    quotas: Dict[QuotaType, Quota]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QuotaManager:
    """Gestor de quotas."""
    
    def __init__(self):
        """Inicializa el gestor de quotas."""
        self.user_plans: Dict[str, str] = {}  # user_id -> plan_id
        self.plans: Dict[str, QuotaPlan] = {}
        self.user_quotas: Dict[str, Dict[QuotaType, Quota]] = {}
        
        # Crear plan por defecto
        self._create_default_plan()
    
    def _create_default_plan(self):
        """Crea plan por defecto."""
        default_plan = QuotaPlan(
            plan_id="default",
            name="Default Plan",
            quotas={
                QuotaType.REQUESTS_PER_DAY: Quota(
                    quota_type=QuotaType.REQUESTS_PER_DAY,
                    limit=1000,
                    period_seconds=86400
                ),
                QuotaType.REQUESTS_PER_HOUR: Quota(
                    quota_type=QuotaType.REQUESTS_PER_HOUR,
                    limit=100,
                    period_seconds=3600
                ),
                QuotaType.STORAGE_GB: Quota(
                    quota_type=QuotaType.STORAGE_GB,
                    limit=10.0
                )
            }
        )
        self.plans["default"] = default_plan
    
    def create_plan(
        self,
        plan_id: str,
        name: str,
        quotas: Dict[QuotaType, float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Crea un plan de quotas.
        
        Args:
            plan_id: ID del plan
            name: Nombre del plan
            quotas: Diccionario de quotas
            metadata: Metadatos adicionales
        """
        quota_objects = {}
        for quota_type, limit in quotas.items():
            period_seconds = None
            if quota_type == QuotaType.REQUESTS_PER_DAY:
                period_seconds = 86400
            elif quota_type == QuotaType.REQUESTS_PER_HOUR:
                period_seconds = 3600
            elif quota_type == QuotaType.REQUESTS_PER_MINUTE:
                period_seconds = 60
            
            quota_objects[quota_type] = Quota(
                quota_type=quota_type,
                limit=limit,
                period_seconds=period_seconds
            )
        
        plan = QuotaPlan(
            plan_id=plan_id,
            name=name,
            quotas=quota_objects,
            metadata=metadata or {}
        )
        
        self.plans[plan_id] = plan
        logger.info(f"Plan creado: {plan_id}")
    
    def assign_plan(self, user_id: str, plan_id: str):
        """
        Asigna un plan a un usuario.
        
        Args:
            user_id: ID de usuario
            plan_id: ID del plan
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan {plan_id} no existe")
        
        self.user_plans[user_id] = plan_id
        
        # Inicializar quotas del usuario
        plan = self.plans[plan_id]
        self.user_quotas[user_id] = {}
        for quota_type, quota in plan.quotas.items():
            reset_at = None
            if quota.period_seconds:
                reset_at = datetime.now() + timedelta(seconds=quota.period_seconds)
            
            self.user_quotas[user_id][quota_type] = Quota(
                quota_type=quota_type,
                limit=quota.limit,
                current=0.0,
                reset_at=reset_at,
                period_seconds=quota.period_seconds
            )
        
        logger.info(f"Plan {plan_id} asignado a usuario {user_id}")
    
    def check_quota(
        self,
        user_id: str,
        quota_type: QuotaType,
        amount: float = 1.0
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Verifica si hay quota disponible.
        
        Args:
            user_id: ID de usuario
            quota_type: Tipo de quota
            amount: Cantidad a verificar
        
        Returns:
            (permitido, información)
        """
        # Obtener plan del usuario
        plan_id = self.user_plans.get(user_id, "default")
        if plan_id not in self.plans:
            plan_id = "default"
        
        # Inicializar quotas si no existen
        if user_id not in self.user_quotas:
            self.assign_plan(user_id, plan_id)
        
        quota = self.user_quotas[user_id].get(quota_type)
        if not quota:
            # No hay límite para este tipo
            return True, {"unlimited": True}
        
        # Verificar si necesita reset
        if quota.reset_at and datetime.now() >= quota.reset_at:
            quota.current = 0.0
            if quota.period_seconds:
                quota.reset_at = datetime.now() + timedelta(seconds=quota.period_seconds)
        
        # Verificar quota
        available = quota.limit - quota.current
        allowed = available >= amount
        
        info = {
            "limit": quota.limit,
            "current": quota.current,
            "available": max(0, available),
            "reset_at": quota.reset_at.isoformat() if quota.reset_at else None
        }
        
        return allowed, info
    
    def consume_quota(
        self,
        user_id: str,
        quota_type: QuotaType,
        amount: float = 1.0
    ):
        """
        Consume quota.
        
        Args:
            user_id: ID de usuario
            quota_type: Tipo de quota
            amount: Cantidad a consumir
        """
        if user_id not in self.user_quotas:
            plan_id = self.user_plans.get(user_id, "default")
            self.assign_plan(user_id, plan_id)
        
        quota = self.user_quotas[user_id].get(quota_type)
        if quota:
            quota.current += amount
            logger.debug(f"Quota consumida: {user_id} - {quota_type.value} - {amount}")
    
    def get_user_quotas(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene quotas de un usuario.
        
        Args:
            user_id: ID de usuario
        
        Returns:
            Quotas del usuario
        """
        plan_id = self.user_plans.get(user_id, "default")
        
        if user_id not in self.user_quotas:
            self.assign_plan(user_id, plan_id)
        
        quotas = {}
        for quota_type, quota in self.user_quotas[user_id].items():
            quotas[quota_type.value] = {
                "limit": quota.limit,
                "current": quota.current,
                "available": max(0, quota.limit - quota.current),
                "reset_at": quota.reset_at.isoformat() if quota.reset_at else None
            }
        
        return {
            "user_id": user_id,
            "plan_id": plan_id,
            "quotas": quotas
        }
    
    def get_plans(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los planes.
        
        Returns:
            Lista de planes
        """
        return [
            {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "quotas": {
                    qt.value: q.limit
                    for qt, q in plan.quotas.items()
                },
                "metadata": plan.metadata
            }
            for plan in self.plans.values()
        ]


