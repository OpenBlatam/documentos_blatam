"""
Módulo principal del sistema de creación de contenido viral
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ContentConfig:
    """Configuración para la creación de contenido"""
    content_type: str  # 'blog', 'social_media', 'email', 'landing_page'
    platform: str  # 'twitter', 'instagram', 'tiktok', 'linkedin'
    tone: str  # 'professional', 'casual', 'trending', 'educational'
    target_audience: str
    viral_hooks: List[str]
    

class ViralContentGenerator:
    """Generador de contenido optimizado para viralidad"""
    
    def __init__(self, config: ContentConfig):
        self.config = config
        self.viral_elements = self._load_viral_elements()
    
    def _load_viral_elements(self) -> Dict:
        """Carga elementos virales actuales"""
        return {
            'hashtags': {
                'twitter': ['#ContentCreatorLife', '#DigitalMarketingHacks', '#ViralStrategy', '#CreatorEconomy', '#AIContent'],
                'instagram': ['#ContentCreator', '#ViralContent', '#MarketingDigital', '#Trending', '#Reels'],
                'tiktok': ['#FYP', '#ParaTi', '#Viral', '#TrendingAudio', '#ContentCreation']
            },
            'hooks': [
                "POV: Estás a punto de descubrir el secreto del contenido viral...",
                "GRWM para crear contenido que explota en redes 🚀",
                "Lo que nadie te dice sobre el contenido que realmente funciona...",
                "El algoritmo me mostró esto y cambié mi estrategia para siempre"
            ],
            'cta_phrases': [
                "Link en bio para más tips 🔗",
                "Duplica este contenido y etiquétame 📱",
                "Guarda esto para después ⬇️",
                "Comparte tu experiencia en comentarios 💬"
            ]
        }
    
    def generate_hook(self) -> str:
        """Genera un hook scroll-stopping"""
        import random
        return random.choice(self.viral_elements['hooks'])
    
    def generate_hashtags(self, platform: str) -> str:
        """Genera hashtags específicos para plataforma"""
        tags = self.viral_elements['hashtags'].get(platform, [])
        return ' '.join(tags[:5])  # Máximo 5 hashtags
    
    def format_heading(self, text: str, level: int = 2) -> str:
        """Formatea encabezados según reglas"""
        if level == 2:
            return f"## {text}"
        return text
    
    def format_list(self, items: List[str], ordered: bool = False) -> str:
        """Formatea listas según reglas"""
        if len(items) <= 1:
            return items[0] if items else ""
        
        if ordered:
            return '\n'.join([f"{i+1}. {item}" for i, item in enumerate(items)])
        else:
            return '\n'.join([f"- {item}" for item in items])
    
    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Formatea tablas markdown"""
        if not headers or not rows:
            return ""
        
        # Header
        table = f"| {' | '.join(headers)} |\n"
        # Separator
        table += f"|{'|'.join(['---'] * len(headers))}|\n"
        # Rows
        for row in rows:
            table += f"| {' | '.join(row)} |\n"
        
        return table
    
    def format_math_expression(self, expression: str, inline: bool = True) -> str:
        """Formatea expresiones matemáticas en LaTeX"""
        if inline:
            return f"\\({expression}\\)"
        else:
            return f"\\[{expression}\\]"
    
    def add_citation(self, text: str, sources: List[int]) -> str:
        """Añade citas al texto"""
        if not sources:
            return text
        
        citations = ''.join([f"[{source}]" for source in sources])
        return f"{text}{citations}"


class BlogContentGenerator(ViralContentGenerator):
    """Generador especializado en contenido de blog"""
    
    def generate_article(self, title: str, sections: List[Dict]) -> str:
        """Genera un artículo completo de blog"""
        
        content = f"{self.generate_hook()}\n\n"
        
        for section in sections:
            content += f"{self.format_heading(section['title'])}\n\n"
            content += f"{section['content']}\n\n"
            
            if 'list' in section:
                content += f"{self.format_list(section['list'])}\n\n"
            
            if 'table' in section:
                content += f"{self.format_table(section['table']['headers'], section['table']['rows'])}\n\n"
        
        # Call to action final
        import random
        cta = random.choice(self.viral_elements['cta_phrases'])
        content += f"{cta}\n\n"
        
        # Hashtags
        content += f"{self.generate_hashtags('twitter')}\n"
        
        return content


class SocialMediaGenerator(ViralContentGenerator):
    """Generador especializado en contenido para redes sociales"""
    
    def generate_thread(self, topic: str, points: List[str]) -> str:
        """Genera un hilo de Twitter/X"""
        content = f"{self.generate_hook()}\n\n"
        
        for i, point in enumerate(points, 1):
            content += f"{i}/{len(points)} {point}\n\n"
        
        content += f"{self.generate_hashtags('twitter')}\n"
        return content
    
    def generate_instagram_caption(self, main_text: str, features: List[str]) -> str:
        """Genera caption para Instagram"""
        content = f"{main_text}\n\n"
        
        if features:
            content += "✨ Lo que encontrarás:\n"
            content += f"{self.format_list(features)}\n\n"
        
        content += f"{self.generate_hashtags('instagram')}\n"
        return content