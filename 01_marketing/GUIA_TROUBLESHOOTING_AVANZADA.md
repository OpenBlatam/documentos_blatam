# 🔧 Guía de Troubleshooting Avanzada

**Versión:** 1.0  
**Fecha:** Mayo 2025  
**Nivel:** Avanzado

---

## 📋 Índice

1. [Problemas de Generación](#problemas-de-generación)
2. [Problemas de Formato](#problemas-de-formato)
3. [Problemas de Contenido](#problemas-de-contenido)
4. [Problemas de Integración](#problemas-de-integración)
5. [Problemas de Métricas](#problemas-de-métricas)
6. [Problemas de Optimización](#problemas-de-optimización)
7. [Soluciones Rápidas](#soluciones-rápidas)

---

## Problemas de Generación

### ❌ Problema: El calendario no se genera o está incompleto

**Síntomas:**
- La IA no responde
- El calendario se corta a la mitad
- Faltan días o semanas

**Causas Posibles:**
1. Brief demasiado largo o complejo
2. Token limit alcanzado
3. Instrucciones contradictorias
4. Formato de brief incorrecto

**Soluciones:**

#### Solución 1: Simplificar el Brief
```
❌ MAL:
Marca: [500 palabras de descripción]
Plataformas: [lista de 10 plataformas]
[20 temas diferentes]
[10 objetivos]

✅ BIEN:
Marca: [Nombre breve]
Plataformas: [2-3 principales]
Temas: [3-5 temas clave]
Objetivos: [1-2 objetivos principales]
```

#### Solución 2: Dividir en Fases
```
Fase 1: Generar calendario semanal
Fase 2: Expandir a mensual
Fase 3: Agregar detalles
```

#### Solución 3: Usar Prompt Más Específico
```
En lugar de: "Crea un calendario completo"
Usa: "Crea un calendario semanal con 7 posts, uno por día"
```

---

### ❌ Problema: El calendario es demasiado genérico

**Síntomas:**
- Contenido sin personalidad
- Temas muy generales
- Falta de especificidad

**Soluciones:**

#### Solución 1: Agregar Ejemplos
```
Temas: Sostenibilidad
Ejemplos: "Cómo reducir residuos en el hogar", 
          "Marcas sostenibles locales",
          "Impacto ambiental de la moda rápida"
```

#### Solución 2: Especificar Voz y Tono
```
❌ MAL: "Voz profesional"
✅ BIEN: "Voz profesional pero accesible, 
         usa lenguaje técnico explicado, 
         tono consultivo, evita jerga excesiva"
```

#### Solución 3: Incluir Contexto de Marca
```
Agrega al brief:
- Valores de la marca
- Mensajes clave
- Ejemplos de contenido que te gusta
- Contenido que NO quieres
```

---

## Problemas de Formato

### ❌ Problema: Las tablas no se formatean correctamente

**Síntomas:**
- Tablas desalineadas
- Columnas faltantes
- Formato inconsistente

**Soluciones:**

#### Solución 1: Especificar Formato en el Brief
```
Agrega al final del brief:
"Formato requerido: Tabla Markdown con columnas:
Date | Platform | Content Type | Topic | Caption Preview | Hashtags | Posting Time | Status"
```

#### Solución 2: Usar Template de Tabla
```
Incluye en el brief un ejemplo de cómo quieres la tabla:
| Date | Platform | Type | Topic | Caption | Hashtags | Time |
|------|----------|------|-------|---------|----------|------|
| 2025-05-20 | Instagram | Educativo | Sostenibilidad | ... | #hashtag | 11:00 |
```

#### Solución 3: Post-Procesamiento
```
Usa el script de conversión para normalizar:
python scripts/converter_markdown_to_csv.py calendario.md sheets
```

---

### ❌ Problema: Fechas y horarios incorrectos

**Síntomas:**
- Fechas en formato incorrecto
- Horarios sin zona horaria
- Días de la semana incorrectos

**Soluciones:**

#### Solución 1: Especificar Formato de Fecha
```
Agrega al brief:
"Formato de fecha: YYYY-MM-DD (ej: 2025-05-20)
Formato de hora: HH:MM en formato 24h (ej: 14:30)
Zona horaria: [Tu zona horaria, ej: UTC-5, EST]"
```

#### Solución 2: Proporcionar Calendario Base
```
Incluye en el brief:
"Semana del 20 al 26 de mayo de 2025:
- Lunes 20: [tema]
- Martes 21: [tema]
..."
```

#### Solución 3: Validación Post-Generación
```
Usa el script de análisis:
python scripts/analyze_calendar.py calendario.md
Revisa la sección de frecuencia
```

---

## Problemas de Contenido

### ❌ Problema: El contenido no se alinea con la marca

**Síntomas:**
- Voz inconsistente
- Temas fuera de marca
- Mensajes incorrectos

**Soluciones:**

#### Solución 1: Brand Guidelines Detalladas
```
Incluye en el brief:
Voz y Tono:
- Palabras que SÍ usar: [lista]
- Palabras que NO usar: [lista]
- Frases clave de la marca: [lista]
- Ejemplos de contenido que representa la marca: [links/ejemplos]
```

#### Solución 2: Ejemplos Positivos y Negativos
```
Agrega:
"Ejemplos de contenido que SÍ queremos: [ejemplos]
Ejemplos de contenido que NO queremos: [ejemplos]"
```

#### Solución 3: Revisión Iterativa
```
Paso 1: Generar calendario base
Paso 2: Revisar y marcar posts que no encajan
Paso 3: Pedir regeneración de esos posts específicos
```

---

### ❌ Problema: Falta de variedad en el contenido

**Síntomas:**
- Mismos temas repetidos
- Mismo formato siempre
- Falta de creatividad

**Soluciones:**

#### Solución 1: Especificar Variedad
```
Agrega al brief:
"Distribución de tipos de contenido:
- Educativo: 30%
- Entretenimiento: 25%
- Promocional: 20%
- Comunidad: 15%
- Liderazgo: 10%

Formatos a incluir:
- Carousels
- Videos cortos
- Posts estáticos
- Stories
- Reels"
```

#### Solución 2: Lista de Temas Expandida
```
En lugar de: "Temas: Sostenibilidad, Moda"
Usa: "Temas principales: Sostenibilidad, Moda
Subtemas: 
- Sostenibilidad: [5 subtemas]
- Moda: [5 subtemas]
- Lifestyle: [5 subtemas]"
```

#### Solución 3: Solicitar Variaciones
```
Agrega: "Para cada tema, crea 3 variaciones diferentes:
1. Enfoque educativo
2. Enfoque inspiracional  
3. Enfoque práctico"
```

---

## Problemas de Integración

### ❌ Problema: El CSV no se importa correctamente

**Síntomas:**
- Errores al importar
- Columnas incorrectas
- Datos perdidos

**Soluciones:**

#### Solución 1: Verificar Formato de Herramienta
```
Consulta: GUIA_INTEGRACION_HERRAMIENTAS.md
Verifica el formato exacto requerido
Ajusta el script de conversión si es necesario
```

#### Solución 2: Validar CSV Antes de Importar
```
1. Abre el CSV en Excel/Sheets
2. Verifica que todas las columnas estén presentes
3. Verifica que no haya caracteres especiales problemáticos
4. Verifica encoding (debe ser UTF-8)
```

#### Solución 3: Limpiar Datos
```
Problemas comunes:
- Comas en captions → usar comillas
- Saltos de línea → reemplazar con espacios
- Caracteres especiales → codificar correctamente
```

---

### ❌ Problema: Hashtags no se importan correctamente

**Síntomas:**
- Hashtags perdidos
- Formato incorrecto
- Demasiados/pocos hashtags

**Soluciones:**

#### Solución 1: Especificar Formato de Hashtags
```
Agrega al brief:
"Formato de hashtags: Separados por espacios, 
máximo 10 por post para Instagram,
máximo 2 para Twitter/X"
```

#### Solución 2: Columna Dedicada
```
Asegúrate de que los hashtags estén en columna separada
No mezclar con el caption
```

#### Solución 3: Validación Post-Conversión
```
Revisa el CSV generado
Verifica que los hashtags estén en la columna correcta
Ajusta manualmente si es necesario
```

---

## Problemas de Métricas

### ❌ Problema: No sé qué métricas usar

**Síntomas:**
- KPIs no definidos
- Métricas irrelevantes
- Falta de objetivos claros

**Soluciones:**

#### Solución 1: Usar Template de KPIs
```
Consulta: PLANTILLAS_ESPECIALIZADAS.md
Cada industria tiene KPIs específicos recomendados
```

#### Solución 2: Definir KPIs por Objetivo
```
Si objetivo es Awareness:
- Alcance
- Impresiones
- Crecimiento de seguidores

Si objetivo es Engagement:
- Engagement rate
- Likes, comentarios, shares
- Tiempo de visualización

Si objetivo es Conversiones:
- Clics al sitio
- Conversiones
- ROI
```

#### Solución 3: Usar Dashboard Excel
```
Abre: SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.xlsx
Ve a hoja "16_Dashboard"
Usa las métricas predefinidas como guía
```

---

### ❌ Problema: Métricas no alcanzan objetivos

**Síntomas:**
- Engagement bajo
- Pocas conversiones
- Alcance limitado

**Soluciones:**

#### Solución 1: Análisis de Contenido
```
Usa: python scripts/analyze_calendar.py calendario.md
Revisa:
- Balance promocional vs. valor
- Distribución de tipos de contenido
- Frecuencia de posting
```

#### Solución 2: Ajustar Estrategia
```
Si engagement bajo:
- Aumentar contenido de valor
- Mejorar horarios de posting
- Aumentar interacción con audiencia

Si conversiones bajas:
- Revisar CTAs
- Mejorar contenido promocional
- Optimizar landing pages
```

#### Solución 3: A/B Testing
```
Prueba diferentes:
- Horarios de posting
- Tipos de contenido
- Formatos
- Hashtags
```

---

## Problemas de Optimización

### ❌ Problema: El calendario no es eficiente

**Síntomas:**
- Demasiado trabajo manual
- Falta de repurposing
- Contenido duplicado

**Soluciones:**

#### Solución 1: Estrategia de Repurposing
```
Identifica contenido "anchor" (principal)
Crea variaciones para otras plataformas:
- Artículo largo → Carousel
- Video → Clips cortos
- Post → Thread
```

#### Solución 2: Automatización
```
Usa scripts:
- Conversión automática
- Análisis automático
- Integración con herramientas
```

#### Solución 3: Templates Reutilizables
```
Crea templates para:
- Tipos de posts comunes
- Formatos de captions
- Estrategias de hashtags
```

---

## Soluciones Rápidas

### ⚡ Checklist de Troubleshooting Rápido

**Antes de generar:**
- [ ] Brief es específico y completo
- [ ] Objetivos están claros
- [ ] Audiencia está bien definida
- [ ] Temas están especificados
- [ ] Formato requerido está claro

**Después de generar:**
- [ ] Revisar estructura del calendario
- [ ] Verificar fechas y horarios
- [ ] Revisar balance de contenido
- [ ] Validar formato de tablas
- [ ] Verificar hashtags

**Antes de importar:**
- [ ] CSV está en formato correcto
- [ ] Todas las columnas presentes
- [ ] Encoding es UTF-8
- [ ] Datos están limpios
- [ ] Hashtags están separados

---

### 🔍 Diagnóstico Rápido

**Si el calendario es genérico:**
→ Agrega más contexto de marca y ejemplos

**Si faltan días:**
→ Simplifica el brief o divide en fases

**Si el formato está mal:**
→ Especifica formato exacto en el brief

**Si no se alinea con marca:**
→ Agrega brand guidelines detalladas

**Si las métricas son bajas:**
→ Analiza balance y ajusta estrategia

---

## 📞 Escalación

### Si nada funciona:

1. **Revisa la documentación:**
   - `GUIA_USO_SISTEMA_CALENDARIO.md`
   - `CASOS_ESTUDIO_CALENDARIOS.md`
   - `PLANTILLAS_ESPECIALIZADAS.md`

2. **Usa plantillas probadas:**
   - Copia un caso de estudio similar
   - Adapta a tu marca
   - Ajusta según resultados

3. **Divide y conquista:**
   - Genera calendario semanal primero
   - Expande a mensual después
   - Agrega detalles gradualmente

4. **Itera:**
   - Genera versión 1
   - Revisa y ajusta
   - Genera versión 2 mejorada
   - Repite hasta obtener resultado deseado

---

**Última actualización:** Mayo 2025  
**Versión:** 1.0

---

*Esta guía cubre los problemas más comunes y sus soluciones. Si encuentras un problema no cubierto, documenta el caso para futuras mejoras.*




