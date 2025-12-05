#!/bin/bash
# Script para ejecutar tests

echo "🧪 Ejecutando tests..."
echo ""

# Verificar si pytest está disponible
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest no está instalado. Instalar con: pip install pytest"
    exit 1
fi

# Ejecutar tests
if [ "$1" == "--coverage" ]; then
    echo "📊 Ejecutando tests con cobertura..."
    pytest --cov=. --cov-report=html --cov-report=term
else
    echo "📝 Ejecutando tests..."
    pytest "$@"
fi

echo ""
echo "✅ Tests completados"



