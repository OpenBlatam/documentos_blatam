#!/usr/bin/env python3
"""
Servidor de Chat - Similar a ChatGPT
=====================================

Script principal para ejecutar el servidor de chat.
Puede ejecutarse directamente o como módulo.
"""

import os
import sys
from pathlib import Path

# Añadir el directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from core.chat_api import create_chat_app
from core.utils import setup_logger
import uvicorn

logger = setup_logger(__name__)


def main():
    """Función principal para ejecutar el servidor."""
    # Configuración desde variables de entorno
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    system_prompt = os.getenv("SYSTEM_PROMPT")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(
        "Iniciando servidor de chat",
        provider=provider,
        model=model,
        host=host,
        port=port
    )
    
    # Crear aplicación
    app = create_chat_app(
        provider=provider,
        model=model,
        api_key=api_key,
        system_prompt=system_prompt
    )
    
    # Ejecutar servidor
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()



