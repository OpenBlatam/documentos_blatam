# Ejemplos de Uso de la API Sora

## 🚀 Inicio Rápido

### 1. Iniciar el Servidor

```bash
# Opción 1: Usando CLI
sora serve --port 8000

# Opción 2: Directamente con Python
python -m sora.api_server --port 8000

# Opción 3: Desde código
from sora import SoraAPIServer
server = SoraAPIServer()
server.run(host="0.0.0.0", port=8000)
```

### 2. Acceder a la Documentación

Una vez iniciado el servidor, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📝 Ejemplos de Uso

### Text-to-Video

#### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/text-to-video"

payload = {
    "prompt": "A cinematic shot of a futuristic city at sunset",
    "num_inference_steps": 20,
    "seed": 42,
    "fps": 24,
    "resolution": [256, 256],
    "video_length": 16,
    "hidden_dim": 512
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Video ID: {result['video_id']}")
print(f"Status: {result['status']}")
print(f"Download URL: {result['download_url']}")

# Descargar video
video_url = f"http://localhost:8000{result['download_url']}"
video_response = requests.get(video_url)

with open("output.mp4", "wb") as f:
    f.write(video_response.content)
```

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/text-to-video" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "num_inference_steps": 20,
    "fps": 24,
    "resolution": [256, 256]
  }'
```

#### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/api/v1/text-to-video', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    prompt: 'A cat playing piano',
    num_inference_steps: 20,
    fps: 24,
    resolution: [256, 256]
  })
});

const result = await response.json();
console.log('Video ID:', result.video_id);
console.log('Download URL:', result.download_url);
```

### Image-to-Video

#### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/image-to-video"

with open("image.jpg", "rb") as f:
    files = {"file": f}
    data = {
        "motion_strength": 0.7,
        "num_inference_steps": 20,
        "fps": 24,
        "resolution": "[256, 256]",
        "video_length": 16
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Video ID: {result['video_id']}")
    
    # Descargar video
    video_url = f"http://localhost:8000{result['download_url']}"
    video_response = requests.get(video_url)
    
    with open("animated.mp4", "wb") as f:
        f.write(video_response.content)
```

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/image-to-video" \
  -F "file=@image.jpg" \
  -F "motion_strength=0.7" \
  -F "num_inference_steps=20" \
  -F "fps=24" \
  -F "resolution=[256,256]"
```

### Gestión de Modelos

#### Listar Modelos Cargados

```python
import requests

response = requests.get("http://localhost:8000/api/v1/models")
models = response.json()

print(f"Modelos cargados: {models['count']}")
print(f"Keys: {models['models']}")
```

#### Descargar Modelo

```python
import requests

model_key = "text2video_512_16"
response = requests.delete(f"http://localhost:8000/api/v1/models/{model_key}")

print(response.json())
```

### Health Check

```python
import requests

response = requests.get("http://localhost:8000/health")
status = response.json()

print(f"Status: {status['status']}")
print(f"Models loaded: {status['models_loaded']}")
```

## 🔧 Configuración Avanzada

### Usar Directorio Personalizado para Modelos

```python
from pathlib import Path
from sora import SoraAPIServer

models_dir = Path("./my_models")
server = SoraAPIServer(models_dir=models_dir)
server.run(port=8000)
```

### Integración con FastAPI Existente

```python
from fastapi import FastAPI
from sora import create_app

# Crear app Sora
sora_app = create_app()

# Integrar con app existente
main_app = FastAPI()

# Montar app Sora
main_app.mount("/sora", sora_app)
```

## 📊 Monitoreo y Logging

El servidor incluye logging automático de todas las requests:

```python
# Los logs incluyen:
# - Método HTTP
# - URL
# - Status code
# - Tiempo de procesamiento
```

## 🚨 Manejo de Errores

### Errores Comunes

```python
import requests

try:
    response = requests.post("http://localhost:8000/api/v1/text-to-video", json={
        "prompt": "test"
    })
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"Error HTTP: {e}")
    print(f"Response: {e.response.json()}")
