#!/usr/bin/env python3
"""
Sistema de Backup Automático - Crea backups automáticos de documentos
y permite restauración.
"""

import os
import shutil
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

class SistemaBackup:
    """Sistema de backup automático"""
    
    def __init__(self, directorio_base=None):
        if directorio_base is None:
            self.directorio_base = '/Users/adan/Documents/documentos_blatam/01_marketing'
        else:
            self.directorio_base = directorio_base
        
        self.directorio_backups = os.path.join(self.directorio_base, 'Backups')
        os.makedirs(self.directorio_backups, exist_ok=True)
        
        self.archivo_metadatos = os.path.join(self.directorio_backups, 'metadatos_backups.json')
        self.metadatos = self.cargar_metadatos()
    
    def cargar_metadatos(self):
        """Carga metadatos de backups"""
        if os.path.exists(self.archivo_metadatos):
            with open(self.archivo_metadatos, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'backups': []}
    
    def guardar_metadatos(self):
        """Guarda metadatos"""
        with open(self.archivo_metadatos, 'w', encoding='utf-8') as f:
            json.dump(self.metadatos, f, indent=2, ensure_ascii=False)
    
    def calcular_hash_archivo(self, archivo):
        """Calcula hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(archivo, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️  Error calculando hash de {archivo}: {e}")
            return None
    
    def crear_backup_completo(self, nombre_backup=None):
        """Crea backup completo del directorio"""
        if nombre_backup is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f"BACKUP_COMPLETO_{timestamp}"
        
        archivo_backup = os.path.join(self.directorio_backups, f"{nombre_backup}.zip")
        
        print(f"📦 Creando backup: {nombre_backup}")
        print("-"*70)
        
        # Archivos a incluir
        extensiones_incluir = ['.py', '.md', '.docx', '.xlsx', '.pptx', '.pdf', 
                               '.html', '.png', '.json', '.txt', '.xml', '.csv']
        
        archivos_incluidos = []
        tamaño_total = 0
        
        with zipfile.ZipFile(archivo_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Incluir scripts Python
            for archivo in Path(self.directorio_base).glob('*.py'):
                if 'Backups' not in str(archivo) and 'Exportaciones' not in str(archivo):
                    zipf.write(archivo, archivo.name)
                    archivos_incluidos.append(archivo.name)
                    tamaño_total += archivo.stat().st_size
            
            # Incluir documentos Markdown importantes
            for archivo in Path(self.directorio_base).glob('*.md'):
                if 'SISTEMAS_PROMPTS' in archivo.name or 'README' in archivo.name or 'RESUMEN' in archivo.name:
                    zipf.write(archivo, archivo.name)
                    archivos_incluidos.append(archivo.name)
                    tamaño_total += archivo.stat().st_size
            
            # Incluir documentos generados recientes (últimos 30 días)
            fecha_limite = datetime.now() - timedelta(days=30)
            for ext in ['.docx', '.xlsx', '.pptx', '.pdf', '.html']:
                for archivo in Path(self.directorio_base).glob(f'*{ext}'):
                    if 'Backups' not in str(archivo):
                        fecha_mod = datetime.fromtimestamp(archivo.stat().st_mtime)
                        if fecha_mod > fecha_limite:
                            zipf.write(archivo, archivo.name)
                            archivos_incluidos.append(archivo.name)
                            tamaño_total += archivo.stat().st_size
            
            # Crear archivo de índice
            indice = {
                'fecha_creacion': datetime.now().isoformat(),
                'nombre_backup': nombre_backup,
                'total_archivos': len(archivos_incluidos),
                'tamaño_total_bytes': tamaño_total,
                'tamaño_total_mb': tamaño_total / 1024 / 1024,
                'archivos': archivos_incluidos
            }
            
            zipf.writestr('INDICE_BACKUP.json', json.dumps(indice, indent=2, ensure_ascii=False))
        
        # Calcular hash del backup
        hash_backup = self.calcular_hash_archivo(archivo_backup)
        
        # Guardar metadatos
        tamaño_backup = os.path.getsize(archivo_backup)
        self.metadatos['backups'].append({
            'nombre': nombre_backup,
            'archivo': archivo_backup,
            'fecha': datetime.now().isoformat(),
            'tamaño_mb': tamaño_backup / 1024 / 1024,
            'hash': hash_backup,
            'archivos_incluidos': len(archivos_incluidos),
            'tipo': 'completo'
        })
        self.guardar_metadatos()
        
        print(f"✅ Backup creado: {archivo_backup}")
        print(f"   Tamaño: {tamaño_backup / 1024 / 1024:.2f} MB")
        print(f"   Archivos: {len(archivos_incluidos)}")
        print(f"   Hash: {hash_backup}")
        
        return archivo_backup
    
    def crear_backup_incremental(self):
        """Crea backup incremental (solo cambios)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = f"BACKUP_INCREMENTAL_{timestamp}"
        
        # Obtener último backup
        if not self.metadatos['backups']:
            print("⚠️  No hay backups previos, creando backup completo...")
            return self.crear_backup_completo(nombre_backup.replace('INCREMENTAL', 'COMPLETO'))
        
        ultimo_backup = max(self.metadatos['backups'], key=lambda x: x['fecha'])
        print(f"📦 Creando backup incremental basado en: {ultimo_backup['nombre']}")
        
        # Por simplicidad, crear backup completo pero marcado como incremental
        return self.crear_backup_completo(nombre_backup)
    
    def listar_backups(self):
        """Lista todos los backups disponibles"""
        print("\n📋 BACKUPS DISPONIBLES")
        print("="*70)
        
        if not self.metadatos['backups']:
            print("No hay backups disponibles")
            return
        
        for i, backup in enumerate(sorted(self.metadatos['backups'], 
                                          key=lambda x: x['fecha'], reverse=True), 1):
            fecha = datetime.fromisoformat(backup['fecha']).strftime('%d/%m/%Y %H:%M:%S')
            print(f"\n{i}. {backup['nombre']}")
            print(f"   Fecha: {fecha}")
            print(f"   Tamaño: {backup['tamaño_mb']:.2f} MB")
            print(f"   Archivos: {backup['archivos_incluidos']}")
            print(f"   Archivo: {backup['archivo']}")
    
    def restaurar_backup(self, nombre_backup, directorio_destino=None):
        """Restaura un backup"""
        backup_info = None
        for backup in self.metadatos['backups']:
            if backup['nombre'] == nombre_backup:
                backup_info = backup
                break
        
        if not backup_info:
            print(f"❌ Backup no encontrado: {nombre_backup}")
            return False
        
        if not os.path.exists(backup_info['archivo']):
            print(f"❌ Archivo de backup no encontrado: {backup_info['archivo']}")
            return False
        
        if directorio_destino is None:
            directorio_destino = os.path.join(self.directorio_base, 'Restauracion')
        os.makedirs(directorio_destino, exist_ok=True)
        
        print(f"🔄 Restaurando backup: {nombre_backup}")
        print(f"   Destino: {directorio_destino}")
        
        try:
            with zipfile.ZipFile(backup_info['archivo'], 'r') as zipf:
                zipf.extractall(directorio_destino)
            
            print(f"✅ Backup restaurado exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error restaurando backup: {e}")
            return False
    
    def limpiar_backups_antiguos(self, dias=30):
        """Elimina backups más antiguos que X días"""
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        backups_a_eliminar = []
        for backup in self.metadatos['backups']:
            fecha_backup = datetime.fromisoformat(backup['fecha'])
            if fecha_backup < fecha_limite:
                backups_a_eliminar.append(backup)
        
        if not backups_a_eliminar:
            print(f"✅ No hay backups antiguos (más de {dias} días)")
            return
        
        print(f"🗑️  Eliminando {len(backups_a_eliminar)} backups antiguos...")
        
        for backup in backups_a_eliminar:
            try:
                if os.path.exists(backup['archivo']):
                    os.remove(backup['archivo'])
                self.metadatos['backups'].remove(backup)
                print(f"   ✓ Eliminado: {backup['nombre']}")
            except Exception as e:
                print(f"   ❌ Error eliminando {backup['nombre']}: {e}")
        
        self.guardar_metadatos()
        print(f"✅ Limpieza completada")

