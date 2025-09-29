#!/usr/bin/env python3
"""
Sistema Maestro de Gestión - Integración completa del sistema de organización empresarial
"""

import os
import sys
import subprocess
from datetime import datetime

class SystemManager:
    def __init__(self, base_path="/Users/adan/frontier"):
        self.base_path = base_path
        self.tools = {
            'search': 'search_documents.py',
            'organize': 'auto_organize.py',
            'backup': 'backup_system.py',
            'analytics': 'analytics_system.py',
            'maintenance': 'maintenance_system.py'
        }
    
    def run_tool(self, tool_name, *args):
        """Ejecutar herramienta específica"""
        if tool_name not in self.tools:
            print(f"❌ Herramienta no encontrada: {tool_name}")
            return False
        
        tool_path = os.path.join(self.base_path, self.tools[tool_name])
        if not os.path.exists(tool_path):
            print(f"❌ Archivo de herramienta no encontrado: {tool_path}")
            return False
        
        try:
            # Ejecutar herramienta
            cmd = [sys.executable, tool_path] + list(args)
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"❌ Error ejecutando {tool_name}: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error ejecutando {tool_name}: {e}")
            return False
    
    def show_system_status(self):
        """Mostrar estado del sistema"""
        print("🏢 SISTEMA DE ORGANIZACIÓN EMPRESARIAL - ESTADO ACTUAL")
        print("=" * 60)
        
        # Verificar archivos de sistema
        system_files = [
            'README.md', 'NAVIGATION.md', 'DASHBOARD.md',
            'ORGANIZATION_SUMMARY.md', 'FINAL_ORGANIZATION_REPORT.md'
        ]
        
        print("📋 Archivos de Sistema:")
        for file in system_files:
            status = "✅" if os.path.exists(os.path.join(self.base_path, file)) else "❌"
            print(f"   {status} {file}")
        
        # Verificar herramientas
        print("\n🛠️ Herramientas Disponibles:")
        for tool_name, tool_file in self.tools.items():
            status = "✅" if os.path.exists(os.path.join(self.base_path, tool_file)) else "❌"
            print(f"   {status} {tool_name}: {tool_file}")
        
        # Verificar áreas de negocio
        business_areas = [
            '01_Marketing', '02_Finance', '03_Human_Resources', '04_Operations',
            '05_Technology', '06_Strategy', '07_Risk_Management', '08_AI_Artificial_Intelligence',
            '09_Sales', '10_Customer_Service', '11_Research_Development', '12_Quality_Assurance',
            '13_Legal_Compliance', '14_Procurement', '15_Logistics', '16_Data_Analytics',
            '17_Innovation', '18_Sustainability', '19_International_Business', '20_Project_Management'
        ]
        
        print(f"\n🏢 Áreas de Negocio ({len(business_areas)}):")
        active_areas = 0
        for area in business_areas:
            area_path = os.path.join(self.base_path, area)
            if os.path.exists(area_path):
                # Contar archivos
                file_count = 0
                for root, dirs, files in os.walk(area_path):
                    file_count += len([f for f in files if f.endswith('.md')])
                
                if file_count > 0:
                    active_areas += 1
                    print(f"   ✅ {area}: {file_count} archivos")
                else:
                    print(f"   ⚠️  {area}: 0 archivos")
            else:
                print(f"   ❌ {area}: No existe")
        
        print(f"\n📊 Resumen: {active_areas}/{len(business_areas)} áreas activas")
    
    def show_main_menu(self):
        """Mostrar menú principal"""
        print("\n🎯 SISTEMA MAESTRO DE GESTIÓN EMPRESARIAL")
        print("=" * 50)
        print("1. 🔍 Búsqueda de Documentos")
        print("2. 📁 Organización Automática")
        print("3. 💾 Sistema de Backup")
        print("4. 📊 Analytics Avanzado")
        print("5. 🔧 Mantenimiento del Sistema")
        print("6. 📋 Estado del Sistema")
        print("7. 🚀 Ejecutar Mantenimiento Completo")
        print("8. 📖 Ver Documentación")
        print("9. ❌ Salir")
    
    def run_search_system(self):
        """Ejecutar sistema de búsqueda"""
        print("\n🔍 SISTEMA DE BÚSQUEDA DE DOCUMENTOS")
        print("=" * 40)
        return self.run_tool('search')
    
    def run_organization_system(self):
        """Ejecutar sistema de organización"""
        print("\n📁 SISTEMA DE ORGANIZACIÓN AUTOMÁTICA")
        print("=" * 40)
        return self.run_tool('organize')
    
    def run_backup_system(self):
        """Ejecutar sistema de backup"""
        print("\n💾 SISTEMA DE BACKUP Y RECUPERACIÓN")
        print("=" * 40)
        return self.run_tool('backup')
    
    def run_analytics_system(self):
        """Ejecutar sistema de analytics"""
        print("\n📊 SISTEMA DE ANALYTICS AVANZADO")
        print("=" * 40)
        return self.run_tool('analytics')
    
    def run_maintenance_system(self):
        """Ejecutar sistema de mantenimiento"""
        print("\n🔧 SISTEMA DE MANTENIMIENTO")
        print("=" * 40)
        return self.run_tool('maintenance')
    
    def run_complete_maintenance(self):
        """Ejecutar mantenimiento completo"""
        print("\n🚀 MANTENIMIENTO COMPLETO DEL SISTEMA")
        print("=" * 50)
        
        steps = [
            ("Verificando estado del sistema", lambda: self.show_system_status()),
            ("Ejecutando organización automática", lambda: self.run_tool('organize')),
            ("Ejecutando analytics", lambda: self.run_tool('analytics')),
            ("Ejecutando mantenimiento", lambda: self.run_tool('maintenance')),
            ("Creando backup", lambda: self.run_tool('backup'))
        ]
        
        for step_name, step_function in steps:
            print(f"\n🔄 {step_name}...")
            try:
                step_function()
                print(f"✅ {step_name} completado")
            except Exception as e:
                print(f"❌ Error en {step_name}: {e}")
        
        print("\n🎉 Mantenimiento completo finalizado!")
    
    def show_documentation(self):
        """Mostrar documentación del sistema"""
        print("\n📖 DOCUMENTACIÓN DEL SISTEMA")
        print("=" * 40)
        
        docs = [
            ("README.md", "Punto de entrada principal del sistema"),
            ("NAVIGATION.md", "Navegación completa por áreas de negocio"),
            ("DASHBOARD.md", "Métricas y KPIs en tiempo real"),
            ("ORGANIZATION_SUMMARY.md", "Resumen ejecutivo de la organización"),
            ("FINAL_ORGANIZATION_REPORT.md", "Reporte completo del sistema")
        ]
        
        print("📋 Documentos disponibles:")
        for doc, description in docs:
            status = "✅" if os.path.exists(os.path.join(self.base_path, doc)) else "❌"
            print(f"   {status} {doc}: {description}")
        
        print("\n🛠️ Herramientas disponibles:")
        for tool_name, tool_file in self.tools.items():
            status = "✅" if os.path.exists(os.path.join(self.base_path, tool_file)) else "❌"
            print(f"   {status} {tool_name}: {tool_file}")
        
        print("\n💡 Uso recomendado:")
        print("   1. Comience con README.md para entender el sistema")
        print("   2. Use NAVIGATION.md para explorar áreas de negocio")
        print("   3. Consulte DASHBOARD.md para métricas actuales")
        print("   4. Use las herramientas según sus necesidades")
    
    def run(self):
        """Ejecutar sistema maestro"""
        while True:
            self.show_main_menu()
            choice = input("\nSeleccione una opción (1-9): ").strip()
            
            if choice == '1':
                self.run_search_system()
            elif choice == '2':
                self.run_organization_system()
            elif choice == '3':
                self.run_backup_system()
            elif choice == '4':
                self.run_analytics_system()
            elif choice == '5':
                self.run_maintenance_system()
            elif choice == '6':
                self.show_system_status()
            elif choice == '7':
                self.run_complete_maintenance()
            elif choice == '8':
                self.show_documentation()
            elif choice == '9':
                print("\n👋 ¡Gracias por usar el Sistema de Organización Empresarial!")
                break
            else:
                print("❌ Opción no válida. Intente nuevamente.")
            
            input("\nPresione Enter para continuar...")

def main():
    manager = SystemManager()
    
    print("🏢 SISTEMA MAESTRO DE ORGANIZACIÓN EMPRESARIAL")
    print("=" * 60)
    print("Bienvenido al sistema integrado de gestión empresarial")
    print("Con 717 archivos organizados en 20 áreas de negocio")
    print("=" * 60)
    
    manager.run()

if __name__ == "__main__":
    main()
