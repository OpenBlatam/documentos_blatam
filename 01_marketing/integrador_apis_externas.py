#!/usr/bin/env python3
"""
Integrador de APIs Externas - Integra el sistema con APIs externas
para enriquecer documentos con datos en tiempo real.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

class IntegradorAPIs:
    """Integra con APIs externas"""
    
    def __init__(self):
        self.directorio = '/Users/adan/Documents/documentos_blatam/01_marketing'
        self.archivo_config = os.path.join(self.directorio, 'config_apis.json')
        self.config = self.cargar_config()
    
    def cargar_config(self):
        """Carga configuración de APIs"""
        config_default = {
            'apis_activas': {
                'exchange_rate': False,
                'weather': False,
                'news': False,
                'stock': False
            },
            'api_keys': {
                'exchange_rate': '',
                'weather': '',
                'news': '',
                'stock': ''
            },
            'timeout': 10,
            'cache_minutos': 60
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
    
    def obtener_tipo_cambio(self, moneda_origen='USD', moneda_destino='EUR'):
        """Obtiene tipo de cambio (simulado)"""
        if not self.config['apis_activas']['exchange_rate']:
            # Datos simulados
            tipos_cambio = {
                'USD_EUR': 0.85,
                'USD_GBP': 0.73,
                'USD_JPY': 110.0,
                'USD_MXN': 20.0
            }
            clave = f"{moneda_origen}_{moneda_destino}"
            return {
                'moneda_origen': moneda_origen,
                'moneda_destino': moneda_destino,
                'tipo_cambio': tipos_cambio.get(clave, 1.0),
                'fecha': datetime.now().isoformat(),
                'fuente': 'simulado'
            }
        
        # En implementación real, usaría API como exchangerate-api.com
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{moneda_origen}"
            response = requests.get(url, timeout=self.config['timeout'])
            data = response.json()
            return {
                'moneda_origen': moneda_origen,
                'moneda_destino': moneda_destino,
                'tipo_cambio': data['rates'].get(moneda_destino, 1.0),
                'fecha': datetime.now().isoformat(),
                'fuente': 'api'
            }
        except Exception as e:
            print(f"⚠️  Error obteniendo tipo de cambio: {e}")
            return None
    
    def obtener_clima(self, ciudad='Madrid'):
        """Obtiene datos del clima (simulado)"""
        if not self.config['apis_activas']['weather']:
            # Datos simulados
            return {
                'ciudad': ciudad,
                'temperatura': 22,
                'descripcion': 'Parcialmente nublado',
                'humedad': 65,
                'viento': 15,
                'fecha': datetime.now().isoformat(),
                'fuente': 'simulado'
            }
        
        # En implementación real, usaría OpenWeatherMap API
        try:
            api_key = self.config['api_keys']['weather']
            url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=self.config['timeout'])
            data = response.json()
            return {
                'ciudad': ciudad,
                'temperatura': data['main']['temp'],
                'descripcion': data['weather'][0]['description'],
                'humedad': data['main']['humidity'],
                'viento': data['wind']['speed'],
                'fecha': datetime.now().isoformat(),
                'fuente': 'api'
            }
        except Exception as e:
            print(f"⚠️  Error obteniendo clima: {e}")
            return None
    
    def obtener_noticias(self, tema='tecnologia', limite=5):
        """Obtiene noticias (simulado)"""
        if not self.config['apis_activas']['news']:
            # Datos simulados
            noticias = [
                {'titulo': 'Avances en IA', 'fecha': '2025-11-22', 'fuente': 'Tech News'},
                {'titulo': 'Nuevas tendencias en marketing', 'fecha': '2025-11-21', 'fuente': 'Marketing Today'},
                {'titulo': 'Innovación en documentos', 'fecha': '2025-11-20', 'fuente': 'Business Weekly'}
            ]
            return {
                'tema': tema,
                'noticias': noticias[:limite],
                'fecha': datetime.now().isoformat(),
                'fuente': 'simulado'
            }
        
        # En implementación real, usaría NewsAPI
        return None
    
    def obtener_datos_accion(self, simbolo='AAPL'):
        """Obtiene datos de acciones (simulado)"""
        if not self.config['apis_activas']['stock']:
            # Datos simulados
            return {
                'simbolo': simbolo,
                'precio': 150.25,
                'cambio': 2.5,
                'cambio_porcentual': 1.69,
                'volumen': 50000000,
                'fecha': datetime.now().isoformat(),
                'fuente': 'simulado'
            }
        
        # En implementación real, usaría Alpha Vantage o similar
        return None
    
    def generar_datos_enriquecidos(self):
        """Genera conjunto de datos enriquecidos con APIs"""
        datos = {
            'fecha': datetime.now().isoformat(),
            'tipos_cambio': {},
            'clima': {},
            'noticias': None,
            'acciones': {}
        }
        
        # Tipos de cambio
        monedas = [('USD', 'EUR'), ('USD', 'GBP'), ('USD', 'MXN')]
        for origen, destino in monedas:
            cambio = self.obtener_tipo_cambio(origen, destino)
            if cambio:
                datos['tipos_cambio'][f"{origen}_{destino}"] = cambio
        
        # Clima
        ciudades = ['Madrid', 'Barcelona', 'México DF']
        for ciudad in ciudades:
            clima = self.obtener_clima(ciudad)
            if clima:
                datos['clima'][ciudad] = clima
        
        # Noticias
        datos['noticias'] = self.obtener_noticias('tecnologia', 5)
        
        # Acciones
        simbolos = ['AAPL', 'GOOGL', 'MSFT']
        for simbolo in simbolos:
            accion = self.obtener_datos_accion(simbolo)
            if accion:
                datos['acciones'][simbolo] = accion
        
        return datos
    
    def guardar_datos_enriquecidos(self, datos, archivo_salida=None):
        """Guarda datos enriquecidos"""
        if archivo_salida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = os.path.join(
                self.directorio,
                f'DATOS_ENRIQUECIDOS_{timestamp}.json'
            )
        
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Datos enriquecidos guardados: {archivo_salida}")
        return archivo_salida

def main():
    """Función principal"""
    integrador = IntegradorAPIs()
    
    print("🌐 INTEGRADOR DE APIs EXTERNAS")
    print("="*70)
    print("\n📊 Obteniendo datos de APIs externas...\n")
    
    # Generar datos enriquecidos
    datos = integrador.generar_datos_enriquecidos()
    
    # Guardar
    archivo = integrador.guardar_datos_enriquecidos(datos)
    
    # Mostrar resumen
    print("\n📋 Resumen de datos obtenidos:")
    print(f"   Tipos de cambio: {len(datos['tipos_cambio'])}")
    print(f"   Datos de clima: {len(datos['clima'])}")
    print(f"   Noticias: {len(datos['noticias']['noticias']) if datos['noticias'] else 0}")
    print(f"   Acciones: {len(datos['acciones'])}")
    
    print(f"\n✅ Integración completada!")
    print(f"📁 Archivo: {archivo}")

if __name__ == "__main__":
    main()








