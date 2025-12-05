# Top Papers sobre Autonomía (LLM Agents) — 2024-2025

**Fecha de extracción**: 2025-11-23

## 📊 Resumen

Este directorio contiene la información extraída de los **8 papers top** sobre agentes LLM autónomos publicados en 2024-2025.

### Estadísticas

- **Total de papers**: 8
- **Papers 2025**: 5
- **Papers 2024**: 3
- **Categorías**:
  - Agentes generales: 4
  - Conducción autónoma: 2
  - Surveys: 2
- **Autores únicos**: 35
- **Técnicas únicas**: 30

## 📁 Archivos Generados

1. **`llm_agents_papers.json`** - Datos estructurados en JSON con toda la información de cada paper
2. **`LLM_AGENTS_PAPERS.md`** - Reporte completo en Markdown con descripciones detalladas
3. **`summary.json`** - Resumen estadístico de los papers

## 📚 Papers Extraídos

### Agentes Generales (4 papers)

1. **SimuRA** (2025) - Simulative Reasoning Architecture con World Model basado en LLM
2. **Concurrent Modular Agent** (2025) - Framework con módulos concurrentes y estado global
3. **Formal-LLM** (2024) - Integración de lenguaje formal y natural para agentes controlables
4. **MARS** (2025) - Memory-Enhanced Agents con Reflective Self-improvement

### Conducción Autónoma (2 papers)

5. **Empowering Autonomous Driving with LLMs** (2024) - Safety perspective con verificador de seguridad
6. **DriveAgent** (2025) - Multi-Agent framework con sensores y agentes de razonamiento

### Surveys (2 papers)

7. **Survey on LLM-Based Autonomous Agents** (2024) - Revisión sistemática de memoria, planificación y herramientas
8. **Survey on LLM-Powered Autonomous Driving** (2025) - Revisión de LLMs en vehículos autónomos

## 🔧 Uso

### Cargar datos JSON

```python
import json
from pathlib import Path

# Cargar papers
with open('llm_agents_papers.json', 'r') as f:
    papers = json.load(f)

# Filtrar por categoría
agents_papers = [p for p in papers if p['category'] == 'agents']
```

### Ver reporte Markdown

El archivo `LLM_AGENTS_PAPERS.md` contiene un reporte completo con:
- Descripciones detalladas
- Contribuciones clave
- Técnicas utilizadas
- Arquitecturas propuestas

## 📝 Notas

- Los papers están organizados por categoría en el reporte Markdown
- Cada paper incluye: título, autores, año, venue, descripción, contribuciones, técnicas y arquitectura
- Los IDs de papers se generan automáticamente a partir del título

## 🚀 Próximos Pasos

Para implementar estos papers como módulos Python (similar a otros papers en el proyecto):

1. Crear archivos `paper_*.py` en las carpetas correspondientes (`papers/agents/`, `papers/autonomous_driving/`, etc.)
2. Implementar las clases `Config` y `Module` siguiendo el patrón de `BasePaperConfig` y `BasePaperModule`
3. Registrar los papers en el `PaperRegistry`

## 📖 Referencias

- Ver `../papers/README_PAPERS.md` para la estructura de implementación de papers
- Ver `../papers/core/paper_base.py` para las clases base
- Ver `../papers/core/paper_registry_refactored.py` para el registro de papers



