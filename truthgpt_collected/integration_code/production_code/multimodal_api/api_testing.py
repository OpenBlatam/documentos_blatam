#!/usr/bin/env python3
"""
Utilidades de Testing para la API Multimodal.

Proporciona helpers para testing de la API.
"""

from typing import Dict, Any, Optional, List
import asyncio
import time

try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from core.utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class APITester:
    """Tester para la API."""
    
    def __init__(self, app):
        """
        Inicializa el tester.
        
        Args:
            app: Aplicación FastAPI
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI no está disponible")
        
        self.client = TestClient(app)
        self.results: List[Dict[str, Any]] = []
    
    def test_endpoint(
        self,
        method: str,
        path: str,
        expected_status: int = 200,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prueba un endpoint.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            path: Ruta del endpoint
            expected_status: Status esperado
            **kwargs: Argumentos adicionales para el request
        
        Returns:
            Resultado de la prueba
        """
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.client.get(path, **kwargs)
            elif method.upper() == "POST":
                response = self.client.post(path, **kwargs)
            elif method.upper() == "PUT":
                response = self.client.put(path, **kwargs)
            elif method.upper() == "DELETE":
                response = self.client.delete(path, **kwargs)
            else:
                raise ValueError(f"Método no soportado: {method}")
            
            duration = time.time() - start_time
            success = response.status_code == expected_status
            
            result = {
                "method": method,
                "path": path,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "duration": duration,
                "response_size": len(response.content) if response.content else 0
            }
            
            self.results.append(result)
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "method": method,
                "path": path,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "duration": duration,
                "error": str(e)
            }
            self.results.append(result)
            return result
    
    def test_generation(
        self,
        modality: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prueba generación.
        
        Args:
            modality: Modalidad
            prompt: Prompt
            parameters: Parámetros
        
        Returns:
            Resultado
        """
        payload = {
            "modality": modality,
            "prompt": prompt,
            "parameters": parameters or {}
        }
        
        return self.test_endpoint(
            "POST",
            "/api/v1/generate",
            expected_status=200,
            json=payload
        )
    
    def test_health(self) -> Dict[str, Any]:
        """Prueba health check."""
        return self.test_endpoint("GET", "/health", expected_status=200)
    
    def test_metrics(self) -> Dict[str, Any]:
        """Prueba métricas."""
        return self.test_endpoint("GET", "/metrics", expected_status=200)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de pruebas.
        
        Returns:
            Resumen
        """
        if not self.results:
            return {"total": 0}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        failed = total - successful
        
        durations = [r.get("duration", 0) for r in self.results]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_duration": avg_duration,
            "results": self.results
        }
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """
        Ejecuta smoke tests básicos.
        
        Returns:
            Resultados
        """
        logger.info("Ejecutando smoke tests...")
        
        # Health check
        self.test_health()
        
        # Metrics
        self.test_metrics()
        
        # Analytics
        self.test_endpoint("GET", "/analytics", expected_status=200)
        
        # Version
        self.test_endpoint("GET", "/version", expected_status=200)
        
        return self.get_summary()


