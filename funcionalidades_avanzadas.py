#!/usr/bin/env python3
"""
Funcionalidades avanzadas adicionales:
- Análisis de SEO
- Detección de errores comunes
- Sugerencias de mejora
- Análisis de accesibilidad
- Generación de índice automático
"""

import re
from collections import Counter
from datetime import datetime

def analyze_seo(content, title=""):
    """Analiza aspectos SEO del documento"""
    content_lower = content.lower()
    
    # Meta tags básicos
    has_title = bool(title or re.search(r'^#\s+.+', content, re.MULTILINE))
    has_description = bool(re.search(r'description|descripción', content_lower))
    
    # Headers
    h1_count = len(re.findall(r'^#\s+', content, re.MULTILINE))
    h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
    h3_count = len(re.findall(r'^###\s+', content, re.MULTILINE))
    
    # Enlaces
    internal_links = len(re.findall(r'\[([^\]]+)\]\([^h][^\)]+\)', content))
    external_links = len(re.findall(r'\[([^\]]+)\]\(https?://', content))
    
    # Imágenes con alt text
    images_with_alt = len(re.findall(r'!\[([^\]]+)\]', content))
    images_total = len(re.findall(r'!\[', content))
    alt_text_ratio = images_with_alt / max(images_total, 1)
    
    # Longitud de contenido
    word_count = len(re.findall(r'\b\w+\b', content))
    optimal_length = 300 <= word_count <= 2500  # Para artículos
    
    # Keywords density
    words = re.findall(r'\b\w{4,}\b', content_lower)
    word_freq = Counter(words)
    stop_words = {'este', 'esta', 'estos', 'estas', 'también', 'tambien', 'puede', 'pueden'}
    keywords = {w: c for w, c in word_freq.items() if w not in stop_words and len(w) > 3}
    top_keywords = dict(list(keywords.most_common(5)))
    
    # Score SEO (0-100)
    seo_score = 0
    if has_title:
        seo_score += 20
    if has_description:
        seo_score += 10
    if h1_count == 1:
        seo_score += 15
    if h2_count >= 2:
        seo_score += 15
    if external_links >= 3:
        seo_score += 10
    if alt_text_ratio >= 0.8:
        seo_score += 10
    if optimal_length:
        seo_score += 10
    if len(top_keywords) >= 3:
        seo_score += 10
    
    return {
        'seo_score': min(100, seo_score),
        'has_title': has_title,
        'has_description': has_description,
        'h1_count': h1_count,
        'h2_count': h2_count,
        'h3_count': h3_count,
        'internal_links': internal_links,
        'external_links': external_links,
        'alt_text_ratio': round(alt_text_ratio, 2),
        'optimal_length': optimal_length,
        'top_keywords': top_keywords,
        'recommendations': generate_seo_recommendations(seo_score, has_title, h1_count, external_links, alt_text_ratio)
    }

def generate_seo_recommendations(score, has_title, h1_count, external_links, alt_text_ratio):
    """Genera recomendaciones SEO"""
    recommendations = []
    
    if not has_title:
        recommendations.append("Agregar un título principal (H1)")
    if h1_count != 1:
        recommendations.append(f"Tener exactamente 1 H1 (actualmente: {h1_count})")
    if external_links < 3:
        recommendations.append(f"Agregar más enlaces externos (actualmente: {external_links})")
    if alt_text_ratio < 0.8:
        recommendations.append(f"Mejorar ratio de alt text en imágenes ({alt_text_ratio:.0%})")
    if score < 70:
        recommendations.append("Mejorar estructura general del documento para SEO")
    
    return recommendations if recommendations else ["Documento bien optimizado para SEO"]

def detect_common_errors(content):
    """Detecta errores comunes en documentos"""
    errors = []
    warnings = []
    
    # Errores de formato
    lines = content.split('\n')
    
    # Headers sin espacio después de #
    for i, line in enumerate(lines[:100], 1):  # Revisar primeras 100 líneas
        if re.match(r'^#+[^#\s]', line):
            errors.append(f"Línea {i}: Header sin espacio después de #")
    
    # Enlaces rotos (sin URL)
    broken_links = re.findall(r'\[([^\]]+)\]\(\)', content)
    if broken_links:
        errors.append(f"Enlaces sin URL: {len(broken_links)} encontrados")
    
    # Imágenes sin alt text
    images_no_alt = re.findall(r'!\[\]\(', content)
    if images_no_alt:
        warnings.append(f"Imágenes sin texto alternativo: {len(images_no_alt)}")
    
    # Listas mal formateadas
    malformed_lists = 0
    for line in lines:
        if line.strip().startswith('-') or line.strip().startswith('*'):
            if not re.match(r'^[\s]*[-*+]\s+', line):
                malformed_lists += 1
    if malformed_lists > 0:
        warnings.append(f"Listas potencialmente mal formateadas: {malformed_lists}")
    
    # Tablas mal formateadas
    table_lines = [l for l in lines if '|' in l]
    if table_lines:
        for i, line in enumerate(table_lines[:10], 1):
            if line.count('|') < 2:
                warnings.append(f"Tabla potencialmente mal formateada en línea {i}")
    
    # Código sin lenguaje especificado
    code_blocks = re.findall(r'```(\w*)', content)
    unspecified_code = sum(1 for lang in code_blocks if not lang)
    if unspecified_code > 0:
        warnings.append(f"Bloques de código sin lenguaje especificado: {unspecified_code}")
    
    return {
        'errors': errors,
        'warnings': warnings,
        'error_count': len(errors),
        'warning_count': len(warnings),
        'quality_issues': len(errors) + len(warnings)
    }

