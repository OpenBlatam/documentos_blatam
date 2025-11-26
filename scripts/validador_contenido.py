#!/usr/bin/env python3
"""
Validador de Contenido - OpenBlatam

Script para validar que el contenido cumple con los estándares de calidad
y las guías de estilo establecidas.
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class ValidadorContenido:
    def __init__(self):
        self.errores = []
        self.advertencias = []
        
        # Reglas de validación
        self.reglas = {
            'longitud_parrafo': 5,  # líneas máximas por párrafo
            'longitud_titulo': 80,   # caracteres máximos en título
            'encabezados_minimos': 2, # mínimo de encabezados H2
        }
        
        # Patrones regex
        self.patrones = {
            'encabezado_h2': r'^##\s+.+$',
            'encabezado_h1': r'^#\s+.+$',
            'lista_una_linea': r'^-\s+[^\n]+\n(?!\s*-)',
            'enlace_generico': r'\[click aquí\]',
        }
    
    def validar_archivo(self, ruta_archivo: str) -> Dict:
        """Valida un archivo Markdown individual"""
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            self.errores = []
            self.advertencias = []
            
            # Ejecutar validaciones
            self._validar_estructura(contenido)
            self._validar_formato(contenido)
            self._validar_contenido(contenido)
            
            return {
                'valido': len(self.errores) == 0,
                'errores': self.errores,
                'advertencias': self.advertencias,
                'archivo': ruta_archivo
            }
            
        except Exception as e:
            return {
                'valido': False,
                'errores': [f'Error al leer archivo: {str(e)}'],
                'advertencias': [],
                'archivo': ruta_archivo
            }
    
    def _validar_estructura(self, contenido: str):
        """Valida la estructura del documento"""
        lineas = contenido.split('\n')
        
        # Verificar que no empiece con encabezado
        if lineas and lineas[0].startswith('#'):
            self.errores.append("El documento no debe comenzar con un encabezado")
        
        # Contar encabezados H2
        encabezados_h2 = [l for l in lineas if re.match(self.patrones['encabezado_h2'], l)]
        if len(encabezados_h2) < self.reglas['encabezados_minimos']:
            self.advertencias.append(f"Documento tiene pocos encabezados H2 ({len(encabezados_h2)})")
        
        # Verificar longitud de párrafos
        parrafo_actual = []
        for linea in lineas:
            if linea.strip() == '':
                if len(parrafo_actual) > self.reglas['longitud_parrafo']:
                    self.advertencias.append(f"Párrafo demasiado largo ({len(parrafo_actual)} líneas)")
                parrafo_actual = []
            elif not linea.startswith('#') and not linea.startswith('-') and not linea.startswith('|'):
                parrafo_actual.append(linea)
    
    def _validar_formato(self, contenido: str):
        """Valida el formato y estilo"""
        
        # Verificar enlaces genéricos
        if re.search(self.patrones['enlace_generico'], contenido, re.IGNORECASE):
            self.errores.append("Evitar enlaces genéricos como 'click aquí'")
        
        # Verificar listas con un solo elemento
        if re.search(self.patrones['lista_una_linea'], contenido, re.MULTILINE):
            self.advertencias.append("Lista con un solo elemento detectada")
        
        # Verificar código sin lenguaje especificado
        bloques_codigo = re.findall(r'(\w+)?', contenido)
        for bloque in bloques_codigo:
            if not bloque:
                self.advertencias.append("Bloque de código sin lenguaje especificado")
    
    def _validar_contenido(self, contenido: str):
        """Validaciones de contenido semántico"""
        
        # Verificar que tenga introducción
        primeras_lineas = '\n'.join(contenido.split('\n')[:5])
        if not any(palabra in primeras_lineas.lower() for palabra in ['valor', 'beneficio', 'propósito', 'objetivo']):
            self.advertencias.append("La introducción podría enfatizar más el valor para el lector")
        
        # Verificar conclusión
        ultimas_lineas = '\n'.join(contenido.split('\n')[-5:])
        if not any(palabra in ultimas_lineas.lower() for palabra in ['conclusión', 'resumen', 'siguiente paso']):
            self.advertencias.append("Falta una conclusión clara o llamado a la acción")

def main():
    """Función principal del validador"""
    if len(sys.argv) != 2:
        print("Uso: python validador_contenido.py <ruta_archivo_o_directorio>")
        sys.exit(1)
    
    ruta = sys.argv[1]
    validador = ValidadorContenido()
    
    if os.path.isfile(ruta):
        # Validar archivo individual
        resultado = validador.validar_archivo(ruta)
        mostrar_resultado(resultado)
    elif os.path.isdir(ruta):
        # Validar todos los archivos Markdown en el directorio
        archivos_md = list(Path(ruta).glob('**/*.md'))
        for archivo in archivos_md:
            resultado = validador.validar_archivo(str(archivo))
            mostrar_resultado(resultado)
    else:
        print(f"Ruta no válida: {ruta}")
        sys.exit(1)

def mostrar_resultado(resultado: Dict):
    """Muestra los resultados de la validación"""
    print(f"\n{'='*50}")
    print(f"Archivo: {resultado['archivo']}")
    print(f"Válido: {'✓' if resultado['valido'] else '✗'}")
    
    if resultado['errores']:
        print("\n❌ Errores:")
        for error in resultado['errores']:
            print(f"  - {error}")
    
    if resultado['advertencias']:
        print("\n⚠️  Advertencias:")
        for advertencia in resultado['advertencias']:
            print(f"  - {advertencia}")
    
    if not resultado['errores'] and not resultado['advertencias']:
        print("\n✅ El documento cumple con todos los estándares de calidad")

if __name__ == "__main__":
    main()