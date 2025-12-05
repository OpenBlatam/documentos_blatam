#!/usr/bin/env python3
"""
Utilidades para APIs y servicios web.

Incluye:
- FastAPI helpers
- Flask helpers
- Async HTTP clients
- Request utilities
"""

from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps
import time

try:
    from fastapi import FastAPI, Request, Response, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from flask import Flask, request, jsonify, make_response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    import aiohttp
    import asyncio
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .utils import setup_logger, retry_on_failure

logger = setup_logger(__name__)


def create_fastapi_app(
    title: str = "ML API",
    version: str = "1.0.0",
    enable_cors: bool = True
) -> Any:
    """
    Crea una aplicación FastAPI con configuración por defecto.
    
    Args:
        title: Título de la API
        version: Versión de la API
        enable_cors: Si True, habilita CORS
    
    Returns:
        Aplicación FastAPI
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI no está instalado. Instala con: pip install fastapi uvicorn")
    
    app = FastAPI(title=title, version=version)
    
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        return response
    
    return app


def create_flask_app(name: str = "ML API") -> Any:
    """
    Crea una aplicación Flask con configuración por defecto.
    
    Args:
        name: Nombre de la aplicación
    
    Returns:
        Aplicación Flask
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask no está instalado. Instala con: pip install flask")
    
    app = Flask(name)
    
    @app.before_request
    def log_request_info():
        logger.info(
            "Request received",
            method=request.method,
            url=request.url,
            remote_addr=request.remote_addr
        )
    
    @app.after_request
    def log_response_info(response):
        logger.info(
            "Response sent",
            status_code=response.status_code
        )
        return response
    
    return app


@retry_on_failure(max_attempts=3)
def http_get(url: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Realiza una petición HTTP GET.
    
    Args:
        url: URL a consultar
        **kwargs: Argumentos adicionales para requests
    
    Returns:
        Respuesta JSON o None
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests no está instalado. Instala con: pip install requests")
    
    from .error_handling import retry, RetryStrategy, safe_execute
    
    @retry(
        max_attempts=3,
        delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=(requests.RequestException, requests.Timeout, requests.ConnectionError)
    )
    def _make_request():
        response = requests.get(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    
    result, error = safe_execute(_make_request, default_value=None, log_errors=True)
    if error:
        logger.error("Error en petición HTTP", url=url, error=str(error))
    return result


async def async_http_get(url: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Realiza una petición HTTP GET asíncrona.
    
    Args:
        url: URL a consultar
        **kwargs: Argumentos adicionales
    
    Returns:
        Respuesta JSON o None
    """
    if HTTPX_AVAILABLE:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0, **kwargs)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error en petición HTTP asíncrona", url=url, error=str(e))
                return None
    elif AIOHTTP_AVAILABLE:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error("Error en petición HTTP asíncrona", url=url, error=str(e))
                return None
    else:
        raise ImportError("httpx o aiohttp no están instalados")


def api_error_handler(func: Callable) -> Callable:
    """
    Decorador para manejo de errores en APIs.
    
    Args:
        func: Función a decorar
    
    Returns:
        Función decorada
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error("Error en API", error=str(e), function=func.__name__)
            if FASTAPI_AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
            elif FLASK_AVAILABLE:
                return jsonify({"error": str(e)}), 500
            else:
                raise
    
    return wrapper

