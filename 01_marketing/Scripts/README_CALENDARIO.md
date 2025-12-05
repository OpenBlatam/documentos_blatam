# 🤖 Scripts de Automatización - Sistema de Calendario

**Versión:** 1.0  
**Fecha:** Mayo 2025

---

## 📋 Scripts Disponibles

### 1. converter_markdown_to_csv.py

**Propósito:** Convierte calendarios Markdown a CSV para herramientas de scheduling

**Uso:**
```bash
python converter_markdown_to_csv.py <archivo.md> <formato> [output.csv]
```

**Formatos soportados:**
- `hootsuite` - Formato para Hootsuite
- `buffer` - Formato para Buffer
- `later` - Formato para Later
- `sheets` - Formato para Google Sheets

**Ejemplos:**
```bash
# Convertir a Hootsuite
python converter_markdown_to_csv.py calendario.md hootsuite calendario_hootsuite.csv

# Convertir a Buffer
python converter_markdown_to_csv.py calendario.md buffer calendario_buffer.csv

# Convertir a Google Sheets
python converter_markdown_to_csv.py calendario.md sheets calendario_sheets.csv
```

**Características:**
- ✅ Parseo automático de tablas Markdown
- ✅ Normalización de datos
- ✅ Validación de formato
- ✅ Encoding UTF-8
- ✅ Manejo de errores

---

### 2. analyze_calendar.py

**Propósito:** Analiza calendarios generados y proporciona insights

**Uso:**
```bash
python analyze_calendar.py <archivo_calendario.md>
```

**Ejemplo:**
```bash
python analyze_calendar.py calendario.md
```

**Análisis proporcionado:**
- 📊 Distribución por plataforma
- 📝 Distribución por tipo de contenido
- 🎯 Top temas más usados
- ⏰ Frecuencia de posting
- ⚖️ Balance promocional vs. valor
- 🏷️ Análisis de hashtags

**Salida:**
```
📊 ANÁLISIS DE DISTRIBUCIÓN
📱 Distribución por Plataforma:
  Instagram: 20 posts (44.4%)
  Facebook: 15 posts (33.3%)
  ...

📝 Distribución por Tipo de Contenido:
  Educativo: 15 posts (33.3%)
  ...

⚖️ ANÁLISIS DE BALANCE
💰 Contenido Promocional: 10 posts (22.2%)
📚 Contenido de Valor: 35 posts (77.8%)
💡 Recomendación: ✅ Balance adecuado
```

---

## 🔧 Requisitos

### Python 3.6+

Los scripts requieren Python 3.6 o superior. No requieren dependencias externas (solo librerías estándar).

### Verificar instalación:
```bash
python3 --version
```

---

## 📦 Instalación

No requiere instalación. Los scripts son standalone y usan solo librerías estándar de Python.

### Hacer ejecutables (opcional):
```bash
chmod +x scripts/*.py
```

---

## 🚀 Uso Rápido

### Flujo Completo:

1. **Generar calendario** con el sistema de IA
2. **Guardar** como archivo Markdown (ej: `calendario.md`)
3. **Analizar** el calendario:
   ```bash
   python scripts/analyze_calendar.py calendario.md
   ```
4. **Convertir** a formato de herramienta:
   ```bash
   python scripts/converter_markdown_to_csv.py calendario.md hootsuite output.csv
   ```
5. **Importar** el CSV en tu herramienta de scheduling

---

## 📝 Formato Esperado

Los scripts esperan calendarios en formato Markdown con tablas:

```markdown
| Date | Platform | Content Type | Topic | Caption Preview | Hashtags | Posting Time | Status |
|------|----------|--------------|-------|-----------------|----------|--------------|--------|
| 2025-05-20 | Instagram | Educativo | Sostenibilidad | Caption... | #hashtag1 | 11:00 | Programado |
```

---

## 🐛 Solución de Problemas

### Error: "No se encontró el archivo"
- Verifica que el archivo existe
- Verifica la ruta correcta
- Usa ruta absoluta si es necesario

### Error: "No se encontraron posts"
- Verifica que el archivo Markdown contiene una tabla
- Verifica el formato de la tabla (debe tener pipes `|`)
- Asegúrate de que hay datos en las filas

### Error de encoding
- Los scripts usan UTF-8 por defecto
- Si hay problemas, verifica el encoding del archivo

---

## 💡 Tips

1. **Analiza primero:** Usa `analyze_calendar.py` antes de convertir para verificar el calendario
2. **Revisa el output:** Siempre revisa el CSV generado antes de importar
3. **Backup:** Guarda el Markdown original antes de convertir
4. **Prueba con un post:** Prueba la conversión con un calendario pequeño primero

---

## 🔄 Integración con Herramientas

### Hootsuite:
1. Convertir: `python converter_markdown_to_csv.py calendario.md hootsuite`
2. Importar en Hootsuite: Composer → Bulk Upload
3. Revisar y programar

### Buffer:
1. Convertir: `python converter_markdown_to_csv.py calendario.md buffer`
2. Importar en Buffer: Queue → Bulk Upload
3. Revisar y programar

### Google Sheets:
1. Convertir: `python converter_markdown_to_csv.py calendario.md sheets`
2. Abrir CSV en Google Sheets
3. Usar como base para automatización con Zapier

---

## 📚 Documentación Relacionada

- `GUIA_INTEGRACION_HERRAMIENTAS.md` - Guía completa de integración
- `GUIA_USO_SISTEMA_CALENDARIO.md` - Guía de uso del sistema
- `QUICK_START_CALENDARIO.md` - Inicio rápido

---

## 🤝 Contribuciones

Para mejorar los scripts:
1. Revisa el código
2. Prueba con diferentes calendarios
3. Reporta bugs o sugiere mejoras

---

**Última actualización:** Mayo 2025  
**Versión:** 1.0

---

*Estos scripts facilitan la automatización y análisis de calendarios generados con el sistema.*









