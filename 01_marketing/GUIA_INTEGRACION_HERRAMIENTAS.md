# 🔗 Guía de Integración con Herramientas de Scheduling

**Versión:** 1.0  
**Fecha:** Mayo 2025  
**Propósito:** Integrar calendarios generados con herramientas populares

---

## 📋 Índice

1. [Herramientas Soportadas](#herramientas-soportadas)
2. [Hootsuite](#hootsuite)
3. [Buffer](#buffer)
4. [Later](#later)
5. [Sprout Social](#sprout-social)
6. [Meta Business Suite](#meta-business-suite)
7. [Google Sheets como Base](#google-sheets-como-base)
8. [Automatización con Zapier](#automatización-con-zapier)
9. [Scripts de Conversión](#scripts-de-conversión)

---

## Herramientas Soportadas

Esta guía cubre la integración con las siguientes herramientas:

- ✅ Hootsuite
- ✅ Buffer
- ✅ Later
- ✅ Sprout Social
- ✅ Meta Business Suite
- ✅ Google Sheets
- ✅ Zapier (automatización)
- ✅ Custom APIs

---

## Hootsuite

### Formato de Importación

Hootsuite acepta archivos CSV con las siguientes columnas:

```csv
Date,Time,Platform,Message,Link,Image URL
2025-05-20,11:00,Instagram,"Caption del post",https://example.com,https://example.com/image.jpg
2025-05-20,13:00,Facebook,"Caption del post",https://example.com,https://example.com/image.jpg
```

### Pasos de Integración

1. **Generar Calendario** con el sistema de IA
2. **Exportar a CSV** usando el formato de Hootsuite
3. **Importar en Hootsuite:**
   - Ve a "Composer" → "Bulk Upload"
   - Selecciona tu archivo CSV
   - Revisa y programa posts

### Template CSV para Hootsuite

```csv
Date,Time,Platform,Message,Link,Image URL
[YYYY-MM-DD],[HH:MM],[Instagram/Facebook/Twitter/LinkedIn],[Caption],[URL opcional],[URL imagen]
```

### Ejemplo Completo

```csv
Date,Time,Platform,Message,Link,Image URL
2025-05-20,11:00,Instagram,"🌟 Nuevo post sobre sostenibilidad! #EcoFashion #Sostenibilidad",https://ecofashion.com/post1,https://ecofashion.com/images/post1.jpg
2025-05-20,13:00,Facebook,"Comparte tu outfit sostenible favorito en los comentarios 👇",https://ecofashion.com/post1,https://ecofashion.com/images/post1.jpg
```

---

## Buffer

### Formato de Importación

Buffer usa un formato similar pero con columnas ligeramente diferentes:

```csv
Date,Time,Platform,Text,Link,Image,Profile
2025-05-20,11:00,Instagram,"Caption del post",https://example.com,https://example.com/image.jpg,@username
```

### Pasos de Integración

1. **Generar Calendario** con el sistema
2. **Convertir a formato Buffer:**
   - Usa el script de conversión (ver abajo)
   - O manualmente ajusta las columnas
3. **Importar en Buffer:**
   - Ve a "Queue" → "Bulk Upload"
   - Sube tu CSV
   - Revisa y programa

### Template CSV para Buffer

```csv
Date,Time,Platform,Text,Link,Image,Profile
[YYYY-MM-DD],[HH:MM],[instagram/facebook/twitter/linkedin],[Caption],[URL],[URL imagen],[@username]
```

---

## Later

### Formato de Importación

Later tiene un formato específico con hashtags separados:

```csv
Date,Time,Platform,Caption,Media URL,Hashtags,First Comment
2025-05-20,11:00,Instagram,"Caption principal",https://example.com/image.jpg,"#hashtag1 #hashtag2 #hashtag3","Primer comentario opcional"
```

### Pasos de Integración

1. **Generar Calendario** con hashtags incluidos
2. **Formatear para Later:**
   - Separar hashtags en columna dedicada
   - Incluir URLs de media
3. **Importar en Later:**
   - Ve a "Calendar" → "Bulk Upload"
   - Sube CSV
   - Revisa y programa

### Template CSV para Later

```csv
Date,Time,Platform,Caption,Media URL,Hashtags,First Comment
[YYYY-MM-DD],[HH:MM],[Instagram/Facebook/Twitter/Pinterest],[Caption],[URL media],[#hashtag1 #hashtag2],[Comentario opcional]
```

---

## Sprout Social

### Formato de Importación

Sprout Social requiere un formato más estructurado:

```csv
Date,Time,Platform,Message,Link,Image URL,Hashtags,First Comment
2025-05-20,11:00,Instagram,"Caption",https://example.com,https://example.com/image.jpg,"#hashtag1 #hashtag2",""
```

### Pasos de Integración

1. **Generar Calendario**
2. **Formatear para Sprout:**
   - Incluir todas las columnas requeridas
   - Formato de fecha: YYYY-MM-DD
   - Formato de hora: HH:MM (24h)
3. **Importar en Sprout:**
   - Ve a "Publishing" → "Bulk Upload"
   - Sube CSV
   - Revisa y programa

---

## Meta Business Suite

### Formato de Importación

Meta Business Suite (Facebook/Instagram) usa formato JSON o CSV:

```csv
Date,Time,Platform,Message,Link,Image URL
2025-05-20,11:00,Instagram,"Caption",https://example.com,https://example.com/image.jpg
```

### Pasos de Integración

1. **Generar Calendario**
2. **Filtrar solo Facebook/Instagram**
3. **Importar en Meta Business Suite:**
   - Ve a "Posts" → "Create Post"
   - Usa "Schedule" para programar
   - O importa CSV si está disponible

### Notas Importantes

- Meta Business Suite maneja Facebook e Instagram juntos
- Los hashtags funcionan mejor en Instagram
- Los links en posts de Instagram van en la bio (no en el post)

---

## Google Sheets como Base

### Estrategia

Usar Google Sheets como base central y conectar con otras herramientas:

### Estructura de Hoja

| Fecha | Hora | Plataforma | Tipo | Tema | Caption | Hashtags | Link | Imagen | Estado |
|-------|------|------------|------|------|---------|----------|------|--------|--------|
| 2025-05-20 | 11:00 | Instagram | Educativo | Sostenibilidad | Caption... | #hashtag1 | URL | URL | Programado |

### Ventajas

- ✅ Fácil de editar y colaborar
- ✅ Puede conectarse con múltiples herramientas
- ✅ Historial de cambios
- ✅ Fácil de compartir

### Integración con Zapier

Ver sección de Zapier más abajo.

---

## Automatización con Zapier

### Flujo Recomendado

**Trigger:** Nuevo calendario generado  
**Action:** Crear posts en herramienta de scheduling

### Zap Templates

#### Zap 1: Google Sheets → Buffer

1. **Trigger:** Nueva fila en Google Sheets
2. **Filter:** Si "Estado" = "Listo para programar"
3. **Action:** Crear post en Buffer
   - Mapear columnas: Date, Time, Platform, Caption, etc.

#### Zap 2: Google Sheets → Hootsuite

1. **Trigger:** Nueva fila en Google Sheets
2. **Filter:** Si "Estado" = "Aprobado"
3. **Action:** Crear post en Hootsuite
   - Mapear columnas correspondientes

#### Zap 3: Calendario IA → Google Sheets

1. **Trigger:** Nuevo calendario generado (webhook)
2. **Action:** Agregar filas a Google Sheets
   - Parsear calendario Markdown
   - Convertir a filas de hoja

### Configuración de Zapier

**Paso 1:** Conectar Google Sheets
- Autenticar con Google
- Seleccionar hoja específica

**Paso 2:** Configurar Trigger
- Nueva fila agregada
- O fila actualizada

**Paso 3:** Configurar Action
- Seleccionar herramienta (Buffer, Hootsuite, etc.)
- Mapear campos:
  - Date → Fecha de publicación
  - Time → Hora de publicación
  - Platform → Plataforma
  - Caption → Mensaje
  - Hashtags → Hashtags
  - Image URL → Media

**Paso 4:** Probar y Activar

---

## Scripts de Conversión

### Script Python: Markdown a CSV (Hootsuite)

```python
#!/usr/bin/env python3
"""Convierte calendario Markdown a CSV para Hootsuite"""

import re
import csv
from datetime import datetime

def markdown_to_hootsuite_csv(markdown_file, output_file):
    """Convierte tabla Markdown a CSV de Hootsuite"""
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraer tabla Markdown
    table_pattern = r'\|(.+)\|'
    rows = re.findall(table_pattern, content)
    
    # Procesar filas
    posts = []
    for row in rows[2:]:  # Saltar header y separador
        cells = [cell.strip() for cell in row.split('|') if cell.strip()]
        if len(cells) >= 4:
            date = cells[0]
            time = cells[7] if len(cells) > 7 else "11:00"
            platform = cells[1]
            caption = cells[4] if len(cells) > 4 else ""
            link = cells[5] if len(cells) > 5 else ""
            image = cells[6] if len(cells) > 6 else ""
            
            posts.append({
                'Date': date,
                'Time': time,
                'Platform': platform,
                'Message': caption,
                'Link': link,
                'Image URL': image
            })
    
    # Escribir CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Time', 'Platform', 'Message', 'Link', 'Image URL'])
        writer.writeheader()
        writer.writerows(posts)
    
    print(f"✅ CSV creado: {output_file}")

if __name__ == '__main__':
    markdown_to_hootsuite_csv('calendario.md', 'calendario_hootsuite.csv')
```

### Script Python: Markdown a CSV (Buffer)

```python
#!/usr/bin/env python3
"""Convierte calendario Markdown a CSV para Buffer"""

def markdown_to_buffer_csv(markdown_file, output_file, username):
    """Similar al anterior pero con formato Buffer"""
    # Similar estructura, ajustar columnas
    pass
```

### Script Python: Markdown a Google Sheets

```python
#!/usr/bin/env python3
"""Sube calendario Markdown a Google Sheets"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def upload_to_google_sheets(markdown_file, sheet_name):
    """Sube calendario a Google Sheets"""
    
    # Autenticar
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    
    # Abrir o crear hoja
    try:
        sheet = client.open(sheet_name).sheet1
    except:
        sheet = client.create(sheet_name).sheet1
    
    # Parsear Markdown y subir datos
    # (similar a scripts anteriores)
    
    print(f"✅ Calendario subido a Google Sheets: {sheet_name}")
```

---

## 🔄 Flujo de Trabajo Recomendado

### Opción 1: Manual

1. Generar calendario con IA
2. Copiar tabla Markdown
3. Convertir a CSV (script o manual)
4. Importar en herramienta de scheduling
5. Revisar y programar

### Opción 2: Semi-Automático

1. Generar calendario con IA
2. Guardar en Google Sheets
3. Usar Zapier para conectar Sheets → Scheduling Tool
4. Revisar y aprobar en herramienta

### Opción 3: Automático (Avanzado)

1. Generar calendario con IA (API)
2. Parsear automáticamente
3. Subir a Google Sheets
4. Zapier detecta cambios
5. Crea posts automáticamente
6. Notificación para revisión

---

## 📝 Checklist de Integración

Antes de integrar, verifica:

- [ ] Formato de fecha correcto (YYYY-MM-DD)
- [ ] Formato de hora correcto (HH:MM 24h)
- [ ] Nombres de plataformas correctos
- [ ] URLs de imágenes válidas
- [ ] Hashtags formateados correctamente
- [ ] Captions dentro del límite de caracteres
- [ ] Timezone especificado
- [ ] Campos requeridos completos

---

## 🛠️ Herramientas Adicionales

### Convertidores Online

- **CSV to JSON:** Para APIs
- **Markdown to CSV:** Para conversión rápida
- **Excel to CSV:** Si trabajas en Excel

### APIs Disponibles

- **Buffer API:** Para automatización completa
- **Hootsuite API:** Para integración programática
- **Meta Graph API:** Para Facebook/Instagram
- **Twitter API:** Para Twitter/X
- **LinkedIn API:** Para LinkedIn

---

## 📚 Recursos Adicionales

### Documentación Oficial

- [Hootsuite Bulk Upload](https://help.hootsuite.com/)
- [Buffer API Docs](https://buffer.com/developers/api)
- [Later API](https://docs.later.com/)
- [Zapier Templates](https://zapier.com/apps)

### Tutoriales

- Cómo configurar Zapier para social media
- Automatización de contenido con APIs
- Integración Google Sheets con herramientas

---

**Última actualización:** Mayo 2025  
**Versión:** 1.0

---

*Esta guía te ayudará a integrar tus calendarios generados con las herramientas de scheduling más populares del mercado.*




