#!/usr/bin/env python3
"""
Exportador Universal de Formatos - Convierte documentos a múltiples formatos
incluyendo CSV, JSON, XML, TXT y más.
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook

class ExportadorUniversal:
    """Exporta documentos a múltiples formatos"""
    
    def __init__(self, directorio_base=None):
        if directorio_base is None:
            self.directorio_base = '/Users/adan/Documents/documentos_blatam/01_marketing'
        else:
            self.directorio_base = directorio_base
        
        self.directorio_exportaciones = os.path.join(self.directorio_base, 'Exportaciones')
        os.makedirs(self.directorio_exportaciones, exist_ok=True)
    
    def excel_a_csv(self, archivo_excel, archivo_csv=None):
        """Convierte Excel a CSV"""
        if archivo_csv is None:
            nombre_base = Path(archivo_excel).stem
            archivo_csv = os.path.join(
                self.directorio_exportaciones,
                f'{nombre_base}.csv'
            )
        
        try:
            # Leer todas las hojas
            excel_file = pd.ExcelFile(archivo_excel)
            
            if len(excel_file.sheet_names) == 1:
                # Una sola hoja - CSV simple
                df = pd.read_excel(archivo_excel)
                df.to_csv(archivo_csv, index=False, encoding='utf-8')
                print(f"✓ Excel → CSV: {archivo_csv}")
            else:
                # Múltiples hojas - CSV por hoja
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(archivo_excel, sheet_name=sheet_name)
                    nombre_hoja = sheet_name.replace('/', '_').replace('\\', '_')
                    csv_hoja = os.path.join(
                        self.directorio_exportaciones,
                        f'{Path(archivo_excel).stem}_{nombre_hoja}.csv'
                    )
                    df.to_csv(csv_hoja, index=False, encoding='utf-8')
                    print(f"✓ Excel → CSV (hoja '{sheet_name}'): {csv_hoja}")
            
            return archivo_csv
        except Exception as e:
            print(f"❌ Error convirtiendo Excel a CSV: {e}")
            return None
    
    def excel_a_json(self, archivo_excel, archivo_json=None):
        """Convierte Excel a JSON"""
        if archivo_json is None:
            nombre_base = Path(archivo_excel).stem
            archivo_json = os.path.join(
                self.directorio_exportaciones,
                f'{nombre_base}.json'
            )
        
        try:
            excel_file = pd.ExcelFile(archivo_excel)
            datos = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(archivo_excel, sheet_name=sheet_name)
                # Convertir DataFrame a diccionario
                datos[sheet_name] = df.to_dict('records')
            
            with open(archivo_json, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✓ Excel → JSON: {archivo_json}")
            return archivo_json
        except Exception as e:
            print(f"❌ Error convirtiendo Excel a JSON: {e}")
            return None
    
    def excel_a_xml(self, archivo_excel, archivo_xml=None):
        """Convierte Excel a XML"""
        if archivo_xml is None:
            nombre_base = Path(archivo_excel).stem
            archivo_xml = os.path.join(
                self.directorio_exportaciones,
                f'{nombre_base}.xml'
            )
        
        try:
            excel_file = pd.ExcelFile(archivo_excel)
            root = ET.Element('Workbook')
            root.set('name', Path(archivo_excel).stem)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(archivo_excel, sheet_name=sheet_name)
                sheet_elem = ET.SubElement(root, 'Sheet')
                sheet_elem.set('name', sheet_name)
                
                # Headers
                headers = ET.SubElement(sheet_elem, 'Headers')
                for col in df.columns:
                    header = ET.SubElement(headers, 'Header')
                    header.text = str(col)
                
                # Rows
                rows = ET.SubElement(sheet_elem, 'Rows')
                for _, row in df.iterrows():
                    row_elem = ET.SubElement(rows, 'Row')
                    for col in df.columns:
                        cell = ET.SubElement(row_elem, 'Cell')
                        cell.set('column', str(col))
                        cell.text = str(row[col]) if pd.notna(row[col]) else ''
            
            tree = ET.ElementTree(root)
            ET.indent(tree, space='  ')
            tree.write(archivo_xml, encoding='utf-8', xml_declaration=True)
            
            print(f"✓ Excel → XML: {archivo_xml}")
            return archivo_xml
        except Exception as e:
            print(f"❌ Error convirtiendo Excel a XML: {e}")
            return None
    
    def excel_a_txt(self, archivo_excel, archivo_txt=None):
        """Convierte Excel a TXT formateado"""
        if archivo_txt is None:
            nombre_base = Path(archivo_excel).stem
            archivo_txt = os.path.join(
                self.directorio_exportaciones,
                f'{nombre_base}.txt'
            )
        
        try:
            excel_file = pd.ExcelFile(archivo_excel)
            
            with open(archivo_txt, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write(f"EXPORTACIÓN DE: {Path(archivo_excel).name}\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*70 + "\n\n")
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(archivo_excel, sheet_name=sheet_name)
                    
                    f.write(f"\n{'='*70}\n")
                    f.write(f"HOJA: {sheet_name}\n")
                    f.write(f"{'='*70}\n\n")
                    
                    # Escribir como tabla
                    f.write(df.to_string(index=False))
                    f.write("\n\n")
            
            print(f"✓ Excel → TXT: {archivo_txt}")
            return archivo_txt
        except Exception as e:
            print(f"❌ Error convirtiendo Excel a TXT: {e}")
            return None
    
    def exportar_todos_formatos(self, archivo_excel):
        """Exporta un archivo Excel a todos los formatos disponibles"""
        print(f"\n📤 Exportando: {Path(archivo_excel).name}")
        print("-"*70)
        
        resultados = {
            'archivo_origen': archivo_excel,
            'fecha': datetime.now().isoformat(),
            'formatos': {}
        }
        
        # CSV
        csv_file = self.excel_a_csv(archivo_excel)
        if csv_file:
            resultados['formatos']['csv'] = csv_file
        
        # JSON
        json_file = self.excel_a_json(archivo_excel)
        if json_file:
            resultados['formatos']['json'] = json_file
        
        # XML
        xml_file = self.excel_a_xml(archivo_excel)
        if xml_file:
            resultados['formatos']['xml'] = xml_file
        
        # TXT
        txt_file = self.excel_a_txt(archivo_excel)
        if txt_file:
            resultados['formatos']['txt'] = txt_file
        
        return resultados
    
    def exportar_directorio_completo(self):
        """Exporta todos los archivos Excel del directorio"""
        archivos_excel = list(Path(self.directorio_base).glob('*.xlsx'))
        
        # Filtrar archivos de exportación
        archivos_excel = [f for f in archivos_excel 
                         if 'Exportaciones' not in str(f)]
        
        print(f"\n📤 Exportando {len(archivos_excel)} archivos Excel...")
        print("="*70)
        
        todos_resultados = []
        
        for archivo in archivos_excel:
            try:
                resultado = self.exportar_todos_formatos(str(archivo))
                todos_resultados.append(resultado)
            except Exception as e:
                print(f"❌ Error procesando {archivo.name}: {e}")
        
        # Guardar resumen
        resumen_file = os.path.join(
            self.directorio_exportaciones,
            f'RESUMEN_EXPORTACION_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        with open(resumen_file, 'w', encoding='utf-8') as f:
            json.dump({
                'fecha': datetime.now().isoformat(),
                'total_archivos': len(todos_resultados),
                'resultados': todos_resultados
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Exportación completada!")
        print(f"📁 Archivos guardados en: {self.directorio_exportaciones}")
        print(f"📄 Resumen: {resumen_file}")
        
        return todos_resultados

def main():
    """Función principal"""
    exportador = ExportadorUniversal()
    
    print("🌐 EXPORTADOR UNIVERSAL DE FORMATOS")
    print("="*70)
    print("\nOpciones:")
    print("1. Exportar todos los archivos Excel del directorio")
    print("2. Exportar un archivo específico")
    
    import sys
    if len(sys.argv) > 1:
        archivo_especifico = sys.argv[1]
        if os.path.exists(archivo_especifico):
            exportador.exportar_todos_formatos(archivo_especifico)
        else:
            print(f"❌ Archivo no encontrado: {archivo_especifico}")
    else:
        exportador.exportar_directorio_completo()

if __name__ == "__main__":
    main()








