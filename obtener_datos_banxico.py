#!/usr/bin/env python3
"""
Script para obtener datos económicos del Banco de México (Banxico)
para completar la Actividad 1: Análisis de Indicadores Económicos

Este script utiliza la API del Sistema de Información Económica (SIE) de Banxico
para obtener datos de:
- Inflación (INPC)
- Tipo de cambio peso-dólar
- Tasa de interés (TIIE 28 días)
- Divisas internacionales

Requisitos:
    pip install requests pandas openpyxl

Nota: Para usar la API de Banxico, necesitas registrarte y obtener un token en:
https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CF107&locale=es
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class ObtenerDatosBanxico:
    """Clase para obtener datos del Banco de México"""
    
    def __init__(self, token=None):
        """
        Inicializa la clase
        
        Args:
            token: Token de API de Banxico (opcional, pero recomendado)
        """
        self.base_url = "https://www.banxico.org.mx/SieAPIRest/service/v1"
        self.token = token
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.token:
            self.headers['Bmx-Token'] = self.token
    
    def obtener_serie(self, serie_id, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene una serie de datos de Banxico
        
        Args:
            serie_id: ID de la serie (ej: 'SP74638' para INPC)
            fecha_inicio: Fecha de inicio (formato: YYYY-MM-DD)
            fecha_fin: Fecha de fin (formato: YYYY-MM-DD)
        
        Returns:
            DataFrame con los datos
        """
        url = f"{self.base_url}/series/{serie_id}/datos"
        
        params = {}
        if fecha_inicio:
            params['inicio'] = fecha_inicio
        if fecha_fin:
            params['fin'] = fecha_fin
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'bmx' in data and 'series' in data['bmx']:
                serie = data['bmx']['series'][0]
                datos = serie['datos']
                
                # Convertir a DataFrame
                df = pd.DataFrame(datos)
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['dato'] = pd.to_numeric(df['dato'], errors='coerce')
                
                return df
            else:
                print(f"⚠️  No se encontraron datos para la serie {serie_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al obtener datos: {e}")
            return None
    
    def obtener_inflacion_anual(self, años=5):
        """
        Obtiene datos de inflación anual (INPC)
        
        Args:
            años: Número de años a obtener (default: 5)
        
        Returns:
            DataFrame con inflación anual por año
        """
        # Serie ID para INPC variación anual
        # Nota: Este ID puede cambiar, verificar en el sitio de Banxico
        serie_id = "SP74638"  # INPC General, variación anual
        
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=años*365)
        
        df = self.obtener_serie(serie_id, 
                               fecha_inicio.strftime('%Y-%m-%d'),
                               fecha_fin.strftime('%Y-%m-%d'))
        
        if df is not None:
            # Agrupar por año y obtener el último valor de cada año
            df['año'] = df['fecha'].dt.year
            df_anual = df.groupby('año')['dato'].last().reset_index()
            df_anual.columns = ['Año', 'Inflación (%)']
            return df_anual
        
        return None
    
    def obtener_tipo_cambio(self, años=5):
        """
        Obtiene datos del tipo de cambio peso-dólar
        
        Args:
            años: Número de años a obtener (default: 5)
        
        Returns:
            DataFrame con tipo de cambio por año
        """
        # Serie ID para tipo de cambio peso-dólar
        serie_id = "SF63528"  # Tipo de cambio peso-dólar
        
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=años*365)
        
        df = self.obtener_serie(serie_id,
                               fecha_inicio.strftime('%Y-%m-%d'),
                               fecha_fin.strftime('%Y-%m-%d'))
        
        if df is not None:
            # Agrupar por año y obtener el promedio anual
            df['año'] = df['fecha'].dt.year
            df_anual = df.groupby('año')['dato'].mean().reset_index()
            df_anual.columns = ['Año', 'Tipo de Cambio (Pesos/Dólar)']
            return df_anual
        
        return None
    
    def obtener_tiie_28_dias(self, años=5):
        """
        Obtiene datos de TIIE a 28 días
        
        Args:
            años: Número de años a obtener (default: 5)
        
        Returns:
            DataFrame con TIIE por año
        """
        # Serie ID para TIIE a 28 días
        serie_id = "SF43783"  # TIIE a 28 días
        
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=años*365)
        
        df = self.obtener_serie(serie_id,
                               fecha_inicio.strftime('%Y-%m-%d'),
                               fecha_fin.strftime('%Y-%m-%d'))
        
        if df is not None:
            # Agrupar por año y obtener el promedio anual
            df['año'] = df['fecha'].dt.year
            df_anual = df.groupby('año')['dato'].mean().reset_index()
            df_anual.columns = ['Año', 'TIIE 28 días (%)']
            return df_anual
        
        return None
    
    def obtener_divisas(self, años=5):
        """
        Obtiene datos de divisas internacionales
        
        Args:
            años: Número de años a obtener (default: 5)
        
        Returns:
            DataFrame con divisas por año
        """
        # IDs de series para divisas
        series = {
            'Dólar EUA': 'SF43718',  # Dólar EUA
            'Euro': 'SF46410',       # Euro
            'Yen Japonés': 'SF46406', # Yen japonés
            'Libra Esterlina': 'SF46407', # Libra esterlina
            'Yuan Chino': 'SF46411'   # Yuan chino
        }
        
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=años*365)
        
        resultados = {}
        
        for nombre, serie_id in series.items():
            df = self.obtener_serie(serie_id,
                                   fecha_inicio.strftime('%Y-%m-%d'),
                                   fecha_fin.strftime('%Y-%m-%d'))
            
            if df is not None:
                df['año'] = df['fecha'].dt.year
                df_anual = df.groupby('año')['dato'].mean().reset_index()
                resultados[nombre] = df_anual
        
        # Combinar todos los resultados
        if resultados:
            df_final = None
            for nombre, df in resultados.items():
                if df_final is None:
                    df_final = df.rename(columns={'dato': nombre})
                else:
                    df_final = df_final.merge(
                        df.rename(columns={'dato': nombre}),
                        on='año',
                        how='outer'
                    )
            return df_final.rename(columns={'año': 'Año'})
        
        return None
    
    def generar_cuadro_a(self, años=5):
        """
        Genera el Cuadro A con todos los indicadores principales
        
        Args:
            años: Número de años a obtener (default: 5)
        
        Returns:
            DataFrame con el Cuadro A completo
        """
        print("📊 Obteniendo datos para Cuadro A...")
        
        # Obtener cada indicador
        inflacion = self.obtener_inflacion_anual(años)
        tipo_cambio = self.obtener_tipo_cambio(años)
        tiie = self.obtener_tiie_28_dias(años)
        
        # Combinar todos los datos
        cuadro_a = None
        
        if inflacion is not None:
            cuadro_a = inflacion.copy()
        
        if tipo_cambio is not None:
            if cuadro_a is not None:
                cuadro_a = cuadro_a.merge(
                    tipo_cambio[['Año', 'Tipo de Cambio (Pesos/Dólar)']],
                    on='Año',
                    how='outer'
                )
            else:
                cuadro_a = tipo_cambio.copy()
        
        if tiie is not None:
            if cuadro_a is not None:
                cuadro_a = cuadro_a.merge(
                    tiie[['Año', 'TIIE 28 días (%)']],
                    on='Año',
                    how='outer'
                )
            else:
                cuadro_a = tiie.copy()
        
        if cuadro_a is not None:
            cuadro_a = cuadro_a.sort_values('Año').reset_index(drop=True)
            # Renombrar columnas para que coincidan con el formato del documento
            cuadro_a.columns = [
                'Año',
                'Índice Nacional de Precios al Consumidor (Variación anual %)',
                'Tipo de Cambio Peso-Dólar (Pesos por dólar)',
                'TIIE a 28 días (Tasa de interés % anual)'
            ]
        
        return cuadro_a
    
    def generar_cuadro_b(self, años=5):
        """
        Genera el Cuadro B con divisas internacionales
        
        Args:
            años: Número de años a obtener (default: 5)
        
        Returns:
            DataFrame con el Cuadro B completo
        """
        print("💱 Obteniendo datos para Cuadro B...")
        
        divisas = self.obtener_divisas(años)
        
        if divisas is not None:
            # Renombrar columnas para que coincidan con el formato del documento
            divisas.columns = [
                'Año',
                'Dólar EUA (Pesos por unidad)',
                'Euro (Pesos por unidad)',
                'Yen Japonés (Pesos por unidad)',
                'Libra Esterlina (Pesos por unidad)',
                'Yuan Chino (Pesos por unidad)'
            ]
        
        return divisas
    
    def exportar_a_excel(self, cuadro_a=None, cuadro_b=None, nombre_archivo='datos_banxico.xlsx'):
        """
        Exporta los cuadros a un archivo Excel
        
        Args:
            cuadro_a: DataFrame del Cuadro A
            cuadro_b: DataFrame del Cuadro B
            nombre_archivo: Nombre del archivo Excel
        """
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            if cuadro_a is not None:
                cuadro_a.to_excel(writer, sheet_name='Cuadro A', index=False)
                print(f"✅ Cuadro A exportado a {nombre_archivo}")
            
            if cuadro_b is not None:
                cuadro_b.to_excel(writer, sheet_name='Cuadro B', index=False)
                print(f"✅ Cuadro B exportado a {nombre_archivo}")
        
        print(f"📄 Archivo Excel creado: {nombre_archivo}")


