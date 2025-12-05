# Sistema Avanzado de Conversión de Documentos

## 📋 Descripción

Sistema completo y mejorado para convertir documentos a múltiples formatos (PDF, Word, Excel) utilizando todas las librerías disponibles en Python. El sistema detecta automáticamente qué librerías están instaladas y utiliza la mejor opción disponible.

## 🚀 Características

- ✅ **Múltiples formatos**: PDF, Word (.docx), Excel (.xlsx)
- ✅ **Detección automática**: Detecta librerías instaladas automáticamente
- ✅ **Múltiples métodos**: Intenta diferentes métodos si uno falla
- ✅ **Estilos profesionales**: Soporte para estilos simple, professional y premium
- ✅ **Conversión masiva**: Convierte múltiples formatos a la vez
- ✅ **Manejo de errores robusto**: Continúa con métodos alternativos si uno falla

## 📦 Instalación

### Instalación básica

```bash
pip install -r requirements_document_converter.txt
```

### Instalación automática desde el script

```bash
python document_converter_advanced.py --install-deps
```

## 🔧 Uso

### Desde línea de comandos

```bash
# Convertir a todos los formatos
python document_converter_advanced.py documento.md

# Convertir solo a PDF
python document_converter_advanced.py documento.md -f pdf

# Convertir a Word y Excel con estilo premium
python document_converter_advanced.py documento.md -f word excel --style premium

# Especificar directorio de salida
python document_converter_advanced.py documento.md -o mi_carpeta
```

### Desde Python

```python
from document_converter_advanced import DocumentConverterAdvanced

# Crear convertidor
converter = DocumentConverterAdvanced(output_dir="mis_documentos")

# Convertir a PDF
pdf_file = converter.convert_to_pdf("documento.md")

# Convertir a Word con estilo profesional
word_file = converter.convert_to_word("documento.md", style="professional")

# Convertir a Excel
excel_file = converter.convert_to_excel("documento.md", style="premium")

# Convertir a múltiples formatos
results = converter.convert_all_formats(
    "documento.md",
    formats=['pdf', 'word', 'excel'],
    word={'style': 'professional'},
    excel={'style': 'premium'}
)

print(results)
# {'pdf': 'mis_documentos/documento.pdf', 
#  'word': 'mis_documentos/documento.docx', 
#  'excel': 'mis_documentos/documento.xlsx'}
```

## 📚 Librerías Soportadas

### PDF

1. **reportlab** - Generación programática de PDFs
   - ✅ Instalación: `pip install reportlab`
   - ✅ Mejor para: PDFs desde cero con control total

2. **weasyprint** - HTML/CSS a PDF
   - ✅ Instalación: `pip install weasyprint`
   - ✅ Mejor para: Conversión de HTML/Markdown con estilos CSS

3. **pdfkit** - Wrapper para wkhtmltopdf
   - ✅ Instalación: `pip install pdfkit` + instalar wkhtmltopdf
   - ✅ Mejor para: Conversión HTML a PDF de alta calidad

4. **docx2pdf** - DOCX a PDF directo
   - ✅ Instalación: `pip install docx2pdf`
   - ✅ Mejor para: Conversión rápida de Word a PDF

5. **PyMuPDF (fitz)** - Manipulación avanzada
   - ✅ Instalación: `pip install PyMuPDF`
   - ✅ Mejor para: Procesamiento y manipulación de PDFs existentes

6. **xhtml2pdf** - HTML/XHTML a PDF
   - ✅ Instalación: `pip install xhtml2pdf`
   - ✅ Mejor para: Conversión HTML simple

7. **fpdf2** - Biblioteca ligera
   - ✅ Instalación: `pip install fpdf2`
   - ✅ Mejor para: PDFs simples y rápidos

8. **LibreOffice** - Herramienta del sistema
   - ✅ Instalación: Instalar LibreOffice en el sistema
   - ✅ Mejor para: Conversión universal cuando está disponible

### Word

1. **python-docx** - Creación y edición de Word
   - ✅ Instalación: `pip install python-docx`
   - ✅ Mejor para: Creación de documentos Word profesionales

