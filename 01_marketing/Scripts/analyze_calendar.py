#!/usr/bin/env python3
"""
Script para analizar calendarios de contenido generados
Proporciona insights sobre distribución, balance, y optimización
"""

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

class CalendarAnalyzer:
    """Analiza calendarios de contenido y proporciona insights"""
    
    def __init__(self, markdown_file):
        self.markdown_file = markdown_file
        self.posts = []
        self.parse_markdown()
    
    def parse_markdown(self):
        """Parsea el archivo Markdown y extrae información del calendario"""
        try:
            with open(self.markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {self.markdown_file}")
            sys.exit(1)
        
        # Buscar tabla del calendario
        lines = content.split('\n')
        in_table = False
        headers = []
        
        for line in lines:
            if '|' in line and not line.strip().startswith('---'):
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                
                if not in_table and len(cells) > 3:
                    headers = cells
                    in_table = True
                    continue
                
                if in_table and len(cells) == len(headers):
                    post = dict(zip(headers, cells))
                    self.posts.append(post)
        
        print(f"✅ Parseados {len(self.posts)} posts del calendario\n")
    
    def analyze_distribution(self):
        """Analiza la distribución de contenido"""
        print("=" * 60)
        print("📊 ANÁLISIS DE DISTRIBUCIÓN")
        print("=" * 60)
        
        # Por plataforma
        platforms = Counter([post.get('Platform', 'N/A') for post in self.posts])
        print("\n📱 Distribución por Plataforma:")
        for platform, count in platforms.most_common():
            percentage = (count / len(self.posts)) * 100
            print(f"  {platform}: {count} posts ({percentage:.1f}%)")
        
        # Por tipo de contenido
        content_types = Counter([post.get('Content Type', 'N/A') for post in self.posts])
        print("\n📝 Distribución por Tipo de Contenido:")
        for ctype, count in content_types.most_common():
            percentage = (count / len(self.posts)) * 100
            print(f"  {ctype}: {count} posts ({percentage:.1f}%)")
        
        # Por tema
        topics = Counter([post.get('Topic', 'N/A') for post in self.posts])
        print("\n🎯 Top 5 Temas:")
        for topic, count in topics.most_common(5):
            percentage = (count / len(self.posts)) * 100
            print(f"  {topic}: {count} posts ({percentage:.1f}%)")
    
    def analyze_frequency(self):
        """Analiza la frecuencia de posting"""
        print("\n" + "=" * 60)
        print("⏰ ANÁLISIS DE FRECUENCIA")
        print("=" * 60)
        
        # Posts por día de la semana
        days = []
        for post in self.posts:
            date_str = post.get('Date', '')
            if date_str:
                try:
                    # Intentar parsear fecha
                    if ' ' in date_str:
                        date_str = date_str.split()[0]
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    days.append(date_obj.strftime('%A'))
                except:
                    pass
        
        if days:
            day_dist = Counter(days)
            print("\n📅 Distribución por Día de la Semana:")
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in day_order:
                if day in day_dist:
                    count = day_dist[day]
                    percentage = (count / len(days)) * 100
                    print(f"  {day}: {count} posts ({percentage:.1f}%)")
        
        # Frecuencia promedio
        if len(self.posts) > 0:
            print(f"\n📈 Frecuencia Promedio:")
            print(f"  Total posts: {len(self.posts)}")
            if days:
                unique_days = len(set(days))
                print(f"  Días con contenido: {unique_days}")
                print(f"  Posts por día: {len(self.posts) / unique_days:.1f}")
    
    def analyze_balance(self):
        """Analiza el balance de contenido"""
        print("\n" + "=" * 60)
        print("⚖️ ANÁLISIS DE BALANCE")
        print("=" * 60)
        
        # Contar contenido promocional vs. valor
        promotional_keywords = ['promo', 'oferta', 'descuento', 'venta', 'comprar', 'ahora']
        value_keywords = ['tip', 'guía', 'cómo', 'tutorial', 'educativo', 'aprende']
        
        promotional_count = 0
        value_count = 0
        
        for post in self.posts:
            caption = post.get('Caption Preview', '').lower()
            topic = post.get('Topic', '').lower()
            content = (caption + ' ' + topic).lower()
            
            if any(keyword in content for keyword in promotional_keywords):
                promotional_count += 1
            if any(keyword in content for keyword in value_keywords):
                value_count += 1
        
        total = len(self.posts)
        if total > 0:
            promo_pct = (promotional_count / total) * 100
            value_pct = (value_count / total) * 100
            
            print(f"\n💰 Contenido Promocional: {promotional_count} posts ({promo_pct:.1f}%)")
            print(f"📚 Contenido de Valor: {value_count} posts ({value_pct:.1f}%)")
            
            # Recomendación
            print("\n💡 Recomendación:")
            if promo_pct > 30:
                print("  ⚠️ Contenido muy promocional. Considera aumentar contenido de valor.")
            elif promo_pct < 10:
                print("  ✅ Buen balance. Podrías considerar más contenido promocional estratégico.")
            else:
                print("  ✅ Balance adecuado entre valor y promoción.")
    
    def analyze_hashtags(self):
        """Analiza el uso de hashtags"""
        print("\n" + "=" * 60)
        print("🏷️ ANÁLISIS DE HASHTAGS")
        print("=" * 60)
        
        all_hashtags = []
        for post in self.posts:
            hashtags = post.get('Hashtags', '')
            # Extraer hashtags
            hashtag_list = re.findall(r'#\w+', hashtags)
            all_hashtags.extend(hashtag_list)
        
        if all_hashtags:
            hashtag_count = Counter(all_hashtags)
            print(f"\n📊 Total de hashtags únicos: {len(hashtag_count)}")
            print(f"📊 Total de hashtags usados: {len(all_hashtags)}")
            print(f"📊 Promedio por post: {len(all_hashtags) / len(self.posts):.1f}")
            
            print("\n🔥 Top 10 Hashtags Más Usados:")
            for hashtag, count in hashtag_count.most_common(10):
                print(f"  {hashtag}: {count} veces")
        else:
            print("\n⚠️ No se encontraron hashtags en el calendario")
    
    def generate_report(self):
        """Genera reporte completo"""
        print("\n" + "=" * 60)
        print("📋 REPORTE COMPLETO DE ANÁLISIS")
        print("=" * 60)
        print(f"\n📁 Archivo analizado: {self.markdown_file}")
        print(f"📅 Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total de posts: {len(self.posts)}")
        
        self.analyze_distribution()
        self.analyze_frequency()
        self.analyze_balance()
        self.analyze_hashtags()
        
        print("\n" + "=" * 60)
        print("✅ Análisis completado")
        print("=" * 60)


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python analyze_calendar.py <archivo_calendario.md>")
        print("\nEjemplo:")
        print("  python analyze_calendar.py calendario.md")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    analyzer = CalendarAnalyzer(markdown_file)
    analyzer.generate_report()


if __name__ == '__main__':
    main()









