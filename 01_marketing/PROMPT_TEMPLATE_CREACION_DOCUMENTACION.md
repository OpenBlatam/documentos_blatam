# 🎯 Prompt Template: Creación de Documentación Maestra Completa

> **Template y metodología** para crear documentación técnica exhaustiva y bien estructurada. Basado en el proceso de creación del Índice Maestro del Sistema de DMs de LinkedIn.

**Versión:** 1.0  
**Tipo:** Prompt Template / Guía Metodológica  
**Aplicable a:** Sistemas técnicos complejos, documentación de software, guías de usuario

---

## 📋 Prompt Base para Creación de Documentación

```
Eres un experto en documentación técnica y organización de información. Tu tarea es crear 
un documento maestro completo que consolide toda la documentación de un sistema técnico 
complejo.

OBJETIVO:
Crear un "Índice Maestro" que sirva como punto de entrada único para todo el sistema, 
organizando más de 150 recursos (scripts, workflows, templates, guías) en una estructura 
navegable y accesible.

REQUISITOS:
1. El documento debe tener múltiples puntos de entrada según el tipo de usuario
2. Debe incluir sistemas de navegación (índices, tablas de contenido, quick links)
3. Debe ser autocontenido pero con referencias cruzadas
4. Debe priorizar la acción inmediata (comandos listos para usar)
5. Debe seguir una progresión de simple a complejo

ESTRUCTURA REQUERIDA:
[Ver sección "Estructura Detallada" más abajo]

PRINCIPIOS DE DISEÑO:
- Múltiples puntos de entrada
- Progresión lógica (simple → complejo)
- Búsqueda rápida (índices alfabéticos y por funcionalidad)
- Autocontención (cada sección tiene contexto suficiente)
- Acción inmediata (comandos y ejemplos listos para usar)

FORMATO:
- Markdown con emojis para identificación visual rápida
- Bloques de código con sintaxis highlighting
- Diagramas ASCII para visualización
- Tablas para datos estructurados
- Enlaces internos para navegación
```

---

## 🏗️ Estructura Detallada del Documento

### 1. **Encabezado y Metadatos**

```markdown
# 📚 [Título del Sistema] – Índice Maestro

> **Descripción breve** del sistema. Propósito y alcance.

**Versión:** X.0 | **Estado:** [Activo/En desarrollo] | **Última actualización:** {{AUTO}}

[Párrafo introductorio explicando qué es el índice y cuántos recursos organiza]
```

### 2. **Guía de Uso del Documento**

```markdown
### 📖 Cómo usar este documento

**Si es tu primera vez:**
1. Lee [Quick Start] para setup inicial
2. Revisa [Quick Reference] para comandos esenciales
3. Consulta [Visión General] para entender el sistema

**Para operación diaria:**
- Usa [Quick Reference] como cheat sheet
- Consulta [Tips y Shortcuts] para workflows rápidos
- Revisa [Ejecución Rápida] para comandos

**Para resolver problemas:**
- Ve directamente a [Troubleshooting]
- Consulta [FAQ] para preguntas comunes

**Para optimizar:**
- Revisa [Mejores Prácticas]
- Consulta [Flujos de Trabajo] avanzados

**Búsqueda rápida:**
- Comandos: [Índice Alfabético]
- Scripts: [Índice por Funcionalidad]
- Problemas: [Troubleshooting]
- Ejemplos: [Quick Reference]
```

### 3. **Tabla de Contenidos Jerárquica**

Organizar en 5 secciones principales:

#### 🚀 Inicio Rápido
- Comandos Esenciales (Cheat Sheet Rápido)
- Quick Start - Primeros Pasos
- Quick Reference (Cheat Sheet Completo)
- Quick Links (por necesidad)

#### 📖 Fundamentos
- Visión General
- Arquitectura del Sistema
- Núcleo Operativo
- Documentación y Reportes

#### ⚙️ Operación
- Ejecución Rápida
- Estructura de Datos
- Configuración
- Tips y Shortcuts
- Flujos de Trabajo

#### 🔧 Soporte y Optimización
- Troubleshooting
- Integraciones y Automatización
- Mejores Prácticas

#### 📚 Referencias
- Datos y Fuentes Esperadas
- FAQ - Preguntas Frecuentes
- Referencias Relacionadas
- Resumen de Recursos
- Resumen Ejecutivo
- Guía de Escalamiento
- Índices de Búsqueda
- Roadmap Futuro

