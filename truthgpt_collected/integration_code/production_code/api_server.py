#!/usr/bin/env python3
"""
Servidor API
============

Script para iniciar el servidor API unificado.
"""

import uvicorn
import argparse
from pathlib import Path

from application import create_app

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Servidor API Unificado')
    parser.add_argument('--host', default='0.0.0.0', help='Host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Puerto (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Recargar automáticamente')
    parser.add_argument('--workers', type=int, default=1, help='Número de workers')
    
    args = parser.parse_args()
    
    app = create_app()
    
    print("=" * 60)
    print("🚀 Production Code API Server")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Workers: {args.workers}")
    print(f"Reload: {args.reload}")
    print("=" * 60)
    print(f"\n📡 API disponible en: http://{args.host}:{args.port}")
    print(f"📊 Dashboard: http://{args.host}:{args.port}/dashboard")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    print("\n")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1
    )


if __name__ == "__main__":
    main()


