#!/usr/bin/env python3
"""
Sistema de Automatización Programada - Ejecuta conversiones automáticamente
según horarios y condiciones configuradas.
"""

import os
import json
import schedule
import time
from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path

class AutomatizadorDocumentos:
    """Clase para automatizar la generación de documentos"""
    
    def __init__(self, config_path='config_automatizacion.json'):
        self.config_path = config_path
        self.directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
        self.config = self.cargar_config()
        self.log_file = os.path.join(self.directorio, 'log_automatizacion.txt')
        
    def cargar_config(self):
        """Carga configuración desde JSON"""
        config_default = {
            'horarios': {
                'diario': '09:00',
                'semanal': 'lunes 08:00',
                'mensual': '1 07:00'
            },
            'scripts_a_ejecutar': [
                'convertir_completo_ultra_premium.py',
                'analisis_predictivo_avanzado.py',
                'mejoras_avanzadas_analisis.py'
            ],
            'notificaciones': {
                'email': False,
                'archivo_log': True
            },
            'condiciones': {
                'solo_dias_laborables': True,
                'horario_activo': {'inicio': '08:00', 'fin': '20:00'}
            }
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            self.guardar_config(config_default)
            return config_default
    
    def guardar_config(self, config):
        """Guarda configuración en JSON"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def log(self, mensaje):
        """Registra mensaje en log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {mensaje}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
        
        print(log_line.strip())
    
    def es_dia_laborable(self):
        """Verifica si es día laborable"""
        hoy = datetime.now()
        return hoy.weekday() < 5  # 0-4 = Lunes-Viernes
    
    def esta_en_horario_activo(self):
        """Verifica si está en horario activo"""
        ahora = datetime.now().time()
        inicio = datetime.strptime(self.config['condiciones']['horario_activo']['inicio'], '%H:%M').time()
        fin = datetime.strptime(self.config['condiciones']['horario_activo']['fin'], '%H:%M').time()
        return inicio <= ahora <= fin
    
    def ejecutar_script(self, script_name):
        """Ejecuta un script específico"""
        script_path = os.path.join(self.directorio, script_name)
        
        if not os.path.exists(script_path):
            self.log(f"⚠️  Script no encontrado: {script_name}")
            return False
        
        try:
            self.log(f"🔄 Ejecutando: {script_name}")
            inicio = datetime.now()
            
            resultado = subprocess.run(
                [sys.executable, script_path],
                cwd=self.directorio,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            fin = datetime.now()
            duracion = (fin - inicio).total_seconds()
            
            if resultado.returncode == 0:
                self.log(f"✅ {script_name} completado en {duracion:.1f}s")
                return True
            else:
                self.log(f"❌ {script_name} falló: {resultado.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏱️  {script_name} - Tiempo agotado")
            return False
        except Exception as e:
            self.log(f"❌ Error ejecutando {script_name}: {e}")
            return False
    
    def ejecutar_todos_los_scripts(self):
        """Ejecuta todos los scripts configurados"""
        if self.config['condiciones']['solo_dias_laborables'] and not self.es_dia_laborable():
            self.log("⏸️  No es día laborable, saltando ejecución")
            return
        
        if not self.esta_en_horario_activo():
            self.log("⏸️  Fuera de horario activo, saltando ejecución")
            return
        
        self.log("="*70)
        self.log("🚀 INICIANDO EJECUCIÓN AUTOMÁTICA")
        self.log("="*70)
        
        resultados = []
        for script in self.config['scripts_a_ejecutar']:
            exito = self.ejecutar_script(script)
            resultados.append({'script': script, 'exito': exito})
        
        self.log("="*70)
        self.log(f"✅ Ejecución completada: {sum(1 for r in resultados if r['exito'])}/{len(resultados)} exitosos")
        self.log("="*70)
        
        return resultados
    
    def programar_tareas(self):
        """Programa las tareas según configuración"""
        # Tarea diaria
        if 'diario' in self.config['horarios']:
            schedule.every().day.at(self.config['horarios']['diario']).do(
                self.ejecutar_todos_los_scripts
            )
            self.log(f"📅 Tarea diaria programada: {self.config['horarios']['diario']}")
        
        # Tarea semanal
        if 'semanal' in self.config['horarios']:
            dia, hora = self.config['horarios']['semanal'].split()
            dias_semana = {
                'lunes': schedule.every().monday,
                'martes': schedule.every().tuesday,
                'miercoles': schedule.every().wednesday,
                'miércoles': schedule.every().wednesday,
                'jueves': schedule.every().thursday,
                'viernes': schedule.every().friday,
                'sabado': schedule.every().saturday,
                'sábado': schedule.every().saturday,
                'domingo': schedule.every().sunday
            }
            if dia.lower() in dias_semana:
                dias_semana[dia.lower()].at(hora).do(self.ejecutar_todos_los_scripts)
                self.log(f"📅 Tarea semanal programada: {dia} a las {hora}")
        
        # Tarea mensual
        if 'mensual' in self.config['horarios']:
            dia, hora = self.config['horarios']['mensual'].split()
            schedule.every().month.do(self.ejecutar_todos_los_scripts)
            self.log(f"📅 Tarea mensual programada: día {dia} a las {hora}")
    
    def ejecutar_ahora(self):
        """Ejecuta inmediatamente"""
        return self.ejecutar_todos_los_scripts()
    
    def iniciar_monitoreo(self):
        """Inicia el monitoreo continuo"""
        self.log("="*70)
        self.log("🤖 SISTEMA DE AUTOMATIZACIÓN INICIADO")
        self.log("="*70)
        
        self.programar_tareas()
        
        self.log("\n📋 Tareas programadas:")
        for job in schedule.jobs:
            self.log(f"   • {job}")
        
        self.log("\n⏳ Monitoreo activo. Presiona Ctrl+C para detener.\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            self.log("\n🛑 Sistema detenido por el usuario")

def main():
    """Función principal"""
    automatizador = AutomatizadorDocumentos()
    
    import argparse
    parser = argparse.ArgumentParser(description='Sistema de Automatización de Documentos')
    parser.add_argument('--ejecutar-ahora', action='store_true', 
                       help='Ejecuta inmediatamente sin programar')
    parser.add_argument('--monitoreo', action='store_true',
                       help='Inicia monitoreo continuo')
    
    args = parser.parse_args()
    
    if args.ejecutar_ahora:
        automatizador.ejecutar_ahora()
    elif args.monitoreo:
        automatizador.iniciar_monitoreo()
    else:
        print("Uso:")
        print("  python3 sistema_automatizacion_programada.py --ejecutar-ahora")
        print("  python3 sistema_automatizacion_programada.py --monitoreo")
        print("\nO ejecuta sin argumentos para ver esta ayuda")

if __name__ == "__main__":
    main()



