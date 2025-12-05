#!/bin/bash
# Script de instalación rápida para el Sistema de Conversión de Documentos
# ===========================================================================

echo "=========================================="
echo "Instalación del Sistema de Conversión"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 encontrado${NC}"
echo ""

# Instalar librerías básicas
echo "📦 Instalando librerías básicas..."
pip3 install python-docx openpyxl pandas markdown Pillow

# Instalar librerías PDF (opcionales pero recomendadas)
echo ""
echo "📄 Instalando librerías PDF..."
pip3 install reportlab weasyprint pypdf PyMuPDF

# Instalar librerías adicionales
echo ""
echo "🛠️  Instalando librerías adicionales..."
pip3 install beautifulsoup4 matplotlib seaborn

# Verificar instalación
echo ""
echo "=========================================="
echo "Verificando instalación..."
echo "=========================================="
python3 -c "
from document_converter_advanced import DocumentConverterAdvanced
converter = DocumentConverterAdvanced()
print('\n📚 Librerías detectadas:')
print('PDF:', sum(1 for k in ['reportlab', 'weasyprint', 'pypdf', 'PyMuPDF'] if converter.available_libraries.get(k)))
print('Word:', sum(1 for k in ['python-docx'] if converter.available_libraries.get(k)))
print('Excel:', sum(1 for k in ['openpyxl', 'pandas'] if converter.available_libraries.get(k)))
print('\n✅ Sistema listo para usar!')
"

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Instalación completada"
echo "==========================================${NC}"
echo ""
echo "💡 Próximos pasos:"
echo "   1. Ejecuta: python3 ejemplo_uso_converter.py"
echo "   2. Lee: README_DOCUMENT_CONVERTER.md"
echo ""

