#!/usr/bin/env python3
"""
Script para convertir calendarios Markdown a CSV para herramientas de scheduling
Soporta: Hootsuite, Buffer, Later, Sprout Social, Meta Business Suite
"""

import re
import csv
import sys
from datetime import datetime
from pathlib import Path

class CalendarConverter:
    """Convierte calendarios Markdown a diferentes formatos CSV"""
    
    def __init__(self, markdown_file):
        self.markdown_file = markdown_file
        self.posts = []
        self.parse_markdown()
    
    def parse_markdown(self):
        """Parsea el archivo Markdown y extrae la tabla del calendario"""
        try:
            with open(self.markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {self.markdown_file}")
            sys.exit(1)
        
        # Buscar tabla Markdown
        # Formato esperado: | Date | Platform | Content Type | Topic | Caption Preview | Hashtags | Posting Time | Status |
        table_pattern = r'\|(.+?)\|'
        lines = content.split('\n')
        
        in_table = False
        headers = []
        
        for line in lines:
            if '|' in line and not line.strip().startswith('---'):
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                
                if not in_table and len(cells) > 3:
                    # Primera fila es el header
                    headers = cells
                    in_table = True
                    continue
                
                if in_table and len(cells) == len(headers):
                    # Fila de datos
                    post = dict(zip(headers, cells))
                    self.posts.append(post)
        
        print(f"✅ Parseados {len(self.posts)} posts del calendario")
    
    def to_hootsuite_csv(self, output_file):
        """Convierte a formato CSV de Hootsuite"""
        fieldnames = ['Date', 'Time', 'Platform', 'Message', 'Link', 'Image URL']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for post in self.posts:
                # Extraer fecha y hora
                date_str = post.get('Date', '')
                time_str = post.get('Posting Time', '11:00')
                
                # Parsear fecha si es necesario
                if ' ' in date_str:
                    date_str = date_str.split()[0]
                
                # Normalizar plataforma
                platform = post.get('Platform', '').strip()
                platform_map = {
                    'Instagram': 'Instagram',
                    'Facebook': 'Facebook',
                    'Twitter': 'Twitter',
                    'LinkedIn': 'LinkedIn',
                    'TikTok': 'TikTok',
                    'YouTube': 'YouTube',
                    'Pinterest': 'Pinterest'
                }
                platform = platform_map.get(platform, platform)
                
                writer.writerow({
                    'Date': date_str,
                    'Time': time_str.split()[0] if ' ' in time_str else time_str,
                    'Platform': platform,
                    'Message': post.get('Caption Preview', '') + ' ' + post.get('Hashtags', ''),
                    'Link': post.get('Link', ''),
                    'Image URL': post.get('Image URL', '')
                })
        
        print(f"✅ CSV de Hootsuite creado: {output_file}")
    
    def to_buffer_csv(self, output_file, username='@username'):
        """Convierte a formato CSV de Buffer"""
        fieldnames = ['Date', 'Time', 'Platform', 'Text', 'Link', 'Image', 'Profile']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for post in self.posts:
                date_str = post.get('Date', '')
                time_str = post.get('Posting Time', '11:00')
                
                if ' ' in date_str:
                    date_str = date_str.split()[0]
                
                platform = post.get('Platform', '').lower().strip()
                platform_map = {
                    'instagram': 'instagram',
                    'facebook': 'facebook',
                    'twitter': 'twitter',
                    'linkedin': 'linkedin'
                }
                platform = platform_map.get(platform, platform)
                
                writer.writerow({
                    'Date': date_str,
                    'Time': time_str.split()[0] if ' ' in time_str else time_str,
                    'Platform': platform,
                    'Text': post.get('Caption Preview', ''),
                    'Link': post.get('Link', ''),
                    'Image': post.get('Image URL', ''),
                    'Profile': username
                })
        
        print(f"✅ CSV de Buffer creado: {output_file}")
    
    def to_later_csv(self, output_file):
        """Convierte a formato CSV de Later"""
        fieldnames = ['Date', 'Time', 'Platform', 'Caption', 'Media URL', 'Hashtags', 'First Comment']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for post in self.posts:
                date_str = post.get('Date', '')
                time_str = post.get('Posting Time', '11:00')
                
                if ' ' in date_str:
                    date_str = date_str.split()[0]
                
                # Separar hashtags del caption
                caption = post.get('Caption Preview', '')
                hashtags = post.get('Hashtags', '')
                
                # Remover hashtags del caption si están incluidos
                caption_clean = re.sub(r'#\w+\s*', '', caption).strip()
                
                writer.writerow({
                    'Date': date_str,
                    'Time': time_str.split()[0] if ' ' in time_str else time_str,
                    'Platform': post.get('Platform', ''),
                    'Caption': caption_clean,
                    'Media URL': post.get('Image URL', ''),
                    'Hashtags': hashtags,
                    'First Comment': ''
                })
        
        print(f"✅ CSV de Later creado: {output_file}")
    
    def to_google_sheets_format(self, output_file):
        """Convierte a formato compatible con Google Sheets"""
        fieldnames = ['Fecha', 'Hora', 'Plataforma', 'Tipo', 'Tema', 'Caption', 'Hashtags', 'Link', 'Imagen', 'Estado']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for post in self.posts:
                date_str = post.get('Date', '')
                time_str = post.get('Posting Time', '11:00')
                
                if ' ' in date_str:
                    date_str = date_str.split()[0]
                
                writer.writerow({
                    'Fecha': date_str,
                    'Hora': time_str.split()[0] if ' ' in time_str else time_str,
                    'Plataforma': post.get('Platform', ''),
                    'Tipo': post.get('Content Type', ''),
                    'Tema': post.get('Topic', ''),
                    'Caption': post.get('Caption Preview', ''),
                    'Hashtags': post.get('Hashtags', ''),
                    'Link': post.get('Link', ''),
                    'Imagen': post.get('Image URL', ''),
                    'Estado': post.get('Status', 'Pendiente')
                })
        
        print(f"✅ CSV para Google Sheets creado: {output_file}")


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python converter_markdown_to_csv.py <archivo_markdown> [formato] [output]")
        print("\nFormatos disponibles:")
        print("  - hootsuite (por defecto)")
        print("  - buffer")
        print("  - later")
        print("  - sheets")
        print("\nEjemplo:")
        print("  python converter_markdown_to_csv.py calendario.md hootsuite calendario_hootsuite.csv")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    format_type = sys.argv[2] if len(sys.argv) > 2 else 'hootsuite'
    output_file = sys.argv[3] if len(sys.argv) > 3 else f'calendario_{format_type}.csv'
    
    converter = CalendarConverter(markdown_file)
    
    if format_type == 'hootsuite':
        converter.to_hootsuite_csv(output_file)
    elif format_type == 'buffer':
        converter.to_buffer_csv(output_file)
    elif format_type == 'later':
        converter.to_later_csv(output_file)
    elif format_type == 'sheets':
        converter.to_google_sheets_format(output_file)
    else:
        print(f"❌ Formato no reconocido: {format_type}")
        print("Formatos disponibles: hootsuite, buffer, later, sheets")
        sys.exit(1)
    
    print(f"\n✅ Conversión completada: {output_file}")


if __name__ == '__main__':
    main()









