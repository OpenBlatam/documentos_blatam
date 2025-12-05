#!/usr/bin/env python3
"""
Utilidades para procesamiento de datos.

Incluye:
- Procesamiento con pandas
- Análisis estadístico con scipy
- Preprocesamiento con scikit-learn
- Visualización
"""

from typing import Dict, Any, Optional, List, Union, Tuple
import torch
import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from scipy import stats
    from scipy.stats import normaltest, shapiro
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute

logger = setup_logger(__name__)


def tensor_to_dataframe(tensor: torch.Tensor, columns: Optional[List[str]] = None) -> Any:
    """
    Convierte un tensor de PyTorch a DataFrame de pandas.
    
    Args:
        tensor: Tensor a convertir
        columns: Nombres de columnas (opcional)
    
    Returns:
        DataFrame de pandas
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas no está instalado. Instala con: pip install pandas")
    
    if tensor.requires_grad:
        tensor = tensor.detach()
    
    numpy_array = tensor.cpu().numpy()
    
    if len(numpy_array.shape) == 1:
        numpy_array = numpy_array.reshape(-1, 1)
    
    return pd.DataFrame(numpy_array, columns=columns)


def dataframe_to_tensor(df: Any, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    """
    Convierte un DataFrame de pandas a tensor de PyTorch.
    
    Args:
        df: DataFrame a convertir
        dtype: Tipo de dato del tensor
    
    Returns:
        Tensor de PyTorch
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas no está instalado")
    
    numpy_array = df.values
    return torch.from_numpy(numpy_array).to(dtype)


def normalize_tensor(tensor: torch.Tensor, method: str = "standard") -> Tuple[torch.Tensor, Dict[str, Any]]:
    """
    Normaliza un tensor usando diferentes métodos.
    
    Args:
        tensor: Tensor a normalizar
        method: Método de normalización ("standard", "minmax", "robust")
    
    Returns:
        Tuple (tensor_normalizado, estadísticas)
    """
    if not SKLEARN_AVAILABLE:
        logger.warning("scikit-learn no disponible, usando normalización manual")
        if method == "standard":
            mean = tensor.mean()
            std = tensor.std()
            normalized = (tensor - mean) / (std + 1e-8)
            stats = {"mean": mean.item(), "std": std.item()}
        elif method == "minmax":
            min_val = tensor.min()
            max_val = tensor.max()
            normalized = (tensor - min_val) / (max_val - min_val + 1e-8)
            stats = {"min": min_val.item(), "max": max_val.item()}
        else:
            normalized = tensor
            stats = {}
        return normalized, stats
    
    numpy_array = tensor.detach().cpu().numpy()
    
    if method == "standard":
        scaler = StandardScaler()
    elif method == "minmax":
        scaler = MinMaxScaler()
    elif method == "robust":
        scaler = RobustScaler()
    else:
        raise ValueError(f"Método de normalización no soportado: {method}")
    
    normalized_array = scaler.fit_transform(numpy_array.reshape(-1, 1)).reshape(numpy_array.shape)
    normalized_tensor = torch.from_numpy(normalized_array).to(tensor.device).to(tensor.dtype)
    
    stats = {
        "mean": scaler.mean_[0] if hasattr(scaler, 'mean_') else None,
        "std": scaler.scale_[0] if hasattr(scaler, 'scale_') else None,
        "min": scaler.data_min_[0] if hasattr(scaler, 'data_min_') else None,
        "max": scaler.data_max_[0] if hasattr(scaler, 'data_max_') else None,
    }
    
    return normalized_tensor, stats