def main():
    """Función principal"""
    sistema = SistemaBackup()
    
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Backup Automático')
    parser.add_argument('--crear', action='store_true', help='Crear backup completo')
    parser.add_argument('--incremental', action='store_true', help='Crear backup incremental')
    parser.add_argument('--listar', action='store_true', help='Listar backups')
    parser.add_argument('--restaurar', type=str, help='Restaurar backup (nombre)')
    parser.add_argument('--limpiar', type=int, metavar='DIAS', help='Limpiar backups más antiguos que X días')
    
    args = parser.parse_args()
    
    if args.crear:
        sistema.crear_backup_completo()
    elif args.incremental:
        sistema.crear_backup_incremental()
    elif args.listar:
        sistema.listar_backups()
    elif args.restaurar:
        sistema.restaurar_backup(args.restaurar)
    elif args.limpiar:
        sistema.limpiar_backups_antiguos(args.limpiar)
    else:
        print("Sistema de Backup Automático")
        print("="*70)
        print("\nOpciones:")
        print("  --crear          Crear backup completo")
        print("  --incremental    Crear backup incremental")
        print("  --listar         Listar backups disponibles")
        print("  --restaurar NOMBRE  Restaurar backup")
        print("  --limpiar DIAS   Limpiar backups antiguos")
        print("\nEjemplo:")
        print("  python3 sistema_backup_automatico.py --crear")
        print("  python3 sistema_backup_automatico.py --listar")
        print("  python3 sistema_backup_automatico.py --restaurar BACKUP_COMPLETO_20251122_120000")

if __name__ == "__main__":
    main()



