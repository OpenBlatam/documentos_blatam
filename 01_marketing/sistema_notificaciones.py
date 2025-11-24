#!/usr/bin/env python3
"""
Sistema de Notificaciones - Envía notificaciones sobre eventos del sistema
y estado de procesos.
"""

import os
import json
from datetime import datetime
from pathlib import Path

class SistemaNotificaciones:
    """Sistema de notificaciones"""
    
    def __init__(self):
        self.directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
        self.archivo_log = os.path.join(self.directorio, 'notificaciones.log')
        self.archivo_config = os.path.join(self.directorio, 'config_notificaciones.json')
        self.config = self.cargar_config()
    
    def cargar_config(self):
        """Carga configuración"""
        config_default = {
            'notificaciones_activas': True,
            'niveles': ['info', 'warning', 'error', 'success'],
            'canales': {
                'archivo_log': True,
                'consola': True,
                'email': False,
                'webhook': False
            },
            'formato': 'detallado'
        }
        
        if os.path.exists(self.archivo_config):
            with open(self.archivo_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            self.guardar_config(config_default)
            return config_default
    
    def guardar_config(self, config):
        """Guarda configuración"""
        with open(self.archivo_config, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def notificar(self, nivel, mensaje, detalles=None):
        """Envía una notificación"""
        if not self.config['notificaciones_activas']:
            return
        
        if nivel not in self.config['niveles']:
            return
        
        notificacion = {
            'timestamp': datetime.now().isoformat(),
            'nivel': nivel,
            'mensaje': mensaje,
            'detalles': detalles or {}
        }
        
        # Formatear mensaje
        emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }.get(nivel, '📢')
        
        mensaje_formateado = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {emoji} [{nivel.upper()}] {mensaje}"
        
        # Canal: Consola
        if self.config['canales']['consola']:
            print(mensaje_formateado)
            if detalles:
                for key, value in detalles.items():
                    print(f"   {key}: {value}")
        
        # Canal: Archivo log
        if self.config['canales']['archivo_log']:
            with open(self.archivo_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(notificacion, ensure_ascii=False) + '\n')
        
        # Canal: Email (simulado)
        if self.config['canales']['email']:
            self._enviar_email(notificacion)
        
        # Canal: Webhook (simulado)
        if self.config['canales']['webhook']:
            self._enviar_webhook(notificacion)
        
        return notificacion
    
    def _enviar_email(self, notificacion):
        """Simula envío de email"""
        # En implementación real, usaría smtplib o servicio de email
        print(f"📧 [EMAIL] {notificacion['mensaje']}")
    
    def _enviar_webhook(self, notificacion):
        """Simula envío de webhook"""
        # En implementación real, usaría requests para enviar a webhook
        print(f"🔗 [WEBHOOK] {notificacion['mensaje']}")
    
    def notificar_exito(self, mensaje, detalles=None):
        """Notificación de éxito"""
        return self.notificar('success', mensaje, detalles)
    
    def notificar_info(self, mensaje, detalles=None):
        """Notificación informativa"""
        return self.notificar('info', mensaje, detalles)
    
    def notificar_advertencia(self, mensaje, detalles=None):
        """Notificación de advertencia"""
        return self.notificar('warning', mensaje, detalles)
    
    def notificar_error(self, mensaje, detalles=None):
        """Notificación de error"""
        return self.notificar('error', mensaje, detalles)
    
    def notificar_proceso_iniciado(self, nombre_proceso):
        """Notifica inicio de proceso"""
        return self.notificar_info(f"Proceso iniciado: {nombre_proceso}")
    
    def notificar_proceso_completado(self, nombre_proceso, duracion=None):
        """Notifica finalización de proceso"""
        detalles = {}
        if duracion:
            detalles['duracion_segundos'] = duracion
        return self.notificar_exito(f"Proceso completado: {nombre_proceso}", detalles)
    
    def notificar_proceso_fallido(self, nombre_proceso, error=None):
        """Notifica fallo de proceso"""
        detalles = {}
        if error:
            detalles['error'] = str(error)
        return self.notificar_error(f"Proceso fallido: {nombre_proceso}", detalles)
    
    def obtener_notificaciones_recientes(self, limite=50):
        """Obtiene notificaciones recientes"""
        if not os.path.exists(self.archivo_log):
            return []
        
        notificaciones = []
        try:
            with open(self.archivo_log, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
                for linea in lineas[-limite:]:
                    try:
                        notificacion = json.loads(linea.strip())
                        notificaciones.append(notificacion)
                    except:
                        pass
        except:
            pass
        
        return notificaciones[::-1]  # Más recientes primero
    
    def generar_resumen_notificaciones(self):
        """Genera resumen de notificaciones"""
        notificaciones = self.obtener_notificaciones_recientes(1000)
        
        if not notificaciones:
            return {
                'total': 0,
                'por_nivel': {},
                'ultimas_24h': 0
            }
        
        resumen = {
            'total': len(notificaciones),
            'por_nivel': {},
            'ultimas_24h': 0
        }
        
        fecha_limite = datetime.now().timestamp() - 86400  # 24 horas
        
        for notif in notificaciones:
            nivel = notif.get('nivel', 'unknown')
            resumen['por_nivel'][nivel] = resumen['por_nivel'].get(nivel, 0) + 1
            
            try:
                timestamp = datetime.fromisoformat(notif['timestamp']).timestamp()
                if timestamp > fecha_limite:
                    resumen['ultimas_24h'] += 1
            except:
                pass
        
        return resumen

def main():
    """Función principal - Ejemplo de uso"""
    sistema = SistemaNotificaciones()
    
    print("🔔 SISTEMA DE NOTIFICACIONES")
    print("="*70)
    
    # Ejemplos de notificaciones
    sistema.notificar_proceso_iniciado("Generación de documentos")
    sistema.notificar_info("Procesando 10 archivos", {'archivos': 10})
    sistema.notificar_exito("Documento generado", {'archivo': 'reporte.xlsx'})
    sistema.notificar_advertencia("Tamaño de archivo grande", {'tamaño_mb': 15})
    sistema.notificar_proceso_completado("Generación de documentos", duracion=45.2)
    
    # Resumen
    resumen = sistema.generar_resumen_notificaciones()
    print(f"\n📊 Resumen:")
    print(f"   Total notificaciones: {resumen['total']}")
    print(f"   Últimas 24h: {resumen['ultimas_24h']}")
    print(f"   Por nivel: {resumen['por_nivel']}")

if __name__ == "__main__":
    main()



