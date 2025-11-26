"""
Módulo de formateo especializado para contenido viral
"""

import re
from typing import List


class ContentFormatter:
    """Formateador de contenido siguiendo reglas virales"""
    
    @staticmethod
    def validate_content_structure(content: str) -> List[str]:
        """Valida que el contenido siga las reglas de estructura"""
        errors = []
        
        lines = content.split('\n')
        
        # Regla: Nunca empezar con header
        if lines and lines[0].startswith('#'):
            errors.append("El contenido no debe empezar con un encabezado")
        
        # Regla: Nunca listas con un solo elemento
        bullet_count = 0
        in_list = False
        
        for line in lines:
            if line.strip().startswith(('-', '*', '1.', '2.')):
                if not in_list:
                    in_list = True
                    bullet_count = 1
                else:
                    bullet_count += 1
            else:
                if in_list and bullet_count == 1:
                    errors.append("Encontrada lista con un solo elemento")
                in_list = False
                bullet_count = 0
        
        # Regla: Verificar citas
        citation_pattern = r'\[\d+\]'
        citations = re.findall(citation_pattern, content)
        if not citations:
            errors.append("El contenido debe incluir citas de investigación")
        
        return errors
    
    @staticmethod
    def optimize_for_platform(content: str, platform: str) -> str:
        """Optimiza el contenido para plataforma específica"""
        
        optimizations = {
            'twitter': {
                'max_length': 280,
                'hashtag_count': 3,
                'emoji_usage': 'limited'
            },
            'instagram': {
                'max_length': 2200,
                'hashtag_count': 10,
                'emoji_usage': 'moderate'
            },
            'tiktok': {
                'max_length': 150,
                'hashtag_count': 5,
                'emoji_usage': 'frequent'
            },
            'linkedin': {
                'max_length': 1300,
                'hashtag_count': 5,
                'emoji_usage': 'professional'
            }
        }
        
        platform_rules = optimizations.get(platform, {})
        
        # Aplicar optimizaciones básicas
        if len(content) > platform_rules.get('max_length', 1000):
            content = content[:platform_rules['max_length'] - 100] + "..."
        
        return content
    
    @staticmethod
    def extract_engagement_elements(content: str) -> Dict:
        """Extrae elementos de engagement del contenido"""
        elements = {
            'hooks': [],
            'ctas': [],
            'questions': [],
            'hashtags': []
        }
        
        # Extraer hooks (primeras líneas)
        lines = content.split('\n')
        if lines:
            elements['hooks'].append(lines[0])
        
        # Extraer CTAs (últimas líneas)
        if len(lines) > 3:
            elements['ctas'].extend(lines[-3:])
        
        # Extraer hashtags
        hashtag_pattern = r'#\w+'
        elements['hashtags'] = re.findall(hashtag_pattern, content)
        
        # Extraer preguntas
        question_pattern = r'[^.!?]*\\?[^.!?]*[?]'
        elements['questions'] = re.findall(question_pattern, content)
        
        return elements
    
    @staticmethod
    def calculate_viral_score(content: str) -> float:
        """Calcula un score de viralidad potencial"""
        score = 0.0
        
        elements = ContentFormatter.extract_engagement_elements(content)
        
        # Puntos por hook efectivo
        if elements['hooks']:
            hook = elements['hooks'][0]
            if any(word in hook.lower() for word in ['pov', 'grwm', 'secret', 'discover']):
                score += 25
        
        # Puntos por CTAs
        if elements['ctas']:
            score += min(len(elements['ctas']) * 5, 15)
        
        # Puntos por preguntas engaging
        if elements['questions']:
            score += min(len(elements['questions']) * 8, 24)
        
        # Puntos por hashtags estratégicos
        if 3 <= len(elements['hashtags']) <= 8:
            score += 20
        
        # Puntos por estructura (encabezados)
        header_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
        score += min(header_count * 6, 18)
        
        return min(score, 100)


class MathFormatter:
    """Formateador especializado en expresiones matemáticas"""
    
    @staticmethod
    def format_math_content(text: str) -> str:
        """Convierte expresiones matemáticas al formato LaTeX correcto"""
        
        # Reemplazar $...$ por \(...\)
        text = re.sub(r'\$(.*?)\$', r'\\(\1\\)', text)
        
        # Reemplazar $$...$$ por \[...\]
        text = re.sub(r'\$\$(.*?)\$\$', r'\\[\1\\]', text)
        
        return text
    
    @staticmethod
    def validate_math_syntax(text: str) -> List[str]:
        """Valida la sintaxis de expresiones matemáticas"""
        errors = []
        
        # Buscar usos incorrectos de $
        if '$' in text:
            errors.append("Se encontraron símbolos $ - usar \\( y \\) para inline math")
        
        # Buscar \label (prohibido)
        if '\\label' in text:
            errors.append("Se encontró \\label - está prohibido en las reglas")
        
        return errors