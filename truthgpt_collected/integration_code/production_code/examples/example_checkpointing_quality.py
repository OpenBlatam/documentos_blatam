#!/usr/bin/env python3
"""
Ejemplo de Uso del Sistema de Checkpointing y Quality Assurance
================================================================

Este script demuestra cómo usar las nuevas utilidades de checkpointing
y quality assurance.
"""

import torch
from pathlib import Path

from core import (
    CheckpointManager,
    save_checkpoint,
    load_checkpoint,
    check_module_quality,
    QualityChecker
)


def example_checkpoint_manager():
    """Ejemplo: Uso de CheckpointManager."""
    print("=" * 60)
    print("EJEMPLO 1: CheckpointManager")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        manager = CheckpointManager(
            checkpoint_dir='example_checkpoints/',
            max_checkpoints=3,
            keep_best=True,
            metric_name='loss',
            mode='min'
        )
        
        print("\n📊 Guardando checkpoints:")
        for epoch in range(3):
            loss = 1.0 - epoch * 0.2
            metrics = {'loss': loss, 'accuracy': 0.5 + epoch * 0.1}
            
            path = manager.save_checkpoint(
                module,
                epoch=epoch,
                step=epoch * 100,
                loss=loss,
                metrics=metrics
            )
            print(f"  ✓ Epoch {epoch}: {Path(path).name} (loss={loss:.2f})")
        
        print(f"\n📊 Mejor checkpoint: {manager.best_checkpoint}")
        print(f"📊 Mejor métrica: {manager.best_metric}")
        
        print("\n📊 Listando checkpoints:")
        checkpoints = manager.list_checkpoints()
        for ckpt in checkpoints:
            print(f"  - {Path(ckpt.checkpoint_path).name}: loss={ckpt.loss:.2f}")
        
        print("\n📊 Cargando mejor checkpoint:")
        checkpoint = manager.load_checkpoint(load_best=True)
        print(f"  ✓ Cargado: epoch={checkpoint['epoch']}, loss={checkpoint['loss']:.2f}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_simple_checkpointing():
    """Ejemplo: Checkpointing simple."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Checkpointing Simple")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        print("\n📊 Guardando checkpoint:")
        path = save_checkpoint(
            module,
            'example_simple.pt',
            epoch=10,
            step=1000,
            loss=0.5,
            metrics={'accuracy': 0.95}
        )
        print(f"  ✓ Guardado: {path}")
        
        print("\n📊 Cargando checkpoint:")
        checkpoint = load_checkpoint('example_simple.pt', device='cpu')
        print(f"  ✓ Cargado: epoch={checkpoint['epoch']}, loss={checkpoint['loss']:.2f}")
        print(f"  ✓ Model class: {checkpoint['model_class']}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_quality_check():
    """Ejemplo: Verificación de calidad."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Verificación de Calidad")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        hidden_states = torch.randn(2, 64, 512)
        
        print("\n📊 Verificando calidad del módulo:")
        report = check_module_quality(module, hidden_states)
        
        print(f"\n📈 Score: {report.score:.2f}")
        print(f"📈 Passed: {report.passed}")
        print(f"📈 Issues: {len(report.issues)}")
        print(f"📈 Warnings: {len(report.warnings)}")
        
        if report.issues:
            print("\n❌ Errores encontrados:")
            for issue in report.issues:
                print(f"  - [{issue.category}] {issue.message}")
                if issue.suggestion:
                    print(f"    → {issue.suggestion}")
        
        if report.warnings:
            print("\n⚠️ Advertencias:")
            for warning in report.warnings:
                print(f"  - [{warning.category}] {warning.message}")
                if warning.suggestion:
                    print(f"    → {warning.suggestion}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


def example_detailed_quality_check():
    """Ejemplo: Verificación detallada de calidad."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Verificación Detallada")
    print("=" * 60)
    
    try:
        from research.paper_malto import MaltoModule, MaltoConfig
        
        config = MaltoConfig(hidden_dim=512)
        module = MaltoModule(config)
        
        hidden_states = torch.randn(2, 64, 512)
        
        print("\n📊 Verificación detallada:")
        checker = QualityChecker()
        report = checker.check_module(module, hidden_states)
        
        print(f"\n📊 Resumen:")
        print(f"  - Módulo: {report.module_name}")
        print(f"  - Score: {report.score:.2f}")
        print(f"  - Passed: {report.passed}")
        
        print(f"\n📊 Desglose:")
        print(f"  - Errores: {len(report.issues)}")
        print(f"  - Advertencias: {len(report.warnings)}")
        
        if report.issues:
            print("\n❌ Errores por categoría:")
            by_category = {}
            for issue in report.issues:
                if issue.category not in by_category:
                    by_category[issue.category] = []
                by_category[issue.category].append(issue)
            
            for category, issues in by_category.items():
                print(f"  {category}: {len(issues)}")
                for issue in issues:
                    print(f"    - {issue.message}")
        
    except ImportError as e:
        print(f"  ⚠️ No se pudo importar módulo de ejemplo: {e}")


if __name__ == "__main__":
    print("\n🚀 EJEMPLOS DE CHECKPOINTING Y QUALITY ASSURANCE\n")
    
    try:
        example_checkpoint_manager()
    except Exception as e:
        print(f"Error en ejemplo 1: {e}")
    
    try:
        example_simple_checkpointing()
    except Exception as e:
        print(f"Error en ejemplo 2: {e}")
    
    try:
        example_quality_check()
    except Exception as e:
        print(f"Error en ejemplo 3: {e}")
    
    try:
        example_detailed_quality_check()
    except Exception as e:
        print(f"Error en ejemplo 4: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados")
    print("=" * 60)


