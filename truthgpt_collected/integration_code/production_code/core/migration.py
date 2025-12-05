#!/usr/bin/env python3
"""
Migration Utilities for Paper Modules
=====================================

Utilidades para migrar archivos antiguos a las nuevas convenciones.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


def migrate_logging(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Migra un archivo para usar setup_logger en lugar de logging.basicConfig.
    
    Args:
        file_path: Ruta del archivo a migrar
    
    Returns:
        Tupla (success, changes) donde changes es lista de cambios realizados
    """
    def _migrate_logging_internal():
        changes = []
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Detectar si ya usa setup_logger
        if 'setup_logger' in content:
            return False, ['Ya usa setup_logger']
        
        # Buscar imports de logging
        if 'import logging' in content:
            # Reemplazar logging.basicConfig
            if 'logging.basicConfig' in content:
                content = re.sub(
                    r'logging\.basicConfig\([^)]*\)',
                    '',
                    content
                )
                changes.append('Removido logging.basicConfig')
            
            # Reemplazar logger = logging.getLogger
            if 'logger = logging.getLogger(__name__)' in content:
                # Buscar imports para determinar ruta
                if 'from ..core.paper_base' in content or 'from ...core.paper_base' in content:
                    # Ya tiene imports relativos
                    import_line = 'from .utils import setup_logger'
                    if 'from ..core.utils' in content or 'from ...core.utils' in content:
                        pass  # Ya importa
                    else:
                        # Añadir import después de paper_base import
                        content = re.sub(
                            r'(from \.\.?\.?core\.paper_base import[^\n]+\n)',
                            r'\1from .utils import setup_logger\n',
                            content
                        )
                        changes.append('Añadido import de setup_logger')
                else:
                    # Intentar añadir import
                    if 'from core.paper_base' in content:
                        content = re.sub(
                            r'(from core\.paper_base import[^\n]+\n)',
                            r'\1from core.utils import setup_logger\n',
                            content
                        )
                        changes.append('Añadido import de setup_logger')
                
                # Reemplazar logger assignment
                content = re.sub(
                    r'logger = logging\.getLogger\(__name__\)',
                    'logger = setup_logger(__name__)',
                    content
                )
                changes.append('Reemplazado logging.getLogger con setup_logger')
            
            # Remover import logging si ya no se usa
            if 'import logging' in content and 'logging.' not in content.replace('logger = setup_logger', ''):
                content = re.sub(r'^import logging\n', '', content, flags=re.MULTILINE)
                changes.append('Removido import logging no usado')
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            logger.info("Archivo migrado", file=str(file_path), changes=changes)
            return True, changes
        else:
            return False, ['No se encontraron cambios necesarios']
    
    result, error = safe_execute(_migrate_logging_internal, default_value=(False, ['Error en migración']), log_errors=True)
    if error:
        logger.error("Error migrando archivo", file=str(file_path), error=str(error))
        return False, [f'Error: {str(error)}']
    return result


