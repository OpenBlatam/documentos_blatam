#!/bin/bash
# Script para convertir A1_ADZ.docx a PDF en macOS

echo "============================================================"
echo "CONVERTIR A1_ADZ.docx A PDF"
echo "============================================================"
echo ""

# Verificar si el archivo existe
if [ ! -f "A1_ADZ.docx" ]; then
    echo "❌ Error: No se encontró el archivo A1_ADZ.docx"
    exit 1
fi

echo "📄 Archivo encontrado: A1_ADZ.docx"
echo ""

# Método 1: Intentar con LibreOffice (si está instalado)
if command -v libreoffice &> /dev/null; then
    echo "🔄 Convirtiendo con LibreOffice..."
    libreoffice --headless --convert-to pdf A1_ADZ.docx
    if [ -f "A1_ADZ.pdf" ]; then
        echo "✅ PDF creado exitosamente: A1_ADZ.pdf"
        exit 0
    fi
fi

# Método 2: Intentar con textutil (macOS nativo)
if command -v textutil &> /dev/null; then
    echo "🔄 Intentando con textutil..."
    # textutil no convierte directamente a PDF, pero podemos intentar
    echo "⚠️  textutil no soporta conversión directa a PDF"
fi

# Método 3: Usar Python con docx2pdf
if command -v python3 &> /dev/null; then
    python3 -c "
try:
    from docx2pdf import convert
    convert('A1_ADZ.docx', 'A1_ADZ.pdf')
    print('✅ PDF creado exitosamente con docx2pdf')
except ImportError:
    print('⚠️  docx2pdf no está instalado')
    print('   Instale con: pip install docx2pdf')
except Exception as e:
    print(f'⚠️  Error: {e}')
" 2>&1
    
    if [ -f "A1_ADZ.pdf" ]; then
        echo "✅ PDF creado exitosamente: A1_ADZ.pdf"
        exit 0
    fi
fi

# Si ningún método funcionó, mostrar instrucciones
echo ""
echo "⚠️  No se pudo convertir automáticamente a PDF"
echo ""
echo "💡 INSTRUCCIONES MANUALES:"
echo ""
echo "OPCIÓN 1 - Microsoft Word (Recomendado):"
echo "   1. Abra A1_ADZ.docx en Microsoft Word"
echo "   2. Vaya a Archivo > Guardar como"
echo "   3. Seleccione formato PDF"
echo "   4. Guarde como A1_ADZ.pdf"
echo ""
echo "OPCIÓN 2 - Páginas (macOS):"
echo "   1. Abra A1_ADZ.docx en Páginas"
echo "   2. Vaya a Archivo > Exportar a > PDF"
echo "   3. Guarde como A1_ADZ.pdf"
echo ""
echo "OPCIÓN 3 - Instalar docx2pdf:"
echo "   pip install docx2pdf"
echo "   python3 -c \"from docx2pdf import convert; convert('A1_ADZ.docx', 'A1_ADZ.pdf')\""
echo ""
echo "OPCIÓN 4 - Instalar LibreOffice:"
echo "   brew install --cask libreoffice"
echo "   libreoffice --headless --convert-to pdf A1_ADZ.docx"
echo ""