### 4. **Mapa Visual del Sistema**

```markdown
## 🗺️ Mapa Visual del Sistema

```
[Diagrama ASCII del flujo del sistema]
```

**Flujo Principal:**
1. [Paso 1] → Descripción
2. [Paso 2] → Descripción
3. [Paso 3] → Descripción
...
```

### 5. **Comandos Esenciales (Top 5)**

```markdown
## ⚡ Comandos Esenciales (Cheat Sheet Rápido)

### Los 5 comandos que usarás 90% del tiempo:

```bash
# 1. [Comando más usado] - Descripción
comando_1

# 2. [Segundo más usado] - Descripción
comando_2

# ... etc
```

### Workflow típico:

```bash
# Paso 1: [Acción]
comando_paso_1

# Paso 2: [Acción]
comando_paso_2
```

### Comandos de emergencia:

```bash
# [Situación de emergencia]
comando_emergencia
```
```

### 6. **Quick Start (5 minutos)**

```markdown
## ⚡ Quick Start - Primeros Pasos

### Setup Inicial (5 minutos)

```bash
# 1. [Acción inicial]
comando_1

# 2. [Siguiente acción]
comando_2
```

### Tu Primera [Operación] (15 minutos)

```bash
# 1. [Preparación]
# Ejemplo: archivo.csv
# estructura,ejemplo

# 2. [Ejecución]
comando_ejecucion
```

### Monitoreo Básico (Diario)

```bash
# [Comando de monitoreo]
comando_monitoreo
```
```

---

## 📝 Checklist de Contenido por Sección

### ✅ Sección: Inicio Rápido

- [ ] **Comandos Esenciales**: Top 5 comandos más usados
- [ ] **Workflow típico**: Proceso completo paso a paso
- [ ] **Comandos de emergencia**: Situaciones críticas
- [ ] **Quick Start**: Setup en 5 minutos
- [ ] **Primera operación**: Guía de 15 minutos
- [ ] **Monitoreo básico**: Comandos diarios
- [ ] **Quick Reference**: Cheat sheet completo
- [ ] **Quick Links**: Enlaces por necesidad específica

### ✅ Sección: Fundamentos

- [ ] **Visión General**: Qué es el sistema, propósito, alcance
- [ ] **Arquitectura**: Componentes principales, flujo de datos
- [ ] **Núcleo Operativo**: Scripts principales con descripción
- [ ] **Documentación**: Lista de documentos relacionados

### ✅ Sección: Operación

- [ ] **Ejecución Rápida**: Todos los comandos principales organizados
- [ ] **Estructura de Datos**: Formatos esperados (CSV, JSON, etc.)
- [ ] **Configuración**: Variables de entorno, archivos de config
- [ ] **Tips y Shortcuts**: Atajos útiles del día a día
- [ ] **Flujos de Trabajo**: Procesos recomendados y casos de uso

### ✅ Sección: Soporte y Optimización

- [ ] **Troubleshooting**: Problemas comunes y soluciones
- [ ] **Integraciones**: Conexiones externas documentadas
- [ ] **Mejores Prácticas**: Guías de uso óptimo

### ✅ Sección: Referencias

- [ ] **Datos y Fuentes**: Archivos del sistema esperados
- [ ] **FAQ**: Preguntas frecuentes con respuestas
- [ ] **Referencias**: Documentación relacionada
- [ ] **Resumen de Recursos**: Estadísticas del sistema
- [ ] **Resumen Ejecutivo**: Visión general rápida
- [ ] **Guía de Escalamiento**: Crecimiento por fases
- [ ] **Índice Alfabético**: Búsqueda por nombre
- [ ] **Índice por Funcionalidad**: Búsqueda por propósito
- [ ] **Roadmap**: Próximas características

---

## 🎨 Principios de Diseño a Aplicar

### 1. **Principio de Múltiples Puntos de Entrada**

**Aplicación:**
- Crear diferentes rutas según el tipo de usuario (nuevo, experto, troubleshooting)
- Cada sección debe poder accederse de múltiples formas
- Quick Links para necesidades específicas

**Ejemplo:**
```markdown
**Para nuevos usuarios:** [Quick Start](#quick-start)
**Para operadores:** [Quick Reference](#quick-reference)
**Para troubleshooting:** [Troubleshooting](#troubleshooting)
```

