# Arquitectura en Capas (`production_code`)

> Objetivo: aislar responsabilidades, minimizar dependencias circulares y permitir intercambio rápido de módulos/modelos manteniendo pipelines estables.

## Visión General

```
Presentación (FastAPI/CLI/UI/WebSocket)
        ↓  (DTOs + Validaciones)
Aplicación (Servicios/Orquestadores)
        ↓  (Contratos + Eventos)
Dominio (Entidades/Reglas/Contratos)
        ↓  (Adapters registrados)
Infraestructura (Providers/Drivers externos)
```

## Capas y Responsables

### Presentación
- Archivos: `api_unified.py`, `api_server.py`, `chat_server.py`, `cli.py`, `cli_unified.py`, `dashboard.html`, `api_middleware.py`, `api_auth.py`.
- Funciones: exponer HTTP/WebSocket/CLI, validar inputs con Pydantic, mapear DTOs ↔ modelos de dominio, aplicar middleware (auth, rate limiting, logging) sin acceso directo a `core/` o `memory/`.
- Dependencias permitidas: `application.service_container`, contratos DTO propios y utilidades específicas de presentación (ej. `api_utils` limitado a serialización/logging).

### Aplicación
- Archivos: `services/`, `integration_pipeline.py`, `docs_generator.py`, `monitoring_system.py`, `testing_suite.py`, `improve_models.py`, coordinadores de `multimodal_api/`, `sora/`.
- Funciones: implementar casos de uso, coordinar múltiples módulos de dominio, aplicar políticas (reintentos con `safe_execute`, cuotas, scheduling), emitir eventos a monitoreo/auditoría.
- Depende exclusivamente de contratos definidos en Dominio y de factories/providers expuestos por Infraestructura a través del `ServiceContainer`.

### Dominio
- Archivos: `core/`, `memory/`, `research/`, `inference/`, `architecture/`, `techniques/`, `code/`, `best/`, `redundancy/`, `model_data/`.
- Funciones: entidades, agregados, validaciones profundas, métricas internas y contratos (Protocol/ABC) como `MemoryModule`, `ChatEngine`, `RedundancyModule`, `ConfigRepository`.
- No conoce frameworks externos; cualquier necesidad se expresa como contrato/evento.

### Infraestructura
- Archivos: `api_utils.py`, `config_manager.py`, adaptadores concretos en `services/`, `multimodal_api/`, `sora/`, `model_data/`, `static/`, integración con caches, storage, tracing.
- Funciones: implementar contratos de Dominio usando dependencias reales (FastAPI, httpx/requests, Ray, wandb, Redis, S3, Prometheus), gestionar configuración multi-formato y exponer factories/registries para DI.
- Se agrupa en `infrastructure/providers/<tipo>` (LLM, memoria, redundancia, monitoreo, storage).

## Reglas de Importación

| Puede importar → | Presentación | Aplicación | Dominio | Infraestructura |
|------------------|--------------|-----------|---------|-----------------|
| **Presentación** | —            | ✅        | 🚫      | Solo helpers propios (`api_utils`) |
| **Aplicación**   | 🚫           | —         | ✅ (contratos) | ✅ (providers vía container/factories) |
| **Dominio**      | 🚫           | 🚫        | —       | 🚫 |
| **Infraestructura** | 🚫        | ✅ (para exponer providers/fachadas) | ✅ (implementa contratos) | — |

Notas:
- `services/` actúa como capa de aplicación **si** expone métodos de orquestación; los adaptadores concretos que tocan SDKs externos deben moverse a `infrastructure/providers`.
- Cualquier importación prohibida debe reemplazarse con una interfaz/contrato en `domain/contracts`.

## Service Container

Archivo sugerido: `application/service_container.py`.

Responsabilidades:
1. Construir configuraciones estratificadas (`PresentationConfig`, `ApplicationConfig`, `DomainConfig`, `InfrastructureConfig`) utilizando `ConfigManager`.
2. Registrar providers (memoria, redundancia, chat engines, telemetría) por nombre.
3. Exponer factories `get_pipeline_service()`, `get_chat_service()`, etc., utilizados por `Depends` en FastAPI, CLI y pruebas.
4. Gestionar ciclo de vida (singletons vs scoped) y recursos compartidos (clientes httpx, pools).

Ejemplo de integración en FastAPI:

```python
container = ServiceContainer.from_env()

app = FastAPI(...)
app.state.container = container

@router.post("/pipeline/run")
def run_pipeline(dto: PipelineDTO, service: PipelineService = Depends(container.provide_pipeline)):
    return service.run(dto.to_command())
```

