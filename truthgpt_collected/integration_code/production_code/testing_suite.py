#!/usr/bin/env python3
"""
Sistema de Testing Integrado
============================

Suite completa de tests para todos los módulos.
"""

import unittest
import torch
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import time

from core.utils import setup_logger

logger = setup_logger(__name__)


class ModuleTestResult:
    """Resultado de test de módulo."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
        self.errors: List[str] = []
        self.duration = 0.0
        self.timestamp = time.time()
    
    def add_result(self, passed: bool, error: Optional[str] = None):
        """Añade resultado de test."""
        self.tests_total += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            if error:
                self.errors.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'module': self.module_name,
            'passed': self.tests_passed,
            'failed': self.tests_failed,
            'total': self.tests_total,
            'success_rate': self.tests_passed / self.tests_total if self.tests_total > 0 else 0.0,
            'duration': self.duration,
            'errors': self.errors
        }


class IntegratedTestSuite:
    """
    Suite de tests integrada.
    
    Ejecuta tests para todos los módulos.
    """
    
    def __init__(self):
        """Inicializa suite de tests."""
        self.results: Dict[str, ModuleTestResult] = {}
        logger.info("IntegratedTestSuite inicializado")
    
    def test_memory_module(self) -> ModuleTestResult:
        """Tests para módulo de memoria."""
        result = ModuleTestResult("memory")
        start_time = time.time()
        
        try:
            from memory import create_memory_system, Paper2506_15841v2Config
            
            # Test 1: Crear sistema
            try:
                config = Paper2506_15841v2Config(memory_dim=256)
                memory = create_memory_system("2506_15841v2", **config.__dict__ if hasattr(config, '__dict__') else {})
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error creando sistema: {e}")
                return result
            
            # Test 2: Almacenar episodio
            try:
                episode = torch.randn(256)
                success = memory.store_episode(episode, metadata={'test': True})
                result.add_result(success)
            except Exception as e:
                result.add_result(False, f"Error almacenando: {e}")
            
            # Test 3: Recuperar episodios
            try:
                query = torch.randn(256)
                retrieved, weights = memory.retrieve_episodes(query, k=5)
                result.add_result(retrieved.shape[0] > 0)
            except Exception as e:
                result.add_result(False, f"Error recuperando: {e}")
            
            # Test 4: Estadísticas
            try:
                stats = memory.get_episodic_stats()
                result.add_result('episodic_size' in stats)
            except Exception as e:
                result.add_result(False, f"Error obteniendo stats: {e}")
            
            # Test 5: Caché
            try:
                memory.clear_cache()
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error limpiando caché: {e}")
        
        except ImportError:
            result.add_result(False, "Módulo memory no disponible")
        
        result.duration = time.time() - start_time
        self.results['memory'] = result
        return result
    
    def test_redundancy_module(self) -> ModuleTestResult:
        """Tests para módulo de redundancia."""
        result = ModuleTestResult("redundancy")
        start_time = time.time()
        
        try:
            from redundancy import create_redundancy_suppressor, Paper2510_00071Config
            
            # Test 1: Crear sistema
            try:
                config = Paper2510_00071Config(similarity_threshold=0.85)
                redundancy = create_redundancy_suppressor("2510_00071", **config.__dict__ if hasattr(config, '__dict__') else {})
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error creando sistema: {e}")
                return result
            
            # Test 2: Procesar bulk
            try:
                items = torch.randn(20, 32, 512)
                unique_items, stats = redundancy.process_bulk(items)
                result.add_result(unique_items.shape[0] <= items.shape[0])
            except Exception as e:
                result.add_result(False, f"Error procesando: {e}")
            
            # Test 3: Métricas
            try:
                metrics = redundancy.get_metrics()
                result.add_result('total_processed' in metrics)
            except Exception as e:
                result.add_result(False, f"Error obteniendo métricas: {e}")
            
            # Test 4: Caché
            try:
                redundancy.clear_cache()
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error limpiando caché: {e}")
        
        except ImportError:
            result.add_result(False, "Módulo redundancy no disponible")
        
        result.duration = time.time() - start_time
        self.results['redundancy'] = result
        return result
    
    def test_pipeline_module(self) -> ModuleTestResult:
        """Tests para pipeline integrado."""
        result = ModuleTestResult("pipeline")
        start_time = time.time()
        
        try:
            from integration_pipeline import create_integrated_pipeline
            
            # Test 1: Crear pipeline
            try:
                pipeline = create_integrated_pipeline(
                    enable_memory=True,
                    enable_redundancy=True,
                    enable_video=False,
                    enable_chat=False
                )
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error creando pipeline: {e}")
                return result
            
            # Test 2: Procesar pipeline
            try:
                data = torch.randn(10, 32, 512)
                output, metadata = pipeline.process_pipeline(data)
                result.add_result(output.shape[0] > 0)
            except Exception as e:
                result.add_result(False, f"Error procesando: {e}")
            
            # Test 3: Estadísticas
            try:
                stats = pipeline.get_pipeline_stats()
                result.add_result('total_processed' in stats)
            except Exception as e:
                result.add_result(False, f"Error obteniendo stats: {e}")
        
        except ImportError:
            result.add_result(False, "Módulo pipeline no disponible")
        
        result.duration = time.time() - start_time
        self.results['pipeline'] = result
        return result
    
    def test_config_manager(self) -> ModuleTestResult:
        """Tests para gestor de configuración."""
        result = ModuleTestResult("config_manager")
        start_time = time.time()
        
        try:
            from core.config_manager import ConfigManager, ModuleType
            
            # Test 1: Crear gestor
            try:
                manager = ConfigManager()
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error creando gestor: {e}")
                return result
            
            # Test 2: Obtener configuración
            try:
                config = manager.get_config(ModuleType.MEMORY)
                result.add_result('memory_dim' in config)
            except Exception as e:
                result.add_result(False, f"Error obteniendo config: {e}")
            
            # Test 3: Actualizar configuración
            try:
                manager.update_config(ModuleType.MEMORY, memory_dim=1024)
                config = manager.get_config(ModuleType.MEMORY)
                result.add_result(config['memory_dim'] == 1024)
            except Exception as e:
                result.add_result(False, f"Error actualizando config: {e}")
            
            # Test 4: Validar
            try:
                valid, errors = manager.validate_config(ModuleType.MEMORY)
                result.add_result(isinstance(valid, bool))
            except Exception as e:
                result.add_result(False, f"Error validando: {e}")
        
        except ImportError:
            result.add_result(False, "Módulo config_manager no disponible")
        
        result.duration = time.time() - start_time
        self.results['config_manager'] = result
        return result
    
    def test_monitoring_system(self) -> ModuleTestResult:
        """Tests para sistema de monitoreo."""
        result = ModuleTestResult("monitoring")
        start_time = time.time()
        
        try:
            from monitoring_system import get_system_monitor
            
            # Test 1: Obtener monitor
            try:
                monitor = get_system_monitor()
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error obteniendo monitor: {e}")
                return result
            
            # Test 2: Registrar métricas
            try:
                monitor.metrics_collector.increment("test.counter")
                monitor.metrics_collector.set_gauge("test.gauge", 0.5)
                result.add_result(True)
            except Exception as e:
                result.add_result(False, f"Error registrando métricas: {e}")
            
            # Test 3: Health checks
            try:
                health = monitor.health_monitor.get_overall_health()
                result.add_result('status' in health)
            except Exception as e:
                result.add_result(False, f"Error health checks: {e}")
            
            # Test 4: Estado del sistema
            try:
                status = monitor.get_system_status()
                result.add_result('health' in status and 'metrics' in status)
            except Exception as e:
                result.add_result(False, f"Error obteniendo estado: {e}")
        
        except ImportError:
            result.add_result(False, "Módulo monitoring no disponible")
        
        result.duration = time.time() - start_time
        self.results['monitoring'] = result
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Ejecuta todos los tests.
        
        Returns:
            Diccionario con resultados
        """
        logger.info("Ejecutando todos los tests...")
        
        self.test_memory_module()
        self.test_redundancy_module()
        self.test_pipeline_module()
        self.test_config_manager()
        self.test_monitoring_system()
        
        # Resumen
        total_passed = sum(r.tests_passed for r in self.results.values())
        total_failed = sum(r.tests_failed for r in self.results.values())
        total_tests = sum(r.tests_total for r in self.results.values())
        total_duration = sum(r.duration for r in self.results.values())
        
        summary = {
            'timestamp': time.time(),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'success_rate': total_passed / total_tests if total_tests > 0 else 0.0,
            'total_duration': total_duration,
            'modules': {k: v.to_dict() for k, v in self.results.items()}
        }
        
        logger.info(f"Tests completados: {total_passed}/{total_tests} pasaron")
        
        return summary
    
    def export_results(self, filepath: str) -> bool:
        """
        Exporta resultados a archivo.
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            True si se exportó exitosamente
        """
        try:
            summary = {
                'timestamp': time.time(),
                'modules': {k: v.to_dict() for k, v in self.results.items()}
            }
            
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Resultados exportados a {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exportando resultados: {e}")
            return False


def run_tests(output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Función helper para ejecutar todos los tests.
    
    Args:
        output_file: Archivo para exportar resultados (opcional)
    
    Returns:
        Diccionario con resultados
    """
    suite = IntegratedTestSuite()
    results = suite.run_all_tests()
    
    if output_file:
        suite.export_results(output_file)
    
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Ejecutando Suite de Tests Integrada")
    print("=" * 60 + "\n")
    
    suite = IntegratedTestSuite()
    results = suite.run_all_tests()
    
    print("\n" + "=" * 60)
    print("Resumen de Tests")
    print("=" * 60)
    print(f"Total tests: {results['total_tests']}")
    print(f"Pasados: {results['total_passed']}")
    print(f"Fallidos: {results['total_failed']}")
    print(f"Tasa de éxito: {results['success_rate']:.2%}")
    print(f"Duración total: {results['total_duration']:.2f}s")
    
    print("\nPor módulo:")
    for module, module_results in results['modules'].items():
        print(f"  {module}: {module_results['passed']}/{module_results['total']} "
              f"({module_results['success_rate']:.2%})")
    
    # Exportar resultados
    suite.export_results("test_results.json")
    print("\n✅ Resultados exportados a test_results.json")


