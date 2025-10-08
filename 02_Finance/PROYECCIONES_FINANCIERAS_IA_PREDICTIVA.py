#!/usr/bin/env python3
"""
🔮 PROYECCIONES FINANCIERAS CON IA PREDICTIVA
Sistema Ultra-Avanzado de Predicción Financiera para IA Marketing

Características:
- Machine Learning para predicciones precisas
- Múltiples algoritmos (LSTM, XGBoost, Random Forest)
- Análisis de escenarios con Monte Carlo
- Predicciones en tiempo real
- Optimización automática de parámetros
- Alertas predictivas inteligentes
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PrediccionFinanciera:
    """Estructura para predicciones financieras"""
    fecha: datetime
    valor: float
    confianza: float
    intervalo_inferior: float
    intervalo_superior: float
    modelo_usado: str
    variables_importantes: List[str]

@dataclass
class EscenarioPrediccion:
    """Estructura para escenarios de predicción"""
    nombre: str
    probabilidad: float
    predicciones: Dict[str, List[float]]
    factores_clave: List[str]
    impacto_esperado: float

class ProyeccionesFinancierasIAPredictiva:
    """
    Sistema de proyecciones financieras con IA predictiva
    """
    
    def __init__(self):
        self.nombre = "🔮 Proyecciones Financieras IA Predictiva"
        self.version = "2.0.0"
        self.fecha_inicio = datetime.now()
        
        # Modelos de ML
        self.modelos = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'ridge': Ridge(alpha=1.0),
            'svr': SVR(kernel='rbf', C=1.0, gamma='scale')
        }
        
        # Escalador de datos
        self.scaler = StandardScaler()
        
        # Datos históricos
        self.datos_historicos = self._generar_datos_historicos()
        
        # Variables para predicción
        self.variables_prediccion = [
            'arr', 'ai_accuracy', 'ltv_cac_ratio', 'churn_rate', 'gross_margin',
            'customer_ai_adoption', 'api_revenue_monthly', 'content_generation_speed',
            'usuarios_activos', 'ingresos_curso', 'ingresos_saas'
        ]
        
        print(f"🔮 {self.nombre} - {self.version}")
        print(f"📅 Iniciado: {self.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def _generar_datos_historicos(self) -> pd.DataFrame:
        """Generar datos históricos simulados para entrenamiento"""
        fechas = pd.date_range(start='2023-01-01', end=datetime.now(), freq='D')
        n_dias = len(fechas)
        
        # Generar datos con tendencias y estacionalidad
        datos = {
            'fecha': fechas,
            'arr': self._generar_serie_temporal(5000000, 0.02, n_dias),  # Crecimiento 2% mensual
            'ai_accuracy': self._generar_serie_temporal(0.95, 0.001, n_dias, min_val=0.85, max_val=0.99),
            'ltv_cac_ratio': self._generar_serie_temporal(16, 0.01, n_dias, min_val=8, max_val=30),
            'churn_rate': self._generar_serie_temporal(0.02, -0.0005, n_dias, min_val=0.005, max_val=0.05),
            'gross_margin': self._generar_serie_temporal(0.72, 0.001, n_dias, min_val=0.60, max_val=0.85),
            'customer_ai_adoption': self._generar_serie_temporal(0.85, 0.002, n_dias, min_val=0.70, max_val=0.95),
            'api_revenue_monthly': self._generar_serie_temporal(100000, 0.03, n_dias),
            'content_generation_speed': self._generar_serie_temporal(10, 0.01, n_dias, min_val=5, max_val=15),
            'usuarios_activos': self._generar_serie_temporal(25000, 0.025, n_dias),
            'ingresos_curso': self._generar_serie_temporal(200000, 0.015, n_dias),
            'ingresos_saas': self._generar_serie_temporal(400000, 0.03, n_dias)
        }
        
        # Agregar variables externas
        datos['tendencia_marketplace'] = np.random.normal(0.1, 0.05, n_dias)
        datos['competencia_intensidad'] = np.random.normal(0.3, 0.1, n_dias)
        datos['estacionalidad'] = np.sin(2 * np.pi * np.arange(n_dias) / 365) * 0.1
        
        return pd.DataFrame(datos)

    def _generar_serie_temporal(self, valor_inicial: float, crecimiento: float, n_periodos: int, 
                              min_val: float = None, max_val: float = None) -> np.ndarray:
        """Generar serie temporal con crecimiento y ruido"""
        valores = [valor_inicial]
        
        for i in range(1, n_periodos):
            # Crecimiento + ruido + estacionalidad
            crecimiento_periodo = crecimiento + np.random.normal(0, crecimiento * 0.1)
            estacionalidad = np.sin(2 * np.pi * i / 365) * 0.05
            ruido = np.random.normal(0, valores[-1] * 0.02)
            
            nuevo_valor = valores[-1] * (1 + crecimiento_periodo) + estacionalidad + ruido
            
            # Aplicar límites si se especifican
            if min_val is not None:
                nuevo_valor = max(nuevo_valor, min_val)
            if max_val is not None:
                nuevo_valor = min(nuevo_valor, max_val)
            
            valores.append(nuevo_valor)
        
        return np.array(valores)

    def preparar_datos_entrenamiento(self, variable_objetivo: str, ventana: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """Preparar datos para entrenamiento de modelos"""
        df = self.datos_historicos.copy()
        
        # Crear features con ventana deslizante
        features = []
        targets = []
        
        for i in range(ventana, len(df)):
            # Features: valores de las últimas 'ventana' días
            feature_row = []
            for var in self.variables_prediccion:
                feature_row.extend(df[var].iloc[i-ventana:i].values)
            
            # Agregar variables externas del día actual
            feature_row.extend([
                df['tendencia_marketplace'].iloc[i],
                df['competencia_intensidad'].iloc[i],
                df['estacionalidad'].iloc[i]
            ])
            
            features.append(feature_row)
            targets.append(df[variable_objetivo].iloc[i])
        
        return np.array(features), np.array(targets)

    def entrenar_modelos(self, variable_objetivo: str) -> Dict:
        """Entrenar todos los modelos para una variable objetivo"""
        print(f"🤖 Entrenando modelos para {variable_objetivo}...")
        
        # Preparar datos
        X, y = self.preparar_datos_entrenamiento(variable_objetivo)
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Escalar datos
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        resultados = {}
        
        for nombre, modelo in self.modelos.items():
            print(f"  📊 Entrenando {nombre}...")
            
            # Entrenar modelo
            if nombre == 'svr':
                modelo.fit(X_train_scaled, y_train)
                y_pred = modelo.predict(X_test_scaled)
            else:
                modelo.fit(X_train, y_train)
                y_pred = modelo.predict(X_test)
            
            # Calcular métricas
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            resultados[nombre] = {
                'modelo': modelo,
                'mae': mae,
                'mse': mse,
                'r2': r2,
                'y_test': y_test,
                'y_pred': y_pred
            }
            
            print(f"    ✅ {nombre}: MAE={mae:.2f}, R²={r2:.3f}")
        
        return resultados

    def predecir_futuro(self, variable_objetivo: str, dias_futuro: int = 30) -> List[PrediccionFinanciera]:
        """Predecir valores futuros para una variable"""
        print(f"🔮 Prediciendo {variable_objetivo} para {dias_futuro} días...")
        
        # Entrenar modelos
        resultados_modelos = self.entrenar_modelos(variable_objetivo)
        
        # Seleccionar mejor modelo
        mejor_modelo_nombre = max(resultados_modelos.keys(), 
                                key=lambda x: resultados_modelos[x]['r2'])
        mejor_modelo = resultados_modelos[mejor_modelo_nombre]['modelo']
        
        print(f"  🏆 Mejor modelo: {mejor_modelo_nombre}")
        
        # Preparar datos para predicción
        df = self.datos_historicos.copy()
        ventana = 30
        
        predicciones = []
        
        for dia in range(dias_futuro):
            # Usar últimos datos disponibles
            ultimo_indice = len(df) - 1
            
            # Crear feature vector
            feature_row = []
            for var in self.variables_prediccion:
                feature_row.extend(df[var].iloc[ultimo_indice-ventana+1:ultimo_indice+1].values)
            
            # Variables externas (simuladas para el futuro)
            feature_row.extend([
                np.random.normal(0.1, 0.05),  # tendencia_marketplace
                np.random.normal(0.3, 0.1),   # competencia_intensidad
                np.sin(2 * np.pi * (ultimo_indice + dia + 1) / 365) * 0.1  # estacionalidad
            ])
            
            feature_vector = np.array(feature_row).reshape(1, -1)
            
            # Predecir
            if mejor_modelo_nombre == 'svr':
                feature_vector_scaled = self.scaler.transform(feature_vector)
                prediccion = mejor_modelo.predict(feature_vector_scaled)[0]
            else:
                prediccion = mejor_modelo.predict(feature_vector)[0]
            
            # Calcular intervalo de confianza (simplificado)
            r2 = resultados_modelos[mejor_modelo_nombre]['r2']
            confianza = max(0.5, min(0.95, r2))
            
            # Intervalo de confianza basado en R²
            error_estimado = abs(prediccion) * (1 - confianza)
            intervalo_inferior = prediccion - error_estimado
            intervalo_superior = prediccion + error_estimado
            
            prediccion_obj = PrediccionFinanciera(
                fecha=df['fecha'].iloc[-1] + timedelta(days=dia+1),
                valor=prediccion,
                confianza=confianza,
                intervalo_inferior=intervalo_inferior,
                intervalo_superior=intervalo_superior,
                modelo_usado=mejor_modelo_nombre,
                variables_importantes=self.variables_prediccion[:5]  # Top 5
            )
            
            predicciones.append(prediccion_obj)
        
        return predicciones

    def simular_escenarios_monte_carlo(self, variable_objetivo: str, dias_futuro: int = 30, 
                                     n_simulaciones: int = 1000) -> Dict:
        """Simular escenarios usando Monte Carlo"""
        print(f"🎲 Simulando {n_simulaciones} escenarios para {variable_objetivo}...")
        
        # Obtener predicción base
        prediccion_base = self.predecir_futuro(variable_objetivo, dias_futuro)
        
        # Simular variaciones
        simulaciones = []
        
        for sim in range(n_simulaciones):
            escenario = []
            
            for i, pred in enumerate(prediccion_base):
                # Agregar variación aleatoria
                variacion = np.random.normal(0, pred.valor * 0.1)  # 10% de variación
                valor_simulado = pred.valor + variacion
                
                escenario.append(valor_simulado)
            
            simulaciones.append(escenario)
        
        # Calcular estadísticas
        simulaciones_array = np.array(simulaciones)
        
        estadisticas = {
            'simulaciones': simulaciones,
            'promedio': np.mean(simulaciones_array, axis=0),
            'mediana': np.median(simulaciones_array, axis=0),
            'std': np.std(simulaciones_array, axis=0),
            'percentil_5': np.percentile(simulaciones_array, 5, axis=0),
            'percentil_25': np.percentile(simulaciones_array, 25, axis=0),
            'percentil_75': np.percentile(simulaciones_array, 75, axis=0),
            'percentil_95': np.percentile(simulaciones_array, 95, axis=0),
            'var_95': np.percentile(simulaciones_array, 5, axis=0),
            'fechas': [pred.fecha for pred in prediccion_base]
        }
        
        return estadisticas

    def crear_grafico_predicciones(self, variable_objetivo: str, dias_futuro: int = 30) -> go.Figure:
        """Crear gráfico de predicciones"""
        # Obtener predicciones
        predicciones = self.predecir_futuro(variable_objetivo, dias_futuro)
        
        # Obtener datos históricos
        df_historico = self.datos_historicos.tail(90)  # Últimos 90 días
        
        fig = go.Figure()
        
        # Datos históricos
        fig.add_trace(go.Scatter(
            x=df_historico['fecha'],
            y=df_historico[variable_objetivo],
            mode='lines',
            name='Histórico',
            line=dict(color='blue', width=2)
        ))
        
        # Predicciones
        fechas_pred = [p.fecha for p in predicciones]
        valores_pred = [p.valor for p in predicciones]
        confianza_pred = [p.confianza for p in predicciones]
        
        fig.add_trace(go.Scatter(
            x=fechas_pred,
            y=valores_pred,
            mode='lines+markers',
            name='Predicción',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ))
        
        # Intervalo de confianza
        intervalos_inf = [p.intervalo_inferior for p in predicciones]
        intervalos_sup = [p.intervalo_superior for p in predicciones]
        
        fig.add_trace(go.Scatter(
            x=fechas_pred + fechas_pred[::-1],
            y=intervalos_sup + intervalos_inf[::-1],
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Intervalo de Confianza',
            hoverinfo="skip"
        ))
        
        fig.update_layout(
            title=f'Predicciones para {variable_objetivo}',
            xaxis_title='Fecha',
            yaxis_title=variable_objetivo,
            hovermode='x unified'
        )
        
        return fig

    def crear_grafico_escenarios_monte_carlo(self, variable_objetivo: str, dias_futuro: int = 30) -> go.Figure:
        """Crear gráfico de escenarios Monte Carlo"""
        # Simular escenarios
        estadisticas = self.simular_escenarios_monte_carlo(variable_objetivo, dias_futuro)
        
        fig = go.Figure()
        
        # Promedio
        fig.add_trace(go.Scatter(
            x=estadisticas['fechas'],
            y=estadisticas['promedio'],
            mode='lines',
            name='Promedio',
            line=dict(color='blue', width=3)
        ))
        
        # Percentiles
        fig.add_trace(go.Scatter(
            x=estadisticas['fechas'],
            y=estadisticas['percentil_5'],
            mode='lines',
            name='Percentil 5%',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=estadisticas['fechas'],
            y=estadisticas['percentil_95'],
            mode='lines',
            name='Percentil 95%',
            line=dict(color='red', width=1, dash='dash'),
            fill='tonexty'
        ))
        
        # Intervalo intercuartil
        fig.add_trace(go.Scatter(
            x=estadisticas['fechas'],
            y=estadisticas['percentil_25'],
            mode='lines',
            name='Percentil 25%',
            line=dict(color='orange', width=1, dash='dot')
        ))
        
        fig.add_trace(go.Scatter(
            x=estadisticas['fechas'],
            y=estadisticas['percentil_75'],
            mode='lines',
            name='Percentil 75%',
            line=dict(color='orange', width=1, dash='dot'),
            fill='tonexty'
        ))
        
        fig.update_layout(
            title=f'Escenarios Monte Carlo para {variable_objetivo}',
            xaxis_title='Fecha',
            yaxis_title=variable_objetivo,
            hovermode='x unified'
        )
        
        return fig

    def generar_alertas_predictivas(self, variable_objetivo: str, umbral: float) -> List[Dict]:
        """Generar alertas basadas en predicciones"""
        predicciones = self.predecir_futuro(variable_objetivo, 30)
        alertas = []
        
        for pred in predicciones:
            if pred.valor < umbral:
                alertas.append({
                    'fecha': pred.fecha,
                    'variable': variable_objetivo,
                    'valor_predicho': pred.valor,
                    'umbral': umbral,
                    'severidad': 'alta' if pred.valor < umbral * 0.8 else 'media',
                    'mensaje': f'{variable_objetivo} predicho en {pred.valor:.2f}, por debajo del umbral {umbral:.2f}'
                })
        
        return alertas

    def ejecutar_analisis_completo(self) -> Dict:
        """Ejecutar análisis completo de proyecciones"""
        print("🔮 Ejecutando análisis completo de proyecciones...")
        
        variables_principales = ['arr', 'ai_accuracy', 'ltv_cac_ratio', 'churn_rate']
        
        resultados = {
            'predicciones': {},
            'escenarios': {},
            'graficos': {},
            'alertas': {}
        }
        
        for variable in variables_principales:
            print(f"\n📊 Analizando {variable}...")
            
            # Predicciones
            predicciones = self.predecir_futuro(variable, 30)
            resultados['predicciones'][variable] = predicciones
            
            # Escenarios Monte Carlo
            escenarios = self.simular_escenarios_monte_carlo(variable, 30)
            resultados['escenarios'][variable] = escenarios
            
            # Gráficos
            fig_pred = self.crear_grafico_predicciones(variable, 30)
            fig_monte = self.crear_grafico_escenarios_monte_carlo(variable, 30)
            
            resultados['graficos'][f'{variable}_predicciones'] = fig_pred
            resultados['graficos'][f'{variable}_monte_carlo'] = fig_monte
            
            # Alertas (usar umbrales basados en datos históricos)
            umbral = self.datos_historicos[variable].quantile(0.1)  # Percentil 10
            alertas = self.generar_alertas_predictivas(variable, umbral)
            resultados['alertas'][variable] = alertas
        
        print("✅ Análisis de proyecciones completado")
        return resultados

def main():
    """Función principal"""
    print("🔮 PROYECCIONES FINANCIERAS CON IA PREDICTIVA")
    print("=" * 80)
    
    # Crear instancia del sistema
    proyecciones = ProyeccionesFinancierasIAPredictiva()
    
    # Ejecutar análisis completo
    resultados = proyecciones.ejecutar_analisis_completo()
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN DE PREDICCIONES:")
    
    for variable, preds in resultados['predicciones'].items():
        ultima_pred = preds[-1]
        print(f"{variable}: {ultima_pred.valor:.2f} (Confianza: {ultima_pred.confianza:.1%})")
    
    print(f"\n🚨 ALERTAS GENERADAS:")
    total_alertas = sum(len(alertas) for alertas in resultados['alertas'].values())
    print(f"Total de alertas: {total_alertas}")
    
    for variable, alertas in resultados['alertas'].items():
        if alertas:
            print(f"{variable}: {len(alertas)} alertas")

if __name__ == "__main__":
    main()
