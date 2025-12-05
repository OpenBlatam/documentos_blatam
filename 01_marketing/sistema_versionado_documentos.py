#!/usr/bin/env python3
"""
Sistema de Versionado de Documentos - Gestiona versiones de documentos
y permite comparar y restaurar versiones anteriores.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import hashlib

class SistemaVersionado:
    """Sistema de versionado de documentos"""
    
    def __init__(self, directorio_base=None):
        if directorio_base is None:
            self.directorio_base = '/Users/adan/Documents/documentos_blatam/01_marketing'
        else:
            self.directorio_base = directorio_base
        
        self.directorio_versiones = os.path.join(self.directorio_base, 'Versiones')
        os.makedirs(self.directorio_versiones, exist_ok=True)
        
        self.archivo_metadatos = os.path.join(self.directorio_versiones, 'metadatos_versiones.json')
        self.metadatos = self.cargar_metadatos()
    
    def cargar_metadatos(self):
        """Carga metadatos de versiones"""
        if os.path.exists(self.archivo_metadatos):
            with open(self.archivo_metadatos, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'versiones': {}}
    
    def guardar_metadatos(self):
        """Guarda metadatos"""
        with open(self.archivo_metadatos, 'w', encoding='utf-8') as f:
            json.dump(self.metadatos, f, indent=2, ensure_ascii=False)
    
    def calcular_hash(self, archivo):
        """Calcula hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(archivo, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️  Error calculando hash: {e}")
            return None
    
    def crear_version(self, archivo_origen, comentario=None, etiqueta=None):
        """Crea una nueva versión de un documento"""
        if not os.path.exists(archivo_origen):
            print(f"❌ Archivo no encontrado: {archivo_origen}")
            return None
        
        nombre_archivo = Path(archivo_origen).name
        nombre_base = Path(archivo_origen).stem
        extension = Path(archivo_origen).suffix
        
        # Calcular hash
        hash_archivo = self.calcular_hash(archivo_origen)
        
        # Verificar si ya existe esta versión
        if nombre_archivo in self.metadatos['versiones']:
            for version in self.metadatos['versiones'][nombre_archivo]:
                if version['hash'] == hash_archivo:
                    print(f"ℹ️  Esta versión ya existe: {version['version']}")
                    return version['version']
        
        # Crear número de versión
        if nombre_archivo not in self.metadatos['versiones']:
            self.metadatos['versiones'][nombre_archivo] = []
        
        version_numero = len(self.metadatos['versiones'][nombre_archivo]) + 1
        
        # Crear directorio de versión
        directorio_version = os.path.join(
            self.directorio_versiones,
            nombre_base,
            f"v{version_numero}"
        )
        os.makedirs(directorio_version, exist_ok=True)
        
        # Copiar archivo
        archivo_version = os.path.join(
            directorio_version,
            f"{nombre_base}_v{version_numero}{extension}"
        )
        shutil.copy2(archivo_origen, archivo_version)
        
        # Guardar metadatos
        version_info = {
            'version': version_numero,
            'fecha': datetime.now().isoformat(),
            'archivo_original': archivo_origen,
            'archivo_version': archivo_version,
            'hash': hash_archivo,
            'tamaño_bytes': os.path.getsize(archivo_origen),
            'comentario': comentario or '',
            'etiqueta': etiqueta or '',
            'autor': os.getenv('USER', 'sistema')
        }
        
        self.metadatos['versiones'][nombre_archivo].append(version_info)
        self.guardar_metadatos()
        
        print(f"✅ Versión {version_numero} creada: {archivo_version}")
        return version_numero
    
    def listar_versiones(self, nombre_archivo):
        """Lista todas las versiones de un archivo"""
        if nombre_archivo not in self.metadatos['versiones']:
            print(f"ℹ️  No hay versiones para: {nombre_archivo}")
            return []
        
        print(f"\n📋 Versiones de: {nombre_archivo}")
        print("="*70)
        
        versiones = self.metadatos['versiones'][nombre_archivo]
        for version in sorted(versiones, key=lambda x: x['version'], reverse=True):
            fecha = datetime.fromisoformat(version['fecha']).strftime('%d/%m/%Y %H:%M:%S')
            print(f"\nVersión {version['version']}")
            print(f"  Fecha: {fecha}")
            print(f"  Tamaño: {version['tamaño_bytes'] / 1024:.1f} KB")
            print(f"  Hash: {version['hash'][:16]}...")
            if version['comentario']:
                print(f"  Comentario: {version['comentario']}")
            if version['etiqueta']:
                print(f"  Etiqueta: {version['etiqueta']}")
            print(f"  Archivo: {version['archivo_version']}")
        
        return versiones
    
    def restaurar_version(self, nombre_archivo, numero_version, directorio_destino=None):
        """Restaura una versión específica"""
        if nombre_archivo not in self.metadatos['versiones']:
            print(f"❌ No hay versiones para: {nombre_archivo}")
            return False
        
        version_info = None
        for version in self.metadatos['versiones'][nombre_archivo]:
            if version['version'] == numero_version:
                version_info = version
                break
        
        if not version_info:
            print(f"❌ Versión {numero_version} no encontrada")
            return False
        
        if not os.path.exists(version_info['archivo_version']):
            print(f"❌ Archivo de versión no encontrado: {version_info['archivo_version']}")
            return False
        
        if directorio_destino is None:
            directorio_destino = self.directorio_base
        
        archivo_destino = os.path.join(
            directorio_destino,
            f"{Path(nombre_archivo).stem}_restaurado_v{numero_version}{Path(nombre_archivo).suffix}"
        )
        
        shutil.copy2(version_info['archivo_version'], archivo_destino)
        
        print(f"✅ Versión {numero_version} restaurada: {archivo_destino}")
        return archivo_destino
    
    def comparar_versiones(self, nombre_archivo, version1, version2):
        """Compara dos versiones"""
        if nombre_archivo not in self.metadatos['versiones']:
            print(f"❌ No hay versiones para: {nombre_archivo}")
            return None
        
        v1_info = None
        v2_info = None
        
        for version in self.metadatos['versiones'][nombre_archivo]:
            if version['version'] == version1:
                v1_info = version
            if version['version'] == version2:
                v2_info = version
        
        if not v1_info or not v2_info:
            print(f"❌ Una o ambas versiones no encontradas")
            return None
        
        comparacion = {
            'archivo': nombre_archivo,
            'version1': version1,
            'version2': version2,
            'fecha1': v1_info['fecha'],
            'fecha2': v2_info['fecha'],
            'tamaño1': v1_info['tamaño_bytes'],
            'tamaño2': v2_info['tamaño_bytes'],
            'diferencia_tamaño': v2_info['tamaño_bytes'] - v1_info['tamaño_bytes'],
            'hash1': v1_info['hash'],
            'hash2': v2_info['hash'],
            'son_iguales': v1_info['hash'] == v2_info['hash']
        }
        
        print(f"\n🔍 Comparación de versiones:")
        print(f"   Versión {version1} vs Versión {version2}")
        print(f"   Son iguales: {'✅ Sí' if comparacion['son_iguales'] else '❌ No'}")
        print(f"   Diferencia de tamaño: {comparacion['diferencia_tamaño'] / 1024:.1f} KB")
        
        return comparacion
    
    def listar_todos_archivos_versionados(self):
        """Lista todos los archivos con versiones"""
        print("\n📚 ARCHIVOS VERSIONADOS")
        print("="*70)
        
        if not self.metadatos['versiones']:
            print("No hay archivos versionados")
            return
        
        for nombre_archivo, versiones in self.metadatos['versiones'].items():
            print(f"\n📄 {nombre_archivo}")
            print(f"   Versiones: {len(versiones)}")
            print(f"   Última versión: {max(v['version'] for v in versiones)}")

def main():
    """Función principal"""
    sistema = SistemaVersionado()
    
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Versionado de Documentos')
    parser.add_argument('--crear', type=str, metavar='ARCHIVO', help='Crear versión de archivo')
    parser.add_argument('--comentario', type=str, help='Comentario para la versión')
    parser.add_argument('--etiqueta', type=str, help='Etiqueta para la versión')
    parser.add_argument('--listar', type=str, metavar='ARCHIVO', help='Listar versiones de archivo')
    parser.add_argument('--restaurar', type=str, nargs=2, metavar=('ARCHIVO', 'VERSION'),
                       help='Restaurar versión específica')
    parser.add_argument('--comparar', type=str, nargs=3, metavar=('ARCHIVO', 'V1', 'V2'),
                       help='Comparar dos versiones')
    parser.add_argument('--listar-todos', action='store_true', help='Listar todos los archivos versionados')
    
    args = parser.parse_args()
    
    if args.crear:
        sistema.crear_version(args.crear, args.comentario, args.etiqueta)
    elif args.listar:
        sistema.listar_versiones(args.listar)
    elif args.restaurar:
        sistema.restaurar_version(args.restaurar[0], int(args.restaurar[1]))
    elif args.comparar:
        sistema.comparar_versiones(args.comparar[0], int(args.comparar[1]), int(args.comparar[2]))
    elif args.listar_todos:
        sistema.listar_todos_archivos_versionados()
    else:
        print("Sistema de Versionado de Documentos")
        print("="*70)
        print("\nOpciones:")
        print("  --crear ARCHIVO [--comentario TEXTO] [--etiqueta TEXTO]")
        print("  --listar ARCHIVO")
        print("  --restaurar ARCHIVO VERSION")
        print("  --comparar ARCHIVO V1 V2")
        print("  --listar-todos")
        print("\nEjemplo:")
        print("  python3 sistema_versionado_documentos.py --crear reporte.xlsx --comentario 'Versión inicial'")
        print("  python3 sistema_versionado_documentos.py --listar reporte.xlsx")

if __name__ == "__main__":
    main()








