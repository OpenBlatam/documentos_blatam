# 📋 Instrucciones para Generar Documentos Word y PDF

Este documento explica cómo generar los documentos Word (.docx) y PDF a partir del archivo Markdown del Sistema de Calendario de Contenido de Redes Sociales.

## 📦 Requisitos Previos

### Opción 1: Generación Automática con Python

Instala las siguientes librerías de Python:

```bash
pip install python-docx markdown2 weasyprint
```

**Nota:** `weasyprint` puede requerir dependencias del sistema adicionales:
- **macOS:** `brew install cairo pango gdk-pixbuf libffi`
- **Linux (Ubuntu/Debian):** `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0`
- **Windows:** Las dependencias se instalan automáticamente con pip

### Opción 2: Generación Manual (Sin Python)

Puedes convertir el Markdown manualmente usando herramientas online o software de escritorio.

## 🚀 Método 1: Script Automático

### Ejecutar el Script

```bash
cd /Users/adan/Documents/documentos_blatam/01_marketing
python3 generar_documentos_calendario.py
```

El script generará:
- `SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.docx` (Word)
- `SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.pdf` (PDF)

## 🖥️ Método 2: Conversión Manual

### Para Word (.docx)

1. **Usando Pandoc (Recomendado):**
   ```bash
   # Instalar pandoc
   brew install pandoc  # macOS
   # o
   sudo apt-get install pandoc  # Linux
   
   # Convertir
   pandoc SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.md \
     -o SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.docx \
     --reference-doc=template.docx  # Opcional: usar plantilla
   ```

2. **Usando Herramientas Online:**
   - [CloudConvert](https://cloudconvert.com/md-to-docx)
   - [Zamzar](https://www.zamzar.com/convert/md-to-docx/)
   - [Markdown to Word](https://www.markdowntoword.com/)

3. **Usando Microsoft Word:**
   - Abre Word
   - Archivo → Abrir → Selecciona el archivo .md
   - Word convertirá automáticamente el Markdown
   - Guarda como .docx

### Para PDF

1. **Usando Pandoc:**
   ```bash
   pandoc SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.md \
     -o SISTEMA_CALENDARIO_CONTENIDO_REDES_SOCIALES.pdf \
     --pdf-engine=xelatex \
     -V geometry:margin=1in \
     -V fontsize=11pt
   ```

2. **Desde HTML (Método Simple):**
   - Abre el archivo Markdown en un editor que soporte exportación a HTML
   - Exporta como HTML
   - Abre el HTML en un navegador (Chrome, Firefox, Safari)
   - Archivo → Imprimir → Guardar como PDF

3. **Usando Herramientas Online:**
   - [Markdown to PDF](https://www.markdowntopdf.com/)
   - [Dillinger](https://dillinger.io/) (exporta a PDF)

4. **Usando VS Code:**
   - Instala la extensión "Markdown PDF"
   - Abre el archivo .md
   - Clic derecho → "Markdown PDF: Export (pdf)"

## 🎨 Personalización del Formato

### Ajustar Estilos en Word

Después de generar el documento Word, puedes personalizar:

1. **Colores Corporativos:**
   - Títulos H1: `#667eea` (Azul primario)
   - Títulos H2: `#764ba2` (Púrpura secundario)

2. **Tipografía:**
   - Títulos: Calibri, 18-24pt
   - Cuerpo: Calibri, 11pt
   - Código: Courier New, 10pt

3. **Márgenes:**
   - Superior/Inferior: 2.54 cm (1 pulgada)
   - Izquierdo/Derecho: 2.54 cm (1 pulgada)

### Ajustar Estilos en PDF

Edita el script `generar_documentos_calendario.py` y modifica la sección de estilos CSS en la función `markdown_to_pdf()`.

## 📝 Notas Importantes

1. **Emojis:** Algunos conversores pueden no mostrar emojis correctamente. Considera reemplazarlos con texto si es necesario.

2. **Tablas:** Las tablas Markdown se convertirán automáticamente, pero pueden requerir ajustes manuales en Word.

3. **Imágenes:** Si agregas imágenes, asegúrate de que las rutas sean relativas o absolutas correctas.

4. **Formato de Código:** Los bloques de código se mantendrán, pero el resaltado de sintaxis puede perderse en Word.

## 🔧 Solución de Problemas

### Error: "python-docx no encontrado"
```bash
pip install python-docx
```

### Error: "weasyprint no funciona"
- Usa el método manual de conversión
- O genera solo el Word y convierte manualmente a PDF

### Error: "Pandoc no encontrado"
```bash
# macOS
brew install pandoc

# Linux
sudo apt-get install pandoc texlive-xetex

# Windows
# Descarga desde: https://pandoc.org/installing.html
```

### Las tablas no se ven bien
- Abre el documento Word
- Selecciona la tabla
- Herramientas de tabla → Diseño → Ajustar automáticamente

## 📚 Recursos Adicionales

- [Documentación de Pandoc](https://pandoc.org/MANUAL.html)
- [Guía de Markdown](https://www.markdownguide.org/)
- [Python-docx Documentation](https://python-docx.readthedocs.io/)

---

**Última actualización:** Mayo 2025