### 2. **Principio de Progresión**

**Aplicación:**
- De lo simple a lo complejo
- De lo básico a lo avanzado
- De lo general a lo específico

**Estructura:**
1. Comandos esenciales (5 más usados)
2. Quick Start (setup básico)
3. Fundamentos (entender el sistema)
4. Operación (uso diario)
5. Optimización (avanzado)

### 3. **Principio de Búsqueda Rápida**

**Aplicación:**
- Índices alfabéticos para búsqueda por nombre
- Índices por funcionalidad para búsqueda por propósito
- Quick Links para necesidades específicas
- Tabla de contenidos jerárquica

**Implementación:**
```markdown
## Índice Alfabético de Comandos

- [comando_a](#comando-a) - Descripción breve
- [comando_b](#comando-b) - Descripción breve

## Índice por Funcionalidad

### Monitoreo
- [comando_monitoreo](#comando-monitoreo)
- [comando_analisis](#comando-analisis)

### Validación
- [comando_validacion](#comando-validacion)
```

### 4. **Principio de Autocontención**

**Aplicación:**
- Cada sección tiene contexto suficiente
- Referencias cruzadas cuando es necesario
- Ejemplos completos y funcionales

**Ejemplo:**
```markdown
## Configuración

### Variables de Entorno

```bash
# Variable: SLACK_WEBHOOK_URL
# Propósito: Notificaciones de alertas
# Ejemplo:
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
# Ver también: [Integraciones](#integraciones)
```
```

### 5. **Principio de Acción Inmediata**

**Aplicación:**
- Comandos listos para copiar y pegar
- Ejemplos prácticos desde el inicio
- Workflows completos documentados

**Ejemplo:**
```markdown
## Tu Primera Campaña

```bash
# 1. Preparar archivo CSV
cat > recipients.csv << EOF
recipient,campaign
https://linkedin.com/in/user1,curso_ia
https://linkedin.com/in/user2,curso_ia
EOF

# 2. Ejecutar comando
npm run dm:queue:smart

# 3. Validar
npm run dm:queue:validate
```
```

---

## 🔄 Proceso de Creación Paso a Paso

### Fase 1: Análisis y Recopilación (Día 1-2)

**Tareas:**
1. **Inventario completo**
   - Listar todos los scripts disponibles
   - Identificar workflows existentes
   - Recopilar documentación dispersa
   - Identificar templates y ejemplos

2. **Categorización**
   - Agrupar por funcionalidad
   - Identificar comandos principales
   - Separar por nivel de complejidad
   - Detectar dependencias

3. **Identificación de gaps**
   - Documentación faltante
   - Ejemplos que faltan
   - Casos de uso no documentados
   - Troubleshooting incompleto

**Output:**
- Lista completa de recursos
- Mapa de categorías
- Lista de gaps identificados

### Fase 2: Diseño de Estructura (Día 3)

**Tareas:**
1. **Diseñar arquitectura del documento**
   - Definir secciones principales
   - Crear jerarquía de subsecciones
   - Planificar sistema de navegación

2. **Definir puntos de entrada**
   - Quick Start para nuevos usuarios
   - Quick Reference para operadores
   - Troubleshooting para problemas
   - Índices para búsqueda

3. **Planificar referencias cruzadas**
   - Identificar relaciones entre secciones
   - Planificar enlaces internos
   - Diseñar flujo de navegación

**Output:**
- Estructura completa del documento
- Mapa de navegación
- Plan de referencias cruzadas

### Fase 3: Creación de Contenido (Día 4-7)

**Tareas:**
1. **Encabezado y metadatos**
   - Título descriptivo
   - Descripción breve
   - Versión y estado

2. **Guía de uso**
   - Instrucciones para diferentes usuarios
   - Rutas de navegación sugeridas

3. **Tabla de contenidos**
   - Estructura jerárquica completa
   - Enlaces a todas las secciones

4. **Mapa visual**
   - Diagrama ASCII del sistema
   - Flujo principal explicado

5. **Sección por sección**
   - Comandos esenciales
   - Quick Start
   - Fundamentos
   - Operación
   - Soporte
   - Referencias

**Output:**
- Documento completo con todas las secciones
- Contenido estructurado y organizado

