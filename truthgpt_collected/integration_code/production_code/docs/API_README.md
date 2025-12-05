# 🌐 API REST Unificada

## ✨ Características

- ✅ **API REST completa**: Endpoints para todos los módulos
- ✅ **FastAPI**: Framework moderno y rápido
- ✅ **Documentación automática**: Swagger UI en `/docs`
- ✅ **CORS habilitado**: Para uso desde web
- ✅ **Dashboard web**: Interfaz visual para monitoreo

## 🚀 Iniciar Servidor

```bash
# Básico
python api_server.py

# Con opciones
python api_server.py --host 0.0.0.0 --port 8000 --reload

# Con múltiples workers
python api_server.py --workers 4
```

## 📡 Endpoints Disponibles

### Memory
- `POST /api/v1/memory/store` - Almacenar episodio
- `POST /api/v1/memory/retrieve` - Recuperar episodios
- `GET /api/v1/memory/stats` - Estadísticas

### Redundancy
- `POST /api/v1/redundancy/process` - Procesar eliminando redundancias
- `GET /api/v1/redundancy/stats` - Estadísticas

### Pipeline
- `POST /api/v1/pipeline/process` - Procesar a través del pipeline
- `GET /api/v1/pipeline/stats` - Estadísticas

### Chat
- `POST /api/v1/chat` - Chat con memoria

### Config
- `GET /api/v1/config` - Obtener configuración
- `PUT /api/v1/config/{module}` - Actualizar configuración

### Monitoring
- `GET /api/v1/monitor/status` - Estado del sistema
- `GET /api/v1/monitor/health` - Health checks
- `GET /api/v1/monitor/metrics` - Métricas

### Utilidades
- `GET /` - Información de la API
- `GET /health` - Health check
- `GET /dashboard` - Dashboard web
- `GET /docs` - Documentación Swagger

## 📊 Dashboard Web

Accede al dashboard en: `http://localhost:8000/dashboard`

Características:
- ✅ Visualización de métricas en tiempo real
- ✅ Health status de todos los módulos
- ✅ Auto-refresh cada 30 segundos
- ✅ Acciones rápidas (refresh, export, clear cache)

## 🔧 Ejemplos de Uso

### Almacenar en Memoria
```bash
curl -X POST "http://localhost:8000/api/v1/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "episode": [0.1, 0.2, 0.3, ...],
    "metadata": {"source": "test"},
    "tags": ["test", "example"]
  }'
```

### Recuperar de Memoria
```bash
curl -X POST "http://localhost:8000/api/v1/memory/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": [0.1, 0.2, 0.3, ...],
    "k": 5
  }'
```

### Procesar Pipeline
```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/process" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [[[0.1, 0.2], [0.3, 0.4]], ...],
    "use_memory": true,
    "use_redundancy": true
  }'
```

### Obtener Estado
```bash
curl "http://localhost:8000/api/v1/monitor/status"
```

## 📚 Documentación Interactiva

Accede a Swagger UI en: `http://localhost:8000/docs`

Incluye:
- ✅ Todos los endpoints
- ✅ Modelos de datos
- ✅ Ejemplos de requests
- ✅ Pruebas interactivas

## 🎉 Resultado

API REST completa con:
- ✅ Endpoints para todos los módulos
- ✅ Dashboard web
- ✅ Documentación automática
- ✅ Health checks
- ✅ Métricas en tiempo real

