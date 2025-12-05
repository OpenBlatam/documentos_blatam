#!/bin/bash
# Script para solucionar el error NSFileProviderInternalErrorDomain 12

echo "============================================================"
echo "SOLUCIONAR ERROR NSFileProviderInternalErrorDomain 12"
echo "============================================================"
echo ""

# 1. Limpiar atributos extendidos
echo "1. Limpiando atributos extendidos..."
xattr -c A1_ADZ.docx 2>/dev/null
echo "   ✓ Atributos extendidos eliminados"
echo ""

# 2. Verificar permisos
echo "2. Verificando permisos..."
chmod 644 A1_ADZ.docx
echo "   ✓ Permisos actualizados"
echo ""

# 3. Crear copia sin atributos extendidos
echo "3. Creando copia limpia..."
cp A1_ADZ.docx A1_ADZ_limpio.docx
xattr -c A1_ADZ_limpio.docx 2>/dev/null
chmod 644 A1_ADZ_limpio.docx
echo "   ✓ Copia limpia creada: A1_ADZ_limpio.docx"
echo ""

# 4. Verificar que el archivo no esté en uso
echo "4. Verificando procesos que usan el archivo..."
if lsof A1_ADZ.docx 2>/dev/null | grep -q .; then
    echo "   ⚠️  El archivo está siendo usado por otro proceso"
    lsof A1_ADZ.docx
else
    echo "   ✓ Archivo no está en uso"
fi
echo ""

echo "============================================================"
echo "SOLUCIONES ADICIONALES:"
echo "============================================================"
echo ""
echo "Si el error persiste, intenta:"
echo ""
echo "1. Cerrar todas las aplicaciones que puedan estar usando el archivo"
echo "   (Word, Pages, Preview, Finder, etc.)"
echo ""
echo "2. Reiniciar Finder:"
echo "   killall Finder"
echo ""
echo "3. Si el archivo está en iCloud, descargarlo localmente:"
echo "   - Click derecho en el archivo > Descargar ahora"
echo ""
echo "4. Abrir el archivo desde Terminal:"
echo "   open A1_ADZ.docx"
echo ""
echo "5. Usar la copia limpia:"
echo "   open A1_ADZ_limpio.docx"
echo ""
echo "6. Si nada funciona, regenerar el documento:"
echo "   python3 generar_documento_word_pdf.py"
echo ""
echo "============================================================"