### Fase 4: Optimización y Refinamiento (Día 8-9)

**Tareas:**
1. **Revisión de navegación**
   - Verificar todos los enlaces
   - Asegurar referencias cruzadas
   - Validar estructura jerárquica

2. **Enriquecimiento de contenido**
   - Agregar ejemplos donde falten
   - Completar casos de uso
   - Mejorar explicaciones

3. **Optimización de usabilidad**
   - Verificar comandos copiables
   - Validar ejemplos funcionales
   - Asegurar progresión lógica

4. **Creación de índices**
   - Índice alfabético de comandos
   - Índice por funcionalidad
   - Quick Links por necesidad

**Output:**
- Documento refinado y optimizado
- Índices completos
- Navegación verificada

### Fase 5: Validación y Ajustes (Día 10)

**Tareas:**
1. **Revisión técnica**
   - Verificar exactitud de comandos
   - Validar ejemplos
   - Comprobar referencias

2. **Revisión de usabilidad**
   - Probar navegación
   - Verificar claridad
   - Validar progresión

3. **Ajustes finales**
   - Corregir errores encontrados
   - Mejorar claridad
   - Optimizar formato

**Output:**
- Documento final validado
- Lista de mejoras futuras

---

## 📊 Métricas de Calidad

### Cobertura
- [ ] Todos los comandos principales documentados
- [ ] Todos los scripts referenciados
- [ ] Todos los workflows explicados
- [ ] Todos los casos de uso cubiertos

### Navegación
- [ ] Tabla de contenidos completa
- [ ] Índices alfabéticos funcionales
- [ ] Índices por funcionalidad completos
- [ ] Quick Links organizados
- [ ] Referencias cruzadas verificadas

### Usabilidad
- [ ] Quick Start funcional (setup en 5 min)
- [ ] Comandos listos para copiar
- [ ] Ejemplos completos y funcionales
- [ ] Troubleshooting con soluciones
- [ ] Progresión lógica verificada

### Completitud
- [ ] Visión general clara
- [ ] Arquitectura documentada
- [ ] Configuración explicada
- [ ] Mejores prácticas incluidas
- [ ] Roadmap futuro definido

---

## 🎯 Template de Prompt para IA

```
Crea un documento maestro de documentación técnica para [NOMBRE_DEL_SISTEMA] que:

1. SIRVA COMO PUNTO DE ENTRADA ÚNICO
   - Organice más de [N] recursos (scripts, workflows, templates, guías)
   - Proporcione múltiples puntos de entrada según tipo de usuario
   - Incluya sistemas de navegación completos

2. SIGA LA ESTRUCTURA ESTABLECIDA
   - 🚀 Inicio Rápido (comandos esenciales, quick start, quick reference, quick links)
   - 📖 Fundamentos (visión general, arquitectura, núcleo operativo, documentación)
   - ⚙️ Operación (ejecución rápida, estructura de datos, configuración, tips, workflows)
   - 🔧 Soporte y Optimización (troubleshooting, integraciones, mejores prácticas)
   - 📚 Referencias (datos, FAQ, referencias, resúmenes, índices, roadmap)

3. APLIQUE PRINCIPIOS DE DISEÑO
   - Múltiples puntos de entrada
   - Progresión de simple a complejo
   - Búsqueda rápida (índices alfabéticos y por funcionalidad)
   - Autocontención (cada sección con contexto suficiente)
   - Acción inmediata (comandos y ejemplos listos para usar)

4. INCLUYA ELEMENTOS ESPECÍFICOS
   - Mapa visual del sistema (diagrama ASCII)
   - Top 5 comandos más usados
   - Workflow típico paso a paso
   - Comandos de emergencia
   - Quick Start (setup en 5 minutos)
   - Guía de primera operación (15 minutos)
   - Estructura de datos esperados
   - Variables de entorno
   - Troubleshooting completo
   - Índices de búsqueda rápida

5. FORMATO Y ESTILO
   - Markdown con emojis para identificación visual
   - Bloques de código con sintaxis highlighting
   - Diagramas ASCII para visualización
   - Tablas para datos estructurados
   - Enlaces internos para navegación

CONTEXTO DEL SISTEMA:
[Describir el sistema, sus componentes principales, comandos clave, estructura de archivos, etc.]

RECURSOS A ORGANIZAR:
[Lista de scripts, workflows, templates, guías, etc. que deben ser referenciados]

COMANDOS PRINCIPALES:
[Lista de comandos principales del sistema con descripciones breves]

ESTRUCTURA DE DATOS:
[Formatos esperados: CSV, JSON, etc. con ejemplos]

VARIABLES DE CONFIGURACIÓN:
[Variables de entorno, archivos de config, etc.]

PROBLEMAS COMUNES:
[Lista de problemas comunes y sus soluciones]
```

