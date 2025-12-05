#!/usr/bin/env python3
"""
Script para ejecutar el servidor de la API Multimodal.

Uso:
    python -m multimodal_api.run_server
    python -m multimodal_api.run_server --host 0.0.0.0 --port 8000
"""

import argparse
from multimodal_api.api_server import MultimodalAPIServer
from multimodal_api.middleware import RateLimitConfig, CacheConfig
from multimodal_api.config import config


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="API de Generación Multimodal")
    parser.add_argument("--host", type=str, default=config.host, help="Host del servidor")
    parser.add_argument("--port", type=int, default=config.port, help="Puerto del servidor")
    parser.add_argument("--reload", action="store_true", help="Recarga automática (desarrollo)")
    
    args = parser.parse_args()
    
    # Configurar rate limiting
    rate_limit_config = RateLimitConfig(
        max_requests=config.rate_limit_max_requests,
        window_seconds=config.rate_limit_window_seconds,
        strategy=config.rate_limit_strategy
    )
    
    # Configurar cache
    cache_config = CacheConfig(
        backend=config.cache_backend,
        redis_url=config.cache_redis_url,
        default_ttl=config.cache_default_ttl,
        max_size=config.cache_max_size
    )
    
    # Crear y ejecutar servidor
    server = MultimodalAPIServer(
        rate_limit_config=rate_limit_config,
        cache_config=cache_config
    )
    
    print(f"🚀 Iniciando servidor en http://{args.host}:{args.port}")
    print(f"📚 Documentación: http://{args.host}:{args.port}/docs")
    print(f"❤️  Health check: http://{args.host}:{args.port}/health")
    
    server.run(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()