```

### Validación de Inputs

La API valida automáticamente todos los inputs usando Pydantic:

- Resoluciones deben ser válidas
- Valores numéricos deben estar en rangos permitidos
- Tipos de datos deben ser correctos

## 🔐 Seguridad (Futuro)

Para producción, considera agregar:

- Autenticación (API keys, JWT)
- Rate limiting
- Validación de inputs más estricta
- HTTPS
- CORS configurado apropiadamente

## 📈 Performance Tips

1. **Reutilizar Modelos**: Los modelos se mantienen en memoria para reutilización
2. **Batch Processing**: Para múltiples requests, considera procesamiento en batch
3. **Caching**: Los videos generados se guardan temporalmente
4. **Async**: La API es async, puede manejar múltiples requests concurrentes

## 🚦 Rate Limiting y Métricas

### Verificar Rate Limits

```python
import requests

# Obtener información de rate limiting
response = requests.get("http://localhost:8000/api/v1/rate-limit")
limits = response.json()

print(f"Límites: {limits['limits']}")
print(f"Remaining: {limits['remaining']}")
```

### Ver Métricas de la API

```python
import requests

response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()

print(f"Total requests: {metrics['api_metrics']['total_requests']}")
print(f"Success rate: {metrics['api_metrics']['success_rate']:.2%}")
print(f"Avg generation time: {metrics['api_metrics']['average_generation_time']:.2f}s")
```

## 📦 Batch Processing

### Procesar Múltiples Videos

```python
import requests

# Procesar batch de videos
response = requests.post(
    "http://localhost:8000/api/v1/text-to-video/batch",
    json={
        "prompts": [
            "A beautiful sunset",
            "A cat playing piano",
            "A futuristic city"
        ],
        "hidden_dim": 256,
        "video_length": 8,
        "resolution": [128, 128],
        "fps": 24
    }
)

result = response.json()
print(f"Total: {result['total']}")
print(f"Successful: {result['successful']}")
print(f"Failed: {result['failed']}")
```

## 🔄 Async Processing

### Procesamiento Asíncrono

```python
import requests
import time

# Encolar tarea asíncrona
response = requests.post(
    "http://localhost:8000/api/v1/text-to-video/async",
    json={
        "prompt": "A beautiful sunset",
        "num_inference_steps": 20,
        "fps": 24
    }
)

task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# Verificar estado
while True:
    status_response = requests.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
    status = status_response.json()
    
    print(f"Status: {status['status']}")
    
    if status['status'] == 'completed':
        # Obtener resultado
        result_response = requests.get(f"http://localhost:8000/api/v1/tasks/{task_id}/result")
        result = result_response.json()
        print(f"Video ID: {result['video_id']}")
        print(f"Download URL: {result['download_url']}")
        break
    elif status['status'] == 'failed':
        print(f"Error: {status.get('error')}")
        break
    
    time.sleep(2)
```

## 💾 Cache Management

### Estadísticas de Caché

```python
import requests

# Obtener estadísticas
response = requests.get("http://localhost:8000/api/v1/cache/stats")
stats = response.json()

print(f"Hit rate: {stats['hit_rate']:.2f}%")
print(f"Cache size: {stats['cache_size']}/{stats['max_size']}")

# Limpiar caché
response = requests.delete("http://localhost:8000/api/v1/cache")
print(response.json()["message"])
```

## 🔄 Queue Statistics

### Estadísticas de Cola

```python
import requests

response = requests.get("http://localhost:8000/api/v1/queue/stats")
stats = response.json()

print(f"Queue size: {stats['queue_size']}")
print(f"Active workers: {stats['active_workers']}")
print(f"Tasks by status: {stats['tasks_by_status']}")
```

## 🧪 Testing

### Test con pytest

```python
import pytest
from fastapi.testclient import TestClient
from sora import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_text_to_video(client):
    response = client.post("/api/v1/text-to-video", json={
        "prompt": "test",
        "num_inference_steps": 5
    })
    assert response.status_code == 200
    assert "video_id" in response.json()

def test_batch_processing(client):
    response = client.post("/api/v1/text-to-video/batch", json={
        "prompts": ["test1", "test2"]
    })
    assert response.status_code == 200
    assert "total" in response.json()

def test_async_processing(client):
    response = client.post("/api/v1/text-to-video/async", json={
        "prompt": "test"
    })
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_rate_limiting(client):
    # Hacer muchos requests para probar rate limiting
    for _ in range(100):
        response = client.post("/api/v1/text-to-video", json={
            "prompt": "test"
        })
        if response.status_code == 429:
            assert "Rate limit exceeded" in response.json()["detail"]
            break
```

