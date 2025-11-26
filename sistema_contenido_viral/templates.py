"""
Templates predefinidos para diferentes tipos de contenido
"""

from typing import Dict, Any


class ContentTemplates:
    """Plantillas de contenido predefinidas"""
    
    @staticmethod
    def get_blog_template() -> Dict[str, Any]:
        """Template para artículos de blog"""
        return {
            "structure": [
                {
                    "title": "Introducción",
                    "content": "Hook inicial que captura la atención inmediatamente",
                    "type": "paragraph"
                },
                {
                    "title": "El Problema",
                    "content": "Identificación clara del dolor o necesidad del audience",
                    "type": "paragraph",
                    "list": [
                        "Punto clave 1",
                        "Punto clave 2", 
                        "Punto clave 3"
                    ]
                },
                {
                    "title": "La Solución",
                    "content": "Presentación de la solución o estrategia",
                    "type": "paragraph",
                    "table": {
                        "headers": ["Enfoque Tradicional", "Enfoque Viral"],
                        "rows": [
                            ["Resultado 1", "Resultado mejorado 1"],
                            ["Resultado 2", "Resultado mejorado 2"]
                        ]
                    }
                },
                {
                    "title": "Implementación",
                    "content": "Pasos accionables para implementar",
                    "type": "ordered_list",
                    "list": [
                        "Paso 1 con detalles específicos",
                        "Paso 2 con ejemplos concretos",
                        "Paso 3 con métricas medibles"
                    ]
                }
            ],
            "requirements": {
                "min_sections": 3,
                "max_sections": 6,
                "must_include": ["hook", "list", "table", "cta"]
            }
        }
    
    @staticmethod
    def get_social_media_template(platform: str) -> Dict[str, Any]:
        """Template para contenido de redes sociales"""
        templates = {
            "twitter": {
                "max_length": 280,
                "structure": ["hook", "main_point", "engagement_question", "hashtags"],
                "thread_structure": [
                    "Tweet 1: Hook + problema",
                    "Tweet 2: Solución + datos", 
                    "Tweet 3: CTA + hashtags"
                ]
            },
            "instagram": {
                "max_caption_length": 2200,
                "structure": ["hook", "value_proposition", "features_list", "cta", "hashtags"],
                "reel_formats": [
                    "Day in the Life",
                    "Quick Tip", 
                    "Before & After",
                    "Myth Busting"
                ]
            },
            "tiktok": {
                "max_caption_length": 150,
                "structure": ["hook", "entertainment_value", "trend_reference", "cta", "hashtags"],
                "audio_trends": [
                    "Trending audio descriptions",
                    "Voiceover trends", 
                    "Sound-on imperative"
                ]
            }
        }
        return templates.get(platform, {})
    
    @staticmethod
    def get_email_template() -> Dict[str, Any]:
        """Template para emails de marketing"""
        return {
            "structure": [
                "subject_line_optimized",
                "preheader_text", 
                "personalized_greeting",
                "value_proposition",
                "benefits_list",
                "social_proof",
                "urgent_cta",
                "secondary_cta",
                "personal_signature"
            ],
            "best_practices": [
                "Mobile-first design",
                "Clear value above fold",
                "Single primary CTA", 
                "Personalization tokens",
                "A/B test elements"
            ]
        }