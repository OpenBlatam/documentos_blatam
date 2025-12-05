# 🚀 Quick Start - API Multimodal

Guía rápida para empezar a usar la API Multimodal.

## Instalación

```bash
# Instalar dependencias básicas
pip install fastapi uvicorn pydantic

# Opcional: Para cache con Redis
pip install redis

# Opcional: Para WebSockets
pip install websockets
```

## Inicio Rápido

### Opción 1: Script de Ejecución

```bash
python -m multimodal_api.run_server
```

### Opción 2: Desde Código

```python
from multimodal_api import MultimodalAPIServer

server = MultimodalAPIServer()
server.run(host="0.0.0.0", port=8000)
```

## Primer Request

### Generar Video

```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "modality": "video",
    "prompt": "A beautiful sunset over the ocean",
    "parameters": {
      "duration": 10,
      "resolution": "512x512",
      "fps": 24
    }
  }'
```

### Verificar Estado

```bash
curl "http://localhost:8000/api/v1/task/{task_id}"
```

## Ejemplo Python

```python
import requests

# Generar contenido
response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "modality": "image",
        "prompt": "A futuristic cityscape",
        "parameters": {
            "resolution": "1024x1024",
            "style": "cyberpunk"
        }
    }
)

task = response.json()
task_id = task["task_id"]

# Verificar estado
status = requests.get(f"http://localhost:8000/api/v1/task/{task_id}")
print(status.json())
```

## WebSocket para Updates

```python
import asyncio
import websockets
import json

async def listen_updates(task_id: str):
    uri = f"ws://localhost:8000/ws/task/{task_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Update: {data['type']}")

asyncio.run(listen_updates("your-task-id"))
```

## Configuración Básica

Crea un archivo `.env`:

```bash
API_HOST=0.0.0.0
API_PORT=8000
RATE_LIMIT_MAX_REQUESTS=100
CACHE_BACKEND=memory
```

## Documentación Interactiva

Una vez iniciado el servidor, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints Principales

- `POST /api/v1/generate` - Generar contenido
- `GET /api/v1/task/{task_id}` - Estado de tarea
- `GET /health` - Health check
- `GET /metrics` - Métricas
- `WS /ws/task/{task_id}` - WebSocket updates

## Próximos Pasos

1. Lee el [README.md](README.md) para documentación completa
2. Revisa [FEATURES.md](FEATURES.md) para todas las características
3. Consulta [ARCHITECTURE.md](ARCHITECTURE.md) para entender la arquitectura
4. Mira [example_usage.py](example_usage.py) para más ejemplos


