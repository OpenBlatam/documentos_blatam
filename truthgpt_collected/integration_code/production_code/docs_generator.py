#!/usr/bin/env python3
"""
Generador de Documentación Automática
======================================

Genera documentación automática para todos los módulos.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import inspect
import ast
import json
from datetime import datetime

from core.utils import setup_logger

logger = setup_logger(__name__)


class DocumentationGenerator:
    """
    Generador de documentación.
    
    Extrae información de módulos y genera documentación.
    """
    
    def __init__(self, output_dir: str = "docs"):
        """
        Inicializa generador.
        
        Args:
            output_dir: Directorio de salida
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DocumentationGenerator inicializado, output: {output_dir}")
    
    def extract_module_info(self, module) -> Dict[str, Any]:
        """
        Extrae información de un módulo.
        
        Args:
            module: Módulo a analizar
        
        Returns:
            Diccionario con información
        """
        info = {
            'name': getattr(module, '__name__', 'unknown'),
            'doc': inspect.getdoc(module) or '',
            'classes': [],
            'functions': [],
            'constants': []
        }
        
        # Extraer clases
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module.__name__:
                class_info = {
                    'name': name,
                    'doc': inspect.getdoc(obj) or '',
                    'methods': []
                }
                
                # Métodos
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if method_name.startswith('_'):
                        continue
                    method_info = {
                        'name': method_name,
                        'doc': inspect.getdoc(method) or '',
                        'signature': str(inspect.signature(method))
                    }
                    class_info['methods'].append(method_info)
                
                info['classes'].append(class_info)
        
        # Extraer funciones
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ == module.__name__:
                func_info = {
                    'name': name,
                    'doc': inspect.getdoc(obj) or '',
                    'signature': str(inspect.signature(obj))
                }
                info['functions'].append(func_info)
        
        return info
    
    def generate_module_docs(self, module_name: str, module) -> str:
        """
        Genera documentación Markdown para un módulo.
        
        Args:
            module_name: Nombre del módulo
            module: Módulo a documentar
        
        Returns:
            Documentación en Markdown
        """
        info = self.extract_module_info(module)
        
        doc = f"# {module_name}\n\n"
        
        if info['doc']:
            doc += f"{info['doc']}\n\n"
        
        # Clases
        if info['classes']:
            doc += "## Clases\n\n"
            for cls in info['classes']:
                doc += f"### {cls['name']}\n\n"
                if cls['doc']:
                    doc += f"{cls['doc']}\n\n"
                
                if cls['methods']:
                    doc += "#### Métodos\n\n"
                    for method in cls['methods']:
                        doc += f"**{method['name']}**{method['signature']}\n\n"
                        if method['doc']:
                            doc += f"{method['doc']}\n\n"
        
        # Funciones
        if info['functions']:
            doc += "## Funciones\n\n"
            for func in info['functions']:
                doc += f"### {func['name']}\n\n"
                doc += f"```python\n{func['name']}{func['signature']}\n```\n\n"
                if func['doc']:
                    doc += f"{func['doc']}\n\n"
        
        return doc
    
    def generate_api_docs(self, modules: Dict[str, Any]) -> str:
        """
        Genera documentación API completa.
        
        Args:
            modules: Diccionario de módulos
        
        Returns:
            Documentación API en Markdown
        """
        doc = "# API Documentation\n\n"
        doc += f"Generated: {datetime.now().isoformat()}\n\n"
        doc += "## Modules\n\n"
        
        for module_name, module in modules.items():
            doc += f"### {module_name}\n\n"
            module_info = self.extract_module_info(module)
            
            if module_info['classes']:
                doc += "#### Classes\n\n"
                for cls in module_info['classes']:
                    doc += f"- `{cls['name']}`: {cls['doc'][:100] if cls['doc'] else 'No description'}\n"
            
            if module_info['functions']:
                doc += "\n#### Functions\n\n"
                for func in module_info['functions']:
                    doc += f"- `{func['name']}`: {func['doc'][:100] if func['doc'] else 'No description'}\n"
            
            doc += "\n"
        
        return doc
    
    def generate_index(self, modules: List[str]) -> str:
        """
        Genera índice de documentación.
        
        Args:
            modules: Lista de módulos documentados
        
        Returns:
            Índice en Markdown
        """
        doc = "# Documentation Index\n\n"
        doc += f"Generated: {datetime.now().isoformat()}\n\n"
        doc += "## Available Modules\n\n"
        
        for module in modules:
            doc += f"- [{module}]({module}.md)\n"
        
        doc += "\n## Quick Links\n\n"
        doc += "- [API Documentation](API.md)\n"
        doc += "- [Examples](../examples/)\n"
        doc += "- [Configuration](../config/)\n"
        
        return doc
    
    def generate_all_docs(self, modules: Dict[str, Any]):
        """
        Genera toda la documentación.
        
        Args:
            modules: Diccionario de módulos a documentar
        """
        logger.info(f"Generando documentación para {len(modules)} módulos...")
        
        # Generar documentación por módulo
        module_names = []
        for module_name, module in modules.items():
            try:
                doc = self.generate_module_docs(module_name, module)
                output_file = self.output_dir / f"{module_name}.md"
                output_file.write_text(doc, encoding='utf-8')
                module_names.append(module_name)
                logger.info(f"Documentación generada para {module_name}")
            except Exception as e:
                logger.error(f"Error generando docs para {module_name}: {e}")
        
        # Generar API docs
        try:
            api_doc = self.generate_api_docs(modules)
            api_file = self.output_dir / "API.md"
            api_file.write_text(api_doc, encoding='utf-8')
            logger.info("API documentation generated")
        except Exception as e:
            logger.error(f"Error generando API docs: {e}")
        
        # Generar índice
        try:
            index = self.generate_index(module_names)
            index_file = self.output_dir / "INDEX.md"
            index_file.write_text(index, encoding='utf-8')
            logger.info("Index generated")
        except Exception as e:
            logger.error(f"Error generando índice: {e}")
        
        logger.info(f"Documentación generada en {self.output_dir}")


def generate_documentation(output_dir: str = "docs"):
    """
    Función helper para generar documentación.
    
    Args:
        output_dir: Directorio de salida
    """
    generator = DocumentationGenerator(output_dir)
    
    modules = {}
    
    # Importar módulos
    try:
        import memory
        modules['memory'] = memory
    except ImportError:
        pass
    
    try:
        import redundancy
        modules['redundancy'] = redundancy
    except ImportError:
        pass
    
    try:
        import sora
        modules['sora'] = sora
    except ImportError:
        pass
    
    try:
        from integration_pipeline import IntegratedPipeline
        modules['pipeline'] = IntegratedPipeline
    except ImportError:
        pass
    
    try:
        from core.config_manager import ConfigManager
        modules['config_manager'] = ConfigManager
    except ImportError:
        pass
    
    try:
        from monitoring_system import SystemMonitor
        modules['monitoring'] = SystemMonitor
    except ImportError:
        pass
    
    generator.generate_all_docs(modules)


if __name__ == "__main__":
    print("=" * 60)
    print("Generando Documentación Automática")
    print("=" * 60 + "\n")
    
    generate_documentation("docs")
    
    print("\n✅ Documentación generada en docs/")


