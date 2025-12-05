# 🚀 Guía de Deployment - API Multimodal

## Pre-requisitos

### Dependencias del Sistema
```bash
# Python 3.8+
python --version

# Dependencias Python
pip install fastapi uvicorn pydantic redis

# Opcional: Para WebSockets
pip install websockets

# Opcional: Para Redis cache
pip install redis
```

### Variables de Entorno
```bash
# .env
API_HOST=0.0.0.0
API_PORT=8000
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://localhost:6379/0
QUEUE_MAX_WORKERS=4
AUTH_ENABLED=true
JWT_SECRET_KEY=your-secret-key-here
```

## Deployment Local

### Desarrollo
```bash
# Ejecutar servidor de desarrollo
python -m multimodal_api.run_server

# O con uvicorn directamente
uvicorn multimodal_api.api_server:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
# Con gunicorn (recomendado)
gunicorn multimodal_api.api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120

# O con uvicorn
uvicorn multimodal_api.api_server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

## Docker

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "multimodal_api.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Kubernetes

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multimodal-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multimodal-api
  template:
    metadata:
      labels:
        app: multimodal-api
    spec:
      containers:
      - name: api
        image: multimodal-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

## Monitoreo

### Health Checks
```bash
# Health check básico
curl http://localhost:8000/health

# Health check detallado
curl http://localhost:8000/health/detailed
```

### Métricas
```bash
# Métricas del sistema
curl http://localhost:8000/metrics

# Analytics
curl http://localhost:8000/analytics
```

## Backup y Recovery

### Crear Backup
```bash
curl -X POST http://localhost:8000/backup \
  -H "Content-Type: application/json" \
  -d '{"description": "Backup antes de actualización"}'
```

### Restaurar Backup
```bash
curl -X POST http://localhost:8000/backup/{backup_id}/restore
```

## Testing

### Smoke Tests
```python
from multimodal_api import MultimodalAPIServer
from multimodal_api.api_testing import APITester

server = MultimodalAPIServer()
tester = APITester(server.app)
results = tester.run_smoke_tests()
print(results)
```

## Seguridad

### Autenticación
- Configurar `JWT_SECRET_KEY` en variables de entorno
- Habilitar `AUTH_ENABLED=true`
- Usar HTTPS en producción

### Rate Limiting
- Configurar límites apropiados
- Monitorear rate limits por usuario
- Ajustar según carga

## Escalabilidad

### Horizontal Scaling
- Usar múltiples workers
- Load balancer (nginx, HAProxy)
- Redis para cache compartido

### Vertical Scaling
- Aumentar recursos según métricas
- Monitorear uso de CPU/memoria
- Optimizar según analytics

## Troubleshooting

### Logs
```bash
# Ver logs
tail -f logs/api.log

# Logs de errores
grep ERROR logs/api.log
```

### Debugging
```bash
# Modo debug
export LOG_LEVEL=DEBUG
python -m multimodal_api.run_server
```


