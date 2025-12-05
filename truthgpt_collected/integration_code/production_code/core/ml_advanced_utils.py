#!/usr/bin/env python3
"""
Utilidades avanzadas para Machine Learning.

Incluye:
- Modelos adicionales (XGBoost, LightGBM, CatBoost)
- Reinforcement Learning
- Optimización de hiperparámetros
- Interpretabilidad de modelos
"""

from typing import Dict, Any, Optional, List, Union
import torch
import numpy as np

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    from captum.attr import IntegratedGradients, GradientShap
    CAPTUM_AVAILABLE = True
except ImportError:
    CAPTUM_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)


def train_xgboost_model(X_train: np.ndarray, y_train: np.ndarray, **kwargs) -> Optional[Any]:
    """
    Entrena un modelo XGBoost.
    
    Args:
        X_train: Features de entrenamiento
        y_train: Labels de entrenamiento
        **kwargs: Parámetros adicionales para XGBoost
    
    Returns:
        Modelo entrenado o None
    """
    if not XGBOOST_AVAILABLE:
        logger.warning("XGBoost no disponible")
        return None
    
    def _train_xgboost():
        params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            **kwargs
        }
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)
        return model
    
    result, error = safe_execute(_train_xgboost, default_value=None, log_errors=True)
    if result:
        logger.info("Modelo XGBoost entrenado")
    elif error:
        logger.error("Error entrenando XGBoost", error=str(error))
    return result


def train_lightgbm_model(X_train: np.ndarray, y_train: np.ndarray, **kwargs) -> Optional[Any]:
    """
    Entrena un modelo LightGBM.
    
    Args:
        X_train: Features de entrenamiento
        y_train: Labels de entrenamiento
        **kwargs: Parámetros adicionales
    
    Returns:
        Modelo entrenado o None
    """
    if not LIGHTGBM_AVAILABLE:
        logger.warning("LightGBM no disponible")
        return None
    
    def _train_lightgbm():
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            **kwargs
        }
        train_data = lgb.Dataset(X_train, label=y_train)
        model = lgb.train(params, train_data, num_boost_round=100)
        return model
    
    result, error = safe_execute(_train_lightgbm, default_value=None, log_errors=True)
    if result:
        logger.info("Modelo LightGBM entrenado")
    elif error:
        logger.error("Error entrenando LightGBM", error=str(error))
    return result


def explain_model_with_shap(model: Any, X: np.ndarray, feature_names: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Explica un modelo usando SHAP.
    
    Args:
        model: Modelo a explicar
        X: Datos de ejemplo
        feature_names: Nombres de las features
    
    Returns:
        Explicaciones SHAP o None
    """
    if not SHAP_AVAILABLE:
        logger.warning("SHAP no disponible")
        return None
    
    def _explain_shap():
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
        return {
            'shap_values': shap_values.values,
            'base_values': shap_values.base_values,
            'feature_names': feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        }
    
    result, error = safe_execute(_explain_shap, default_value=None, log_errors=True)
    if error:
        logger.error("Error explicando modelo con SHAP", error=str(error))
    return result


def explain_pytorch_model(model: torch.nn.Module, input_tensor: torch.Tensor, target: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Explica un modelo PyTorch usando Captum.
    
    Args:
        model: Modelo PyTorch
        input_tensor: Tensor de entrada
        target: Clase objetivo (opcional)
    
    Returns:
        Atribuciones o None
    """
    if not CAPTUM_AVAILABLE:
        logger.warning("Captum no disponible")
        return None
    
    def _explain_captum():
        model.eval()
        ig = IntegratedGradients(model)
        
        if target is None:
            attributions = ig.attribute(input_tensor)
        else:
            attributions = ig.attribute(input_tensor, target=target)
        
        return {
            'attributions': attributions.detach().cpu().numpy(),
            'sum': attributions.sum().item()
        }
    
    result, error = safe_execute(_explain_captum, default_value=None, log_errors=True)
    if error:
        logger.error("Error explicando modelo PyTorch", error=str(error))
    return result


def optimize_hyperparameters_with_optuna(
    objective_func: Any,
    n_trials: int = 100,
    direction: str = 'minimize'
) -> Optional[Dict[str, Any]]:
    """
    Optimiza hiperparámetros usando Optuna.
    
    Args:
        objective_func: Función objetivo
        n_trials: Número de trials
        direction: Dirección de optimización ('minimize' o 'maximize')
    
    Returns:
        Mejores parámetros o None
    """
    if not OPTUNA_AVAILABLE:
        logger.warning("Optuna no disponible")
        return None
    
    def _optimize_optuna():
        study = optuna.create_study(direction=direction)
        study.optimize(objective_func, n_trials=n_trials)
        return {
            'best_params': study.best_params,
            'best_value': study.best_value,
            'n_trials': len(study.trials)
        }
    
    result, error = safe_execute(_optimize_optuna, default_value=None, log_errors=True)
    if error:
        logger.error("Error optimizando hiperparámetros", error=str(error))
    return result

