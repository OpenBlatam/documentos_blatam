#!/bin/bash
# Script para verificar que los imports estén estandarizados

echo "🔍 Verificando imports estandarizados..."
echo ""

# Verificar que no haya imports root-level (excepto shims deprecated)
echo "❌ Imports root-level no permitidos (excepto shims deprecated):"
grep -r "from (api_utils|config_manager|api_auth|api_middleware) import" --include="*.py" . | grep -v "DEPRECATED\|deprecated\|scripts/" || echo "✅ Ninguno encontrado"
echo ""

# Verificar imports correctos
echo "✅ Imports correctos encontrados:"
grep -r "from core\.config_manager\|from api\.api_utils\|from api\.middleware\|from api\.auth" --include="*.py" . | wc -l | xargs echo "Total:"
echo ""

echo "✅ Verificación completada"



