# Sistema de Chat Conversacional - Similar a ChatGPT

Este sistema proporciona una interfaz de chat conversacional completa, similar a ChatGPT, con manejo de historial, contexto persistente y generación de respuestas de calidad.

## Características

- ✅ **Chat Conversacional**: Manejo completo de conversaciones con historial
- ✅ **Múltiples Proveedores**: Soporte para OpenAI, Anthropic y modelos locales
- ✅ **API REST**: Endpoints completos para integración
- ✅ **Interfaz Web**: UI moderna y responsive similar a ChatGPT
- ✅ **Gestión de Sesiones**: Múltiples conversaciones simultáneas
- ✅ **Contexto Persistente**: Mantiene el historial de la conversación
- ✅ **Calidad de Respuestas**: Optimizado para generar respuestas de alta calidad
- ✅ **Streaming en Tiempo Real**: Respuestas que aparecen palabra por palabra (como ChatGPT)
- ✅ **Caché Inteligente**: Respuestas instantáneas para preguntas frecuentes
- ✅ **Conteo Preciso de Tokens**: Integración con tiktoken para conteo exacto
- ✅ **Análisis de Calidad**: Métricas de calidad en cada respuesta
- ✅ **Rate Limiting**: Protección contra abusos

## Instalación

### Dependencias

```bash
pip install fastapi uvicorn openai anthropic transformers torch
```

O instala todas las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

### Variables de Entorno

Crea un archivo `.env` o configura las siguientes variables:

```bash
# Proveedor LLM (openai, anthropic, local)
LLM_PROVIDER=openai

# Modelo a usar
LLM_MODEL=gpt-3.5-turbo  # o claude-3-opus-20240229 para Anthropic

# API Keys
OPENAI_API_KEY=tu_api_key_aqui
# O
ANTHROPIC_API_KEY=tu_api_key_aqui

# Configuración del servidor
HOST=0.0.0.0
PORT=8000

# Prompt del sistema (opcional)
SYSTEM_PROMPT="Eres un asistente útil y profesional..."
```

## Uso

### 1. Ejecutar el Servidor

```bash
# Opción 1: Usando el script principal
python chat_server.py

# Opción 2: Usando uvicorn directamente
uvicorn core.chat_api:create_chat_app --factory --host 0.0.0.0 --port 8000
```

### 2. Acceder a la Interfaz Web

Abre tu navegador en:
```
http://localhost:8000
```

O directamente:
```
http://localhost:8000/ui
```

### 3. Usar la API REST

#### Enviar un Mensaje

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿cómo estás?",
    "user_id": "user123"
  }'
```

#### Crear una Conversación

```bash
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "system_prompt": "Eres un experto en programación Python"
  }'
```

#### Listar Conversaciones

```bash
curl "http://localhost:8000/api/v1/conversations?user_id=user123"
```

#### Obtener una Conversación

```bash
curl "http://localhost:8000/api/v1/conversations/conv_abc123"
```

#### Obtener Mensajes de una Conversación

```bash
curl "http://localhost:8000/api/v1/conversations/conv_abc123/messages"
```

## Uso en Python

### Ejemplo Básico

```python
from core.chat_engine import ChatEngine

# Inicializar motor de chat
engine = ChatEngine(
    provider="openai",
    model="gpt-3.5-turbo",
    api_key="tu_api_key"
)

# Crear conversación
conversation_id = engine.create_conversation(
    user_id="user123",
    system_prompt="Eres un asistente útil"
)

# Enviar mensaje
response = engine.chat(
    message="¿Qué es Python?",
    conversation_id=conversation_id
)

print(response["response"])
```

### Ejemplo con Modelo Local

```python
from core.chat_engine import ChatEngine

# Inicializar con modelo local
engine = ChatEngine(
    provider="local",
    use_local_model=True,
    local_model_path="microsoft/DialoGPT-medium"
)

# Usar el chat
response = engine.chat("Hola, ¿cómo estás?")
print(response["response"])
```

### Ejemplo con API

```python
from core.chat_api import create_chat_app
import uvicorn

# Crear aplicación
app = create_chat_app(
    provider="openai",
    model="gpt-3.5-turbo"
)

