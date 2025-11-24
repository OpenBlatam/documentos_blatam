# ✅ Sistema de Validación de Calendarios

**Versión:** 1.0  
**Fecha:** Mayo 2025  
**Propósito:** Checklist completo para validar calendarios generados

---

## 📋 Checklist de Validación Completo

### 1. Validación Estructural

#### ✅ Estructura del Documento
- [ ] Tiene introducción (2-4 oraciones, sin header)
- [ ] Tiene sección de estrategia de contenido
- [ ] Tiene calendario en formato tabla
- [ ] Tiene sección de temas/pilares
- [ ] Tiene sección de timing y frecuencia
- [ ] Tiene sección de hashtags
- [ ] Tiene resumen final (sin pregunta)

#### ✅ Formato de Tabla
- [ ] Tabla tiene headers correctos
- [ ] Columnas estándar presentes:
  - Date
  - Platform
  - Content Type
  - Topic/Theme
  - Caption Preview
  - Hashtags
  - Posting Time
  - Status (opcional)
- [ ] Todas las filas tienen datos completos
- [ ] Formato Markdown correcto (pipes `|`)

---

### 2. Validación de Contenido

#### ✅ Completitud
- [ ] Todos los días del período tienen al menos un post
- [ ] Todas las plataformas especificadas están cubiertas
- [ ] Todos los temas mencionados están incluidos
- [ ] Distribución de contenido es balanceada

#### ✅ Calidad de Contenido
- [ ] Captions son específicos (no genéricos)
- [ ] Temas son relevantes para la marca
- [ ] Voz y tono son consistentes
- [ ] Contenido es accionable
- [ ] No hay placeholders genéricos

#### ✅ Balance de Contenido
- [ ] Ratio 80/20 (valor/promocional) o según especificado
- [ ] Variedad de tipos de contenido
- [ ] No hay repetición excesiva
- [ ] Contenido educativo presente
- [ ] Contenido promocional balanceado

---

### 3. Validación de Datos

#### ✅ Fechas
- [ ] Formato correcto (YYYY-MM-DD o especificado)
- [ ] Fechas están en orden cronológico
- [ ] No hay fechas duplicadas incorrectamente
- [ ] Fechas están dentro del período especificado
- [ ] Días de la semana coinciden con fechas

#### ✅ Horarios
- [ ] Formato correcto (HH:MM 24h)
- [ ] Zona horaria especificada
- [ ] Horarios son realistas
- [ ] Horarios están optimizados por plataforma
- [ ] No hay conflictos de horarios

#### ✅ Plataformas
- [ ] Nombres de plataformas son correctos
- [ ] Todas las plataformas del brief están incluidas
- [ ] Distribución entre plataformas es apropiada
- [ ] Contenido está adaptado por plataforma

---

### 4. Validación de Estrategia

#### ✅ Alineación con Objetivos
- [ ] Contenido apoya objetivos principales
- [ ] KPIs mencionados son alcanzables
- [ ] Estrategia es coherente
- [ ] Tácticas apoyan objetivos

#### ✅ Alineación con Audiencia
- [ ] Contenido es relevante para audiencia
- [ ] Voz y tono son apropiados
- [ ] Temas son de interés para audiencia
- [ ] Horarios están optimizados para audiencia

#### ✅ Alineación con Marca
- [ ] Voz y tono son consistentes con marca
- [ ] Valores de marca están reflejados
- [ ] Mensajes clave están presentes
- [ ] No hay contenido que contradiga marca

---

### 5. Validación de Hashtags