def migrate_validate_method(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Añade método validate() a configs que no lo tienen.
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        Tupla (success, changes)
    """
    changes = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Buscar clases Config que heredan de BasePaperConfig
        config_pattern = r'class (\w+Config)\(BasePaperConfig\):'
        matches = list(re.finditer(config_pattern, content))
        
        for match in matches:
            config_name = match.group(1)
            config_start = match.end()
            
            # Buscar el final de la clase (siguiente class o def al mismo nivel)
            class_end = content.find('\nclass ', config_start)
            if class_end == -1:
                class_end = len(content)
            
            class_content = content[config_start:class_end]
            
            # Verificar si ya tiene validate
            if 'def validate(self):' in class_content:
                continue
            
            # Buscar el final de los atributos (último campo o __post_init__)
            # Insertar validate antes del final de la clase
            insert_pos = class_end
            
            # Buscar último método o campo
            last_def = class_content.rfind('\n    def ')
            last_field = class_content.rfind('\n    ')
            
            if last_def > last_field:
                insert_pos = config_start + last_def
            elif last_field != -1:
                insert_pos = config_start + last_field
                # Buscar siguiente línea
                next_line = content.find('\n', insert_pos)
                if next_line != -1:
                    insert_pos = next_line + 1
            
            # Crear método validate básico
            validate_method = f'''    
    def validate(self):
        """Valida la configuración."""
        super().validate()
'''
            
            content = content[:insert_pos] + validate_method + content[insert_pos:]
            changes.append(f'Añadido método validate() a {config_name}')
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            logger.info("Método validate añadido", file=str(file_path), changes=changes)
            return True, changes
        else:
            return False, ['No se encontraron configs sin validate']
    
    except Exception as e:
        logger.error("Error añadiendo validate", file=str(file_path), error=str(e))
        return False, [f'Error: {str(e)}']


def migrate_validate_inputs(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Añade validate_inputs() en forward si no está presente.
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        Tupla (success, changes)
    """
    changes = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Buscar métodos forward
        forward_pattern = r'def forward\(self[^)]*\)[^:]*:'
        matches = list(re.finditer(forward_pattern, content, re.MULTILINE))
        
        for match in matches:
            forward_start = match.end()
            
            # Buscar primera línea del cuerpo (después de docstring)
            body_start = forward_start
            # Saltar docstring si existe
            if '"""' in content[forward_start:forward_start+200]:
                docstring_end = content.find('"""', forward_start + 3)
                if docstring_end != -1:
                    body_start = content.find('\n', docstring_end + 3) + 1
            
            # Verificar si ya tiene validate_inputs
            body_preview = content[body_start:body_start+200]
            if 'validate_inputs' in body_preview or 'self.validate_inputs' in body_preview:
                continue
            
            # Buscar primera línea no vacía del cuerpo
            first_line_start = body_start
            while first_line_start < len(content) and content[first_line_start] in ['\n', ' ', '\t']:
                first_line_start += 1
            
            # Insertar validate_inputs
            indent = '        '  # 8 espacios típicos para métodos
            validate_call = f'{indent}self.validate_inputs(hidden_states, **kwargs)\n\n'
            
            content = content[:first_line_start] + validate_call + content[first_line_start:]
            changes.append('Añadido validate_inputs() en forward')
            break  # Solo el primer forward
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            logger.info("validate_inputs añadido", file=str(file_path), changes=changes)
            return True, changes
        else:
            return False, ['No se encontraron forwards sin validate_inputs']
    
    except Exception as e:
        logger.error("Error añadiendo validate_inputs", file=str(file_path), error=str(e))
        return False, [f'Error: {str(e)}']


def migrate_file(file_path: Path, operations: List[str] = None) -> Dict[str, any]:
    """
    Migra un archivo completo.
    
    Args:
        file_path: Ruta del archivo
        operations: Lista de operaciones ('logging', 'validate', 'validate_inputs')
    
    Returns:
        Diccionario con resultados
    """
    if operations is None:
        operations = ['logging', 'validate', 'validate_inputs']
    
    results = {
        'file': str(file_path),
        'operations': {}
    }
    
    if 'logging' in operations:
        success, changes = migrate_logging(file_path)
        results['operations']['logging'] = {'success': success, 'changes': changes}
    
    if 'validate' in operations:
        success, changes = migrate_validate_method(file_path)
        results['operations']['validate'] = {'success': success, 'changes': changes}
    
    if 'validate_inputs' in operations:
        success, changes = migrate_validate_inputs(file_path)
        results['operations']['validate_inputs'] = {'success': success, 'changes': changes}
    
    return results


def migrate_directory(
    directory: Path,
    pattern: str = 'paper_*.py',
    operations: List[str] = None
) -> Dict[str, any]:
    """
    Migra todos los archivos en un directorio.
    
    Args:
        directory: Directorio a migrar
        pattern: Patrón de archivos
        operations: Operaciones a realizar
    
    Returns:
        Diccionario con resultados
    """
    results = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'files': []
    }
    
    for file_path in directory.rglob(pattern):
        if file_path.is_file():
            results['total_files'] += 1
            try:
                file_result = migrate_file(file_path, operations)
                results['files'].append(file_result)
                
                if any(op.get('success', False) for op in file_result['operations'].values()):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['files'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
                logger.error("Error migrando archivo", file=str(file_path), error=str(e))
    
    logger.info(
        "Migración completada",
        directory=str(directory),
        total=results['total_files'],
        successful=results['successful'],
        failed=results['failed']
    )
    
    return results