def main():
    """Función principal"""
    print("=" * 60)
    print("OBTENER DATOS DEL BANCO DE MÉXICO")
    print("=" * 60)
    print()
    
    # Nota: Para obtener un token, visita:
    # https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CF107&locale=es
    token = os.getenv('BANXICO_TOKEN', None)
    
    if not token:
        print("⚠️  No se encontró token de API de Banxico.")
        print("   Puedes obtener uno en: https://www.banxico.org.mx/SieInternet/")
        print("   O usar el método manual descrito en el documento.")
        print()
        print("   Continuando sin token (puede haber limitaciones)...")
        print()
    
    # Crear instancia
    banxico = ObtenerDatosBanxico(token=token)
    
    # Obtener datos
    try:
        cuadro_a = banxico.generar_cuadro_a(años=5)
        cuadro_b = banxico.generar_cuadro_b(años=5)
        
        # Mostrar resultados
        if cuadro_a is not None:
            print("\n📊 CUADRO A - Indicadores Económicos Principales")
            print("=" * 60)
            print(cuadro_a.to_string(index=False))
            print()
        else:
            print("⚠️  No se pudieron obtener los datos del Cuadro A")
            print("   Por favor, usa el método manual descrito en el documento.")
        
        if cuadro_b is not None:
            print("\n💱 CUADRO B - Divisas Internacionales")
            print("=" * 60)
            print(cuadro_b.to_string(index=False))
            print()
        else:
            print("⚠️  No se pudieron obtener los datos del Cuadro B")
            print("   Por favor, usa el método manual descrito en el documento.")
        
        # Exportar a Excel
        if cuadro_a is not None or cuadro_b is not None:
            banxico.exportar_a_excel(cuadro_a, cuadro_b, 'datos_banxico.xlsx')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("💡 SUGERENCIA:")
        print("   Si el script no funciona, puedes obtener los datos manualmente:")
        print("   1. Visita las URLs proporcionadas en el documento A1_ADZ.md")
        print("   2. Exporta las series a Excel")
        print("   3. Completa los cuadros manualmente")


if __name__ == "__main__":
    main()







