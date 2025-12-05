#!/bin/bash
# Script para verificar calidad del código

echo "🔍 Verificando calidad del código..."
echo ""

# Verificar linting (si ruff está disponible)
if command -v ruff &> /dev/null; then
    echo "📝 Verificando con ruff..."
    ruff check . --quiet || echo "⚠️  Errores de linting encontrados"
    echo ""
else
    echo "⚠️  ruff no está instalado. Instalar con: pip install ruff"
    echo ""
fi

# Verificar formato (si ruff está disponible)
if command -v ruff &> /dev/null; then
    echo "📝 Verificando formato con ruff..."
    ruff format --check . --quiet || echo "⚠️  Archivos necesitan formateo"
    echo ""
fi

# Verificar type hints (si mypy está disponible)
if command -v mypy &> /dev/null; then
    echo "📝 Verificando type hints con mypy..."
    mypy . --ignore-missing-imports --quiet || echo "⚠️  Errores de type checking encontrados"
    echo ""
else
    echo "ℹ️  mypy no está instalado. Instalar con: pip install mypy"
    echo ""
fi

echo "✅ Verificación de calidad completada"