---

## 📝 Ejemplo de Uso del Template

### Input: Sistema de Backup Automatizado

```
Crea un documento maestro de documentación técnica para Sistema de Backup Automatizado que:

1. SIRVA COMO PUNTO DE ENTRADA ÚNICO
   - Organice más de 50 recursos (scripts de backup, workflows de sincronización, templates de configuración, guías de recuperación)
   - Proporcione múltiples puntos de entrada según tipo de usuario (administrador, operador, recuperación)
   - Incluya sistemas de navegación completos

2. SIGA LA ESTRUCTURA ESTABLECIDA
   [Usar estructura completa del template]

3. APLIQUE PRINCIPIOS DE DISEÑO
   [Usar principios del template]

CONTEXTO DEL SISTEMA:
Sistema de backup automatizado que realiza copias de seguridad incrementales de bases de datos y archivos. 
Incluye scripts de backup, verificación de integridad, restauración, y monitoreo.

RECURSOS A ORGANIZAR:
- Scripts/backup_database.sh
- Scripts/backup_files.sh
- Scripts/verify_backup.sh
- Scripts/restore_backup.sh
- Workflows/sync_to_cloud.json
- Templates/backup_config.json
- Guides/recovery_procedures.md

COMANDOS PRINCIPALES:
- backup:run - Ejecutar backup completo
- backup:verify - Verificar integridad de backups
- backup:restore - Restaurar desde backup
- backup:status - Estado de backups
- backup:cleanup - Limpiar backups antiguos

ESTRUCTURA DE DATOS:
- backup_config.json: Configuración de rutas y schedules
- backup_log.csv: Registro de backups con columnas: timestamp, type, status, size

VARIABLES DE CONFIGURACIÓN:
- BACKUP_RETENTION_DAYS=30
- BACKUP_STORAGE_PATH=/backups
- CLOUD_SYNC_ENABLED=true

PROBLEMAS COMUNES:
- Backup falla por espacio insuficiente → Solución: Limpiar backups antiguos
- Verificación de integridad falla → Solución: Re-ejecutar backup
```

---

## 🔍 Checklist Final de Revisión

Antes de considerar el documento completo, verificar:

### Contenido
- [ ] Todas las secciones principales presentes
- [ ] Todos los comandos documentados
- [ ] Todos los recursos referenciados
- [ ] Ejemplos completos y funcionales
- [ ] Casos de uso documentados

### Navegación
- [ ] Tabla de contenidos completa y funcional
- [ ] Todos los enlaces internos funcionan
- [ ] Índices alfabéticos completos
- [ ] Índices por funcionalidad completos
- [ ] Quick Links organizados

### Usabilidad
- [ ] Quick Start permite setup en 5 minutos
- [ ] Comandos son copiables directamente
- [ ] Ejemplos son ejecutables
- [ ] Progresión lógica verificada
- [ ] Múltiples puntos de entrada funcionan

### Calidad
- [ ] Sin errores técnicos
- [ ] Formato consistente
- [ ] Estilo uniforme
- [ ] Referencias verificadas
- [ ] Información actualizada

---

## 📚 Recursos Adicionales

### Herramientas Recomendadas
- **Markdown Linters**: Para validar formato
- **Link Checkers**: Para verificar enlaces internos
- **Spell Checkers**: Para corrección ortográfica
- **Diagram Generators**: Para crear diagramas ASCII

### Mejores Prácticas
- Mantener comandos actualizados
- Revisar ejemplos periódicamente
- Actualizar roadmap según evolución del sistema
- Recopilar feedback de usuarios
- Iterar basado en uso real

---

**Este template está basado en el proceso exitoso de creación del Índice Maestro del Sistema de DMs de LinkedIn (7,363+ líneas, 150+ recursos organizados).**

**Última actualización:** {{AUTO}}


