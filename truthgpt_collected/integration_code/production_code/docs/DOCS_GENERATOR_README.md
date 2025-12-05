# 📚 Generador de Documentación Automática

## ✨ Características

- ✅ **Extracción automática**: Información de módulos, clases y funciones
- ✅ **Documentación Markdown**: Genera docs en formato Markdown
- ✅ **API Documentation**: Documentación completa de API
- ✅ **Índice automático**: Genera índice de todos los módulos

## 🎯 Uso

### Generar Documentación

```python
from docs_generator import generate_documentation

generate_documentation("docs")
```

### Generar Documentación Personalizada

```python
from docs_generator import DocumentationGenerator

generator = DocumentationGenerator("my_docs")

# Documentar módulos específicos
import memory
import redundancy

modules = {
    'memory': memory,
    'redundancy': redundancy
}

generator.generate_all_docs(modules)
```

### CLI

```bash
# Generar documentación
python cli_unified.py docs

# Especificar directorio de salida
python cli_unified.py docs --output my_docs
```

## 📄 Archivos Generados

- `{module}.md` - Documentación por módulo
- `API.md` - Documentación completa de API
- `INDEX.md` - Índice de documentación

## 🎉 Resultado

Sistema completo de documentación con:
- ✅ Extracción automática
- ✅ Formato Markdown
- ✅ API documentation
- ✅ Índice automático

