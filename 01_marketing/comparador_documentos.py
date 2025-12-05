#!/usr/bin/env python3
"""
Comparador de Documentos - Compara versiones de documentos y genera
reportes de diferencias.
"""

import os
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from difflib import unified_diff, SequenceMatcher

class ComparadorDocumentos:
    """Compara documentos y genera reportes de diferencias"""
    
    def __init__(self):
        self.directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
        self.directorio_comparaciones = os.path.join(self.directorio, 'Comparaciones')
        os.makedirs(self.directorio_comparaciones, exist_ok=True)
    
    def comparar_excel(self, archivo1, archivo2):
        """Compara dos archivos Excel"""
        print(f"\n🔍 Comparando:")
        print(f"   Archivo 1: {Path(archivo1).name}")
        print(f"   Archivo 2: {Path(archivo2).name}")
        
        try:
            excel1 = pd.ExcelFile(archivo1)
            excel2 = pd.ExcelFile(archivo2)
            
            diferencias = {
                'archivo1': archivo1,
                'archivo2': archivo2,
                'fecha_comparacion': datetime.now().isoformat(),
                'hojas': {}
            }
            
            # Comparar hojas
            hojas1 = set(excel1.sheet_names)
            hojas2 = set(excel2.sheet_names)
            
            hojas_solo_1 = hojas1 - hojas2
            hojas_solo_2 = hojas2 - hojas1
            hojas_comunes = hojas1 & hojas2
            
            diferencias['hojas_solo_archivo1'] = list(hojas_solo_1)
            diferencias['hojas_solo_archivo2'] = list(hojas_solo_2)
            diferencias['hojas_comunes'] = list(hojas_comunes)
            
            # Comparar contenido de hojas comunes
            for hoja in hojas_comunes:
                df1 = pd.read_excel(archivo1, sheet_name=hoja)
                df2 = pd.read_excel(archivo2, sheet_name=hoja)
                
                diff_hoja = {
                    'filas_archivo1': len(df1),
                    'filas_archivo2': len(df2),
                    'columnas_archivo1': list(df1.columns),
                    'columnas_archivo2': list(df2.columns),
                    'diferencias': []
                }
                
                # Comparar estructura
                if list(df1.columns) != list(df2.columns):
                    diff_hoja['diferencias'].append({
                        'tipo': 'estructura_columnas',
                        'detalle': f"Columnas diferentes: {set(df1.columns) ^ set(df2.columns)}"
                    })
                
                # Comparar filas
                if len(df1) != len(df2):
                    diff_hoja['diferencias'].append({
                        'tipo': 'cantidad_filas',
                        'detalle': f"Archivo 1: {len(df1)} filas, Archivo 2: {len(df2)} filas"
                    })
                
                # Comparar valores (si tienen misma estructura)
                if list(df1.columns) == list(df2.columns):
                    df1_sorted = df1.sort_values(by=df1.columns[0]).reset_index(drop=True)
                    df2_sorted = df2.sort_values(by=df2.columns[0]).reset_index(drop=True)
                    
                    # Comparar fila por fila
                    min_filas = min(len(df1_sorted), len(df2_sorted))
                    filas_diferentes = []
                    
                    for i in range(min_filas):
                        if not df1_sorted.iloc[i].equals(df2_sorted.iloc[i]):
                            filas_diferentes.append(i)
                    
                    if filas_diferentes:
                        diff_hoja['diferencias'].append({
                            'tipo': 'valores_diferentes',
                            'detalle': f"Filas con diferencias: {len(filas_diferentes)} de {min_filas}",
                            'filas': filas_diferentes[:10]  # Primeras 10
                        })
                
                diferencias['hojas'][hoja] = diff_hoja
            
            return diferencias
            
        except Exception as e:
            print(f"❌ Error comparando archivos: {e}")
            return None
    
    def comparar_texto(self, archivo1, archivo2):
        """Compara dos archivos de texto"""
        try:
            with open(archivo1, 'r', encoding='utf-8') as f:
                texto1 = f.readlines()
            with open(archivo2, 'r', encoding='utf-8') as f:
                texto2 = f.readlines()
            
            # Calcular similitud
            matcher = SequenceMatcher(None, texto1, texto2)
            similitud = matcher.ratio()
            
            # Generar diff
            diff = list(unified_diff(
                texto1, texto2,
                fromfile=Path(archivo1).name,
                tofile=Path(archivo2).name,
                lineterm=''
            ))
            
            return {
                'similitud': similitud,
                'porcentaje_similitud': similitud * 100,
                'lineas_diferentes': len(diff),
                'diff': diff[:100]  # Primeras 100 líneas
            }
        except Exception as e:
            print(f"❌ Error comparando texto: {e}")
            return None
    
    def generar_reporte_comparacion(self, diferencias, nombre_archivo=None):
        """Genera reporte de comparación"""
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f'COMPARACION_{timestamp}'
        
        # JSON
        archivo_json = os.path.join(
            self.directorio_comparaciones,
            f'{nombre_archivo}.json'
        )
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(diferencias, f, indent=2, ensure_ascii=False, default=str)
        
        # TXT legible
        archivo_txt = os.path.join(
            self.directorio_comparaciones,
            f'{nombre_archivo}.txt'
        )
        with open(archivo_txt, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("REPORTE DE COMPARACIÓN DE DOCUMENTOS\n")
            f.write("="*70 + "\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write(f"Archivo 1: {Path(diferencias['archivo1']).name}\n")
            f.write(f"Archivo 2: {Path(diferencias['archivo2']).name}\n\n")
            
            if 'hojas' in diferencias:
                f.write("COMPARACIÓN DE HOJAS\n")
                f.write("-"*70 + "\n")
                f.write(f"Hojas solo en Archivo 1: {len(diferencias.get('hojas_solo_archivo1', []))}\n")
                f.write(f"Hojas solo en Archivo 2: {len(diferencias.get('hojas_solo_archivo2', []))}\n")
                f.write(f"Hojas comunes: {len(diferencias.get('hojas_comunes', []))}\n\n")
                
                for hoja, diff_hoja in diferencias['hojas'].items():
                    f.write(f"\nHOJA: {hoja}\n")
                    f.write("-"*70 + "\n")
                    f.write(f"Filas Archivo 1: {diff_hoja['filas_archivo1']}\n")
                    f.write(f"Filas Archivo 2: {diff_hoja['filas_archivo2']}\n")
                    
                    if diff_hoja['diferencias']:
                        f.write("\nDiferencias encontradas:\n")
                        for diff in diff_hoja['diferencias']:
                            f.write(f"  • {diff['tipo']}: {diff['detalle']}\n")
                    else:
                        f.write("\n✓ Sin diferencias detectadas\n")
        
        print(f"\n📄 Reporte guardado:")
        print(f"   • {archivo_json}")
        print(f"   • {archivo_txt}")
        
        return archivo_json, archivo_txt

def main():
    """Función principal"""
    comparador = ComparadorDocumentos()
    
    print("🔍 COMPARADOR DE DOCUMENTOS")
    print("="*70)
    
    import sys
    if len(sys.argv) >= 3:
        archivo1 = sys.argv[1]
        archivo2 = sys.argv[2]
        
        if not os.path.exists(archivo1):
            print(f"❌ Archivo no encontrado: {archivo1}")
            return
        if not os.path.exists(archivo2):
            print(f"❌ Archivo no encontrado: {archivo2}")
            return
        
        if archivo1.endswith('.xlsx') and archivo2.endswith('.xlsx'):
            diferencias = comparador.comparar_excel(archivo1, archivo2)
            if diferencias:
                comparador.generar_reporte_comparacion(diferencias)
        elif archivo1.endswith('.txt') or archivo1.endswith('.md'):
            diferencias = comparador.comparar_texto(archivo1, archivo2)
            if diferencias:
                print(f"\n📊 Similitud: {diferencias['porcentaje_similitud']:.2f}%")
                print(f"📝 Líneas diferentes: {diferencias['lineas_diferentes']}")
        else:
            print("⚠️  Formato no soportado para comparación automática")
    else:
        print("\nUso:")
        print("  python3 comparador_documentos.py <archivo1> <archivo2>")
        print("\nEjemplo:")
        print("  python3 comparador_documentos.py archivo1.xlsx archivo2.xlsx")

if __name__ == "__main__":
    main()