def statistical_analysis(tensor: torch.Tensor) -> Dict[str, Any]:
    """
    Realiza análisis estadístico de un tensor.
    
    Args:
        tensor: Tensor a analizar
    
    Returns:
        Diccionario con estadísticas
    """
    stats_dict = {
        "mean": tensor.mean().item(),
        "std": tensor.std().item(),
        "min": tensor.min().item(),
        "max": tensor.max().item(),
        "median": tensor.median().item(),
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
    }
    
    if SCIPY_AVAILABLE:
        numpy_array = tensor.detach().cpu().numpy().flatten()
        
        def _run_shapiro_test():
            shapiro_stat, shapiro_p = shapiro(numpy_array[:5000])  # Limitamos para performance
            return {
                "shapiro_stat": shapiro_stat,
                "shapiro_p": shapiro_p,
                "is_normal": shapiro_p > 0.05
            }
        
        result, error = safe_execute(_run_shapiro_test, default_value=None, log_errors=False)
        if result:
            stats_dict.update(result)
        elif error:
            logger.warning("Error en test de normalidad", error=str(error))
    
    return stats_dict


def plot_tensor_distribution(tensor: torch.Tensor, title: str = "Distribution", save_path: Optional[str] = None):
    """
    Visualiza la distribución de un tensor.
    
    Args:
        tensor: Tensor a visualizar
        title: Título del gráfico
        save_path: Ruta donde guardar el gráfico (opcional)
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib no disponible, no se puede visualizar")
        return
    
    numpy_array = tensor.detach().cpu().numpy().flatten()
    
    plt.figure(figsize=(10, 6))
    plt.hist(numpy_array, bins=50, alpha=0.7, edgecolor='black')
    plt.title(title)
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info("Gráfico guardado", path=save_path)
    else:
        plt.show()
    
    plt.close()


def plot_interactive_tensor(tensor: torch.Tensor, title: str = "Interactive Plot", save_path: Optional[str] = None):
    """
    Crea una visualización interactiva de un tensor usando Plotly.
    
    Args:
        tensor: Tensor a visualizar
        title: Título del gráfico
        save_path: Ruta donde guardar el gráfico HTML (opcional)
    """
    if not PLOTLY_AVAILABLE:
        logger.warning("plotly no disponible, usando matplotlib")
        plot_tensor_distribution(tensor, title, save_path)
        return
    
    numpy_array = tensor.detach().cpu().numpy().flatten()
    
    fig = go.Figure(data=[go.Histogram(x=numpy_array, nbinsx=50)])
    fig.update_layout(
        title=title,
        xaxis_title="Value",
        yaxis_title="Frequency",
        template="plotly_white"
    )
    
    if save_path:
        fig.write_html(save_path)
        logger.info("Gráfico interactivo guardado", path=save_path)
    else:
        fig.show()


def train_val_split(
    data: torch.Tensor,
    labels: Optional[torch.Tensor] = None,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[torch.Tensor, ...]:
    """
    Divide datos en entrenamiento y validación.
    
    Args:
        data: Datos a dividir
        labels: Etiquetas (opcional)
        test_size: Proporción de datos de test
        random_state: Semilla aleatoria
    
    Returns:
        Tupla con datos divididos
    """
    if not SKLEARN_AVAILABLE:
        indices = torch.randperm(data.shape[0])
        split_idx = int(data.shape[0] * (1 - test_size))
        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]
        
        if labels is not None:
            return data[train_indices], data[val_indices], labels[train_indices], labels[val_indices]
        return data[train_indices], data[val_indices]
    
    numpy_data = data.detach().cpu().numpy()
    
    if labels is not None:
        numpy_labels = labels.detach().cpu().numpy()
        X_train, X_val, y_train, y_val = train_test_split(
            numpy_data, numpy_labels, test_size=test_size, random_state=random_state
        )
        return (
            torch.from_numpy(X_train).to(data.device),
            torch.from_numpy(X_val).to(data.device),
            torch.from_numpy(y_train).to(labels.device),
            torch.from_numpy(y_val).to(labels.device)
        )
    else:
        X_train, X_val = train_test_split(numpy_data, test_size=test_size, random_state=random_state)
        return (
            torch.from_numpy(X_train).to(data.device),
            torch.from_numpy(X_val).to(data.device)
        )

