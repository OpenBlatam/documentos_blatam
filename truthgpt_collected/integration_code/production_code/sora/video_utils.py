#!/usr/bin/env python3
"""
Video Utilities - Utilidades para Procesamiento y Exportación de Video
======================================================================

Utilidades para:
- Exportar videos a diferentes formatos
- Procesar y normalizar videos
- Conversión de formatos
- Visualización
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Union, List
from pathlib import Path
import warnings

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    warnings.warn("OpenCV no disponible, algunas funciones estarán limitadas")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    warnings.warn("Pillow no disponible, algunas funciones estarán limitadas")


def normalize_video(video: torch.Tensor, method: str = "tanh") -> torch.Tensor:
    """
    Normaliza video a rango [0, 1] o [-1, 1].
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        method: Método de normalización ("tanh", "sigmoid", "minmax")
    
    Returns:
        Video normalizado
    """
    if method == "tanh":
        # Asume que el video está en rango [-1, 1] y lo convierte a [0, 1]
        return (video + 1.0) / 2.0
    elif method == "sigmoid":
        return torch.sigmoid(video)
    elif method == "minmax":
        # Normalización min-max
        min_val = video.min()
        max_val = video.max()
        if max_val > min_val:
            return (video - min_val) / (max_val - min_val)
        return video
    else:
        raise ValueError(f"Método de normalización desconocido: {method}")


def denormalize_video(video: torch.Tensor, method: str = "tanh") -> torch.Tensor:
    """
    Desnormaliza video de [0, 1] a [-1, 1] o rango original.
    
    Args:
        video: [batch, frames, channels, height, width] - Video normalizado
        method: Método de desnormalización ("tanh", "sigmoid", "minmax")
    
    Returns:
        Video desnormalizado
    """
    if method == "tanh":
        return video * 2.0 - 1.0
    elif method == "sigmoid":
        return torch.logit(video.clamp(1e-7, 1 - 1e-7))
    elif method == "minmax":
        # Asume rango [0, 1], mantener igual
        return video
    else:
        raise ValueError(f"Método de desnormalización desconocido: {method}")


def video_to_numpy(video: torch.Tensor) -> np.ndarray:
    """
    Convierte video tensor a numpy array.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
    
    Returns:
        [batch, frames, height, width, channels] - Numpy array en formato uint8
    """
    # Normalizar a [0, 1]
    if video.min() < 0:
        video = normalize_video(video, method="tanh")
    
    # Convertir a numpy y uint8
    video_np = video.detach().cpu().numpy()
    video_np = np.clip(video_np, 0, 1)
    video_np = (video_np * 255).astype(np.uint8)
    
    # Reordenar: [B, T, C, H, W] -> [B, T, H, W, C]
    if video_np.ndim == 5:
        video_np = video_np.transpose(0, 1, 3, 4, 2)
    
    return video_np


def save_video_frames(
    video: torch.Tensor,
    output_dir: Union[str, Path],
    prefix: str = "frame",
    format: str = "png"
) -> List[Path]:
    """
    Guarda frames individuales del video.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        output_dir: Directorio de salida
        prefix: Prefijo para nombres de archivo
        format: Formato de imagen ("png", "jpg")
    
    Returns:
        Lista de paths de archivos guardados
    """
    if not PIL_AVAILABLE:
        raise ImportError("Pillow requerido para guardar frames")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_np = video_to_numpy(video)
    saved_paths = []
    
    batch_size, num_frames = video_np.shape[0], video_np.shape[1]
    
    for b in range(batch_size):
        for f in range(num_frames):
            frame = video_np[b, f]
            frame_path = output_dir / f"{prefix}_b{b:03d}_f{f:04d}.{format}"
            
            Image.fromarray(frame).save(frame_path)
            saved_paths.append(frame_path)
    
    return saved_paths


def save_video_opencv(
    video: torch.Tensor,
    output_path: Union[str, Path],
    fps: int = 24,
    codec: str = "mp4v"
) -> bool:
    """
    Guarda video usando OpenCV.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        output_path: Path de salida
        fps: Frames por segundo
        codec: Codec de video (ej: "mp4v", "XVID")
    
    Returns:
        True si se guardó exitosamente
    """
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV requerido para guardar video")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    video_np = video_to_numpy(video)
    
    # Tomar solo el primer batch si hay múltiples
    if video_np.ndim == 5:
        video_np = video_np[0]  # [frames, height, width, channels]
    
    height, width = video_np.shape[1], video_np.shape[2]
    
    # Convertir BGR si es RGB
    if video_np.shape[-1] == 3:
        video_np = cv2.cvtColor(video_np, cv2.COLOR_RGB2BGR)
    
    # Crear VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    try:
        for frame in video_np:
            out.write(frame)
        return True
    finally:
        out.release()


def create_video_gif(
    video: torch.Tensor,
    output_path: Union[str, Path],
    duration: Optional[float] = None,
    fps: int = 24
) -> bool:
    """
    Crea GIF animado desde video.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        output_path: Path de salida
        duration: Duración por frame en segundos (None = calcular desde fps)
        fps: Frames por segundo (usado si duration es None)
    
    Returns:
        True si se guardó exitosamente
    """
    if not PIL_AVAILABLE:
        raise ImportError("Pillow requerido para crear GIF")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    video_np = video_to_numpy(video)
    
    # Tomar solo el primer batch
    if video_np.ndim == 5:
        video_np = video_np[0]  # [frames, height, width, channels]
    
    # Convertir a PIL Images
    frames = [Image.fromarray(frame) for frame in video_np]
    
    # Calcular duration
    if duration is None:
        duration = 1000 / fps  # en milisegundos
    
    # Guardar GIF
    frames[0].save(
        str(output_path),
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0
    )
    
    return True


def resize_video(
    video: torch.Tensor,
    size: Tuple[int, int],
    mode: str = "bilinear"
) -> torch.Tensor:
    """
    Redimensiona video.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        size: (height, width) nueva resolución
        mode: Modo de interpolación ("bilinear", "nearest", "bicubic")
    
    Returns:
        Video redimensionado
    """
    B, T, C, H, W = video.shape
    new_H, new_W = size
    
    # Reshape para procesar todos los frames juntos
    video_reshaped = video.view(B * T, C, H, W)
    
    # Redimensionar
    resized = F.interpolate(
        video_reshaped,
        size=(new_H, new_W),
        mode=mode,
        align_corners=False if mode != "nearest" else None
    )
    
    # Reshape de vuelta
    resized = resized.view(B, T, C, new_H, new_W)
    
    return resized


def extract_frame(video: torch.Tensor, frame_idx: int) -> torch.Tensor:
    """
    Extrae un frame específico del video.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        frame_idx: Índice del frame a extraer
    
    Returns:
        [batch, channels, height, width] - Frame extraído
    """
    if frame_idx < 0 or frame_idx >= video.shape[1]:
        raise ValueError(f"frame_idx {frame_idx} fuera de rango [0, {video.shape[1]})")
    
    return video[:, frame_idx]


def concatenate_videos(videos: List[torch.Tensor], dim: int = 1) -> torch.Tensor:
    """
    Concatena múltiples videos.
    
    Args:
        videos: Lista de videos [batch, frames, channels, height, width]
        dim: Dimensión a lo largo de la cual concatenar (1 para frames)
    
    Returns:
        Video concatenado
    """
    return torch.cat(videos, dim=dim)


def add_temporal_noise(
    video: torch.Tensor,
    noise_strength: float = 0.1
) -> torch.Tensor:
    """
    Agrega ruido temporal al video.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        noise_strength: Fuerza del ruido
    
    Returns:
        Video con ruido agregado
    """
    noise = torch.randn_like(video) * noise_strength
    return video + noise


def temporal_smooth(video: torch.Tensor, kernel_size: int = 3) -> torch.Tensor:
    """
    Suaviza temporalmente el video usando promedio móvil.
    
    Args:
        video: [batch, frames, channels, height, width] - Video tensor
        kernel_size: Tamaño del kernel de suavizado
    
    Returns:
        Video suavizado
    """
    B, T, C, H, W = video.shape
    
    # Crear kernel de promedio
    kernel = torch.ones(1, 1, kernel_size, 1, 1, device=video.device) / kernel_size
    
    # Aplicar convolución 1D temporal
    video_padded = F.pad(video, (0, 0, 0, 0, kernel_size // 2, kernel_size // 2), mode='replicate')
    video_reshaped = video_padded.view(B, 1, T + kernel_size - 1, C, H, W)
    
    smoothed = F.conv3d(
        video_reshaped,
        kernel,
        padding=0
    )
    
    return smoothed.view(B, T, C, H, W)

