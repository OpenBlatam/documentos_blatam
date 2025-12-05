# Sistema de Memoria Avanzado

Sistema completo de memoria episódica y semántica con funcionalidades avanzadas.

## 🚀 Características Principales

- ✅ **Memoria Episódica y Semántica**: Almacenamiento y recuperación inteligente
- ✅ **Persistencia**: Guardado y carga automática
- ✅ **Tags y Categorías**: Organización flexible
- ✅ **Priorización**: Sistema de prioridades dinámicas
- ✅ **Compresión**: Ahorro de espacio inteligente
- ✅ **Caché**: Retrievals rápidos
- ✅ **Analytics**: Análisis completo del sistema
- ✅ **Integración con Chat**: Memoria para conversaciones
- ✅ **Utilidades**: Funciones helper y factory

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🎯 Uso Rápido

### Básico

```python
from memory import Paper2506_15841v2Config, Paper2506_15841v2_MemorySystem

# Crear sistema
config = Paper2506_15841v2Config(memory_dim=512)
memory = Paper2506_15841v2_MemorySystem(config)

# Almacenar
episode = torch.randn(512)
memory.store_episode(episode, metadata={'info': 'test'})

# Recuperar
query = torch.randn(512)
retrieved, weights = memory.retrieve_episodes(query, k=5)
```

### Con Tags y Prioridad

```python
# Almacenar con tags
memory.store_episode_with_tags(
    episode=episode,
    tags=['programming', 'python'],
    priority=0.9
)

# Recuperar por tags
retrieved, weights = memory.retrieve_by_tags(query, tags=['programming'])
```

### Factory Functions

```python
from memory import create_memory_system, create_chat_with_memory

# Crear sistema fácilmente
memory = create_memory_system("2506_15841v2", memory_dim=512)

# Crear chat con memoria
chat = create_chat_with_memory(
    chat_provider="openai",
    memory_paper="2506_15841v2",
    memory_dim=512
)
```

### Analytics

```python
from memory import MemoryAnalytics, MemoryOptimizer

analytics = MemoryAnalytics(memory)
report = analytics.get_comprehensive_report()

optimizer = MemoryOptimizer(memory)
optimizer.optimize_memory_layout()
```

### Utilidades

```python
from memory import (
    create_episode_from_text,
    batch_store_episodes,
    get_memory_health_report
)

# Crear episodio desde texto
episode = create_episode_from_text("Python programming", memory_dim=512)

# Health check
health = get_memory_health_report(memory)
print(f"Status: {health['status']}")
```

## 📚 Documentación Completa

- `MEJORAS_MEMORIA.md` - Mejoras básicas
- `MEJORAS_AVANZADAS.md` - Funcionalidades avanzadas
- `MEJORAS_ANALYTICS.md` - Analytics y optimización
- `RESUMEN_MEJORAS_COMPLETAS.md` - Resumen completo
- `example_usage.py` - Ejemplos de uso

## 🔗 Integración con Chat

```python
from memory import ChatMemoryIntegration
from core.chat_engine import ChatEngine

chat = ChatEngine(provider="openai")
integration = ChatMemoryIntegration(chat)

# Chat con memoria
response = integration.enhance_chat_with_memory(
    "¿Recuerdas nuestra conversación?",
    conversation_id=conv_id
)
```

## 📊 Analytics y Optimización

```python
from memory import MemoryAnalytics, MemoryOptimizer, MemoryExporter

# Analytics
analytics = MemoryAnalytics(memory)
report = analytics.get_comprehensive_report()
analytics.visualize_memory_distribution("analysis.png")

# Optimización
optimizer = MemoryOptimizer(memory)
optimizer.optimize_memory_layout()

# Exportación
exporter = MemoryExporter(memory)
exporter.export_to_json("backup.json")
```

## 🎉 Resultado

Sistema completo de memoria con:
- ✅ Todas las funcionalidades avanzadas
- ✅ Integración completa
- ✅ Analytics y optimización
- ✅ Utilidades y helpers
- ✅ Listo para producción