# Ejecutar servidor
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Endpoints de la API

### POST `/api/v1/chat`
Envía un mensaje y recibe una respuesta.

**Request:**
```json
{
  "message": "Tu mensaje aquí",
  "conversation_id": "conv_abc123",  // Opcional
  "user_id": "user123",              // Opcional
  "temperature": 0.7,                // Opcional
  "max_tokens": 2000                 // Opcional
}
```

**Response:**
```json
{
  "response": "Respuesta del asistente",
  "conversation_id": "conv_abc123",
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {
    "generation_time": 1.23,
    "provider": "openai",
    "model": "gpt-3.5-turbo"
  }
}
```

### POST `/api/v1/conversations`
Crea una nueva conversación.

**Request:**
```json
{
  "user_id": "user123",              // Opcional
  "system_prompt": "Prompt personalizado"  // Opcional
}
```

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "status": "created"
}
```

### GET `/api/v1/conversations`
Lista todas las conversaciones.

**Query Parameters:**
- `user_id` (opcional): Filtrar por usuario

### GET `/api/v1/conversations/{conversation_id}`
Obtiene una conversación específica.

### GET `/api/v1/conversations/{conversation_id}/messages`
Obtiene todos los mensajes de una conversación.

### DELETE `/api/v1/conversations/{conversation_id}`
Elimina una conversación.

### GET `/health`
Health check del servidor.

## Configuración Avanzada

### Personalizar el Prompt del Sistema

```python
engine = ChatEngine(
    provider="openai",
    system_prompt=(
        "Eres un experto en programación Python. "
        "Proporcionas código limpio y bien documentado. "
        "Siempre explicas tus respuestas."
    )
)
```

### Ajustar Parámetros de Generación

```python
response = engine.chat(
    message="Tu mensaje",
    temperature=0.9,      # Más creativo
    max_tokens=1000        # Respuestas más cortas
)
```

### Guardar y Cargar Conversaciones

```python
# Guardar conversación
engine.save_conversation(
    conversation_id="conv_abc123",
    filepath="conversation.json"
)

# Cargar conversación
conversation_id = engine.load_conversation("conversation.json")
```

## Modelos Soportados

### OpenAI
- `gpt-3.5-turbo` (recomendado)
- `gpt-4`
- `gpt-4-turbo-preview`

### Anthropic
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### Modelos Locales
- `microsoft/DialoGPT-medium`
- `microsoft/DialoGPT-large`
- Cualquier modelo compatible con Hugging Face Transformers

## Arquitectura

```
chat_engine.py      # Motor principal de chat
chat_api.py         # API REST (FastAPI)
chat_server.py      # Script para ejecutar el servidor
static/chat.html    # Interfaz web
```

## Mejoras de Calidad

El sistema incluye varias mejoras para garantizar respuestas de calidad:

1. **Gestión de Contexto**: Mantiene el historial relevante
2. **Límite de Tokens**: Evita exceder límites del modelo
3. **Manejo de Errores**: Respuestas de fallback cuando hay errores
4. **Metadata**: Tracking de tiempo de generación y otros métricas
5. **Validación**: Validación de inputs y respuestas

## Troubleshooting

### Error: "LLM client no está disponible"
- Verifica que las API keys estén configuradas
- Asegúrate de tener las dependencias instaladas

### Error: "Modelo local no está disponible"
- Instala `transformers` y `torch`
- Verifica que el modelo existe en Hugging Face

### La interfaz web no carga
- Verifica que el archivo `static/chat.html` exista
- Revisa la consola del navegador para errores

### Respuestas lentas
- Usa modelos más pequeños para desarrollo
- Reduce `max_tokens` en las respuestas
- Considera usar modelos locales para evitar latencia de API

## Próximas Mejoras

- [ ] Streaming de respuestas en tiempo real
- [ ] Soporte para imágenes y archivos
- [ ] Autenticación y autorización
- [ ] Persistencia en base de datos
- [ ] Rate limiting
- [ ] Caché de respuestas frecuentes
- [ ] Análisis de sentimiento
- [ ] Sugerencias de respuestas

## Licencia

Este código es parte del proyecto de producción y sigue la misma licencia del proyecto principal.