#### ✅ Formato
- [ ] Hashtags están en formato correcto (#hashtag)
- [ ] Separados apropiadamente (espacios)
- [ ] Cantidad apropiada por plataforma:
  - Instagram: 5-10
  - Facebook: 1-2
  - Twitter/X: 1-2
  - LinkedIn: 3-5
  - TikTok: 3-5

#### ✅ Relevancia
- [ ] Hashtags son relevantes al contenido
- [ ] Mix de branded, industry, y trending
- [ ] No hay hashtags genéricos excesivos
- [ ] Hashtags están optimizados por plataforma

---

### 6. Validación de Optimización

#### ✅ Frecuencia
- [ ] Frecuencia es apropiada por plataforma
- [ ] No es excesiva (realista de ejecutar)
- [ ] No es insuficiente (mantiene presencia)
- [ ] Distribución semanal es balanceada

#### ✅ Timing
- [ ] Horarios están optimizados
- [ ] Considera zona horaria de audiencia
- [ ] Evita horas muertas
- [ ] Aprovecha horas pico

#### ✅ Repurposing
- [ ] Oportunidades de repurposing identificadas
- [ ] Contenido puede adaptarse entre plataformas
- [ ] Eficiencia de contenido maximizada

---

## 🔍 Validación Automática con Scripts

### Usar Script de Análisis

```bash
python scripts/analyze_calendar.py calendario.md
```

**El script valida:**
- ✅ Distribución por plataforma
- ✅ Distribución por tipo de contenido
- ✅ Frecuencia de posting
- ✅ Balance promocional vs. valor
- ✅ Uso de hashtags

**Revisa el output para:**
- ⚠️ Advertencias sobre balance
- ⚠️ Recomendaciones de optimización
- ⚠️ Problemas de distribución

---

## 📊 Scorecard de Validación

### Sistema de Puntuación

**Estructura (20 puntos):**
- Introducción presente: 5 puntos
- Tabla formateada correctamente: 10 puntos
- Resumen presente: 5 puntos

**Contenido (30 puntos):**
- Completitud: 10 puntos
- Calidad: 10 puntos
- Balance: 10 puntos

**Datos (20 puntos):**
- Fechas correctas: 5 puntos
- Horarios correctos: 5 puntos
- Plataformas correctas: 5 puntos
- Datos completos: 5 puntos

**Estrategia (20 puntos):**
- Alineación con objetivos: 7 puntos
- Alineación con audiencia: 7 puntos
- Alineación con marca: 6 puntos

**Optimización (10 puntos):**
- Frecuencia apropiada: 3 puntos
- Timing optimizado: 4 puntos
- Repurposing: 3 puntos

**Total: 100 puntos**

### Interpretación de Scores

- **90-100 puntos:** ✅ Excelente - Listo para usar
- **80-89 puntos:** ✅ Bueno - Pequeños ajustes recomendados
- **70-79 puntos:** ⚠️ Aceptable - Requiere revisiones
- **<70 puntos:** ❌ Necesita mejoras significativas

---

## 🛠️ Herramientas de Validación

### 1. Validación Manual

**Usa el checklist completo arriba**
- Revisa cada sección
- Marca items completados
- Identifica áreas de mejora

### 2. Validación con Scripts

**Script de Análisis:**
```bash
python scripts/analyze_calendar.py calendario.md
```

**Script de Conversión (valida formato):**
```bash
python scripts/converter_markdown_to_csv.py calendario.md sheets test.csv
# Si genera CSV sin errores, formato es válido
```

### 3. Validación Visual

**Revisa:**
- Estructura visual del documento
- Formato de tablas
- Consistencia de estilo
- Legibilidad

---

## ⚠️ Errores Comunes y Cómo Evitarlos

### Error 1: Fechas Incorrectas
**Causa:** Brief no especifica formato de fecha  
**Solución:** Especificar formato en brief

### Error 2: Contenido Genérico
**Causa:** Brief muy general  
**Solución:** Agregar ejemplos y contexto específico

### Error 3: Desbalance de Contenido
**Causa:** No se especifica ratio  
**Solución:** Especificar ratio en brief (ej: 80/20)

### Error 4: Hashtags Incorrectos
**Causa:** No se especifica cantidad por plataforma  
**Solución:** Especificar cantidad en brief

### Error 5: Horarios Incorrectos
**Causa:** Zona horaria no especificada  
**Solución:** Especificar zona horaria en brief

---

## 📝 Template de Reporte de Validación

```
VALIDACIÓN DE CALENDARIO
========================

Archivo: [nombre]
Fecha: [fecha]
Validador: [nombre]

ESTRUCTURA: [X/20 puntos]
- Introducción: ✅/❌
- Tabla: ✅/❌
- Resumen: ✅/❌

CONTENIDO: [X/30 puntos]
- Completitud: ✅/❌
- Calidad: ✅/❌
- Balance: ✅/❌

DATOS: [X/20 puntos]
- Fechas: ✅/❌
- Horarios: ✅/❌
- Plataformas: ✅/❌

ESTRATEGIA: [X/20 puntos]
- Objetivos: ✅/❌
- Audiencia: ✅/❌
- Marca: ✅/❌

OPTIMIZACIÓN: [X/10 puntos]
- Frecuencia: ✅/❌
- Timing: ✅/❌

SCORE TOTAL: [X/100 puntos]
CALIFICACIÓN: [Excelente/Bueno/Aceptable/Necesita Mejoras]

PROBLEMAS IDENTIFICADOS:
1. [problema]
2. [problema]

RECOMENDACIONES:
1. [recomendación]
2. [recomendación]

ACCIÓN REQUERIDA:
[ ] Aprobado para uso
[ ] Requiere revisiones menores
[ ] Requiere regeneración
```

---

## 🚀 Flujo de Validación Recomendado

### Paso 1: Validación Rápida (5 min)
- [ ] Revisar estructura básica
- [ ] Verificar tabla presente
- [ ] Revisar completitud básica

### Paso 2: Validación Detallada (15 min)
- [ ] Usar checklist completo
- [ ] Revisar cada sección
- [ ] Identificar problemas

### Paso 3: Validación con Scripts (5 min)
- [ ] Ejecutar script de análisis
- [ ] Revisar output
- [ ] Validar formato con conversión

### Paso 4: Validación Final (10 min)
- [ ] Revisar problemas identificados
- [ ] Aplicar correcciones
- [ ] Validar nuevamente

**Total: ~35 minutos**

---

## ✅ Criterios de Aprobación

### Aprobado para Uso:
- ✅ Score > 80 puntos
- ✅ Sin errores críticos
- ✅ Estructura completa
- ✅ Contenido de calidad
- ✅ Datos correctos

### Requiere Revisiones Menores:
- ⚠️ Score 70-79 puntos
- ⚠️ Errores menores presentes
- ⚠️ Ajustes rápidos necesarios

### Requiere Regeneración:
- ❌ Score < 70 puntos
- ❌ Errores críticos
- ❌ Estructura incompleta
- ❌ Contenido de baja calidad

---

**Última actualización:** Mayo 2025  
**Versión:** 1.0

---

*Usa este sistema de validación para asegurar que tus calendarios generados cumplan con estándares de calidad antes de implementarlos.*