## Configuración Estratificada

`config_manager.py` debe exponer:
- `PresentationConfig`: flags de middlewares, CORS, rate limiting.
- `ApplicationConfig`: cuotas, políticas de reintento (`safe_execute`), scheduling.
- `DomainConfig`: hiperparámetros, límites de memoria, thresholds.
- `InfrastructureConfig`: credenciales externas, endpoints, tipos de provider habilitados.

Validaciones cruzadas:
- Si `enable_chat=True` ⇒ `InfrastructureConfig.chat.provider` debe existir.
- Si `redundancy.mode=ensemble` ⇒ deben declararse al menos dos `RedundancyModule`.
- Observabilidad habilitada ⇒ `MonitoringProvider` configurado (Prometheus, W&B, etc.).

## Eventos y Observabilidad

Dominio emite eventos ligeros (`MessageProcessed`, `MemoryThresholdReached`, `PipelineStepFailed`). Aplicación los mapea a métricas/logs y decide la severidad. Infraestructura provee los sinks:
- `MonitoringProvider` → Prometheus/OpenTelemetry.
- `AuditProvider` → Kafka/S3/DB.
- `NotificationProvider` → Slack/Email.

## Orquestadores y Fachadas

- Consolidar orquestadores en `application/orchestrators/` (`DocsOrchestrator`, `MonitoringOrchestrator`, `MultimodalOrchestrator`).
- Cada façade (`MemoryService`, `RedundancyService`, `ChatService`) encapsula interacción con módulos de dominio y se usa desde APIs/CLI.
- Reglas: un orquestador solo coordina servicios/fachadas, nunca importa implementaciones concretas del dominio.

## Mapa de Migración Progresiva

1. **Identificar dependencias prohibidas**: ejecutar `ruff --select RUF100` (o script custom) para detectar imports desde Presentación → Dominio.
2. **Extraer contratos**: mover clases abstractas/protocolos a `domain/contracts/`.
3. **Crear providers**: mover lógica que usa SDKs externos a `infrastructure/providers/<tipo>.py`.
4. **Introducir `ServiceContainer`**: inicializarlo en `api_server.py`, `chat_server.py`, CLI y pruebas.
5. **Actualizar servicios**: inyectar dependencias vía constructor/factory y eliminar singletons globales.
6. **Registrar eventos**: definir `domain/events.py`, mapearlos en `MonitoringService`.
7. **Documentar progreso**: usar la checklist inferior. Cada paso puede ejecutarse por módulo para evitar Big Bang.

## Checklist para Nuevos Módulos

- [ ] ¿A qué capa pertenece? (`presentation`, `application`, `domain`, `infrastructure`).
- [ ] ¿Cumple las reglas de importación?
- [ ] ¿Expone/consume contratos en vez de implementaciones específicas?
- [ ] ¿Tiene configuración declarada en la sección correcta del `ConfigManager`?
- [ ] ¿Emite y documenta eventos relevantes?
- [ ] ¿Cuenta con tests aislados por capa (unitarios para dominio, integración para aplicación/presentación)?
- [ ] ¿Está documentado en `docs/architecture/layers.md` o en `docs/README.md`?

## Diagrama de Flujo (texto)

```
1. Request (HTTP/WebSocket/CLI) llega a Presentación.
2. Middleware valida auth, rate limiting, transforma DTOs.
3. Controller obtiene servicio desde `ServiceContainer`.
4. Servicio de Aplicación orquesta sub-servicios/fachadas.
5. Servicios interactúan con el Dominio a través de contratos.
6. Necesidades externas se resuelven mediante providers de Infraestructura.
7. Dominio emite eventos → Aplicación decide métricas → Infraestructura los envía a sinks.
8. Respuesta se convierte en DTO y se retorna a la capa de Presentación.
```

## Import Guard (Sugerencia)

Implementar un script `python -m tools.verify_layers` que:
- Analiza imports con `importlib_metadata`.
- Valida que cada archivo respete la tabla de dependencias.
- Falla en CI si hay violaciones.

## Recursos Relacionados

- `README.md` → panorama general y enlaces rápidos.
- `docs/README.md` → índice extendido.
- `docs/architecture/layers.md` (este archivo) → reglas detalladas y checklist.

Con estas reglas, `production_code` puede incorporar nuevos modelos, proveedores y canales sin modificar capas superiores, manteniendo estabilidad operativa y favoreciendo pruebas aisladas.