2. **mammoth** - Conversión DOCX
   - ✅ Instalación: `pip install mammoth`
   - ✅ Mejor para: Conversión DOCX a HTML/Markdown

### Excel

1. **openpyxl** - Excel moderno (.xlsx)
   - ✅ Instalación: `pip install openpyxl`
   - ✅ Mejor para: Lectura/escritura de Excel con formato avanzado

2. **xlsxwriter** - Escritura avanzada
   - ✅ Instalación: `pip install xlsxwriter`
   - ✅ Mejor para: Creación de Excel con gráficas y formato complejo

3. **pandas** - Manipulación de datos
   - ✅ Instalación: `pip install pandas`
   - ✅ Mejor para: Conversión de datos estructurados a Excel

4. **xlrd/xlwt** - Excel antiguo (.xls)
   - ✅ Instalación: `pip install xlrd xlwt`
   - ✅ Mejor para: Compatibilidad con formatos antiguos

## 🎨 Estilos Disponibles

### Simple
- Formato básico sin estilos especiales
- Rápido y ligero

### Professional
- Márgenes profesionales (2.5-3 cm)
- Estilos de título personalizados
- Colores corporativos
- Formato consistente

### Premium
- Todo lo de Professional +
- Portadas personalizadas
- Tabla de contenidos automática
- Gráficas y visualizaciones
- Diseño avanzado

## 📝 Formatos de Entrada Soportados

- **Markdown** (.md) - Con soporte para tablas, código, etc.
- **HTML** (.html) - HTML estándar
- **Texto plano** (.txt) - Texto sin formato
- **Word** (.docx) - Para conversión a PDF

## 🔍 Detección Automática

El sistema detecta automáticamente qué librerías están instaladas y utiliza la mejor opción disponible. Si un método falla, intenta automáticamente con métodos alternativos.

```python
converter = DocumentConverterAdvanced()
print(converter.available_libraries)
# {'reportlab': True, 'python-docx': True, 'openpyxl': True, ...}
```

## 🛠️ Ejemplos Avanzados

### Conversión con método específico

```python
# Forzar uso de weasyprint para PDF
pdf_file = converter.convert_to_pdf(
    "documento.md",
    method="weasyprint"
)
```

### Conversión masiva de directorio

```python
from pathlib import Path

converter = DocumentConverterAdvanced()
input_dir = Path("mis_documentos")

for md_file in input_dir.glob("*.md"):
    results = converter.convert_all_formats(
        str(md_file),
        formats=['pdf', 'word', 'excel']
    )
    print(f"Convertido: {md_file.name}")
```

## ⚙️ Configuración

### Variables de entorno

```bash
# Directorio de salida por defecto
export DOCUMENT_OUTPUT_DIR="/ruta/a/salida"

# Estilo por defecto
export DOCUMENT_DEFAULT_STYLE="professional"
```

## 🐛 Solución de Problemas

### Error: "No se pudo convertir a PDF"

1. Verifica que al menos una librería de PDF esté instalada
2. Para HTML/Markdown, instala `weasyprint` o `pdfkit`
3. Para Word a PDF, instala `docx2pdf` o LibreOffice

### Error: "python-docx no está instalado"

```bash
pip install python-docx
```

### Error: "weasyprint requiere dependencias del sistema"

En macOS:
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint
```

En Linux:
```bash
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
pip install weasyprint
```

## 📊 Comparación de Librerías

| Librería | Velocidad | Calidad | Complejidad | Recomendado para |
|----------|-----------|---------|-------------|------------------|
| reportlab | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | PDFs desde cero |
| weasyprint | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | HTML/Markdown a PDF |
| pdfkit | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | HTML a PDF profesional |
| docx2pdf | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | Word a PDF rápido |
| openpyxl | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Excel moderno |
| xlsxwriter | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Excel con gráficas |

## 🤝 Contribuir

Para mejorar este sistema:

1. Agregar nuevas librerías de conversión
2. Mejorar detección automática
3. Agregar más estilos
4. Optimizar rendimiento

## 📄 Licencia

Este código es de uso libre para proyectos internos.

## 🔗 Referencias

- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [WeasyPrint Documentation](https://weasyprint.org/)