def analyze_accessibility(content):
    """Analiza aspectos de accesibilidad"""
    accessibility_score = 100
    issues = []
    
    # Headers jerárquicos
    headers = []
    for line in content.split('\n')[:200]:
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            headers.append(level)
    
    # Verificar jerarquía (no saltar niveles)
    for i in range(len(headers) - 1):
        if headers[i+1] > headers[i] + 1:
            accessibility_score -= 5
            issues.append("Saltos en jerarquía de headers")
            break
    
    # Imágenes con alt text
    images = re.findall(r'!\[([^\]]*)\]\(', content)
    images_no_alt = sum(1 for alt in images if not alt.strip())
    if images_no_alt > 0:
        accessibility_score -= images_no_alt * 3
        issues.append(f"{images_no_alt} imágenes sin texto alternativo")
    
    # Contraste de texto (simulado - verificar uso de código inline)
    code_blocks = len(re.findall(r'`[^`]+`', content))
    if code_blocks > 50:
        # Mucho código inline puede ser difícil de leer
        accessibility_score -= 2
    
    # Longitud de líneas (aproximado)
    long_lines = sum(1 for line in content.split('\n') if len(line) > 100)
    if long_lines > 20:
        accessibility_score -= 5
        issues.append("Muchas líneas muy largas (>100 caracteres)")
    
    # Enlaces descriptivos
    links = re.findall(r'\[([^\]]+)\]\([^\)]+\)', content)
    non_descriptive = sum(1 for text in links if len(text) < 3 or text.lower() in ['click', 'aquí', 'aquí', 'link'])
    if non_descriptive > 0:
        accessibility_score -= non_descriptive * 2
        issues.append(f"{non_descriptive} enlaces no descriptivos")
    
    return {
        'accessibility_score': max(0, accessibility_score),
        'issues': issues,
        'level': 'Excelente' if accessibility_score >= 90 else 'Bueno' if accessibility_score >= 70 else 'Mejorable'
    }

def generate_auto_index(content):
    """Genera índice automático basado en headers"""
    headers = []
    for line in content.split('\n'):
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            if text:
                headers.append((level, text))
    
    if not headers:
        return "No se encontraron headers para generar índice"
    
    index_lines = ["## Índice\n"]
    for level, text in headers[:30]:  # Limitar a 30 entradas
        indent = "  " * (level - 1)
        # Crear anchor (simplificado)
        anchor = text.lower().replace(' ', '-').replace('.', '').replace(',', '')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        index_lines.append(f"{indent}- [{text}](#{anchor})")
    
    return "\n".join(index_lines)

def suggest_improvements(stats, errors, seo, accessibility):
    """Genera sugerencias de mejora basadas en análisis"""
    suggestions = []
    
    # Basado en estadísticas
    if stats.get('total_words', 0) < 300:
        suggestions.append("💡 Considerar expandir el contenido (mínimo 300 palabras recomendado)")
    elif stats.get('total_words', 0) > 10000:
        suggestions.append("💡 Documento muy extenso, considerar dividirlo en múltiples secciones")
    
    if stats.get('total_sections', 0) < 3:
        suggestions.append("💡 Agregar más secciones para mejor organización")
    
    if stats.get('code_blocks', 0) == 0 and '```' in str(stats):
        suggestions.append("💡 Considerar agregar ejemplos de código si es relevante")
    
    if stats.get('links', 0) < 5:
        suggestions.append("💡 Agregar más enlaces para mejor interconexión")
    
    # Basado en errores
    if errors.get('error_count', 0) > 0:
        suggestions.append(f"⚠️ Corregir {errors['error_count']} errores detectados")
    
    if errors.get('warning_count', 0) > 5:
        suggestions.append(f"⚠️ Revisar {errors['warning_count']} advertencias")
    
    # Basado en SEO
    if seo.get('seo_score', 0) < 70:
        suggestions.append("🔍 Mejorar optimización SEO del documento")
        suggestions.extend(seo.get('recommendations', [])[:3])
    
    # Basado en accesibilidad
    if accessibility.get('accessibility_score', 100) < 80:
        suggestions.append("♿ Mejorar accesibilidad del documento")
        suggestions.extend(accessibility.get('issues', [])[:2])
    
    # Basado en calidad de código
    if stats.get('code_quality', 0) < 50:
        suggestions.append("💻 Mejorar documentación de código (agregar comentarios)")
    
    # Basado en estructura
    if stats.get('structure_score', 0) < 60:
        suggestions.append("📐 Mejorar estructura jerárquica del documento")
    
    return suggestions[:10]  # Limitar a 10 sugerencias

def calculate_overall_quality_score(stats, errors, seo, accessibility, code_quality, structure_score):
    """Calcula score de calidad general (0-100)"""
    score = 0
    
    # Contenido (30 puntos)
    word_score = min(30, (stats.get('total_words', 0) / 1000) * 10)
    section_score = min(10, stats.get('total_sections', 0) * 0.5)
    link_score = min(10, stats.get('links', 0) * 0.5)
    score += word_score + section_score + link_score
    
    # Calidad técnica (25 puntos)
    error_penalty = min(25, errors.get('error_count', 0) * 5)
    warning_penalty = min(10, errors.get('warning_count', 0) * 0.5)
    score += max(0, 25 - error_penalty - warning_penalty)
    
    # SEO (15 puntos)
    score += (seo.get('seo_score', 0) / 100) * 15
    
    # Accesibilidad (15 puntos)
    score += (accessibility.get('accessibility_score', 0) / 100) * 15
    
    # Código (10 puntos)
    score += (code_quality / 100) * 10
    
    # Estructura (5 puntos)
    score += (structure_score / 100) * 5
    
    return min(100, max(0, round(score, 1)))

if __name__ == "__main__":
    print("🔧 Módulo de funcionalidades avanzadas cargado correctamente")



